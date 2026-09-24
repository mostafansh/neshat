// The reading screen: shows one case, takes the reader's first read, shows the AI suggestion
// the server sends back, then takes the final read. The page templates/reading/read.html
// holds the markup; docs/reading-api.md is the contract with the server.
//
// Rules this file keeps (see CLAUDE.md):
// - The page never knows the AI suggestion before the server has stored the first read. It
//   arrives only in the answer to "Lock my read" (rule 1).
// - Every AI suggestion is drawn the same way, with no variant (rule 6).
// - The venue is plain HTTP, so no crypto.randomUUID, crypto.subtle, clipboard, wake lock or
//   service worker. Nothing is loaded from another server (rule 7).
// - The image address never goes into the page. The bytes are drawn on a canvas, so a long
//   press cannot offer "Download image".

const reader = document.getElementById('reader');
const API = reader.dataset.api;            // for example "/api/s/wrist-fracture/"
const DONE_URL = reader.dataset.doneUrl;   // the "all cases finished" page
const MAX_ZOOM = 8;         // times the fit size; large images may go further (see zoomAt)
const MAX_PIXEL_SIZE = 4;   // at most zoom, one image pixel may cover at least 4 x 4 screen pixels

const $ = (id) => document.getElementById(id);
const el = {
  progress: $('progress'), frame: $('frame'), canvas: $('view'), aiMark: $('ai-mark'),
  status: $('status'), first: $('first'), lock: $('lock'),
  firstAnswer: $('first-answer'), firstConfidence: $('first-confidence'),
  aiPanel: $('ai-panel'), aiLabel: $('ai-label'), aiConfidence: $('ai-confidence'),
  aiSource: $('ai-source'), final: $('final'), submitFinal: $('submit-final'),
  finalAnswer: $('final-answer'), finalConfidence: $('final-confidence'),
  reloadRow: $('reload-row'), reload: $('reload'),
};

let task = null;        // the case on screen: the JSON from GET current
let submissionId = '';  // the one-time code for the next POST (a retry reuses it)
let startedAt = 0;      // when the image was drawn, or when the AI was shown (for elapsed_ms)
let busy = false;       // a request is in flight: buttons stay disabled
let stopped = false;    // the server refused a request: wait for a reload


// ---- 1. Talking to the server ------------------------------------------------------------

// A 4xx answer. Trying again will not help, so the page shows the server's words and stops.
class Refused extends Error {}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Django checks this token on every POST. The cookie is set by {% csrf_token %} in the page;
// the hidden input it writes is the fallback.
function csrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  if (match) return decodeURIComponent(match[1]);
  const input = reader.querySelector('input[name="csrfmiddlewaretoken"]');
  return input ? input.value : '';
}

// Sends one request and reads its body. Venue Wi-Fi drops out, so a network error, a
// time-out or a 5xx answer is retried after 1, 2, 4, 8, 15, 15... seconds. The retry sends
// the exact same request, with the same submission_id, so the server stores the answer once.
// Each retry allows twice as long (up to 4 minutes), so a slow but working link can still
// finish a large image: a new try starts the download from zero.
async function request(url, options, readBody, timeoutMs = 20000) {
  let wait = 1000;
  for (;;) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let res = null;
    try {
      res = await fetch(url, { ...options, credentials: 'same-origin', signal: controller.signal });
      if (res.status < 500) {
        if (!res.ok) throw new Refused(await refusalText(res));
        const body = await readBody(res);
        if (el.status.dataset.kind === 'warn') showStatus('');  // the connection is back
        return body;
      }
    } catch (err) {
      if (err instanceof Refused) throw err;
      // Otherwise it was a network error or a time-out: try again below.
    } finally {
      clearTimeout(timer);
    }
    // A 5xx answer means the connection works but the server failed: say so, so nobody
    // looks for the fault in the Wi-Fi. data/errors.log on the laptop has the details.
    const serverFault = res && res.status >= 500;
    showStatus(serverFault ? 'The server had a problem. Trying again…' : 'Connection lost. Trying again…', 'warn');
    await sleep(wait);
    wait = Math.min(wait * 2, 15000);
    timeoutMs = Math.min(timeoutMs * 2, 240000);
  }
}

async function refusalText(res) {
  try {
    const data = await res.json();
    if (data && data.error) return data.error;
  } catch { /* not JSON, for example Django's own 403 page */ }
  return `The server refused this request (error ${res.status}).`;
}

