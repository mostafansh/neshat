# How the reading screen talks to the server

The reading screen is one page plus one JavaScript file (`static/js/read.js`). The page asks
the server for the current case, sends the reader's answers, and receives the AI suggestion
only after the first read is stored (CLAUDE.md rule 1). This file is the contract between the
two halves. Change both halves and this file together.

## Words

| Word | Meaning |
|---|---|
| Study | One project, for example "Fracture on hand/wrist X-ray". Has a `key` like `wrist-fracture`. |
| Presentation | One case shown to one reader, at one position in their list. Has a random `alias`. |
| First read | The reader's unaided answer and confidence. Locked once sent. |
| Final read | The answer after the AI suggestion is shown. Locked once sent. |
| Submission ID | A one-time code the server gives with each case. The page sends it back with the answer, so a retried send (bad Wi-Fi) is stored once only. |
| Slice | One 2D image of a scan, for example one MRI image. |
| Stack | All slices of one scan (one series) in display order. A case is one image or one stack of 2 to 64 slices. The reader scrolls through a stack. |
| Stack file | One file that holds every slice of a stack. The page downloads it in one request (see "Stack file" below). |

## Pages (server-rendered HTML)

| Address | What |
|---|---|
| `/projects/` | List of open studies. |
| `/s/<key>/` | Study info and consent. "I agree" enrols the reader. |
| `/s/<key>/read/` | The reading screen. The page has `<div id="reader" data-api="/api/s/<key>/">`. |
| `/s/<key>/done/` | Shown when every case is finished. |

## Data calls (JSON, same site, signed-in reader only)

All POST calls send the header `X-CSRFToken` with the value of the `csrftoken` cookie, and a
JSON body. Errors come back as `{"error": "<plain sentence>"}` with status 400, 403, 404 or 409.

### GET `<api>current`

```json
{
  "state": "reading",
  "position": 3,
  "total": 8,
  "presentation": "p8Kq2mZt0bXa",
  "stage": "first",
  "image": "/i/p8Kq2mZt0bXa/",
  "prefetch": ["/i/pT7wYcN3dLr4/"],
  "question": "Fracture?",
  "choices": [
    {"value": "yes", "label": "Fracture"},
    {"value": "no", "label": "No fracture"},
    {"value": "unsure", "label": "Unsure"}
  ],
  "confidence_max": 5,
  "submission_id": "sQ3x9…",
  "first_read": null,
  "ai": null
}
```

- `state` is `"reading"` or `"done"`. When `"done"`, the other fields are absent and the page
  goes to `/s/<key>/done/`.
- `stage` is `"first"` (nothing locked yet) or `"final"` (first read locked, AI shown, final
  answer not yet sent). `"final"` happens only when the page is reloaded after the lock.
- `first_read` and `ai` are `null` when `stage` is `"first"`. When `stage` is `"final"` they
  hold the locked first read and the AI suggestion, in the same shapes as below.
- `image` is one PNG or one stack file. The page learns which from the response's
  `Content-Type` (see GET `/i/<alias>/`). This response does not say how many slices a case
  has.
- `prefetch` lists at most one image: the next case. The page keeps its raw bytes and content
  type in memory only. It decodes them when that case starts.
- The server sends images only for the current case, the case before and the case after. Any
  other image address returns 404 and is logged.

### POST `/api/p/<alias>/first`

Body: `{"submission_id": "...", "answer": "yes", "confidence": 4, "elapsed_ms": 8123}`

Response 200:

```json
{
  "ai": {
    "source": "AI model (simulated)",
    "answer": "no",
    "label": "No fracture",
    "confidence": 0.86,
    "box": null,
    "box_slices": null
  },
  "submission_id": "sR8y2…"
}
```

- `box` is `null` or `[x, y, width, height]` in image pixels (the image's own size, not the
  screen; for a stack, the size of one slice). The page draws it on the image in the `--ai`
  colour, dashed.
- `box_slices` is `[first, last]` when the box is on a stack: the slices the box is drawn on,
  counted from 0, both included. It is `null` for a single image and when `box` is `null`.
  Like the rest of `ai`, it leaves the server only in this response and in GET `current`
  after the lock (CLAUDE.md rule 1).
- `submission_id` is the new code for the final read.
- Sending the same `submission_id` again with the same answer and confidence returns the same
  response (safe retry). The same code with a different answer (for example from a second tab)
  returns 409, and nothing stored changes.

### POST `/api/p/<alias>/final`

Body: `{"submission_id": "...", "answer": "yes", "confidence": 3, "elapsed_ms": 4410}`

