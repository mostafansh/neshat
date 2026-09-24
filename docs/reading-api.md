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
- `prefetch` lists at most one image: the next case. The page loads it into memory only.
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
    "box": null
  },
  "submission_id": "sR8y2…"
}
```

- `box` is `null` or `[x, y, width, height]` in image pixels (the image's own size, not the
  screen). The page draws it on the image in the `--ai` colour, dashed.
- `submission_id` is the new code for the final read.
- Sending the same `submission_id` again with the same answer and confidence returns the same
  response (safe retry). The same code with a different answer (for example from a second tab)
  returns 409, and nothing stored changes.

### POST `/api/p/<alias>/final`

Body: `{"submission_id": "...", "answer": "yes", "confidence": 3, "elapsed_ms": 4410}`

Response 200: `{"next": true}` (another case waits) or `{"next": false}` (study finished).
The same `submission_id` sent again returns the same response; with a different answer, 409.

### GET `/i/<alias>/`

The image as PNG bytes (8-bit greyscale, pixels only). The page never puts this address in
the page itself (no `<img src>`): it fetches the bytes and draws them on a canvas, so a long
press offers no "Download image".

## Rules for the page

- Plain JavaScript, one ES module, no build step, no libraries.
- No `crypto.randomUUID`, `crypto.subtle`, clipboard, wake lock or service workers: the venue
  is plain HTTP.
- No back button and no way to change a locked read. After the lock, the first-read controls
  disappear; the final answer starts on the first answer.
- The image stays in view while the answers scroll (sticky on a phone, side by side on a wide
  screen).
- A network error, a time-out or a 5xx is retried with the same body. Each retry allows twice
  as long, up to 4 minutes, so a large image still arrives over a slow link. A 4xx stops the
  page with the server's sentence and a "Reload the page" button.
- Nothing from another server.
