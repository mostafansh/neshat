# [Product name]: radiology reader-study and curation site

An online site where radiologists join dataset-curation research projects. They read cases in
the browser. The study design is built in: a blinded first read, the AI reveal (some
suggestions are deliberately wrong), hidden repeats and timing.

First use: a hands-on workshop at the 41st Iranian Congress of Radiology, Tehran, 3-6 Nov 2026.
By then, an online MVP must let attendees join over the internet and take part. The same app
must also run fully offline on a laptop as the fallback.

## Working with the project owner

The project owner is not a software engineer and is not yet familiar with
software-engineering terminology or Git.

Treat this project as a practical introduction to software engineering:

- Use accurate technical terminology; do not avoid important terms merely
  because they may be unfamiliar.
- Define each unfamiliar term in plain language when first introduced and
  explain why it matters in this project.
- Explain decisions, trade-offs, and workflow conventions without assuming
  prior software-engineering knowledge.
- Do not confuse unfamiliarity with software engineering for unfamiliarity
  with radiology or the clinical domain.

Provide proactive Git guidance throughout the project:

- Give a plain-language heads-up before meaningful Git operations.
- Explain what each operation changes and whether the change is local or will
  affect GitHub.
- Report relevant uncommitted changes and the current branch.
- Remind the owner when work should be committed, pushed, or opened as a pull
  request, and explain those terms when introduced.
- Provide the next safe command or action instead of assuming the owner knows
  the Git workflow.
- Ask explicitly before destructive operations, history rewriting, branch
  deletion, or publishing sensitive material.

Write to the owner in Simplified Technical English: short active sentences, one idea each,
context before status. Keep the technical detail; restructure it, do not drop it.

## Rules the code must never break

1. The AI suggestion, whether it is correct or planted, and the correct answer are never sent
   to the browser before the server has stored the reader's first read. The reveal arrives
   only in the response to that commit.
2. A committed read is never edited. A retried submit must not create a second record.
3. A study's design, case order and AI assignments freeze when the study opens.
4. No patient identifiers, accession numbers, DICOM headers or source paths enter this repo,
   the database or the site. The browser receives pixels only.
5. Planted AI suggestions require consent wording, a suspicion question and a debrief.
6. AI overlays use one neutral colour, identical for correct and planted suggestions. Shown AI
   confidence must not reveal which suggestions are planted.
7. The app runs on a laptop with no internet: no CDN, no Google Fonts, no external calls.

## Data rules

- Workshop reads are teaching data. Only room totals leave the laptop or server; then purge.
- Workshop images come from public, openly licensed collections. Credit them in the README.
- No hospital data in this repo. No PACS fetches or hospital report queries from this repo.
  Never send hospital images through Claude: that sends them abroad.
- Never commit data/, images, DICOM, databases, exports or literature/*.pdf.

## How we work

- No new breadth until a real radiologist has used the current thing end to end. Every
  milestone ends with a reader session; next-milestone work waits for it.
- Keep the code small enough for the owner to read end to end. Plans fit on one screen.
  Write a short decision record only when a decision is real. No tests that pin prose.
- M:\dataset_curator (GitHub mostafansh/interface) is a read-only reference. Never modify it.
  Code ported from it cites `mostafansh/interface@b6adb6d` in the commit message.
- Never discard or "clean up" the owner's uncommitted changes.
- Ask before any push, and before adding any dependency.
- Do not add hooks, graphify or other tooling config unless the owner asks.

## Stack

Python 3.12, Django, SQLite, a small custom image viewer in plain JavaScript, uv for packages.
Online host: an Iranian provider (to be chosen). Offline: laptop plus a travel Wi-Fi router.