Response 200: `{"next": true}` (another case waits) or `{"next": false}` (study finished).
The same `submission_id` sent again returns the same response; with a different answer, 409.

### GET `/i/<alias>/`

The case image, pixels only. There are two kinds:

| `Content-Type` | What the bytes are |
|---|---|
| `image/png` | One image: an 8-bit greyscale PNG. |
| `application/vnd.neshat.stack` | One stack file (below): all slices of a stack. |

- Every response has `Cache-Control: private, no-store` and a `Content-Length` header. The
  page uses `Content-Length` to show the download progress.
- Every response writes one row to the access log, with the SHA-256 of the bytes sent.
- The page never puts this address in the page itself (no `<img src>`): it fetches the bytes
  and draws them on a canvas, so a long press offers no "Download image".

### Stack file

All numbers are 4-byte unsigned integers, big-endian (most significant byte first).

| Bytes | What |
|---|---|
| 4 | The ASCII letters `NSTK`. |
| 4 | The slice count `n` (2 to 64). |
| then, for each slice in order: 4, then that length | The byte length of this slice's PNG, then the slice itself as an 8-bit greyscale PNG. |

- So the file is: `NSTK`, `n`, then `n` times [length][PNG bytes].
- Nothing else is in the file: no names, no positions, no dates and no metadata (rule 4).
- The slices come in display order. The first slice is slice 0.
- All slices have the same width and height.
- The page treats a file that breaks this layout as an error, for example a file without
  `NSTK` at the start, or lengths that do not add up to the file size.

## Stacks on the reading screen

These rules apply when a case has more than 1 slice. A single image behaves exactly as before.

- **Start slice.** Every case opens on the middle slice: `Math.floor((n - 1) / 2)`, where `n`
  is the slice count. The start slice never depends on the answer or on the AI box (rule 1).
- **Timer.** The reading timer starts when every slice is decoded and the start slice is on
  screen.
- **Download.** The page reads the response as a stream and shows "Loading image… 1.2 of
  2.9 MB" when `Content-Length` is known and the file is 0.5 MB or more. A smaller file
  keeps "Loading image…". The page decodes every slice before the case starts.
- **Gestures on the image:**
  - One finger (or the mouse button), dragged: after 10 CSS px of movement, the direction is
    fixed for the rest of that drag. Up or down changes the slice; dragging down goes to the
    next slice. Left or right pans.
  - Distance per slice: `max(4, frame height in CSS px / max(n, 8))` CSS px.
  - Two fingers: pinch to zoom, move to pan.
  - Double-tap: resets zoom and pan. It keeps the slice.
  - Mouse wheel: one slice per notch. Small trackpad steps add up to one slice.
    Ctrl or Cmd plus the wheel zooms (a trackpad pinch arrives this way).
  - Keys, with the image focused: Arrow Up and Arrow Down move 1 slice, Page Up and Page Down
    move 5, Home and End go to the first and the last slice.
- **Controls under the image:** a previous button, a slider (1 to `n`), a next button, and the
  label "Slice 12 / 24". A small "12/24" also shows in a corner of the image.
- **Hint:** "Drag up or down for slices. Pinch to zoom. Two fingers to move. Double-tap to
  reset."
- **AI box on a stack:**
  - The page draws the box only on slices `first` to `last` of `box_slices`, in the same
    dashed `--ai` style as on a single image (rule 6).
  - On the reveal, the page goes to the middle slice of that range. It does this for every
    suggestion with a box, correct or planted.
  - The AI panel adds "Box on slices a–b", counted from 1 ("Box on slice a" for a box on
    one slice).
  - The "AI" label in the corner of the image shows only on the slices that carry the box.
  - The slider shows one mark over that range, in `--ai`.

## Rules for the page

- Plain JavaScript, one ES module, no build step, no libraries.
- No `crypto.randomUUID`, `crypto.subtle`, clipboard, wake lock or service workers: the venue
  is plain HTTP.
- No back button and no way to change a locked read. After the lock, the first-read controls
  disappear; the final answer starts on the first answer.
- The image stays in view while the answers scroll (sticky on a phone, side by side on a wide
  screen).
- A network error, a time-out or a 5xx is retried with the same body. Each retry allows twice
  as long, up to 4 minutes. A 4xx stops the page with the server's sentence and a "Reload the
  page" button.
- An image download has no fixed total time limit. It stops only after 20 s with no new bytes
  (a stall), and is then retried. So a slow link can still finish a 3 MB stack.
- When the case changes, the page closes every decoded slice of the previous case, to free
  the phone's memory.
- No `getImageData`: Safari adds noise to canvas read-back on purpose.
- Nothing from another server.