async function readJson(res) {
  // A sign-in page instead of data means the session has ended.
  if (!(res.headers.get('Content-Type') || '').includes('application/json')) {
    throw new Refused('Your session has ended. Reload the page and sign in again.');
  }
  return res.json();
}

function getJson(url) {
  return request(url, { cache: 'no-store' }, readJson);
}

// The body is turned into text once, so every retry sends the same bytes.
function postJson(url, body) {
  const options = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
    body: JSON.stringify(body),
  };
  return request(url, options, readJson);
}

// kind: '' (plain), 'warn' (connection trouble) or 'stop' (refused).
function showStatus(text, kind = '') {
  el.status.textContent = text;
  el.status.className = kind ? `notice notice-${kind}` : 'muted';
  el.status.dataset.kind = kind;
}


// ---- 2. Images: download, decode, keep in memory -----------------------------------------

let picture = null;   // the decoded image of the case on screen
let upcoming = null;  // { url, promise }: the next case's image, loading or ready

// Turns PNG bytes into something a canvas can draw, without an address in the page.
async function decode(blob) {
  if (window.createImageBitmap) {
    try { return await createImageBitmap(blob); } catch { /* older Safari: fall back below */ }
  }
  const objectUrl = URL.createObjectURL(blob);
  try {
    const img = new Image();
    img.src = objectUrl;
    await img.decode();
    return img;
  } finally {
    URL.revokeObjectURL(objectUrl);  // the decoded image stays usable; the address goes
  }
}

// Frees the memory of an image that is no longer needed (phones have little to spare).
function release(pic) {
  if (pic && pic.close) pic.close();
}

// Loads the next case's image while the reader works on this one. One try only: if it
// fails, the next case downloads the image again when it starts.
function prefetch(url) {
  if (upcoming && upcoming.url === url) return;
  if (upcoming) upcoming.promise.then(release, () => {});
  upcoming = null;
  if (!url) return;
  const controller = new AbortController();
  setTimeout(() => controller.abort(), 60000);  // a stalled download must not block the next case
  const promise = fetch(url, { credentials: 'same-origin', signal: controller.signal })
    .then((res) => { if (!res.ok) throw new Error(`prefetch ${res.status}`); return res.blob(); })
    .then(decode);
  promise.catch(() => {});  // a failed prefetch is not an error on screen
  upcoming = { url, promise };
}

// The image for a case: the prefetched copy if there is one, else a fresh download.
async function pictureFor(url) {
  if (upcoming && upcoming.url === url) {
    const { promise } = upcoming;
    upcoming = null;
    try { return await promise; } catch { /* the prefetch failed: download it below */ }
  }
  const blob = await request(url, {}, (res) => res.blob(), 30000);
  return decode(blob);
}


// ---- 3. Drawing: fit, zoom and pan ------------------------------------------------------
// Everything is stored in image pixels (the image's own size). One transform maps image
// pixels to canvas pixels: canvas = image * scale + (x, y). The AI box uses the same
// transform as the image, so it stays on the same spot at every zoom and pan.

const ctx = el.canvas.getContext('2d');
const view = { fit: 1, zoom: 1, x: 0, y: 0 };  // fit: whole image in the frame; zoom: 1 or more
let aiBox = null;                               // [x, y, width, height] in image pixels
let drawPending = false;

const picWidth = () => picture.naturalWidth || picture.width;
const picHeight = () => picture.naturalHeight || picture.height;
const scale = () => view.fit * view.zoom;
const toImage = (px, py) => ({ x: (px - view.x) / scale(), y: (py - view.y) / scale() });
// Canvas pixels per CSS pixel (2 or 3 on most phones).
const pixelRatio = () => el.canvas.width / el.canvas.getBoundingClientRect().width || 1;

// Like CSS object-fit: contain. The whole image shows, centred, nothing cropped.
function fitScale() {
  return Math.min(el.canvas.width / picWidth(), el.canvas.height / picHeight());
}

function resetView() {
  view.fit = fitScale();
  view.zoom = 1;
  clampView();
  draw();
}

// Keeps the image in the frame: centred along an axis where it is smaller than the frame,
// and with no empty gap at the edge along an axis where it is larger.
function clampView() {
  view.x = clampAxis(view.x, el.canvas.width, picWidth() * scale());
  view.y = clampAxis(view.y, el.canvas.height, picHeight() * scale());
}
function clampAxis(offset, room, size) {
  if (size <= room) return (room - size) / 2;
  return Math.min(0, Math.max(room - size, offset));
}

