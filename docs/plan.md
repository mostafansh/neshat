# Build plan: pilot site for the ICR 2026 workshop

_Version of 2026-09-23. Sources: the old-repo review, the critic's review, and the two reports in
`docs/research/`. Update this file when a decision changes._

## Goal

By the 41st Iranian Congress of Radiology (3-6 Nov 2026), an online MVP runs in Iran.
Workshop attendees join it on their phones, read cases, lock an answer, see an AI suggestion
(some are deliberately wrong) and may revise. The room's reads fill a live 2x2 table. After the
exercises, attendees can sign up to join the pilot.

## Decided

| Topic | Decision |
|---|---|
| Repository | New git repo in `im_scared`. The old repo `M:\dataset_curator` is read-only reference; backup in `M:\interface-backup-2026-09-23.bundle`. |
| Workshop data | Teaching data only. Only room totals leave the server, then the reads are purged. No profile questions. |
| Workshop images | Public, openly licensed images (FracAtlas X-rays, TCIA CT). No hospital images. |
| Workshop day | Online first: attendees use the real site on their mobile data, VPN off. A laptop and travel router run the same app as a warm backup, reached through a second QR code. |
| Server | Python + Django + SQLite. One Django app. Server-rendered pages. HTMX only for small live updates (waiting screen, projector, results). |
| Reading screen | One plain JavaScript module (no build step) that talks to Django through a few JSON endpoints: get case, save first read, get AI suggestion, save final read, send events. |
| Images | The server sends ready-to-display 8-bit images, with 2-3 preset windows made on the server. No DICOM and no raw data reach the browser. Marks are stored in image-pixel coordinates with our own IDs, so a later switch to Cornerstone3D does not lose data. |
| CT phase task | 2-3 pre-windowed key images per case, no scrolling viewer (as the deck promises). |
| Hosting | Inside Iran, on a server the owner buys. No Cloudflare and no foreign proxy (sanctions, shutdowns, data abroad). Until the server exists, everything runs locally. Server resources are discussed separately. |
| Study setup | The owner describes each study in chat; Claude writes it as a study file plus a case list and loads it with one command. The friendly study builder comes after the congress. |
| GitHub | A new private repo (name open). The existing private repo `mostafansh/Autoclave` (July 2026 vision for a DICOM cleaning engine) stays untouched. |
| Live room | Organizer-paced: everyone reads the same case at the same time. Same AI suggestion for every reader on a case. Results stay hidden until the organizer presses "Show". |

## Open decisions

1. Repository name on GitHub.
2. Product name (placeholder: [Product name]).
3. The server: which provider, and when it is ready. The first online deploy should happen by
   mid-October at the latest, so the 3-radiologist checkpoint can run online.
4. A written rule for "Unsure" answers in the 2x2 table.

## Must work by feature freeze (Wed 21 Oct)

**Everyone**
- Sign up, sign in, sign out. A project list with the workshop study and one open practice project.
- Consent screen, instructions, reading screen, suspicion question (2 items), debrief.
- Reading screen: image, zoom and pan, preset windows, tap to mark a point, answer, confidence 1-5,
  "Lock my read", AI reveal from the server only, keep or change, final confidence.

**Workshop room**
- Join by QR code into an anonymous seat (no name, no password). The "join the pilot" sign-up at
  the end is not linked to the reads.
- Organizer control: next case, open or close a block, a rule banner, release the debrief.
- Projector view (light, high-contrast theme). Live 2x2 table, confusion matrix, repeat matches,
  % agreement. All results hidden until "Show".
- Export of room totals, then purge.

**Security, from the start**
- The server sends images only for the reader's current case, the case before, and the next case.
- Every image has a random address that works only for that reader, for a few minutes.
- A log of every image sent: who, when, and a fingerprint (hash) of the file.
- Simple rules: requests outside the window (tripwire), too many requests per account, reads that
  are impossibly fast, one account in two places. Response: record, slow down, then lock the
  session and alert the organizer. Count per account, never per internet address.
- A visible random code in a thin strip outside the image, if time allows.

## After the congress

Friendly study builder. Real hospital data with de-identification. Cornerstone3D and Orthanc for
full DICOM viewing. Invisible watermarks after in-house testing. Monitoring page. Sharif security
challenge on a copy with public images. A local AI model that summarises the logs for a person.

## Milestones

Each milestone ends with a real radiologist using the build. The next milestone waits for it.

| Dates | Build | Radiologist checkpoint |
|---|---|---|
| to Sun 27 Sep | Django skeleton, Reading Room style, one image on a phone | You |
| to Mon 5 Oct | Accounts, project list, reading screen with lock, reveal and revise. First deploy as soon as the server exists. | You + 1 ADIR radiologist, over the local network |
| to Tue 13 Oct | Live room, QR join, 2x2, consent, debrief, hidden repeats, image window and access log | 3 radiologists |
| to Wed 21 Oct | CT-phase exercise, export, purge, backups. **Feature freeze.** | Case-difficulty test with 3-5 colleagues |
| to Tue 27 Oct | Fixes only. Offline laptop kit. Runbook. | Full 90-minute dry run, 4-6 readers |
| to Mon 2 Nov | No code | 10+ phones (iOS, Android, VPN on/off). Venue test. |

Dry-run readers learn the trick, so they must not attend the workshop.

## Owner tasks (not code)

- Recruit an MSK and an abdominal radiologist to approve correct answers and planted AI errors.
- Buy the server inside Iran and ask the provider how HTTPS certificates are issued and renewed.
- Buy a travel router. Confirm the workshop slot and whether the venue allows it.
- Write the consent and debrief wording (teaching use, planted suggestions, purge).

## Top risks

1. **Internet shutdown.** 2026 had two long shutdowns. The domestic network mostly stayed up, so
   host in Iran and keep the offline laptop ready. A shutdown in October also stops this Claude
   session: keep the repo on GitHub and on USB.
2. **Scope creep.** The old project died from breadth before reader contact. Keep the weekly
   checkpoints. Past about 4,000 lines of Python, stop and cut.
3. **Study-integrity leaks.** The AI answer, planted flag or truth reaching the browser early; AI
   confidence values that differ between correct and planted. An automated test checks every page.
4. **HTTPS in Iran.** Free certificates may not renew during a shutdown, and Let's Encrypt terms
   may exclude sanctioned countries. Ask the host how it issues certificates.
5. **Case quality.** Noisy public labels, planted errors too obvious or too subtle. Radiologist
   sign-off and a difficulty test before the dry run.
