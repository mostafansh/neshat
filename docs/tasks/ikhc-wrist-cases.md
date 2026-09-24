# Task: prepare the first real study from IKHC images

For a Claude session started in **bypass permissions** mode in this folder. The owner has given
standing permission to run the `report_fetch` and `ikhc_fetch` skills for this (CLAUDE.md,
"How we work" and "Data rules"). Read CLAUDE.md first; its data rules apply to every step.

## Goal

A study folder that `uv run python manage.py load_study <folder> --open` accepts:

- Study: "Fracture on hand/wrist X-ray". Question "Fracture?" with choices
  `yes` (Fracture), `no` (No fracture), `unsure` (Unsure); confidence 1-5.
- 8 cases in a fixed order: 4 with a fracture, 4 without. Also prepare 8 spares (16 in total)
  so the MSK radiologist can swap weak cases without new downloads.
- AI suggestions: correct on 6, deliberately wrong on 2 — one missed fracture (truth yes,
  AI no) and one false alarm (truth no, AI yes). Cases 1 and 2 have correct AI. AI confidence
  0.84-0.91 for every case, planted ones inside the same range (the loader enforces this).
- AI boxes are optional for now (leave `ai_box` empty). Boxes need a radiologist to mark the
  fracture; that marking step comes later.

The folder format and every check are described at the top of `reading/studyfiles.py`.

## Where things go (all OUTSIDE this repo)

```
C:\Users\Mahbod\Desktop\datasets\ikhc-wrist\
    raw\         the downloaded DICOM studies (never copied anywhere else)
    private\     map.csv: case file name -> hospital study key, report date. NEVER in the repo.
    study\       study.json, cases.csv and the de-identified PNG images: what load_study reads
```

## Steps

1. **Find candidates** with `report_fetch`: plain radiographs (X-ray) of the hand or wrist,
   adults, recent years. Pick reports whose impression clearly says a fracture is present, and
   reports that clearly say no fracture. Pull the minimum: report id / study key, date, body
   part and the impression sentence. Never print or store names, national codes, phone
   numbers or addresses.
2. **Download** with `ikhc_fetch`: resolve the candidates to PACS study keys and download them
   into `raw\`.
3. **De-identify** with a small script (it may live in `prep/` in this repo; it must not write
   into the repo): pick the frontal (PA/AP) view, apply the DICOM window (Window Center/Width,
   or 1st-99th percentile when absent), render an 8-bit greyscale PNG, and crop away the
   borders where names and dates are burned in. Write the PNGs to `study\` with neutral names
   (`case-01.png` ...). Write `private\map.csv`. Use `pydicom` (add it with
   `uv add --group prep pydicom`; add a JPEG decoder such as `pylibjpeg` if the files need it).
4. **Write** `study\study.json` and `study\cases.csv` per the Goal section.
5. **Stop and hand over to the owner**:
   - Claude never views the PNGs (CLAUDE.md). The owner opens every PNG and confirms no
     text, name, date or number is left in the image.
   - The owner (and later the MSK radiologist) confirms each truth label against the image.
6. After the owner's confirmation: `uv run python manage.py load_study C:\Users\Mahbod\Desktop\datasets\ikhc-wrist\study --open`,
   then the owner tests it on the phone (docs/runbook.md, venue mode; phone on the hospital
   Wi-Fi).

## Report back (in chat, no patient data)

Counts only: candidates found, downloaded, rendered, and any problems (for example
compressed DICOM that needed a decoder).

Another Claude session may be building the site in this same folder at the same time. Commit
ONLY your own files (`git add prep/ pyproject.toml uv.lock`, never `git add -A`), then push.
Leave every other uncommitted change alone.