// Zooms by `factor` and keeps the image point under (px, py) in the same place. The limit
// is 8 times the fit size, or more for a large image: a full-size radiograph (2000-3000 px
// wide) must still zoom until one image pixel covers 4 x 4 screen pixels.
function zoomAt(px, py, factor) {
  const anchor = toImage(px, py);
  const maxZoom = Math.max(MAX_ZOOM, MAX_PIXEL_SIZE * pixelRatio() / view.fit);
  view.zoom = Math.min(maxZoom, Math.max(1, view.zoom * factor));
  view.x = px - anchor.x * scale();
  view.y = py - anchor.y * scale();
  clampView();
  requestDraw();
}

function panBy(dx, dy) {
  view.x += dx;
  view.y += dy;
  clampView();
  requestDraw();
}

// The canvas has as many pixels as the screen shows (devicePixelRatio), so the image is
// sharp on a phone. Runs on every size change, including turning the phone. It keeps the
// zoom and the image point in the middle of the frame.
function resizeCanvas() {
  const box = el.canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(1, Math.round(box.width * ratio));
  const height = Math.max(1, Math.round(box.height * ratio));
  if (width === el.canvas.width && height === el.canvas.height) return;
  const centre = picture ? toImage(el.canvas.width / 2, el.canvas.height / 2) : null;
  el.canvas.width = width;   // this also clears the canvas
  el.canvas.height = height;
  if (!picture) return;
  view.fit = fitScale();
  view.x = width / 2 - centre.x * scale();
  view.y = height / 2 - centre.y * scale();
  clampView();
  draw();
}

// Many pointer moves arrive per screen refresh; draw once per refresh.
function requestDraw() {
  if (drawPending) return;
  drawPending = true;
  requestAnimationFrame(() => { drawPending = false; draw(); });
}

function draw() {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, el.canvas.width, el.canvas.height);  // the black frame shows through
  if (!picture) return;
  const s = scale();
  ctx.setTransform(s, 0, 0, s, view.x, view.y);
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(picture, 0, 0);
  if (aiBox) drawAiBox(s);
}

// The AI mark: a dashed line in --ai over a solid black line (--viewport), so it shows on
// bone and on air (docs/style.md). Colours come from the frame, which is dark in every
// theme. Line widths are divided by the scale, so they stay 2 and 4 screen pixels thick.
function drawAiBox(s) {
  const colours = getComputedStyle(el.frame);
  const px = pixelRatio() / s;  // one CSS pixel, in image pixels
  const [x, y, w, h] = aiBox;
  ctx.setLineDash([]);
  ctx.lineWidth = 4 * px;
  ctx.strokeStyle = colours.getPropertyValue('--viewport').trim();
  ctx.strokeRect(x, y, w, h);
  ctx.setLineDash([6 * px, 4 * px]);
  ctx.lineWidth = 2 * px;
  ctx.strokeStyle = colours.getPropertyValue('--ai').trim();
  ctx.strokeRect(x, y, w, h);
}


// ---- 4. Gestures: drag, pinch, wheel, double-tap -----------------------------------------
// Pointer Events cover mouse, finger and pen with one set of handlers.

const pointers = new Map();  // pointerId -> { x, y, startX, startY, time }
let twoFingers = false;      // this gesture used two fingers, so it is not a tap
let lastTap = null;

function canvasPoint(event) {
  const box = el.canvas.getBoundingClientRect();
  const ratio = pixelRatio();
  return { x: (event.clientX - box.left) * ratio, y: (event.clientY - box.top) * ratio };
}

function pinch() {
  const [a, b] = [...pointers.values()];
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, d: Math.hypot(a.x - b.x, a.y - b.y) };
}

function onPointerDown(event) {
  if (!picture) return;
  const p = canvasPoint(event);
  pointers.set(event.pointerId, { ...p, startX: p.x, startY: p.y, time: event.timeStamp });
  if (pointers.size > 1) twoFingers = true;
  // Keep getting moves even when the finger leaves the canvas. Fails for synthetic events.
  try { el.canvas.setPointerCapture(event.pointerId); } catch { /* nothing to capture */ }
  el.canvas.classList.add('is-dragging');
}

function onPointerMove(event) {
  const p = pointers.get(event.pointerId);
  if (!p) return;
  const now = canvasPoint(event);
  if (pointers.size === 1) {
    panBy(now.x - p.x, now.y - p.y);
  } else if (pointers.size === 2) {
    // Pan with the midpoint of the two fingers and zoom with their distance.
    const before = pinch();
    p.x = now.x;
    p.y = now.y;
    const after = pinch();
    panBy(after.x - before.x, after.y - before.y);
    if (before.d > 0) zoomAt(after.x, after.y, after.d / before.d);
  }
  p.x = now.x;
  p.y = now.y;
}

