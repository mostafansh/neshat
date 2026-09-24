# Task: finish milestone 1 (hand-over from the chat "Building the actual thing")

**Status (2026-09-24): done.** Steps 1-6 are complete and the owner's phone test passed (see the
checkpoint log in docs/plan.md). The M1 checkpoint still needs one ADIR radiologist.

For a new Claude session in this folder, started in **bypass permissions** mode. The owner
moved chats because permission prompts interrupted the work. Standing permission applies
(CLAUDE.md, "How we work"): commit, push, add packages and download without asking; report
afterwards. Still ask before deleting the owner's data or rewriting Git history.

Read first: CLAUDE.md, docs/plan.md (decisions, milestones, checkpoint log), docs/reading-api.md
(the contract between the reading screen and the server), docs/runbook.md.

## Where things stand (2026-09-24)

- **Milestone 0 is done** and checked by the owner on a Samsung S21 (Chrome, hospital Wi-Fi).
  Finding: a long press on a plain image offers Download/Share/Google Lens, so the reading
  screen draws images on a canvas.
- **The server side of milestone 1 is committed** (38 tests pass): accounts (sign up, sign in,
  sign out), project list, study page with consent, the reading flow in `reading/flow.py`
  (server-only AI reveal, safe retry, fixed order, image window current/previous/next with an
  access log, locked reads refused by a database trigger), `reading/api.py`, the study loader
  `reading/studyfiles.py` with `load_study` and `make_synthetic_study`, and read-only admin.
- **The reading screen is NOT committed yet.** A helper agent wrote
  `templates/reading/read.html`, `static/js/read.js` and an appended section at the end of
  `static/css/reading-room.css`. The agent may not have finished. Check these three files
  against docs/reading-api.md and CLAUDE.md rule 7 (no crypto.randomUUID and similar; plain
  HTTP at the venue); finish or fix them.

## Next steps

1. Load the practice study: `uv run python manage.py make_synthetic_study --replace`.
2. Join the two halves and test the whole flow in the browser at phone width (375 px), in
   venue mode (docs/runbook.md, port 8080): sign up, project list, consent, read, lock, AI
   reveal (dashed box in the --ai colour, aligned while zoomed), revise, next case, reload in
   the middle of a case, finish, done page. No console errors under the CSP. Long press on the
   canvas must not offer "Download image". Use synthetic cases only: Claude never views real
   patient images.
3. Run an independent review (several reviewers, each finding checked by a skeptic), as done
   for milestone 0. Fix what survives. Keep tests passing.
4. Commit and push to `origin main` (GitHub mostafansh/neshat, private).
5. Ask the owner to test on the phone: hospital Wi-Fi, `http://<this PC's Wi-Fi IPv4>:8080`
   (it was 172.21.50.124; check with `Get-NetIPAddress -AddressFamily IPv4`). Record the result
   in the checkpoint log in docs/plan.md.
6. Then the real study: docs/tasks/ikhc-wrist-cases.md.

## How to talk to the owner

Simplified Technical English: short active sentences, context before status, plain-language
definitions of software terms, a plain-language note before Git operations. Do not ask routine
go/no-go questions; decide with sensible defaults and report.
