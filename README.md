# [Product name]

A web site where radiologists join dataset-curation research projects.

> Bring your expertise. We bring the data and the idea. You take part in research with very
> little to learn outside radiology.

## Status

Milestone 1 (in progress, due 5 Oct 2026): accounts, a project list, and the reading screen
(read, lock, AI reveal from the server, revise), tested with synthetic images.

First use: a hands-on workshop at the 41st Iranian Congress of Radiology, 3-6 Nov 2026.
Attendees will read cases on their phones, lock a first answer, see an AI suggestion (some are
deliberately wrong), and decide whether to change their answer. The room's reads fill a live
2x2 table: rescued by the AI versus talked out of a correct read. See [docs/plan.md](docs/plan.md).

## Quick start (Windows, PowerShell)

You need [uv](https://docs.astral.sh/uv/) (it installs Python packages into `.venv`).

```powershell
uv sync                                  # install the packages
uv run python manage.py migrate          # create the database in data/
uv run python manage.py runserver        # start the site for this computer only
```

Open http://127.0.0.1:8000. To test on phones, start the site in venue mode instead; see
[docs/runbook.md](docs/runbook.md).

Load a study:

```powershell
uv run python manage.py make_synthetic_study            # 8 synthetic practice X-rays, opened
uv run python manage.py make_synthetic_stack_study      # 8 synthetic MRI-like stacks, opened
uv run python manage.py load_study <folder> --check     # run every check on a folder; write nothing
uv run python manage.py load_study <folder> --open      # a real study folder (see below)
uv run python manage.py createsuperuser                 # an organizer account for /admin/
```

A study folder holds `study.json`, `cases.csv` and the images. The format and every check are
described at the top of [reading/studyfiles.py](reading/studyfiles.py). Keep folders with real
images outside this repo. Once a study is opened, its design is frozen.

## MRI stacks

A case is one image (an X-ray) or one stack of slices (an MRI series). The reader scrolls
through a stack on the phone: drag up or down, the slider, the mouse wheel or the arrow keys.
A script prepares the slices on the owner's PC in advance. Readers never use 3D Slicer. It stays
on the owner's PC as a checking tool.

- In a study folder, a stack is a folder of slices `000.png`, `001.png`, … (8-bit greyscale,
  2 to 64 slices). `cases.csv` then has a 7th column, `ai_slices`: the slices the AI box is on.
- `load_study <folder> --check` runs every check and re-saves the pixels in memory only. It
  prints one line (cases, stacks, slices) and writes nothing. Run `migrate` after every update,
  before it.
- The two practice studies are drawn by code, with no patient images. Both commands accept
  `--replace`, which deletes the practice study and every answer given to it.
- The first MRI test data is the public UMD dataset. [docs/runbook.md](docs/runbook.md) says how
  to prepare, check and load it.

UMD credit (licence CC BY 4.0, https://creativecommons.org/licenses/by/4.0/):
Pan H, Chen M, Bai W, Li B, et al. "Large-scale uterine myoma MRI dataset covering all FIGO
types with pixel-level annotations." *Scientific Data* 2024;11:410, doi:10.1038/s41597-024-03170-x.
Data: `UMD.zip` on figshare, doi:10.6084/m9.figshare.23541312.v3. Modified for this site:
reoriented, windowed to 8 bits, downsized to 512 px, yes/no answers derived from the masks.

Run the tests:

```powershell
uv run python manage.py test
```

## Folder layout

| Folder | Contents |
|---|---|
| `config/` | Django settings and the list of web addresses (URLs). |
| `reading/` | The app. `models.py` the data, `flow.py` the reading rules, `api.py` the reading screen's data calls, `studyfiles.py` study loading, `tests/` the tests. |
| `templates/` | The HTML pages. `base.html` is the shell every page shares. |
| `static/` | The Reading Room stylesheet and the brand mark. See [docs/style.md](docs/style.md). |
| `data/` | The database, case images and the secret key. Never in git. |
| `docs/` | The plan, the style standard and research reports. |
| `literature/` | A verified reading list. The PDFs stay local and are not in git. |

## Origin

This project restarts an earlier platform (GitHub `mostafansh/interface`). It reuses that
project's ideas and visual style, not its code.
