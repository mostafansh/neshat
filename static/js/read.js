// The reading screen: shows one case, takes the reader's first read, shows the AI suggestion
// the server sends back, then takes the final read. The page templates/reading/read.html
// holds the markup; docs/reading-api.md is the contract with the server.
//
// A case is one image (an X-ray) or a stack of slices (an MRI series). A stack arrives as one
// file. The reader then scrolls through its slices with no further download.
//
// Rules this file keeps (see CLAUDE.md):
// - The page never knows the AI suggestion before the server has stored the first read. It
//   arrives only in the answer to "Lock my read" (rule 1). A stack always opens on its middle
//   slice, never on the slice the AI points at.
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
const STALL_MS = 20000;     // an image download stops after 20 s with no new bytes
const PNG = 'image/png';                       // the file type of one image
const STACK = 'application/vnd.neshat.stack';  // the file type of a stack: all slices of a case

const $ = (id) => document.getElementById(id);
const el = {
  progress: $('progress'), frame: $('frame'), canvas: $('view'), aiMark: $('ai-mark'),
  status: $('status'), first: $('first'), lock: $('lock'),
  firstAnswer: $('first-answer'), firstConfidence: $('first-confidence'),
  aiPanel: $('ai-panel'), aiLabel: $('ai-label'), aiConfidence: $('ai-confidence'),
  aiSource: $('ai-source'), final: $('final'), submitFinal: $('submit-final'),
  finalAnswer: $('final-answer'), finalConfidence: $('final-confidence'),
  reloadRow: $('reload-row'), reload: $('reload'), hint: $('hint'), aiSlices: $('ai-slices'),
  sliceBar: $('slice-bar'), sliceRange: $('slice-range'), sliceAi: $('slice-ai'),
  slicePrev: $('slice-prev'), sliceNext: $('slice-next'), sliceLabel: $('slice-label'),
  sliceBadge: $('slice-badge'),
};

let task = null;        // the case on screen: the JSON from GET current
let submissionId = '';  // the one-time code for the next POST (a retry reuses it)
let startedAt = 0;      // when the image was drawn, or when the AI was shown (for elapsed_ms)
let busy = false;       // a request is in flight: buttons stay disabled
let stopped = false;    // the server refused a request: wait for a reload


// ---- 1. Talking to the server ------------------------------------------------------------

// A 4xx answer, or a file that cannot be used. Trying again will not help, so the page shows
// the words and stops.
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
// Two kinds of time-out:
// - A data call must finish in 20 s. Each retry allows twice as long, up to 4 minutes.
// - An image download (stall = true) may take as long as it needs, but stops after 20 s with
//   no new bytes: readBody calls alive() for every piece that arrives. So a slow but working
//   link can finish a 3 MB stack, and a dead link is noticed after 20 s.
async function request(url, options, readBody, stall = false) {
  let wait = 1000;
  let timeoutMs = stall ? STALL_MS : 20000;
  for (;;) {
    const controller = new AbortController();
    const timer = abortTimer(controller, timeoutMs);
    let res = null;
    try {
      res = await fetch(url, { ...options, credentials: 'same-origin', signal: controller.signal });
      if (res.status < 500) {
        if (!res.ok) throw new Refused(await refusalText(res));
        const body = await readBody(res, timer.restart);
        if (el.status.dataset.kind === 'warn') showStatus('');  // the connection is back
        return body;
      }
    } catch (err) {
      if (err instanceof Refused) throw err;
      // Otherwise it was a network error or a time-out: try again below.
    } finally {
      timer.stop();
    }
    // A 5xx answer means the connection works but the server failed: say so, so nobody
    // looks for the fault in the Wi-Fi. data/errors.log on the laptop has the details.
    const serverFault = res && res.status >= 500;
    showStatus(serverFault ? 'The server had a problem. Trying again…' : 'Connection lost. Trying again…', 'warn');
    await sleep(wait);
    wait = Math.min(wait * 2, 15000);
    if (!stall) timeoutMs = Math.min(timeoutMs * 2, 240000);
  }
}

