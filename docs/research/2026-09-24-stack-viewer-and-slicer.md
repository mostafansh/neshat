# MRI and CT stacks on the phone, and where 3D Slicer belongs (checked 2026-09-24)

**What was built (2026-09-24):** `docs/reading-api.md` and `reading/studyfiles.py` are the
contract. They differ from this report in these places:
- The route is `GET /i/<alias>/`, with no window part.
- The AI payload keeps `"box"` and adds `"box_slices"`, not `{slices, rect}`.
- The server computes the SHA-256 per response and reads the file into memory (no
  `FileResponse`).
- Slices go through `slice_pixels`, which refuses any slice that is not 8-bit mode L.
- The UMD AI box is the 3-D bounding box of the model's largest cyst piece
  (`prep/umd_stack.py` `ai_rect`), not a 2-D box on the key slice.
- scipy also labels the cyst pieces, not only the myoma components.

Three research tracks produced this report. Each track had two independent reviews by
skeptics. This file keeps only the claims that survived review. It applies every correction.
It marks every claim that nobody could source or measure. Numbers in square brackets, such
as [4], point to the numbered sources at the end.

How the work was done:
- All tests that needed pictures or timing used synthetic volumes made with numpy.
- Real UMD files were used for numbers only: shapes, spacing, byte counts, percentiles and
  label counts. Nobody viewed, saved or printed a real image.
- The test PC: Ryzen 7 9800X3D, RTX 5090, 62 GB RAM, Windows 11, 3D Slicer 5.12.4.
- Every Slicer, trame and server process that the research started was stopped.
- No repo file was edited, except this report.

**Terms used below**
- **Volume:** one 3D scan, for example one MRI series. **Slice:** one 2D image of the volume.
  **Stack:** all slices of a volume in order. The reader scrolls through them.
- **Stack viewer:** a screen that shows one slice at a time and lets the reader move through
  the stack with a finger or the mouse wheel.
- **NIfTI:** a research file format for volumes (`.nii` or `.nii.gz`). It holds the voxel
  numbers plus a small header. **DICOM:** the hospital format. Each file holds one image
  plus a large header with patient details.
- **Affine:** a small table of numbers in a NIfTI file. It says where each voxel sits in the
  patient (which way is left, anterior, superior). **Orientation codes** such as `PIR` say
  which way each array axis runs: here toward Posterior, Inferior and Right.
- **Window/level (W/L):** the grey-scale mapping. The window is the range of values shown
  from black to white; the level is its centre. A **preset** is a fixed W/L, such as the
  CT lung window.
- **8-bit:** each pixel is one number from 0 to 255 (256 grey levels). Scanners store more
  (12-16 bits). The server makes 8-bit images, so the phone gets pixels only (rule 4).
- **Lossless / lossy:** a lossless format (PNG, lossless WebP) gives back the exact pixels.
  A lossy format (JPEG, lossy WebP) throws away some detail to make the file smaller.
- **Latency:** the delay before something happens. **Round trip (RTT):** the time for a
  message to go to the server and come back. **Throughput:** how many megabits per second
  (Mbps) a link carries.
- **Preload / prefetch:** download data before the reader needs it. Prefetch here means
  downloading the next case while the reader works on the current one.
- **Decode:** turn a compressed file (PNG, JPEG) into raw pixels in memory. A decoded
  512 x 512 slice takes about 1 MB (4 bytes per pixel, RGBA).
- **ImageBitmap:** the browser's object for one decoded image, ready to draw.
  **LRU cache:** "least recently used": keep a fixed number of decoded slices and drop the
  one unused for the longest time.
- **Secure context:** a page on HTTPS or on `localhost`. The venue LAN is plain HTTP, so some
  browser features are missing there (rule 7).
- **WebSocket:** a connection that stays open so the server can push data to the browser.
- **Headless:** a program that runs with no window or screen.
- **Build step:** a tool that joins and converts many JavaScript files before the browser can
  use them. **ESM:** the modern JavaScript module format. **Vendored:** a copy of a library
  kept inside our own repo.
- **Allowlist:** a list of what is accepted. Everything else is refused. It is safer than a
  blocklist.
- **Percentile:** the value below which a given share of voxels falls. p99.5 is the value
  that 99.5% of voxels are below.

## 1. The question and the short answer

**The owner's words:**
- "we reached a milestone here. now i want to add some mris and ct scans to check. as I
  understood in the first milestone we did not use 3d slicer at all. i want to start using it
  (basically its most simple features first as a test)."
- "I want the stack and a viewer really."
- "I'm doubting the Slicer ... I don't want the user to endure any difficulties using it and
  also be able to use it via phone, so the PNG seems good actually, but I don't know how to
  proceed: remove the Slicer option or host Slicer in server and act on the users' intents in
  the server."

**Short answer (a proposal for the owner to approve):**
1. Do not remove Slicer, and do not host it on the server. Readers never touch Slicer.
2. Slicer belongs on the owner's PC now. Its first simple uses: open a UMD volume and its mask,
   check orientation and brightness, and compare that view with the phone. Later: import messy
   hospital DICOM, check burned-in text, and draw boxes or ground truth.
3. The phone gets a stack of 8-bit PNG slices. A small Python script (nibabel) prepares it on
   the owner's PC. The phone downloads the whole stack of a case in one request and scrolls it
   locally, with no network wait per slice. This extends `read.js` with no library.
4. After the congress, keep the same split. The browser shows slices. Only AI inference runs as
   a server service, for example nnInteractive on the RTX 5090 [55]. Experts who segment use
   desktop Slicer, for example with the SlicerNNInteractive extension [56]. Reconsider
   server-side Slicer (trame-slicer) only when it leaves beta and a GPU server exists [4].
5. Two gates come first. CLAUDE.md says "no new breadth until a real radiologist has used the
   current thing end to end", and M1 still waits for one ADIR radiologist. Also, `docs/plan.md`
   decided "CT phase: 2-3 pre-windowed key images, no scrolling viewer". A stack viewer changes
   that decision, so it needs a short decision record. Start with MRI (UMD) only.

## 2. Option comparison

- **(A)** Our phone stack viewer in plain JavaScript (`read.js`), over slices the server
  prepared in advance.
- **(B1)** Slicer's built-in WebServer module, which renders a slice per HTTP request.
- **(B2)** trame-slicer, Kitware's library that streams Slicer's views to a web page.
- **(C)** Cornerstone3D, the open-source medical viewer library, vendored into the repo.