function onPointerEnd(event) {
  const p = pointers.get(event.pointerId);
  if (!p) return;
  pointers.delete(event.pointerId);
  if (event.type === 'pointerup' && isTap(p, event)) onTap(p, event.timeStamp);
  if (pointers.size === 0) {
    twoFingers = false;
    el.canvas.classList.remove('is-dragging');
  }
}

// A tap: one finger, a short touch, almost no movement (10 CSS px).
function isTap(p, event) {
  const moved = Math.hypot(p.x - p.startX, p.y - p.startY);
  return !twoFingers && moved < 10 * pixelRatio() && event.timeStamp - p.time < 300;
}

// Two taps close in time and place reset the view (double-tap or double-click).
function onTap(p, time) {
  const near = lastTap && Math.hypot(p.x - lastTap.x, p.y - lastTap.y) < 30 * pixelRatio();
  if (near && time - lastTap.time < 350) {
    lastTap = null;
    resetView();
  } else {
    lastTap = { x: p.x, y: p.y, time };
  }
}

function onWheel(event) {
  if (!picture) return;
  event.preventDefault();  // zoom the image, not scroll the page
  const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? 400 : 1;  // lines, pages
  const p = canvasPoint(event);
  zoomAt(p.x, p.y, Math.exp(-event.deltaY * unit * 0.002));
}

el.canvas.addEventListener('pointerdown', onPointerDown);
el.canvas.addEventListener('pointermove', onPointerMove);
el.canvas.addEventListener('pointerup', onPointerEnd);
el.canvas.addEventListener('pointercancel', onPointerEnd);
el.canvas.addEventListener('wheel', onWheel, { passive: false });
// No long-press menu (no "Save", "Share" or "Search image") and no iPhone page zoom.
const block = (event) => event.preventDefault();
for (const type of ['contextmenu', 'gesturestart', 'gesturechange', 'gestureend']) {
  el.frame.addEventListener(type, block);
}
if (window.ResizeObserver) new ResizeObserver(resizeCanvas).observe(el.frame);
else window.addEventListener('resize', resizeCanvas);


// ---- 5. Answer controls -------------------------------------------------------------------
// Built from the server's JSON, so a study can change its choices or its scale.

function fillChoices(fieldset, legend, items) {
  fieldset.querySelector('legend').textContent = legend;
  fieldset.querySelectorAll('label').forEach((label) => label.remove());
  for (const [value, text] of items) {
    const label = document.createElement('label');
    label.className = 'choice';
    const input = document.createElement('input');
    input.type = 'radio';
    input.name = fieldset.id;
    input.value = String(value);
    label.append(input, text);  // text, never HTML
    fieldset.append(label);
  }
}

function checkedValue(fieldset) {
  const input = fieldset.querySelector('input:checked');
  return input ? input.value : null;
}

function setChecked(fieldset, value) {
  for (const input of fieldset.querySelectorAll('input')) input.checked = input.value === String(value);
}

function lockInputs(...fieldsets) {
  for (const fieldset of fieldsets) fieldset.querySelectorAll('input').forEach((i) => { i.disabled = true; });
}

function updateButtons() {
  const off = busy || stopped;
  el.lock.disabled = off || !picture || !checkedValue(el.firstAnswer) || !checkedValue(el.firstConfidence);
  el.submitFinal.disabled = off || !checkedValue(el.finalAnswer) || !checkedValue(el.finalConfidence);
}

const elapsedMs = () => Math.round(performance.now() - startedAt);


// ---- 6. The reading flow ------------------------------------------------------------------

