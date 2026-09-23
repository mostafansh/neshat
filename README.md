# [Product name]

A web site where radiologists join dataset-curation research projects.

> Bring your expertise. We bring the data and the idea. You take part in research with very
> little to learn outside radiology.

## Status

Milestone 0 (September 2026): the site skeleton runs and shows a synthetic test image.

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

Run the tests:

```powershell
uv run python manage.py test
```

## Folder layout

| Folder | Contents |
|---|---|
| `config/` | Django settings and the list of web addresses (URLs). |
| `reading/` | The app: pages, image serving, tests. |
| `templates/` | The HTML pages. `base.html` is the shell every page shares. |
| `static/` | The Reading Room stylesheet and the brand mark. See [docs/style.md](docs/style.md). |
| `data/` | The database, case images and the secret key. Never in git. |
| `docs/` | The plan, the style standard and research reports. |
| `literature/` | A verified reading list. The PDFs stay local and are not in git. |

## Origin

This project restarts an earlier platform (GitHub `mostafansh/interface`). It reuses that
project's ideas and visual style, not its code.