| | (A) Our stack viewer | (B1) Slicer WebServer | (B2) trame-slicer | (C) Cornerstone3D |
|---|---|---|---|---|
| **Reader experience on a phone** | One finger scrolls slices, two fingers zoom and pan, plus a slider. One wait per case for the download. No free W/L. | One shared view: two readers move each other's slice. Images are the size of the desktop view (296x207 px in the default layout); the `size` parameter is ignored. No W/L control [2]. | A desktop 4-view layout for the mouse wheel. Phone touch is untested. A dropped connection (screen lock, app switch) may lose the view state (not verified). | A full viewer with W/L. Its default touch setup scrolls with 3 fingers (configurable) [44]. OHIF's mobile layout is reported broken [46]. |
| **Latency on mobile data** | No network per scroll step. Desktop decode 0.9-3 ms per slice (phone not measured). One download per case: an MRI of about 2.2 MB takes about 2 s at 8 Mbps. | A round trip per step. A 1 MB PNG per step takes about 0.8 s at 10 Mbps (arithmetic). | Measured 108 ms median per step on localhost with the RTX 5090, before any network. On mobile data: estimated 130-250+ ms (not measured). | Same as (A), because pixels are local. |
| **Server load, 30 readers** | One file per case per window. One burst of 30 x 2-3 MB = 60-100 MB when the room moves to a new MRI case. One log row per response. | One Slicer process per reader. Requests run one at a time (measured). | Measured 0.55-0.6 GB resident memory per session: about 16-18 GB for 30 readers. Does not fit a 4 vCPU / 8 GB VPS with no GPU. | Same as (A). |
| **Offline laptop** | Yes. No new runtime packages. | Runs, but opens the laptop to anyone on the LAN. | Possible, but a second heavy stack (1.2 GB install) with Windows path problems. | Yes, if vendored. |
| **Rule 1 (no AI before the lock)** | Yes, if the AI box arrives only in the lock response and the start slice is chosen blind. | No: label maps leak through `/volume`; AI layers through `/slice` and `/screenshot`. | Possible, but outside Django's audit trail. | Our own code decides, as in (A). |
| **Rule 4 (pixels only)** | Yes: 8-bit slices only. | No: whole volumes as NRRD, DICOMweb with headers (including PatientName), any local file readable. | Yes in principle, but frames bypass Django's image window and log. | Yes with a custom loader. The stock web loader calls `getImageData` [52], which Safari corrupts on purpose [34]. |
| **Rule 6 (planted = correct look)** | Yes: one dashed style, extent checks in the loader. | Not applicable. | Possible. | Possible. |
| **Rule 7 (offline, plain HTTP)** | Yes: no CDN; `fetch`, canvas and `createImageBitmap` work on HTTP. | No: `/sampledata` calls the internet; no login at all. | Needs patches: a GitHub favicon URL and a POST to `/paraview/`. Its video mode needs HTTPS [13][14]. | Yes: no SharedArrayBuffer needed since 2.x [47]. |
| **Effort** | `read.js` +130-170 lines (575 to about 720). Python about 100 lines for UMD NIfTI only. Both are estimates. | Not viable. | Large: launcher, proxy, Linux graphics, patches; beta API. | A build step or a pre-built file of at least 3.3 MB minified that the owner cannot read. |
| **Risk for November** | Low for MRI, medium for CT. Phone decode and memory are not yet measured. | Unacceptable. | High. | High (feature freeze 21 Oct). |

### Why not Slicer's WebServer (B1)
- It is a single-user remote control. It has one scene and one set of views. It handles one
  request at a time on the Qt main loop [2].
  - Measured: 4 parallel clients gave almost no speed-up. Sequential: 48 requests in 789 ms.
    Parallel: 712 ms, and the median per request rose from 14.5 ms to 55 ms.
- It has no login. It binds to every network interface on port 2016, although its docs say
  "localhost" [1]. The docs call it "somewhat experimental and a likely security risk" [1].
- With code execution switched off (the default), any caller can still:
  - download a whole volume as NRRD, a research volume format (measured: 15,053,130 bytes, no
    login),
  - clear the scene (`DELETE /mrml`) or quit Slicer (`DELETE /system`, measured),
  - load any local file and read it back (`POST /mrml?localfile=...`, measured),
  - write a file to any path on disk (`/mrml/file?localfile=...`, measured with `.nrrd`),
  - make Slicer download from any URL (`POST /mrml?url=...`; read in the source, not tested),
  - read DICOM files and headers through the DICOMweb handler (a web API for DICOM), which is on
    by default.
- The static-page handler joins paths with no clean-up. Path traversal may be possible (not
  verified).
- `/segmentation` is a stub ("not implemented yet"), so it is not the leak path. The leak paths
  are `/volume`, `/slice` and `/screenshot`.
- With `--no-main-window`, `slicer.app.layoutManager()` is `None`, so `/slice` cannot run
  (measured twice). A Linux server with no screen would need a virtual display (Xvfb) [3].
- **Rule:** keep the WebServer module off. Do not start it even on localhost on a shared or
  venue machine.