// Asks the server where the reader is, then shows that case. The server state always wins:
// after a reload, or after the browser's Back button, the page shows what the server says.
async function loadCase() {
  const data = await getJson(`${API}current`);
  if (data.state === 'done') return finish();
  task = data;
  submissionId = data.submission_id;
  el.progress.textContent = `Case ${data.position} of ${data.total}`;

  const choices = data.choices.map((c) => [c.value, c.label]);
  const scaleItems = Array.from({ length: data.confidence_max }, (_, i) => [i + 1, String(i + 1)]);
  const scaleLegend = `Confidence: 1 (low) to ${data.confidence_max} (high)`;
  fillChoices(el.firstAnswer, data.question, choices);
  fillChoices(el.firstConfidence, scaleLegend, scaleItems);
  fillChoices(el.finalAnswer, data.question, choices);
  fillChoices(el.finalConfidence, scaleLegend, scaleItems);
  for (const part of [el.first, el.aiPanel, el.final, el.aiMark]) part.hidden = true;
  aiBox = null;

  // Clear the last case first: a slow download must never show it under the new case number.
  release(picture);
  picture = null;
  draw();
  showStatus('Loading image…');
  picture = await pictureFor(data.image);
  resizeCanvas();
  resetView();
  startedAt = performance.now();  // the first read's time starts when the image shows
  showStatus('');
  el.first.hidden = false;
  prefetch((data.prefetch || [])[0]);

  // Reloaded after the lock: the first read is stored, so show it with the AI suggestion.
  if (data.stage === 'final') showReveal(data.first_read, data.ai);
}

// Hides the locked first read, then shows the AI suggestion and the final-answer controls.
function showReveal(firstRead, ai) {
  el.first.hidden = true;

  el.aiLabel.textContent = ai.label;
  el.aiConfidence.textContent = ai.confidence == null ? '' : `${Math.round(ai.confidence * 100)}% confidence`;
  el.aiSource.textContent = ai.source ? `Source: ${ai.source}` : '';
  aiBox = Array.isArray(ai.box) && ai.box.length === 4 ? ai.box.map(Number) : null;
  el.aiMark.hidden = !aiBox;
  el.aiPanel.hidden = false;
  draw();

  // Only the answer is pre-selected. The reader rates confidence again after seeing the AI.
  setChecked(el.finalAnswer, firstRead.answer);
  el.final.hidden = false;
  startedAt = performance.now();  // the final read's time starts when the AI shows
}

async function lockFirst() {
  // Read the answer once. Every retry sends this same body with the same submission_id.
  const body = {
    submission_id: submissionId,
    answer: checkedValue(el.firstAnswer),
    confidence: Number(checkedValue(el.firstConfidence)),
    elapsed_ms: elapsedMs(),
  };
  lockInputs(el.firstAnswer, el.firstConfidence);
  showStatus('Saving your first read…');
  const data = await postJson(`/api/p/${encodeURIComponent(task.presentation)}/first`, body);
  submissionId = data.submission_id;  // the new code for the final read
  showStatus('');
  showReveal(body, data.ai);
  scrollToViewer();
  el.aiPanel.focus({ preventScroll: true });  // the Lock button is gone; keep keyboard focus nearby
}

async function sendFinal() {
  const body = {
    submission_id: submissionId,
    answer: checkedValue(el.finalAnswer),
    confidence: Number(checkedValue(el.finalConfidence)),
    elapsed_ms: elapsedMs(),
  };
  lockInputs(el.finalAnswer, el.finalConfidence);
  showStatus('Saving your final answer…');
  const data = await postJson(`/api/p/${encodeURIComponent(task.presentation)}/final`, body);
  if (!data.next) return finish();
  scrollToViewer();
  await loadCase();
}

// Scrolls up until the image sits at the top of the screen, with the panel right under it.
// Never scrolls down: a reader who is already higher up keeps the page title in view.
function scrollToViewer() {
  const top = reader.getBoundingClientRect().top + window.scrollY;
  if (window.scrollY > top) window.scrollTo(0, top);
}

// replace, not assign: the reading page leaves the history, so Back from the done page
// does not bounce the reader straight forward again.
function finish() {
  release(picture);
  location.replace(DONE_URL);
}

// Runs one step with the buttons off, so a double tap cannot send twice.
async function run(step) {
  if (busy || stopped) return;
  busy = true;
  updateButtons();
  try {
    await step();
  } catch (err) {
    stopped = true;
    const known = err instanceof Refused;
    if (!known) console.error(err);  // a bug in this page, not a server answer
    showStatus(known ? err.message : 'Something went wrong on this page. Reload it to continue.', 'stop');
    el.reloadRow.hidden = false;
  } finally {
    busy = false;
    updateButtons();
  }
}

reader.addEventListener('change', updateButtons);
el.lock.addEventListener('click', () => run(lockFirst));
el.submitFinal.addEventListener('click', () => run(sendFinal));
el.reload.addEventListener('click', () => location.reload());
// A page restored from the Back/Forward cache shows old state: ask the server again.
window.addEventListener('pageshow', (event) => { if (event.persisted) location.reload(); });

run(loadCase);