// Aborts a request after `ms`. restart() starts the count again from zero: a download calls
// it whenever bytes arrive, so only a stall stops it.
function abortTimer(controller, ms) {
  let id = 0;
  const restart = () => {
    clearTimeout(id);
    id = setTimeout(() => controller.abort(), ms);
  };
  restart();
  return { restart, stop: () => clearTimeout(id) };
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

// kind: '' (plain), 'warn' (connection trouble) or 'stop' (refused). A new warning or
// refusal is brought into view, once: the reader must see it, but may scroll away again.
function showStatus(text, kind = '') {
  const isNew = kind && kind !== el.status.dataset.kind;
  el.status.textContent = text;
  el.status.className = kind ? `notice notice-${kind}` : 'muted';
  el.status.dataset.kind = kind;
  if (isNew) reveal(el.status);
}

// Scrolls just enough to show an element that is off the screen.
function reveal(element) {
  const box = element.getBoundingClientRect();
  if (box.top < 0 || box.bottom > window.innerHeight) element.scrollIntoView({ block: 'nearest' });
}


// ---- 2. Images: download, unpack, decode, keep in memory ---------------------------------
// A case's image arrives as one of two file types (docs/reading-api.md):
// - image/png: one image.
// - a stack file: the letters "NSTK", the slice count, then for each slice its length and its
//   PNG bytes. Each number is 4 bytes, big-endian. Nothing else: no names, no positions.

let slices = [];      // the decoded slices of the case on screen (just one for a single image)
let sliceIndex = 0;   // the slice on screen, counted from 0
let picture = null;   // slices[sliceIndex]: the decoded image on screen
let upcoming = null;  // { url, promise, controller, showProgress }: the next case's file

// Reads an image answer piece by piece. alive() restarts the stall timer; onProgress gets the
// bytes so far and the total (0 if the server did not say). Returns the raw bytes and their
// type. Decoding waits until the case is on screen.
async function readImage(res, alive, onProgress) {
  const type = (res.headers.get('Content-Type') || '').split(';')[0].trim();
  if (type !== PNG && type !== STACK) {
    throw new Refused('The image did not arrive. Reload the page, and sign in again if asked.');
  }
  const total = Number(res.headers.get('Content-Length')) || 0;
  const stream = res.body.getReader();
  const pieces = [];
  let received = 0;
  for (;;) {
    const { done, value } = await stream.read();
    if (done) break;
    pieces.push(value);
    received += value.length;
    alive();
    onProgress(received, total);
  }
  const bytes = new Uint8Array(received);  // the pieces as one block
  let at = 0;
  for (const piece of pieces) {
    bytes.set(piece, at);
    at += piece.length;
  }
  return { type, bytes };
}

// "Loading image… 1.2 of 2.9 MB", when the server says the size. A file under 0.5 MB arrives
// in a moment and keeps "Loading image…". The text changes at most once per 0.1 MB, so a
// screen reader is not flooded.
function showProgress(received, total) {
  if (total < 500000) return;
  const mb = (bytes) => (bytes / 1e6).toFixed(1);
  const text = `Loading image… ${mb(received)} of ${mb(total)} MB`;
  if (el.status.textContent !== text) showStatus(text);
}

// Cuts a stack file into one PNG Blob per slice. A damaged file stops the page.
function splitStack(bytes) {
  const damaged = () => new Refused(
    'The image of this case is damaged. Reload the page. If this happens again, tell the organiser.');
  const data = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (bytes.length < 8 || String.fromCharCode(...bytes.subarray(0, 4)) !== 'NSTK') throw damaged();
  const count = data.getUint32(4);  // DataView reads big-endian unless told otherwise
  const blobs = [];
  let at = 8;
  while (blobs.length < count) {
    if (at + 4 > bytes.length) throw damaged();
    const length = data.getUint32(at);
    at += 4;
    if (length === 0 || at + length > bytes.length) throw damaged();
    blobs.push(new Blob([bytes.subarray(at, at + length)], { type: PNG }));
    at += length;
  }
  if (count === 0 || at !== bytes.length) throw damaged();  // nothing may follow the last slice
  return blobs;
}

// Decodes every slice before the case starts, so scrolling never waits. A slice that cannot
// be decoded stops the page; the reload frees the memory.
function decodeFile({ type, bytes }) {
  const blobs = type === STACK ? splitStack(bytes) : [new Blob([bytes], { type: PNG })];
  return Promise.all(blobs.map(decode));
}

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

// Downloads the next case's file while the reader works on this one. It keeps the bytes
// only: decoded slices take much more memory, so decoding waits until that case starts.
// One try only: if it fails, the next case downloads the file again when it starts.
function prefetch(url) {
  if (upcoming && upcoming.url === url) return;
  if (upcoming) upcoming.controller.abort();  // no longer needed: save the reader's data
  upcoming = null;
  if (!url) return;
  const controller = new AbortController();
  const timer = abortTimer(controller, STALL_MS);  // a stalled download must not block the next case
  const next = { url, controller, showProgress: false };
  const onProgress = (received, total) => { if (next.showProgress) showProgress(received, total); };
  next.promise = fetch(url, { credentials: 'same-origin', signal: controller.signal })
    .then((res) => {
      if (!res.ok) throw new Error(`prefetch ${res.status}`);
      return readImage(res, timer.restart, onProgress);
    })
    .finally(timer.stop);
  next.promise.catch(() => {});  // a failed prefetch is not an error on screen
  upcoming = next;
}

// The decoded slices of a case: from the prefetched file if there is one, else a fresh
// download. A prefetch that is still running shows its progress from now on.
async function slicesFor(url) {
  let file = null;
  if (upcoming && upcoming.url === url) {
    const next = upcoming;
    upcoming = null;
    next.showProgress = true;
    try { file = await next.promise; } catch { /* the prefetch failed: download it below */ }
  }
  if (!file) file = await request(url, {}, (res, alive) => readImage(res, alive, showProgress), true);
  return decodeFile(file);
}


// ---- 3. Drawing: fit, zoom and pan ------------------------------------------------------
// Everything is stored in image pixels (the image's own size). One transform maps image
// pixels to canvas pixels: canvas = image * scale + (x, y). The AI box uses the same
// transform as the image, so it stays on the same spot at every zoom and pan.

const ctx = el.canvas.getContext('2d');
const view = { fit: 1, zoom: 1, x: 0, y: 0 };  // fit: whole image in the frame; zoom: 1 or more
let aiBox = null;                               // [x, y, width, height] in image pixels
let aiRange = [0, 0];                           // the slices that carry the AI box: first, last
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

// The zoom limit: 8 times the fit size, or more for a large image. A full-size radiograph
// (2000-3000 px wide) must still zoom until one image pixel covers 4 x 4 screen pixels.
const maxZoom = () => Math.max(MAX_ZOOM, MAX_PIXEL_SIZE * pixelRatio() / view.fit);

// Zooms by `factor` and keeps the image point under (px, py) in the same place.
function zoomAt(px, py, factor) {
  const anchor = toImage(px, py);
  view.zoom = Math.min(maxZoom(), Math.max(1, view.zoom * factor));
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
  view.zoom = Math.min(view.zoom, maxZoom());  // the limit depends on the frame size
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
  // On a stack the box belongs to some slices only. The "AI" label shows only with its box.
  const boxHere = Boolean(aiBox) && sliceIndex >= aiRange[0] && sliceIndex <= aiRange[1];
  el.aiMark.hidden = !boxHere;
  if (boxHere) drawAiBox(s);
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


// ---- 4. Slices of a stack ----------------------------------------------------------------
// A stack shows one slice at a time. The slider, the two step buttons, the drag, the wheel
// and the keys all end in showSlice. A single image has no slice controls.

const HINT_SINGLE = el.hint.textContent;  // the page's own hint, for a single image
const HINT_STACK = 'Drag up or down for slices. Pinch to zoom. Two fingers to move. Double-tap to reset.';
const LABEL_SINGLE = el.canvas.getAttribute('aria-label');
const LABEL_STACK = `Case image, one slice of a stack. ${HINT_STACK}`;

// The middle of a range of slices, rounded down. Every case opens on the middle slice of the
// whole stack, never on the slice the AI points at (rule 1).
const middle = (first, last) => Math.floor((first + last) / 2);

// Frees the last case's slices and hides their controls, so a slow download never shows them
// under the new case number. Phones have little memory to spare.
function clearSlices() {
  slices.forEach(release);
  slices = [];
  picture = null;
  el.sliceBar.hidden = true;
  el.sliceBadge.hidden = true;
}

// Puts a new case's decoded slices on screen, on the middle slice. Shows the slice controls
// for a stack, and today's hint and controls for a single image.
function setSlices(list) {
  slices = list;
  sliceIndex = middle(0, slices.length - 1);
  picture = slices[sliceIndex];
  const stack = slices.length > 1;
  reader.classList.toggle('is-stack', stack);  // the CSS makes room for the slice controls
  el.sliceBar.hidden = !stack;
  el.sliceBadge.hidden = !stack;
  el.sliceAi.hidden = true;
  el.hint.textContent = stack ? HINT_STACK : HINT_SINGLE;
  el.canvas.setAttribute('aria-label', stack ? LABEL_STACK : LABEL_SINGLE);
  if (stack) el.frame.tabIndex = 0;  // the arrow keys work on the focused frame
  else el.frame.removeAttribute('tabindex');
  el.sliceRange.max = String(slices.length);
  wheelSum = 0;
  if (stack) showSliceNumber();
}

// Moves to slice `index` (kept inside the stack) and updates the numbers on screen.
function showSlice(index) {
  const i = Math.min(slices.length - 1, Math.max(0, index));
  if (i === sliceIndex) return;
  sliceIndex = i;
  picture = slices[i];
  showSliceNumber();
  requestDraw();
}

// People count slices from 1: "Slice 12 / 24" under the frame, "12/24" in its corner.
function showSliceNumber() {
  const number = sliceIndex + 1;
  const n = slices.length;
  el.sliceRange.value = String(number);
  el.sliceRange.setAttribute('aria-valuetext', `Slice ${number} of ${n}`);
  el.sliceLabel.textContent = `Slice ${number} / ${n}`;
  el.sliceBadge.textContent = `${number}/${n}`;
}

// The server's box_slices: [first, last], counted from 0 (the loader checked they fit). A
// single image has one slice. A box without a range stays on every slice.
function boxRange(range) {
  const valid = Array.isArray(range) && range.length === 2;
  return valid ? range.map(Number) : [0, slices.length - 1];
}

// One dashed --ai mark under the slider, over the slices that carry the AI box. Its ends sit
// half a slice beyond the first and the last slice, so a one-slice box still shows. The CSS
// turns --from and --to (0 to 1 along the slider) into a position.
function markAiSlices() {
  const n = slices.length;
  el.sliceAi.hidden = !aiBox || n < 2;
  if (el.sliceAi.hidden) return;
  const [first, last] = aiRange;
  el.sliceAi.style.setProperty('--from', String(Math.max(0, (first - 0.5) / (n - 1))));
  el.sliceAi.style.setProperty('--to', String(Math.min(1, (last + 0.5) / (n - 1))));
}

el.sliceRange.addEventListener('input', () => showSlice(Number(el.sliceRange.value) - 1));
el.slicePrev.addEventListener('click', () => showSlice(sliceIndex - 1));
el.sliceNext.addEventListener('click', () => showSlice(sliceIndex + 1));


// ---- 5. Gestures: drag, pinch, wheel, double-tap, keys -----------------------------------
// Pointer Events cover mouse, finger and pen with one set of handlers.
// A single image: one finger moves it. A stack: one finger up or down changes the slice, and
// sideways moves the image. Two fingers always pinch to zoom and move the image.

const pointers = new Map();  // pointerId -> { x, y, startX, startY, time }
let twoFingers = false;      // this gesture used two fingers, so it is not a tap
let lastTap = null;
let drag = null;             // a one-finger drag: its start point and slice, and its direction
let wheelSum = 0;            // small trackpad scrolls, added up until they make one slice
const WHEEL_STEP = 50;       // trackpad wheel pixels per slice (see wheelSteps)
const SLICE_KEYS = new Map([['ArrowUp', -1], ['ArrowDown', 1], ['PageUp', -5], ['PageDown', 5]]);

function canvasPoint(event) {
  const box = el.canvas.getBoundingClientRect();
  const ratio = pixelRatio();
  return { x: (event.clientX - box.left) * ratio, y: (event.clientY - box.top) * ratio };
}

function pinch() {
  const [a, b] = [...pointers.values()];
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, d: Math.hypot(a.x - b.x, a.y - b.y) };
}

// A one-finger drag starts. On a stack its direction is not known yet (see lockAxis). After a
// pinch, the finger left down only moves the image, so the zoomed slice stays on screen.
function startDrag(p) {
  drag = { x: p.x, y: p.y, slice: sliceIndex, axis: slices.length > 1 && !twoFingers ? null : 'pan' };
}

// On a stack, the first 10 CSS px of a drag fix its direction until the finger lifts: up or
// down changes the slice, sideways moves the image. Returns false while it is not decided.
function lockAxis(now) {
  if (drag.axis) return true;
  const dx = now.x - drag.x;
  const dy = now.y - drag.y;
  if (Math.hypot(dx, dy) < 10 * pixelRatio()) return false;
  drag.axis = Math.abs(dy) >= Math.abs(dx) ? 'slice' : 'pan';
  return true;
}

// The finger distance for one slice: the frame height spread over the stack (over 8 slices
// for a short stack), and at least 4 CSS px. In canvas pixels, like the pointer positions.
function sliceStep() {
  const frameHeight = el.canvas.getBoundingClientRect().height;
  return Math.max(4, frameHeight / Math.max(slices.length, 8)) * pixelRatio();
}

function onPointerDown(event) {
  if (!picture) return;
  const p = canvasPoint(event);
  pointers.set(event.pointerId, { ...p, startX: p.x, startY: p.y, time: event.timeStamp });
  if (pointers.size === 1) startDrag(pointers.get(event.pointerId));
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
    // While the direction is open nothing moves and p keeps its old place, so a sideways
    // drag then moves the image the whole way at once. Drag down = next slice.
    if (!lockAxis(now)) return;
    if (drag.axis === 'slice') {
      const target = drag.slice + Math.trunc((now.y - drag.y) / sliceStep());
      const i = Math.min(slices.length - 1, Math.max(0, target));
      // Past the first or last slice, count again from the finger, so a drag back responds at once.
      if (i !== target) {
        drag.slice = i;
        drag.y = now.y;
      }
      showSlice(i);
    } else {
      panBy(now.x - p.x, now.y - p.y);
    }
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
  if (pointers.size === 1) startDrag([...pointers.values()][0]);  // the finger left after a pinch
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

// A single image: the wheel zooms. A stack: the wheel changes the slice, and Ctrl (or Cmd)
// plus the wheel zooms. A trackpad pinch arrives as Ctrl + wheel, so it zooms too.
function onWheel(event) {
  if (!picture) return;
  event.preventDefault();  // change the image, not scroll the page
  if (slices.length > 1 && !event.ctrlKey && !event.metaKey) {
    const steps = wheelSteps(event);
    if (steps) showSlice(sliceIndex + steps);
    return;
  }
  const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? 400 : 1;  // lines, pages
  const p = canvasPoint(event);
  zoomAt(p.x, p.y, Math.exp(-event.deltaY * unit * 0.002));
}

// One slice per mouse-wheel notch. A notch is about 100 pixels (or 3 lines). A busy browser
// may join several notches into one event, so a large event counts its notches. A trackpad
// sends many small scrolls; those are added up, one slice per 50 pixels.
function wheelSteps(event) {
  const pixels = event.deltaY * (event.deltaMode === 1 ? 33 : event.deltaMode === 2 ? 100 : 1);
  if (Math.abs(pixels) >= WHEEL_STEP) {
    wheelSum = 0;
    return Math.sign(pixels) * Math.max(1, Math.round(Math.abs(pixels) / 100));
  }
  wheelSum += pixels;
  const steps = Math.trunc(wheelSum / WHEEL_STEP);
  wheelSum -= steps * WHEEL_STEP;
  return steps;
}

// A stack, with the frame focused (by Tab or a click on the image): the arrow keys step one
// slice, Page Up and Page Down five, Home and End go to the first and the last slice.
function onKey(event) {
  if (slices.length < 2 || event.altKey || event.ctrlKey || event.metaKey) return;
  if (event.key === 'Home') showSlice(0);
  else if (event.key === 'End') showSlice(slices.length - 1);
  else if (SLICE_KEYS.has(event.key)) showSlice(sliceIndex + SLICE_KEYS.get(event.key));
  else return;
  event.preventDefault();  // the page does not scroll
}

el.canvas.addEventListener('pointerdown', onPointerDown);
el.canvas.addEventListener('pointermove', onPointerMove);
el.canvas.addEventListener('pointerup', onPointerEnd);
el.canvas.addEventListener('pointercancel', onPointerEnd);
el.canvas.addEventListener('wheel', onWheel, { passive: false });
el.frame.addEventListener('keydown', onKey);
// No long-press menu (no "Save", "Share" or "Search image") and no iPhone page zoom.
const block = (event) => event.preventDefault();
for (const type of ['contextmenu', 'gesturestart', 'gesturechange', 'gestureend']) {
  el.frame.addEventListener(type, block);
}
if (window.ResizeObserver) new ResizeObserver(resizeCanvas).observe(el.frame);
else window.addEventListener('resize', resizeCanvas);


// ---- 6. Answer controls -------------------------------------------------------------------
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


// ---- 7. The reading flow ------------------------------------------------------------------

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
  clearSlices();
  draw();
  showStatus('Loading image…');
  setSlices(await slicesFor(data.image));
  resizeCanvas();
  resetView();
  // The first read's time starts when the image shows. For a stack: when every slice is
  // decoded and the middle slice is drawn.
  startedAt = performance.now();
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
  aiRange = boxRange(ai.box_slices);
  // A stack jumps to the middle of the box's slices. It does this for every suggestion with
  // a box, so the jump gives nothing away (rule 6).
  const boxOnStack = Boolean(aiBox) && slices.length > 1;
  const [a, b] = aiRange.map((i) => i + 1);  // people count slices from 1
  el.aiSlices.textContent = a === b ? `Box on slice ${a}` : `Box on slices ${a}–${b}`;
  el.aiSlices.hidden = !boxOnStack;
  markAiSlices();
  if (boxOnStack) showSlice(middle(...aiRange));
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
  clearSlices();
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
    reveal(el.reloadRow);
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