### Why not trame-slicer (B2), yet
- trame-slicer 1.12.3 (3 Sep 2026) is marked "4 - Beta". Its README warns that the API "has
  not been stabilized" [4][5]. Four releases came out on 2-3 Sep 2026 (1.12.0 to 1.12.3).
  Licence: Apache-2.0 (the wheel's LICENSE file). Kitware calls its core features
  "production-ready" but the project "still in development" [7].
- Its optional `slicer-core` wheel (5.11.0.6, Mar 2026) is 18.6 MB on Windows and 43.3 MB on
  Linux, for Python 3.10-3.13, and pins VTK 9.6.0 [6]. The Slicer-trame extension needs Slicer
  5.10 or later and installs from the Extensions Manager [8].
- trame gives each browser its own server process through a launcher [9]. (Discussion #32 [10]
  is from 2022, trame v1.) One reviewer ran it with synthetic data:
  - One process served two browser tabs with one shared view. Five scroll steps in tab A
    caused 6 image updates in tab B. The server itself prints that multi-user use needs a
    launcher.
  - Resident memory: 386 MB after imports, 481-547 MB with the app built, 549-615 MB with a
    volume loaded and a browser rendering it.
  - Scroll step (wheel event to new frame): median 108 ms (79-114, n=20) on localhost. That is
    already above the 0.1 s limit for a response that feels instant [17].
  - Install: 181 s and a 1.2 GB virtual environment. The VTK 9.6 wheel failed to import from a
    deep Windows folder ("The filename or extension is too long").
  - The default transport was JPEG image frames of 7.6-73.5 kB. Its video mode needs WebCodecs,
    which works only on HTTPS [13][14]. On a plain-HTTP LAN only image frames work. Its client files are served locally, with no
    CDN [15].
- On a Linux server with no GPU, rendering falls back to the CPU (Mesa llvmpipe) [11][12].
  Memory and speed there were not measured.

### Why not Cornerstone3D (C), yet
- Version 5.10.11 (23 Sep 2026) ships only as ESM since 2.x. It needs a bundler or a very large
  import map [47].
- Size: `@cornerstonejs/core` 2,129,092 B minified (569,401 B gzipped); `@cornerstonejs/tools`
  1,134,153 B (300,118 B gzipped) [48][49]. That is at least 3.3 MB, and more with its peer
  packages. `@kitware/vtk.js` is 13.9 MB unpacked [50].
- It no longer needs SharedArrayBuffer or special cross-origin headers [47][54].
  SharedArrayBuffer would need a secure context anyway [53].
- A custom image loader can feed it our 8-bit pixels, which keeps rule 4 [51].
- It is the right viewer after the congress, when we need W/L on raw data, segmentation or
  reformats. Store marks as slice index plus image-pixel coordinates now, so that later move
  is cheap.

## 3. Recommended design for the stack viewer

### 3.1 Slice format and size budget
- Each slice is an 8-bit greyscale **lossless PNG**. The loader already writes this
  (`bare_pixels` then PNG).
- MRI: cap the long side at **512 px**. This keeps download and phone memory small. The UMD
  median is 560 px, and the largest cases are 1152 px. Whether 512 px loses acquired detail is
  **not verified**: the UMD protocol varies between cases (see section 5).
- The same bytes go to every reader. Never adapt quality per reader.
- Other formats, measured on real UMD (byte counts only):
  - Lossless WebP is only 5-12% smaller than PNG. It encodes 3-8 times slower and needs iOS 14
    or later [31].
  - Lossy WebP keeps only 212-220 of 256 grey levels, even at quality 100. Do not use it.
  - JPEG quality 90 is 39-42% of the PNG size. It roughly **halves** the download. This is a
    real option for slow mobile data, but it adds a lossy step to a reader study. Published
    guidance on lossy compression [32][33] applies to original 12-bit data, not to 8-bit
    windowed images; the full texts were not read. **Owner decision.**

| Content | Per case (measured) | Decoded on the phone (arithmetic) |
|---|---|---|
| UMD MRI, native size, PNG | 1.6-8.1 MB in the samples; the largest cases (1152x1152x24, 864x864x30, 800x800x32) 8.6-12.8 MB | 18-127 MB |
| UMD MRI, long side 512 px or less, PNG | 1.9-3.6 MB (3 cases); median 2.2 MB (10 cases) | 34 MB or less |
| Same, JPEG quality 90 | 0.76-1.57 MB (3 cases) | same |
| Synthetic CT, 100 x 512 x 512, soft tissue, PNG | 6.5-9.2 MB (depends on the noise) | 105 MB |
| Synthetic CT, lung window | 5.8-7.1 MB with noise-free air; 9.1-9.7 MB with realistic air noise | 105 MB |
| Synthetic CT, bone window | 5.1-6.2 MB | 105 MB |
| Synthetic CT, all 3 windows | about 20-25 MB | - |

- Real CT was **not measured**. It probably compresses worse than the synthetic phantom
  (table, texture, uneven noise).
- Transfer time (arithmetic): at 8 Mbps, a 2.2 MB MRI takes about 2 s and a 9 MB CT window
  about 9 s. At 1 Mbps per phone (30 phones sharing 30 Mbps), they take about 18 s and 72 s.
- Mobile data per reader: 10 MRI cases need about 20-35 MB. 10 CT cases need about 65-90 MB for
  the default window alone (arithmetic).
- **CT for November:** keep the plan's 2-3 pre-windowed key images unless the owner changes
  that decision. If CT stacks come later: 3-5 mm reconstructions, 120 slices or fewer per
  window, downloaded in chunks (see 3.2).

### 3.2 Request pattern, image window and access log
**One request per case and per window: a "stack file".** Not one request per slice, and not
an atlas (all slices tiled into one big image).

- Why not one request per slice:
  - A case would need 20-600 requests per reader. Each one costs a login check and a SQLite
    log write.
  - Waitress (our server) speaks HTTP/1.0 and 1.1 only. It runs 4 threads by default (the
    runbook sets no `--threads`) and accepts at most 100 connections [23][24]. Browsers open
    about 6 connections per host [25], so 30 phones could open 180.
  - The log would grow from about 300 rows to about 30,000 rows per session (30 readers x 10
    cases x 100 slices).
- Why not an atlas:
  - No byte saving. Measured: MRI 4.62 MB as an atlas against 4.63 MB as separate slices; CT
    5.95 MB against 6.06 MB.
  - A 100-slice CT atlas decodes as one 100 MB block, and nothing shows until all of it has
    arrived. (The iOS canvas-area limit of 16.7 megapixels [26] applies to canvas elements,
    not directly to decoded images. It is not the reason.)
- **Stack file layout:** `NSTK` + a 4-byte slice count + for each slice a 4-byte length and
  then the PNG bytes. No metadata, names or positions. Parsing it took 12 lines of JavaScript
  and 0.6-1.9 ms in desktop Chromium.
- **Route:** `GET /i/<alias>/<window>/` returns the whole stack file.
- **What stays the same:** the image window (current case plus or minus 1), the random
  per-reader alias, and one `ImageAccess` row with a SHA-256 per response
  (`reading/flow.py` `image_bytes`).
- **What changes:**
  - Add a `window` column to `ImageAccess`.
  - Compute the SHA-256 once at load time, not per request. Stream the file with
    `FileResponse` instead of reading 9 MB into memory. (Waitress spools responses over 1 MB
    to a temporary file [24].)
  - Scale the image timeouts with the file size. Today `read.js` restarts every retry from
    zero: the first image try stops at 30 s, then 60, 120 and 240 s. The prefetch makes one try
    and stops at 60 s. The server logs an allowed row when it reads the file, not when the
    download ends. At 1 Mbps, a 9 MB stack (about 72 s) creates 4 allowed rows before it
    succeeds.
  - For CT, split each window into chunks of 2 MB or less, or read the response as it
    streams with the middle slice first. For MRI (2-3.5 MB) one file is fine.
- **Tripwire (rules for suspicious requests):** during the workshop, record and flag; never
  refuse on the count alone. Retries, reloads (images are `no-store`), iOS discarding a tab and
  failed prefetches all add honest rows. M1 sent 18 images for 16 AI reveals. Set the threshold
  from the M2 logs. Count per account, never per IP address.
- **Prefetch:** download only the next case's default window. Keep it as bytes; do not decode
  it.
- **Progress:** show "1.2 of 2.9 MB" while loading. Start the reading timer when the start
  slice is on screen and the stack is complete. Log the load time separately.

### 3.3 Decoding and phone memory
- Split the stack file into Blobs. Decode each slice with `createImageBitmap`. Keep the
  existing fallback (an `Image` from an object URL).
- **MRI (32 slices or fewer, 512 px):** decode the whole stack (34 MB or less). This is simpler
  than a cache.
- **CT:** an LRU cache of 48 decoded slices or fewer. Call `.close()` on each evicted slice.
  48 slices take 50 MB at 512 px and 79 MB at 640 px. Pre-decode 3 slices on each side of the
  current one. During a fast flick, decode only the latest requested slice.
- Keep the compressed bytes of every opened window, so a return to a window needs no new
  download.
- Why this matters: iOS ends a tab that uses too much memory, and the page reloads [28].
  - iOS Safari limits total canvas memory to 384 MB (iOS 15) and 224 MB (iOS 12) [27].
  - Per-page limits land around 300-450 MB on most current iPhones, lower on old ones [28]
    (anecdotal).
  - ImageBitmaps report their memory cost to WebKit since bug 187964 was fixed [29].
  - Only Chrome decodes `createImageBitmap` off the main thread; Safari is slow [30].
  - These limits come from 2018-2026 sources and were **not checked on iOS 17-26**.
- Minimum browsers: `createImageBitmap` needs Safari 15 or later (a reviewer's figure, not
  re-checked). The `Image` fallback has no
  `close()`, so old iPhones free memory less predictably.
- **Gate before building:** a synthetic test page on the owner's Samsung S21 and on at least
  one iPhone (also in a Private tab), over the LAN address. Measure decode time per slice,
  scroll smoothness, and memory with a 120-slice CT.

### 3.4 Window/level
- **MRI:** one fixed window per volume, from whole-volume percentiles.
  - Start with **0.1-99.9**, the rule Slicer 5.12.4 uses for its automatic window (from its
    source code [68]). Then the phone looks like the owner's Slicer view during checks. If the
    phone looks too flat, try 0.5-99.5. It is one number in the script.
  - Never window each slice on its own. Measured on 3 UMD volumes: per-slice p99.5 divided by
    volume p99.5 was 0.72-1.05, 0.63-1.04 and 0.94-1.10. On the central 60% of slices it was
    0.94-1.05. So per-slice windows would make the outer slices jump by up to about 35% in
    brightness.
  - Bright fluid (bladder, cysts) can squeeze the uterine contrast. The owner checks this on
    the phone.
- **CT:** 2-3 presets made on the server, from Radiopaedia [73]: soft tissue W400 L50, lung
  W1500 L-600, bone W1800 L400. The default window downloads first. The others download only
  when the reader taps them. A tap keeps the slice index and the zoom.
- **No W/L on the phone for November.**
  - Never read pixels back with `getImageData`. Safari's Advanced Fingerprinting Protection
    adds noise to canvas readback. It is on by default in Private Browsing and optional for all
    browsing [34][35]. Firefox's fingerprint protection broke the same trick for Mapbox [36].
  - `ctx.filter` is disabled in Safari [39][40].
  - A CSS `brightness()`/`contrast()` filter on the image canvas, with the AI box on a second
    canvas on top, is possible in about 15-20 lines. But on 8-bit data it cannot bring back
    clipped values, so it is not true W/L.
- **After the congress:** send raw 16-bit (or raw 8-bit) values, compressed with gzip. Use a
  lookup table and `putImageData` to apply W/L on the phone. With `Content-Encoding: gzip`,
  `fetch` decompresses natively, also on plain HTTP. `DecompressionStream` also works on HTTP
  (the spec has no secure-context rule [37]; needs Safari 16.4 or later [38]), but tests ran only
  on localhost. Synthetic 16-bit CT was 131-149 KB per slice, about 13-15 MB per 100 slices.
  The phone then holds full Hounsfield values, which is more data to leak. The alternative is
  Cornerstone3D with a custom loader.

### 3.5 Touch gestures
- **More than 1 slice:**
  - One finger dragged vertically changes the slice. Lock the direction after 10 CSS px.
  - Distance per slice: max(4, frame height / max(n, 8)) CSS px, adapted from Cornerstone3D's
    `StackScrollTool` (which uses max(2, ...)) [45]. On a 360 px frame: 15 px per slice for 24
    slices, 4 px for 90 or more.
  - Dragging down goes to the next slice (Cornerstone3D's default). Confirm the direction with
    2-3 radiologists.
  - Two fingers pinch to zoom and pan with the midpoint. `read.js` already does this.
  - Double-tap resets zoom and pan, not the slice.
- **1 slice (X-ray):** keep today's one-finger pan. Moving pan to two fingers on stacks changes
  a gesture the owner approved in M1, so retest it.
- A full-width slider under the frame, with 44 px step buttons and a "Slice 12 / 24" label. The
  same number shows in a corner of the frame.
- Desktop: the mouse wheel changes the slice; Ctrl + wheel (or a trackpad pinch) zooms. Arrow and
  Page keys step through slices.
- Single taps stay free for "tap to mark a point".
- Evidence for the one-finger pattern is thin:
  - A 2016 platform-independent plugin (Balkman and Awan, Dartmouth; not a Radiopaedia plugin)
    uses a single-finger swipe to scroll and two fingers to zoom and pan [41].
  - IMAIOS e-Anatomy scrolls "by dragging your finger" [43].
  - CaseStacks needs a Scroll mode first; pinch and two-finger pan work in every mode [42].
  - Cornerstone3D's example uses 1 finger for W/L, 2 for zoom and 3 for scrolling [44].

### 3.6 Start slice
- Every case opens on the **middle slice**. Never on the key slice: a stack that opens on the
  lesion would give the answer before the lock (rule 1).
- Send the whole acquired stack. Do not crop or trim it around a lesion. The slice range,
  crop and slab rules must be identical for positive and negative cases.
- The slice count and the file size are visible before the lock. They depend on anatomy, so the
  risk is low. The loader refuses a study where the slice-count ranges of two answers (at least
  2 stacks each) do not overlap. It cannot detect a different slab rule in any other way, so the
  prep script must send the whole acquired stack for every case, positive or negative.

### 3.7 AI box per slice
- The AI box becomes `{"slices": [first, last], "rect": [x, y, w, h]}` in image pixels. It
  arrives only in the response to the lock (`POST /first`). It is never part of the stack file
  or the prefetch.
- It is drawn only on those slices, in the one dashed `--ai` style. The slider shows the same
  `--ai` tick for every suggestion.
- On reveal, the viewer jumps to the middle slice of the range. It does this for every
  suggestion, planted or correct.
- The loader extends today's checks in `reading/studyfiles.py` (planted confidences within the
  range of correct ones; for one answer, all suggestions have a box or none). New checks:
  planted box sizes and slice spans lie within the range of the correct ones.
- If boxes or masks come from Slicer, set them to the one neutral colour at export (rule 6).

## 4. Recommended data pipeline

One script, for example `prep/umd_stack.py`, runs on the owner's PC with `uv run --group prep`.
It writes to a dataset folder outside the repo. For the first test: UMD NIfTI only, sagittal
plane only, no resampling, no DICOM. That is about 100 lines (estimate).

### 4.1 NIfTI now (UMD)
1. **Load.** `img = nib.load(path)`. Refuse more than 3 dimensions. Read
   `np.asanyarray(img.dataobj)` (this applies any scaling) and `img.affine`. Never read or
   copy `descrip`, `aux_file`, `intent_name`, header extensions, JSON sidecars, or file and
   folder names. (A **sidecar** is a small text file that dcm2niix writes next to each NIfTI.)
2. **Check the mask.** Assert that the mask's affine and shape equal the image's. In the local
   UMD copy all 300 pairs match. The raw UMD release had 33 masks with placeholder geometry.
3. **Orient.** Permute and flip the axes to fixed display codes, (row, column, slice)
   [69][70]:

   ```python
   TARGET = {"sagittal": ("I", "P", "L"), "axial": ("P", "L", "I"), "coronal": ("I", "L", "P")}
   t = ornt_transform(io_orientation(img.affine), axcodes2ornt(TARGET[plane]))
   vol = apply_orientation(vol, t)
   mask = apply_orientation(mask, t)
   ```

   - Result: sagittal has superior at the top and anterior on the left; axial has anterior at
     the top and patient right on screen left; coronal has superior at the top and patient
     right on screen left. These are the radiology conventions [64][65]. Neuroimaging tools
     can differ, so do not copy their display [66].
   - Checked on all 300 UMD affines: 300/300 came out as IPL. Synthetic markers landed where
     expected.
   - Sagittal slice 0 is the patient's right. Which way a sagittal stack should scroll has no
     source; it is a free choice.
   - These functions only permute and flip. A slightly oblique scan is shown as acquired, as a
     PACS does.
4. **Plane.** Show only the acquired plane (the axis with the largest spacing). No reformats
   when slice spacing is more than about 2 times the in-plane spacing. UMD: 7-21 times (median
   13.3), so no reformats. Isotropic 3D sequences (hospital data later) need a tie-break rule.
5. **Square pixels.** If row and column spacing differ by more than 1%, resample (linear for the
   image, nearest-neighbour for the mask). All UMD pixels are square.
6. **Window to 8 bits** (section 3.4). CT: Hounsfield units (HU) = RescaleSlope x stored value
   + RescaleIntercept [77]. This holds for original, non-localizer, single-energy CT [74]. For
   MONOCHROME1 (minimum shown as white), invert after windowing [75].
7. **Downsample** to a long side of 512 px or less (LANCZOS for the image, nearest for the
   mask).
8. **Truth and AI box** from the mask, in the final display space (section 5).
9. **Output:** neutral case codes; slices `000.png` to `NNN.png` as bare 8-bit PNGs;
   `cases.csv` with the AI slice range. The map from case code to UMD ID stays in the private
   dataset folder. UMD IDs are public, so a reader could look up the truth with them.
10. **Site loader:** re-save every slice through `bare_pixels`. Check that all slices have one
    size, that there are at least 2 slices, and that the AI slice range fits. **Refuse any slice
    that is not 8-bit.** Today `bare_pixels` stretches each 16-bit image to its own range, which
    would silently window each slice on its own.

### 4.2 Where Slicer fits now
- **Orientation reference.** Slicer 5.12.4's default views use the same conventions (read from
  its source [67] and measured headlessly): axial screen-right is patient left and up is
  anterior; sagittal screen-right is posterior and up is superior; coronal screen-right is
  patient left and up is superior.
  - This depends on a user setting (Settings > Views: patient right is screen left). The
    owner's `Slicer.ini` has the default (read-only check).
  - Slicer reslices along the patient axes. On the 16 UMD cases tilted more than 5 degrees, its
    view blends neighbouring slices, while the phone shows the acquired slices. Orientation
    matches, pixels do not. Use "Rotate to volume plane" for a like-for-like check.
- **First simple exercises for the owner:** load a UMD image and its mask (as a segmentation),
  scroll the three views, adjust W/L, look at label 4, and compare with the phone.
- **Later:** import hospital DICOM (the DICOM module sorts series), check burned-in text by eye,
  and draw boxes or ground truth as Markups, exported to JSON.
- Slicer's Python can also run the prep script (measured: NIfTI load 0.08-0.12 s). A nibabel
  script in the uv project is easier for the owner to read and re-run.

### 4.3 DICOM later (hospital MRI and CT)
- **Screen each series from headers only** (pydicom with `stop_before_pixels`). Allowlist:
  - SOP Class (the DICOM object type) CT Image (1.2.840.10008.5.1.4.1.1.2) or MR Image (1.2.840.10008.5.1.4.1.1.4).
    Enhanced CT and Enhanced MR (multi-frame) only through dcm2niix, because the simple sorter
    reads one position per file.
  - ImageType value 1 = ORIGINAL. This also excludes MPR reformats (multiplanar reformats:
    slices re-cut in another plane, marked DERIVED\SECONDARY)
    that CT readers often use. Make that an explicit decision.
  - ImageType value 3 not LOCALIZER. **This works for CT only.** MR has no LOCALIZER term
    [76], so MR localizers need other guards: at least about 10 slices, one orientation, and
    perhaps a SeriesDescription pattern.
  - BurnedInAnnotation (0028,0301) not YES; Modality CT or MR.
  - Refuse Secondary Capture, Structured Reports (including the Radiation Dose SR),
    Presentation States, Encapsulated PDF and Raw Data.
- **Split or choose series.** Multi-echo, Dixon, diffusion and dynamic MR series share slice
  positions. Split them (by EchoTime, ImageType, b-value or TemporalPositionIdentifier), or let
  the owner choose one 3D series per case. Refuse 4D.
- **Sort slices** by the position projected on the slice normal: dot(ImagePositionPatient,
  cross(row cosine, column cosine)). Never by InstanceNumber or SliceLocation; the standard
  defines SliceLocation only against "an unspecified implementation specific reference point"
  [71]. A synthetic shuffled series proved the sort.
  - PixelSpacing is [row spacing, column spacing] [71].
  - Refuse duplicate positions, spacing that varies by more than about 10%, or gantry tilt
    (these thresholds are design choices, not sourced).
  - DICOM coordinates are LPS (x toward the patient's Left, y Posterior, z Superior). nibabel
    uses RAS (Right, Anterior, Superior). Multiply by diag(-1, -1, 1), then use the NIfTI path
    [72].
- **Compressed DICOM.** JPEG 2000 needs pylibjpeg-openjpeg (MIT) [91]. JPEG Lossless needs
  python-gdcm (Apache-2.0, 34 MB) [90], pylibjpeg-libjpeg (GPLv3) [89] or dcm2niix. Whether
  IKHC CT and MR are stored compressed is not known.
- **De-identification.** Only pixels leave the pipeline (rule 4).
  - NIfTI can carry identifiers in `descrip` (80 characters), `aux_file`, `intent_name`,
    `db_name`, header extensions (code 2 is a full DICOM header), file names and JSON sidecars
    [78].
  - dcm2niix by default names files `%f_%p_%t_%s` (folder, protocol, time, series), writes
    "TE=..;Time=.." into `descrip`, and copies ImageComments into `aux_file` [79][80][81]. Its
    default `-ba y` strips patient name, ID and dates from the sidecar, but institution, station
    and device serial number remain.
  - A local folder of hospital dcm2niix output shows this: 92 files; every file name starts with
    6 or more digits and contains a date; all 41 sidecars hold institution, station and
    serial-number keys (no patient-name or ID keys). Its 41 volumes mix orientations (LAS 16,
    RAS 16, PSR 5, LSP 4), 3 are 4D, and 5 series are diffusion.
  - CT originals "do not normally contain" burned-in text [82]. The standard says nothing about
    MR, so the MR half is unsourced. Dose screens, screenshots, Secondary Capture and scanned
    PDFs do carry text [83].
  - Head CT and MR stacks allow a face to be rebuilt (MIDI best practice 15 [83]). They need a
    policy before use.
- **The owner's eye check** now covers 24-120 slices per case instead of one image. Claude may
  not view real images. A contact-sheet page (all slices on one screen) or a written policy is
  needed.
- The full DICOM pipeline is several hundred lines (estimate). Keep it out of this milestone.

### 4.4 Packages
| Package | Version, licence | Where | Needed for |
|---|---|---|---|
| nibabel | 5.4.2, MIT, pure Python, 3.3 MB [84] | prep group | NIfTI load and orientation. **Add now.** |
| scipy | 1.18.1, BSD, 36.7 MB wheel [85] | prep group | Only for counting myoma components |
| pydicom | 3.0.2, MIT [86] | prep group (already there) | DICOM later |
| dcm2niix | 1.0.20260724, BSD-2 text with a "research purposes only" notice, 2.6 MB [88] | prep group, later | Enhanced DICOM, awkward series |
| SimpleITK | 2.5.6, Apache-2.0, 18.9 MB [87] | not needed | - |

- The Django app and the offline venue laptop need none of these.
- `uv run --offline --with nibabel --with scipy` worked from the local cache with the network
  off [92].

## 5. UMD: the first MRI test data

### 5.1 Provenance, licence and citation
- **Paper:** Pan H, Chen M, Bai W, Li B, et al. "Large-scale uterine myoma MRI dataset covering
  all FIGO types with pixel-level annotations." *Scientific Data* 2024;11:410.
  doi:10.1038/s41597-024-03170-x. Received 2023-07-10, published 2024-04-22 [59][60].
- **Data:** figshare, one file `UMD.zip` of 4,759,295,077 bytes, DOI
  10.6084/m9.figshare.23541312.v3, published 2024-01-18 [61][62]. (The paper says 4.12 GB.)
- **Licence:** CC BY 4.0 for the data and the article [63]. Use is allowed with credit.
- **Credit:** CC BY credit must reach the people who see the images. Put one line on the site
  (study description or intro page): paper, figshare DOI, licence link, and "modified:
  reoriented, windowed to 8 bits, downsampled, yes/no answers derived from the masks". Also
  keep it in the README. The figshare DOI is only in the README: its 8-digit run makes the
  loader refuse the study description (the long-number check, rule 4). The site line gives the
  paper DOI, which links to the data, and the licence link.
- **Cohort:** 300 patients aged 21-86 (mean 49.73). One Philips Ingenia 3.0T at Beijing
  Shijitan Hospital, 2015-2023. Sagittal T2. Every case is a surgically and pathologically
  confirmed myoma. 56 were excluded: 26 with multiple intractable myomas, 7 too small, 15 with
  artefacts, 8 with low resolution.
- **The stated protocol does not fit every case.** The paper states FOV 24 x 24 cm and
  4.0 mm slices with a 0.4 mm gap. The local files have FOV 248-400 mm and slice spacing
  4.4-7.5 mm. So the data mix protocols.
- **Labels:** 1 uterine wall, 2 cavity (including the junctional zone), 3 myoma, 4 Nabothian
  cyst. The paper also calls label 4 "nacelle" and "capsule". **Confirm label 4 by eye on a few
  cases before it becomes truth.**
- **Local copy:** only `D:\UMD\data\nnUNet_raw\Dataset501_UMDMyoma` (300 images, 300 masks).
  - The images match the source byte for byte (manifest hashes, 300/300). The masks were
    re-saved as uint8.
  - 33 source masks were named `*_seq.nii.gz` but were not compressed and had placeholder
    geometry. The prep code copied the image geometry into them. One more mask (case 037) had a
    file-name typo.
  - `D:\UMD\UMD` and `D:\UMD.zip` are gone, although `D:\UMD\README.md` calls them "immutable
    inputs". The owner should know. The original DICOM, and any clinical table, need the
    4.76 GB download again. The paper lists no per-case FIGO table (unlikely, not proven).
- **Geometry (all 300, from headers):** orientation PIR; the slice axis is always array axis 2
  (left-right, so sagittal); 20-32 slices; in-plane 480-1152 px, always square; slice spacing
  7-21 times the pixel size; tilt median 1.2 degrees, p90 4.0, max 11.6. No header text, no
  extensions.

### 5.2 Candidate yes/no questions
"Myoma present?" cannot work: every case has a myoma.

| Question | Counts (all 300 masks, numbers only) | Verdict |
|---|---|---|
| **"Nabothian cyst?"** | Present in 127, absent in 173. Key-slice equivalent diameter median 5.7 mm (p10 2.7 mm). 3 mm or more: 111; **5 mm or more: 72**; 8 mm or more: 29. A cyst spans a median of 2 slices; 25% sit on 1 slice. At 512 px the box is about 14 x 13 px (p10 about 5 px). | **Best first test.** Positives: 5 mm or more (72). Negatives: no label 4. It exercises scrolling, zoom and a small box. Clinically minor. |
| "More than one myoma?" | Clearly single: 97 (exactly one component of 0.1 mL or more). Clearly multiple: 120 (two or more of 1 mL or more). Ambiguous: 83. No component of 1 mL or more: 50. | Later, with the clear classes only and radiologist sign-off. Touching myomas share one label and merge. |
| "Submucosal (touching the cavity)?" | Any contact: 86. 5% or more of the border: 44; 10% or more: 23; 25% or more: 12 (not re-checked). | **Do not derive.** Contact is a continuum, and the cavity label includes the junctional zone. |

- Negatives rely on complete annotation. The paper does not say every cyst was drawn. Every
  chosen negative needs a radiologist's look.
- **Real AI suggestions already exist.** nnU-Net is a standard self-configuring segmentation
  model. One reviewer found out-of-fold nnU-Net results for all
  300 cases (`D:\UMD\reports\evaluation\per_case_class_metrics.csv`, about 1,920 prediction
  files under `D:\UMD\models\nnUNet_results`). "Out-of-fold" means each case was predicted by
  a model that did not train on it. Cyst presence, `ensemble_2d_3d` model: 85 true positives,
  42 false negatives, 25 false positives, 148 true negatives (`3d_fullres`: 89/38/23/150).
  - These give real AI boxes with natural errors, instead of or next to planted ones.
  - The 25 false positives are the first negatives to re-check: they may be cysts nobody drew.
  - Wrong suggestions, real or planted, still need the consent wording, suspicion question and
    debrief (rule 5).
  - Later tools for AI-assisted labelling in a web viewer exist (OHIF-AI [58], MONAI Label
    [57]). OHIF-AI bundles cloud language-model backends that must stay off (rule 7).
  - These counts come from one reviewer and were not re-checked.

### 5.3 Key slice and box rules
- **Key slice:** the slice with the largest area of the target label, computed in the final
  display space (after orientation and downsampling).
- **Box:** the bounding box of the largest 2D piece of the label on that slice. Use one shared
  padding and minimum-size rule for all boxes, so correct and planted boxes have the same size
  distribution (rule 6). Store the slice range the box covers.
- Cysts sit near the midline: median position 0.48 of the stack, a median of 1 slice from the
  slice with the most uterine wall.
- **Planted false-positive boxes** need a plausible cervical or midline slice. The nnU-Net
  false positives provide such boxes naturally.
- The case still opens on the middle slice (section 3.6).

## 6. Measurements

Tracks: **S** = server Slicer, **V** = phone viewer, **D** = data pipeline; "-rev" = a
skeptic's re-run.

| What | Result | How (by) |
|---|---|---|
| Slicer 5.12.4 start to exit | 2.25-2.39 s with no main window; 2.97-3.09 s with it (3 runs each) | `--ignore-slicerrc --no-splash --disable-settings --exit-after-startup`, wall clock (S) |
| Slicer memory before and after a 15 MB synthetic volume | No main window: 337 to 369 MB. Main window: 398 to 431 MB, 453 MB after rendering | Windows working set via `K32GetProcessMemoryInfo` (S) |
| `/slice` with `--no-main-window` | `layoutManager()` is None: cannot run | Script check (S, S-rev twice) |
| WebServer `/slice`, one client | median 8.8 ms and about 1 MB per slice (573x446 RGBA PNG, no compression) | curl on localhost, synthetic 560x560x24 (S) |
| WebServer `/slice`, parallel clients | 4 x 12 requests: 0.46 s in total. S-rev: 48 requests 789 ms sequential, 712 ms with 4 in parallel (median 14.5 to 55 ms) | curl (S, S-rev) |
| WebServer output size | 296x207 px in the default layout (about 245 kB), 969x539 in one-up (about 2.09 MB) | curl (S-rev) |
| WebServer with exec off | `/volume` returned 15,053,130 bytes; any local file loaded and read back; a file written to a chosen path; `DELETE /system` quit Slicer | curl, synthetic files only (S, S-rev) |
| Slice render and PNG encode inside Slicer | numpy to PNG: 2.8 ms (no compression) or 8.6-9.0 ms (level 6); slice-logic pipeline: 6.6 ms or 36.3 ms; view grab: 32.7 ms | `time.perf_counter`, 24 synthetic slices (S) |
| trame-slicer 1.12.3 session | Resident memory 549-615 MB with a volume and a browser; 108 ms median per scroll step (79-114, n=20); one shared view across tabs; 181 s and 1.2 GB install | psutil every 5 s; browser JavaScript timing; synthetic volume (S-rev) |
| UMD stack sizes, native size | PNG 1.6-8.1 MB per volume (four samples of 5-10 volumes); largest cases 8.6-12.8 MB PNG, 2.7-4.0 MB JPEG q85 | Pillow and VTK writers in memory, byte counts only (S, S-rev, V, V-rev) |
| UMD stack sizes, long side 512 px or less | PNG median 2.2 MB (10 volumes); 1.9-3.6 MB (3 volumes); JPEG q90 0.76-1.57 MB; lossless WebP 1.64-3.18 MB | Pillow in memory (V, D, D-rev) |
| JPEG against PNG on UMD | q90 = 39-42% of the PNG size; q95 = 55-58% | 5 volumes (V-rev) |
| Grey levels kept on a 0-255 ramp | Lossy WebP: 212-220 (q90-q100); JPEG q90/q95 and lossless WebP: 256 | Pillow round trip (V, V-rev) |
| Synthetic CT, 100 x 512 x 512 | Soft tissue 6.5-9.2 MB; lung 5.8-7.1 MB (clean air) or 9.1-9.7 MB (noisy air); bone 5.1-6.2 MB; 16-bit gzip 13-15 MB | Pillow; phantoms (V, V-rev) |
| Atlas against separate slices | MRI 4.62 against 4.63 MB; CT 5.95 against 6.06 MB; gzip over joined PNGs saves 0% | Pillow (V, V-rev) |
| Desktop Chromium 152 (not a phone) | Decode: PNG 0.9-1.5 ms, lossless WebP 1.5-3 ms, JPEG 0.9-1.4 ms per slice; draw 1.2-2 ms at 1080 px; 100 CT slices in parallel 25-36 ms; stack-file parse 0.6-1.9 ms | Synthetic test page on 127.0.0.1 (V) |
| Canvas readback in Chromium | 16-bit packed in PNG and 8-bit grey: exact | `getImageData` (V). Safari not tested; it adds noise by design. |
| UMD geometry, all 300 | PIR 300/300; slice axis 2; 20-32 slices; 480-1152 px; square; spacing ratio 7.0-21.1 (median 13.3); tilt median 1.2, p90 4.0, max 11.6 degrees; text fields empty | nibabel headers (D, D-rev x2) |
| UMD per-slice brightness | Per-slice p99.5 / volume p99.5: 0.72-1.05, 0.63-1.04, 0.94-1.10; central 60%: 0.94-1.05 | numpy percentiles on 3 volumes (D, D-rev) |
| Orientation recipe | Synthetic markers correct for sagittal (NIfTI) and axial (shuffled DICOM); all 300 UMD affines give IPL | orient_test.py, dicom_test.py (D, D-rev) |
| Slicer default view matrices | Axial x = patient left, y = anterior; sagittal x = posterior, y = superior; coronal x = patient left, y = superior | headless Slicer (D) and source at v5.12.4 (D-rev) |
| UMD labels | See section 5.2 | nibabel + scipy over 300 masks, numbers only (D, D-rev x2) |
| Load and reorient per UMD volume | 0.04-0.25 s | `time.perf_counter` (D, D-rev) |

## 7. What stays open

### Decisions for the owner
1. **Approve the direction:** Slicer on your PC as your tool; the phone gets prepared stacks.
2. **Order of work:** finish M1 with one ADIR radiologist first (CLAUDE.md rule). Then write a
   short decision record that changes "CT: key images, no scrolling" in `docs/plan.md`, or
   limits the stack viewer to MRI. The feature freeze is 21 Oct.
3. **Online or offline as the main workshop mode.** A nationwide blackout ran from 8 Jan 2026;
   the order to end it came on 25 May. It cut mobile data. Experts report the domestic
   National Information Network was also fully disconnected at times. Since then, access has
   been slow, with a whitelist [18][19]. `docs/plan.md` says "the domestic network mostly stayed
   up"; this source disagrees. The network figures do not predict November:
   - Jan 2025: 38.88 Mbps mobile median [22]. Oct 2025: 56.6 Mbps down, 26 ms idle latency to
     the nearest test server [16].
   - meter.net: median ping 99 ms, median download 9.08 Mbps [21].
   - H1 2026: 8.1 Mbps median and 187 ms, a small sample measured mostly to Frankfurt [20].
   Consider making the laptop kit the primary plan.
4. PNG (exact) or JPEG quality 90 (half the download) for stacks.
5. Which yes/no question. The cyst question is easy to derive but clinically minor. Ask the
   radiologist partner.
6. Confirm label 4 by eye on a few cases. Re-check the chosen negatives, first the 25 nnU-Net
   false positives.
7. Use real nnU-Net errors, planted errors, or both.
8. Scroll direction (drag down = next slice?) and the start slice (middle for every case).
9. MRI window: 0.1-99.9 (matches Slicer) or 0.5-99.5 (more contrast).
10. The burned-in-text check for stacks: a contact-sheet page or a written policy.
11. A policy for head CT and MR (face reconstruction).
12. The folder `D:\UMD\single_test\data_001` has hospital file names that start with long
    numbers and dates. Rename it or keep it out of shared places.
13. Re-download UMD (4.76 GB) only if you need its DICOM or clinical tables.
14. nnInteractive's code is Apache-2.0, but its official model weights are CC BY-NC-SA 4.0
    (non-commercial) [55]. Check this before any commercial use. MONAI Label is Apache-2.0
    [57].
15. Do you also want Slicer as a hands-on laptop exercise for attendees? That is a different
    goal from phone reading and needs its own plan.

### Not verified
- Decode speed, scroll smoothness and memory on real phones (Android Chrome, iPhone Safari,
  Private tab) over plain HTTP on the LAN. Only desktop Chromium on localhost was measured.
- iOS memory limits on iOS 17-26, and whether ImageBitmaps count toward the canvas limit.
  The per-device limits [28] are anecdotal.
- Real CT sizes (only synthetic CT was measured).
- `DecompressionStream` and `Content-Encoding: gzip` on a plain-HTTP LAN address (the spec
  allows it; only localhost was tested).
- trame-slicer memory, CPU and frame rate on Linux with no GPU; its behaviour on phone touch.
- Server-side request forgery through `POST /mrml?url=` and path traversal in the static handler
  of Slicer's WebServer (read in the source, not tested).
- Whether 512 px loses acquired detail in UMD (the protocol varies).
- Whether every Nabothian cyst in UMD was annotated.
- The contact percentages for "submucosal" and the "1-3 slices" cyst position (not re-run).
- The nnU-Net cyst counts (one reviewer only).
- Whether MR originals ever carry burned-in text; the claim that CT dose sheets carry
  demographics (search snippets only).
- Whether IKHC CT and MR are stored compressed; whether dcm2niix handles MONOCHROME1.
- nninteractive-server with 12-30 users. Its `--max-sessions` default is reported as 3, and each
  session holds its own image on the GPU [55].
- Loaded network latency in a crowded congress hall; whether a new VPS domain is reachable under
  the whitelist.
- Gesture sources [41][42][43] were read partly through search snippets (captcha or errors).
- Guidance on lossy compression [32][33]: only metadata was read, not the full texts.

## 8. Sources

1. 3D Slicer docs, WebServer module: https://slicer.readthedocs.io/en/latest/user_guide/modules/webserver.html
2. 3D Slicer source, SlicerRequestHandler.py: https://github.com/Slicer/Slicer/blob/main/Modules/Scripted/WebServer/WebServerLib/SlicerRequestHandler.py
3. Slicer Discourse, running Slicer on a headless server (May 2020): https://discourse.slicer.org/t/running-slicer-on-headless-server-installing-extensions-and-more/11689
4. trame-slicer on GitHub: https://github.com/KitwareMedical/trame-slicer
5. trame-slicer on PyPI: https://pypi.org/project/trame-slicer/
6. slicer-core on PyPI (JSON): https://pypi.org/pypi/slicer-core/json
7. Kitware, trame-slicer announcement (20 Nov 2025): https://www.kitware.com/trame-slicer-announcement/
8. Slicer Discourse, Slicer-trame extension (1 Dec 2025): https://discourse.slicer.org/t/new-extension-slicer-trame-bringing-3d-slicer-to-the-web/45298
9. trame Docker README: https://github.com/Kitware/trame/tree/master/docker
10. trame Discussion #32 (Jan 2022): https://github.com/Kitware/trame/discussions/32
11. trame-slicer Docker README: https://github.com/KitwareMedical/trame-slicer/tree/main/docker
12. trame deployment with Docker: https://kitware.github.io/trame/guide/deployment/docker.html
13. trame-rca: https://github.com/Kitware/trame-rca
14. MDN, VideoDecoder: https://developer.mozilla.org/en-US/docs/Web/API/VideoDecoder
15. trame static web client tools: https://trame.readthedocs.io/en/latest/tools.www.html
16. WANA, Speedtest Global Index for Iran, Oct 2025: https://wanaen.com/irans-internet-speed-improves-in-october-rankings/
17. Nielsen Norman Group, response time limits: https://www.nngroup.com/articles/response-times-3-important-limits/
18. Wikipedia, 2026 Internet blackout in Iran (fetched 2026-09-24): https://en.wikipedia.org/wiki/2026_Internet_blackout_in_Iran
19. Filterwatch, technical breakdown of the January 2026 shutdown: https://filter.watch/english/2026/01/16/investigative-report-technical-breakdown-of-the-january-2026-shutdown/
20. SpeedOf.Me, Iran: https://speedof.me/internet-speed/iran
21. meter.net, Iran statistics: https://www.meter.net/stats/country/iran/
22. DataReportal, Digital 2025: Iran: https://datareportal.com/reports/digital-2025-iran
23. Waitress documentation: https://docs.pylonsproject.org/projects/waitress/en/stable/
24. Waitress arguments: https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
25. Chrome's 6 TCP connections limit: https://medium.com/@hnasr/chromes-6-tcp-connections-limit-c199fe550af6
26. PQINA, canvas area exceeds the maximum limit: https://pqina.nl/blog/canvas-area-exceeds-the-maximum-limit/
27. PQINA, total canvas memory use exceeds the maximum limit: https://pqina.nl/blog/total-canvas-memory-use-exceeds-the-maximum-limit/
28. Catch Metrics, RAM internals in WebKit: https://www.catchmetrics.io/blog/deep-dive-ram-internals-webkit
29. WebKit bug 187964, ImageBitmap memory cost: https://bugs.webkit.org/show_bug.cgi?id=187964
30. Ludicon, image loading on the web (May 2026): https://www.ludicon.com/castano/blog/2026/05/image-loading-on-the-web/
31. CSS-Tricks, WebP support in iOS 14: https://css-tricks.com/webp-image-support-coming-to-ios-14/
32. CAR guideline on irreversible compression (J Digit Imaging 2013): https://pmc.ncbi.nlm.nih.gov/articles/PMC3649051/
33. ESR position paper on lossy compression (Insights Imaging 2011): https://link.springer.com/article/10.1007/s13244-011-0071-x
34. WebKit, Private Browsing 2.0: https://webkit.org/blog/15697/private-browsing-2-0/
35. Lapcat Software, Safari fingerprinting protection (Sep 2025): https://lapcatsoftware.com/articles/2025/9/4.html
36. Mapbox GL JS issue #12997: https://github.com/mapbox/mapbox-gl-js/issues/12997
37. WHATWG Compression Streams spec: https://compression.spec.whatwg.org/
38. MDN, DecompressionStream: https://developer.mozilla.org/en-US/docs/Web/API/DecompressionStream
39. Can I use, CanvasRenderingContext2D.filter: https://caniuse.com/mdn-api_canvasrenderingcontext2d_filter
40. MDN, CanvasRenderingContext2D.filter: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/filter
41. Balkman and Awan, J Digit Imaging 2016: https://pmc.ncbi.nlm.nih.gov/articles/PMC4879031/
42. CaseStacks, how to use the DICOM viewer: https://casestacks.com/help/how-to-use-dicom-viewer
43. IMAIOS e-Anatomy, App Store: https://apps.apple.com/us/app/imaios-e-anatomy/id334876403
44. Cornerstone3D, touch events: https://www.cornerstonejs.org/docs/concepts/cornerstone-tools/touchevents/
45. Cornerstone3D, StackScrollTool.ts: https://github.com/cornerstonejs/cornerstone3D/blob/main/packages/tools/src/tools/StackScrollTool.ts
46. OHIF issue #6292 (23 Sep 2026): https://github.com/OHIF/Viewers/issues/6292
47. Cornerstone3D 2.x migration guide: https://www.cornerstonejs.org/docs/migration-guides/2x/general/
48. Bundlephobia, @cornerstonejs/core: https://bundlephobia.com/package/@cornerstonejs/core
49. Bundlephobia, @cornerstonejs/tools: https://bundlephobia.com/package/@cornerstonejs/tools
50. npm registry, @kitware/vtk.js: https://registry.npmjs.org/@kitware/vtk.js/latest
51. Cornerstone3D, image loaders: https://www.cornerstonejs.org/docs/concepts/cornerstone-core/imageloader/
52. Cornerstone3D, registerWebImageLoader.ts: https://github.com/cornerstonejs/cornerstone3D/blob/main/packages/core/examples/webLoader/registerWebImageLoader.ts
53. MDN, SharedArrayBuffer: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer
54. OHIF, cross-origin deployment: https://v3p10.docs.ohif.org/3.9/deployment/cors/
55. nnInteractive: https://github.com/MIC-DKFZ/nnInteractive
56. SlicerNNInteractive: https://github.com/coendevente/SlicerNNInteractive
57. MONAI Label: https://github.com/Project-MONAI/MONAILabel
58. OHIF-AI: https://github.com/CCI-Bonn/OHIF-AI
59. Pan et al., Scientific Data 2024;11:410: https://www.nature.com/articles/s41597-024-03170-x
60. Same paper, PMC11035617: https://pmc.ncbi.nlm.nih.gov/articles/PMC11035617/
61. figshare, UMD.zip: https://figshare.com/articles/dataset/UMD_zip/23541312
62. figshare API, article 23541312: https://api.figshare.com/v2/articles/23541312
63. Creative Commons, CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
64. Radiogyan, imaging planes: https://radiogyan.com/articles/etymology-of-imaging-planes/
65. nibabel, radiological and neurological conventions: https://nipy.org/nibabel/neuro_radio_conventions.html
66. UC Davis, image orientation in display tools (2006): https://atonal.ucdavis.edu/lab_howto/fmri/image_orient_display.htm
67. 3D Slicer source, vtkMRMLSliceNode.cxx at v5.12.4: https://github.com/Slicer/Slicer/blob/v5.12.4/Libs/MRML/Core/vtkMRMLSliceNode.cxx
68. 3D Slicer source, vtkMRMLScalarVolumeDisplayNode.cxx at v5.12.4: https://github.com/Slicer/Slicer/blob/v5.12.4/Libs/MRML/Core/vtkMRMLScalarVolumeDisplayNode.cxx
69. nibabel, image orientation: https://nipy.org/nibabel/image_orientation.html
70. nibabel.orientations reference: https://nipy.org/nibabel/reference/nibabel.orientations.html
71. DICOM PS3.3 C.7.6.2, Image Plane Module: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.2.html
72. nibabel, DICOM orientation: https://nipy.org/nibabel/dicom/dicom_orientation.html
73. Radiopaedia, Windowing (CT): https://radiopaedia.org/articles/windowing-ct
74. DICOM PS3.3 C.8.2, CT modules: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.2.html
75. DICOM PS3.3 C.7.6.3, Image Pixel Module: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.3.html
76. DICOM PS3.3 C.8.3, MR modules: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.3.html
77. DICOM PS3.3 C.11, look-up tables: https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.11.html
78. NIfTI-1 header, nifti1.h: https://raw.githubusercontent.com/NIFTI-Imaging/nifti_clib/master/niftilib/nifti1.h
79. dcm2niix source, main_console.cpp: https://raw.githubusercontent.com/rordenlab/dcm2niix/master/console/main_console.cpp
80. dcm2niix source, nii_dicom_batch.cpp: https://raw.githubusercontent.com/rordenlab/dcm2niix/master/console/nii_dicom_batch.cpp
81. dcm2niix source, nii_dicom.cpp: https://raw.githubusercontent.com/rordenlab/dcm2niix/master/console/nii_dicom.cpp
82. DICOM PS3.15 E.3, de-identification options: https://dicom.nema.org/medical/dicom/current/output/chtml/part15/sect_E.3.html
83. MIDI report on medical image de-identification (arXiv 2303.10473): https://arxiv.org/abs/2303.10473
84. PyPI, nibabel: https://pypi.org/project/nibabel/
85. PyPI, scipy: https://pypi.org/project/scipy/
86. PyPI, pydicom: https://pypi.org/project/pydicom/
87. PyPI, SimpleITK: https://pypi.org/project/SimpleITK/
88. PyPI, dcm2niix: https://pypi.org/project/dcm2niix/
89. PyPI, pylibjpeg-libjpeg: https://pypi.org/project/pylibjpeg-libjpeg/
90. PyPI, python-gdcm: https://pypi.org/project/python-gdcm/
91. PyPI, pylibjpeg-openjpeg: https://pypi.org/project/pylibjpeg-openjpeg/
92. uv, environment variables (offline mode): https://docs.astral.sh/uv/reference/environment/
