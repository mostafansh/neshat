# What RedBrick, MD.ai and similar platforms are built with

I checked each company's public docs, job ads and code repositories. I also read the JavaScript files each web app sends to the browser, which names the libraries it uses. I did all of this on 2026-09-23, and those files change with every release. Where the only evidence is older, I give the date.

**Terms used below**
- **Frontend:** the part of a website that runs in the reader's browser. **Backend:** the code that runs on the server.
- **SPA (single-page app):** the whole site is one JavaScript program in the browser, and it asks the server only for data. The opposite is **server-rendered pages**, where the server sends finished HTML. That is your Django plan. **HTMX** lets those pages update one part at a time without a full reload.
- **React / Vue:** the two most common JavaScript libraries for building SPAs. **TypeScript:** JavaScript with error checking added.
- **WebGL:** how a browser draws using the graphics card. **WASM (WebAssembly):** fast compiled code that runs in the browser. Viewers use it to decompress DICOM.
- **vtk.js:** Kitware's library for drawing medical images and 3D in the browser, built on WebGL. **Cornerstone3D:** an open-source medical image viewer library built on vtk.js. **"Legacy Cornerstone"** is its older generation, which is no longer developed. **OHIF:** a complete open-source viewer app built on Cornerstone3D.
- **DICOMweb:** the standard way to fetch DICOM images from an image archive (for example Orthanc) over the web.
- **Signed URL:** a temporary link to one file that stops working after a few minutes.

## 1. Comparison

| Product | Frontend | Image viewer | Backend | Database / hosting | Deployment | Confidence |
|---|---|---|---|---|---|---|
| **RedBrick AI** | React 17 SPA, built with Vite | Its own viewer written directly on vtk.js. It uses Cornerstone only to decompress DICOM. An AI segmentation tool (SAM-style) partly runs in the browser | GraphQL API behind AWS API Gateway. Programming language **unknown** | DynamoDB for labels, S3, CloudFront, Cognito login. All on AWS | SaaS. Some customers appear to get their own separate copy (annalise.redbrickai.com runs a different build). No self-hosted version of the app found. The AI add-on "Boost" is sold as separately priced instances | High for frontend and viewer; medium for backend and deployment |
| **Encord** | React 19 + TypeScript SPA (Vite), Ant Design + Tailwind | **Cornerstone3D**, with DICOM decompression in background threads. Konva for 2D, three.js for 3D | Python on uvicorn. FastAPI is likely but not confirmed | PostgreSQL + ClickHouse (from a third-party job listing only). GCP + Kubernetes, also AWS. Firebase for hosting and login. EU and US regions | SaaS, install in the customer's own cloud account, or on-premises for Enterprise customers (needs Kubernetes skills) | High; database medium |
| **MD.ai** | React 19 SPA (webpack), MUI, GraphQL client | **Legacy Cornerstone** (cornerstone-core 2.6.1, tools 6.0.6). Axial/coronal/sagittal reformats computed in the browser | GraphQL plus live websocket updates. Node.js/TypeScript + Python per a 2022 job ad. Server headers fit Node/Express | PostgreSQL + Redis (2022 evidence). Kubernetes + Terraform. Google Cloud load balancer in front | SaaS on per-customer subdomains. On-premises install not documented | High for frontend and viewer; medium for backend and database |
| **V7 Darwin** | Vue 3 SPA (Vite) | Its own viewer on vtk.js + canvas. The browser does no DICOM decoding; V7's servers convert DICOM first | Elixir/Phoenix, with Python machine-learning workers | PostgreSQL (AWS RDS), S3 in Ireland. AWS, also Azure | SaaS only. Customers can bring their own storage bucket | High |
| **Labelbox** | React/Redux/TypeScript SPA | **DICOM editor shut down Nov 2024 for lack of use.** Its library is unknown | Node/TypeScript, Python, some Java/Kotlin. GraphQL | MySQL, Spanner, PostgreSQL. GCP + Kubernetes | SaaS only. On-premises product dropped at the end of 2022 | High |
| **grand-challenge.org** (Radboud, open source) | **Server-rendered Django templates + HTMX 1.7 + jQuery + Bootstrap.** No JavaScript build step | CIRRUS: images are drawn on a GPU server in one container per reader and streamed to the browser. Proprietary (built on MeVisLab) | Django + Django REST Framework (Python 3.13). Background jobs on AWS Lambda/Batch; Celery was removed in June 2026 | PostgreSQL + Redis. AWS Ireland, S3. DICOM stored in AWS HealthImaging | Hosted service; reader studies are paid for non-member organisations, priced per study. Code is Apache-2.0 but tied to AWS, and the viewer is not included | High |
| **CVAT** (open source) | React 18 + Redux + Ant Design SPA | Custom 2D drawing canvas + three.js. **No DICOM support**; images must first be converted to PNG | Django 5.2 + DRF + background job queue (RQ) | PostgreSQL, Redis, Kvrocks, ClickHouse | MIT licence. Self-host with Docker Compose or Helm, or use CVAT Online | High |
| **pacsbin** (small commercial viewer; the Gaube studies used it) | Nuxt (Vue) SPA | **Cornerstone3D** + progressive HTJ2K loading since v2 (April 2026). v1 was legacy Cornerstone + jQuery | LiteVNA: its own DICOMweb archive on Cloudflare Workers | MongoDB Atlas. Cloudflare R2, DigitalOcean, AWS | SaaS | High |
| **OHIF v3** (open-source viewer, for reference) | React (18.3.1 in released versions), Tailwind | Cornerstone3D | None. It is a set of static files that reads from any DICOMweb server | none | MIT licence, self-host | High |

**Sources by row**
- **RedBrick:** [app bundle and headers](https://app.redbrickai.com/), [privacy page (DynamoDB, S3)](https://www.redbrickai.com/privacy), [API headers](https://api.redbrickai.com/graphql/), [signed-URL docs](https://app.redbrickai.com/docs/importing-data/import-cloud-data/configuring-aws-s3.md), [Boost 2024](https://www.redbrickai.com/blog/2024-04-02-update)
- **Encord:** [app](https://app.encord.com/), [Cornerstone3D chunk](https://app.encord.com/assets/src-Cs9UoS3L.js), [API headers](https://api.encord.com/), [job ad 2026](https://jobs.ashbyhq.com/encord/61b5882e-5496-4119-841a-63dd8d42cf14), [DevOps ad](https://jobs.ashbyhq.com/encord/1fcf1e4b-ec1b-4a65-ba68-8512bd144d2c), [database listing (third-party)](https://freehire.me/jobs/senior-backend-engineer-scale-data-infrastructure-encord-4fexhqig), [deployment options](https://docs.encord.com/platform-documentation/Other/deployment-options)
- **MD.ai:** [app bundle](https://public.md.ai/annotator/project/LxR6zdR2), [Python client](https://github.com/mdai/mdai-client-py/blob/master/mdai/client.py), [2022 job ad](http://web.archive.org/web/20220610185739/https://boards.greenhouse.io/mdai/jobs/4011987005), [2022 HN stack post](https://news.ycombinator.com/item?id=31238814), [Kubernetes docs 2026](https://docs.md.ai/annotator/models/model-security/), [MPR docs](https://docs.md.ai/annotator/ui/mpr/)
- **V7:** [app bundle](https://darwin.v7labs.com/login), [2021 Elixir case study](https://elixir-lang.org/blog/2021/01/13/orchestrating-computer-vision-with-elixir-at-v7/), [2026 job listing](https://freehire.me/jobs/pioneer-full-stack-engineer-elixir-vue-v7-eiesw2x7), [security page](https://www.v7labs.com/security), [external storage](https://docs.v7labs.com/docs/external-storage-configuration)
- **Labelbox:** [deprecations](https://docs.labelbox.com/docs/deprecations), [job ad](https://job-boards.greenhouse.io/labelbox/jobs/5159327007), [env.js](https://app.labelbox.com/env.js)
- **grand-challenge:** [pyproject](https://github.com/DIAGNijmegen/rse-grand-challenge/blob/main/pyproject.toml), [architecture doc](https://github.com/DIAGNijmegen/rse-grand-challenge/blob/main/app/docs/architecture.rst), [Celery removal](https://github.com/DIAGNijmegen/rse-grand-challenge/pull/4798), [Dec 2025 report (MeVisLab viewer)](https://grand-challenge.org/blogs/december-2025-cycle-report/), [server location](https://grand-challenge.org/documentation/faq-security-location-servers/), [costs](https://grand-challenge.org/documentation/faq-reader-studies-costs-usage/), [CIRRUS](https://rse.diagnijmegen.nl/software/cirrus/)
- **CVAT:** [UI package](https://github.com/cvat-ai/cvat/blob/develop/cvat-ui/package.json), [backend requirements](https://github.com/cvat-ai/cvat/blob/develop/cvat/requirements/base.in), [compose file](https://github.com/cvat-ai/cvat/blob/develop/docker-compose.yml), [DICOM converter](https://github.com/cvat-ai/cvat/blob/develop/utils/dicom_converter/README.md)
- **pacsbin:** [live site](https://pacsbin.com/), [road to 2.0](https://docs.pacsbin.com/news/20250626-the-road-to-2.0), [v2 launch](https://docs.pacsbin.com/news/20260428-hello-v2.html), [infrastructure](https://docs.pacsbin.com/security.html)
- **OHIF / Cornerstone3D:** [OHIF 3.13 package](https://github.com/OHIF/Viewers/blob/v3.13.10/platform/app/package.json), [OHIF deployment](https://docs.ohif.org/deployment/), [Cornerstone3D core](https://github.com/cornerstonejs/cornerstone3D/blob/main/packages/core/package.json)

## 2. Patterns

- **Every commercial product is a JavaScript/TypeScript SPA.** RedBrick, Encord, MD.ai and Labelbox use React; V7 and pacsbin use Vue. The only server-rendered platform is the academic grand-challenge.org, which is built the same way as your plan.
- **No single viewer library dominates, but vtk.js sits underneath nearly all of them.**
  - Encord and pacsbin use Cornerstone3D. So does most of the open-source radiology world through OHIF: XNAT, NCI IDC, TCIA, MIDRC ([showcase](https://ohif.org/showcase/)), plus Flywheel, Kaapana and MONAI Label.
  - RedBrick and V7 wrote their own viewers directly on vtk.js because they sell heavy 3D segmentation and volume rendering.
  - MD.ai still ships legacy Cornerstone in 2026, and pacsbin needed a full rewrite to move off it. Replacing a viewer later is expensive once your tools and saved annotations depend on it.
- **Python is everywhere, mostly behind the scenes.**
  - Encord's API is Python. grand-challenge and CVAT are Django. MD.ai and Labelbox mix Python with Node.js. V7 runs Python machine-learning workers under Elixir.
  - They all ship Python toolkits for customers ([redbrick-sdk](https://pypi.org/project/redbrick-sdk/), darwin-py, mdai-client-py).
- **Server stores labels, browser handles pixels.**
  - RedBrick, Encord and Labelbox store only labels and metadata. The browser downloads pixels straight from the storage bucket through signed URLs and decompresses them itself.
  - V7 is the exception: its servers convert DICOM first. As a result, its privacy mode, where V7 gets read-only access to the customer's bucket, cannot handle raw DICOM ([docs](https://docs.v7labs.com/docs/registering-items-from-external-storage)).
- **DICOMweb and PACS connections are rare.** Only MD.ai (Google Healthcare API plus DICOM push), pacsbin (its own archive) and grand-challenge (AWS HealthImaging) document them. RedBrick and Encord document none.
- **De-identification varies.**
  - On the server after upload at MD.ai ([docs](https://docs.md.ai/annotator/deid/)) and Encord (a paid add-on, [docs](https://docs.encord.com/sdk-documentation/dicom-sdk/sdk-deidentify-dicom)).
  - In the browser before upload at grand-challenge and pacsbin ([docs](https://docs.pacsbin.com/anonymization.html)).
  - None documented at V7.
- **Reader-study logic is thin everywhere.** None of them documents the flow "read unaided, lock the answer, reveal the AI, allow revision". None documents kappa, ICC or MRMC statistics. The closest features:
  - RedBrick has blinded and unblinded review stages for AI output ([blog](https://www.redbrickai.com/blog/2024-02-05-fda-xrays)).
  - MD.ai can hide model outputs, but only for the whole project at once ([docs](https://docs.md.ai/annotator/projects/project-settings/)).
  - Encord's "Golden Label Reveal" shows the correct answer after submit and then locks editing. It reveals ground truth, not AI, and allows no revision ([docs](https://docs.encord.com/end-to-end/BenchmarkQA/annotator-training)).

**Why they all built SPAs.** They sell heavy interactive editors to many companies at once. Those editors do 3D segmentation, volume rendering, AI-assisted masks and, at MD.ai, live collaboration. Encord's team is about 150 people ([YC](https://www.ycombinator.com/companies/encord)). Holding volumes, masks and undo history in browser memory requires a large browser program. Your pilot is some admin pages plus one reading screen that runs in a fixed order, with classification and point or box marks. Their architecture solves a different problem.

## 3. What the published AI-impact reader studies used (the fair comparison)

| Study | Readers | What they built | Viewer | Unaided answer before AI? |
|---|---|---|---|---|
| [Dratsch 2023, *Radiology*](https://research.vu.nl/ws/portalfiles/portal/291201748/Dratsch_et_al._2023_-_Automation_Bias_in_Mammography_-_The_Impact_of_Artificial_Intelligence_BI-RADS_Suggestions_on_Reader_Performance.pdf) | 27, in person | A Windows program in C++/Qt that shows PNGs with a fake AI and writes timings to a local file ([code](https://github.com/DrXCHEN/Automation-Bias)) | Clinical PACS on a second monitor | No: AI shown from the start |
| [Rezazade Mehrizi 2023, *Sci Rep*](https://pmc.ncbi.nlm.nih.gov/articles/PMC10247804/) | 92 radiologists (66% in Iran), remote | Custom web app, technology not reported. Logged time to open the AI and number of answer changes ([supplement](https://static-content.springer.com/esm/art%3A10.1038%2Fs41598-023-36435-3/MediaObjects/41598_2023_36435_MOESM5_ESM.docx)) | Plain images with zoom | Not locked: AI hidden behind a "show" button |
| Gaube [2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7896064/) / [2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC9876883/) | 138 / 106 physicians | Qualtrics survey | Link out to pacsbin; no reading time reported | No |
| [Jabbour 2023, *JAMA*](https://pmc.ncbi.nlm.nih.gov/articles/PMC10731487/) | 457 clinicians | Qualtrics | Static images with heat maps | Different cases without and with AI |
| [Bernstein 2023, *Eur Radiol*](https://pmc.ncbi.nlm.nih.gov/articles/PMC10235827/) | 6 (5 analysed) | Orthanc research PACS. Answers spoken aloud and written down by the experimenter | Clinical PACS monitors | No |
| [Fogliato 2022, FAccT](https://arxiv.org/pdf/2205.09696) (Microsoft [Exp-HAIC](https://github.com/microsoft/Exp-HAIC)) | 19 veterinary radiologists | **Django + server-rendered templates + Bootstrap/jQuery, SQLite database, open source** | A plain image with pan/zoom and brightness/contrast sliders | **Yes: compared "commit, then reveal" with "AI shown at once"** |
| Agarwal 2023 ([NBER](https://www.nber.org/system/files/working_papers/w31422/w31422.pdf)) / Yu 2024 (*Nat Med*) | 227 radiologists, remote | oTree, a Python experiment framework. Full click-by-click log ([Collab-CXR](https://pmc.ncbi.nlm.nih.gov/articles/PMC12049457/)) | One JPEG per case with zoom/contrast | Yes, in one design (same cases, first without, then with AI) |
| [Prinster 2024, *Radiology*](https://pmc.ncbi.nlm.nih.gov/articles/PMC11605106/) | 220 physicians | Custom website, technology unknown | DICOM viewer built into the page (library unknown) | No lock: image first, AI shown when the reader clicks |
| [Kim 2025, *Radiol Med*](https://pmc.ncbi.nlm.nih.gov/articles/PMC12008054/) | 9 | Sectra PACS + Google Forms + a manual time tracker | Clinical PACS | Crossover design with at least 4 weeks' washout |
| Tschandl 2020, *Nat Med* ([stack paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7007585/)) | 302 raters | Laravel (PHP) + React on university servers | Web images, mobile-friendly | Yes, per the study's own description |

What this shows:
- **The bar is low.** A *JAMA* paper and a *Radiology* paper came from Qualtrics and a throwaway desktop program. The largest study used one JPEG per case.
- **Only Prinster built a real DICOM viewer into the page.** Gaube linked out to an external viewer and reported no reading times.
- **The closest match to your plan is Microsoft's Exp-HAIC:** Django, server-rendered templates, a small JavaScript image widget, and commit-then-reveal.
- **Each of these was a one-off app for one study** (Exp-HAIC has been archived since 2023). Nobody has built a reusable platform for many studies that locks the unaided answer on the server and shows real DICOM. That is the gap your site would fill.

## 4. Adopt or fork instead of building?

| Option | Verdict | Cost / reason |
|---|---|---|
| Run a study on grand-challenge.org (hosted) | **Only as a one-off benchmark** | Paid, quoted per study. Data goes to AWS in Ireland, so check hospital data rules and whether access from Iran works. It has an option that carries answers from one case to the next, which *might* approximate commit-then-reveal; this is untested. |
| Fork grand-challenge | **No** | The code is Apache-2.0, but its Docker setup is for development only. Its jobs and viewer hosting are tied to AWS, and the viewer (CIRRUS) is not included; it is available only through research agreements. Months of work, and you still would have no viewer. |
| Use OHIF as the whole app | **No** (maybe later, as a "full viewer" link for CT/MR) | It has its own React build and no users, projects or database. Flywheel did put blind reader-study questions on an OHIF fork ([MR](https://gitlab.com/flywheel-io/public/ohif-viewer/-/merge_requests/378)), but Flywheel's server is proprietary. |
| **Cornerstone3D as your viewer module** | **Yes** | Free (MIT licence). Covers window/level, stack scrolling, point and box marking, and segmentation later ([tools](https://www.cornerstonejs.org/docs/concepts/cornerstone-tools/tools)). The cost is a learning curve and a JavaScript build step. |
| Microsoft Exp-HAIC | **Read it, don't fork it** | MIT licence, archived, SQLite, JPEG only. Copy its data models and its commit-then-reveal logic. |
| **Orthanc** as the image server | **Yes** | Free, one Docker container, and Bernstein 2023 used it as a research PACS. The core is GPLv3 and the DICOMweb plugin is AGPLv3 ([licensing](https://orthanc.uclouvain.be/book/faq/licensing.html)). That only matters if you modify and redistribute it. |
| grand-challenge's browser de-identification package | **Yes** | Apache-2.0 JavaScript package with a matching Python package ([code](https://github.com/DIAGNijmegen/rse-grand-challenge/blob/main/app/grandchallenge/uploads/static/js/dicom_deidentification.mjs)). |
| FDA iMRMC | **Yes, for analysis** | Free statistics software for multi-reader studies ([repo](https://github.com/DIDSR/iMRMC)). Design your data export (reader × case × condition) to feed it. |
| CVAT, Kaapana, XNAT, ePAD, MONAI Label | **No, for now** | CVAT has no DICOM. Kaapana is a whole Kubernetes platform. XNAT's viewer plugin is on the old OHIF 2. ePAD uses legacy Cornerstone. MONAI Label is only useful later for AI segmentation suggestions, and its last release was Nov 2024. |
| RedBrick, Encord, MD.ai | **No** | None has the lock-then-reveal flow or the agreement statistics you need. |

## 5. What this means for your stack decision

**The evidence supports Django + server-rendered pages + HTMX. Make one change: build the reading screen as a small, separate TypeScript app from day one, not as HTMX fragments with viewer code mixed in.**

Why the plan holds:
- The most-used academic reader-study platform, grand-challenge, is Django + HTMX + Bootstrap.
- The one published commit-then-reveal platform, Exp-HAIC, is Django templates.
- CVAT shows Django handles annotation workloads, and Encord's backend is Python.
- In 2021 V7 chose Elixir over Django because it worried Django could not handle its data volume ([source](https://elixir-lang.org/blog/2021/01/13/orchestrating-computer-vision-with-elixir-at-v7/)). At reader-study scale (thousands of cases, dozens of readers) that concern does not apply.
- The commercial products are SPAs because they do large-scale 3D editing, which you are not building now.

What to change or pin down:
1. **The reading screen is one page run by one TypeScript program**, built with Vite and placed inside a Django template. It talks to Django through a few small data endpoints:
   - get the case
   - save the unaided answer
   - get the AI suggestion
   - save the revision
   - send the event log

   Everything else stays HTMX: projects, sign-up, assignments, admin and results. The reason is that the reading screen moves through fixed steps (unaided, locked, revealed, revised) while a live WebGL viewer stays open. If HTMX replaces the part of the page holding the viewer, the loaded images are lost. Cornerstone3D also needs a build step for its decompression code anyway.
2. **The server decides when the AI appears.** The AI suggestion must not be sent to the browser until the server has saved the unaided answer. Otherwise a reader could find it in the page source.
   - Record server-side timestamps.
   - Also keep a client event log in a separate table that is only ever added to, like Collab-CXR's click-by-click file.
3. **Keep the viewer behind your own small interface.**
   - Save marks in image coordinates plus the Study, Series and SOP instance IDs and the frame number, not in Cornerstone's own format. MD.ai being stuck on legacy Cornerstone and pacsbin's full rewrite show the cost of tying yourself to one library.
   - Pin one Cornerstone3D major version. OHIF 3.12 ships Cornerstone3D 4.x, OHIF 3.13 ships 5.x, and the standalone library is at 5.10 ([OHIF 3.12 package](https://github.com/OHIF/Viewers/blob/v3.12.18/platform/app/package.json)).
4. **Pilot viewer scope:** 2D stack viewing only, meaning window/level, zoom, scroll, point and box. Skip 3D volumes and reformats for now. Encord tells users to switch to Firefox for large volumes because of Chrome's memory limits ([docs](https://docs.encord.com/platform-documentation/Annotate/annotate-label-editor/annotate-dicom)).
5. **Pixels come from Orthanc over DICOMweb**, which can stay in-country or at the hospital. Your database holds only answers, marks and metadata, the same split RedBrick and Encord use.
6. **Skip the special cross-origin security headers (COOP/COEP) for now.** Encord runs Cornerstone3D without them. RedBrick needs them only for its multi-threaded in-browser AI. If you need them later, V7's "credentialless" setting is the easiest to live with ([V7 app](https://darwin.v7labs.com/login)).

Don't do either of these:
- A full React SPA for the whole site. It doubles the work with no benefit for the pilot.
- A JPEG-only viewer that you plan to replace later. That repeats the migration cost MD.ai and pacsbin paid.

## 6. Features worth borrowing (inspiration only, not for slides)

**Reading protocol**
- Start with a block of cases where the AI is always right, then introduce planted errors. Dratsch used 12 wrong out of 40, half graded too high and half too low.
- Answer, then reveal (Fogliato). After the reveal, offer Accept / Modify / Reject plus a button to go back to the images (Prinster).
- No going back to earlier cases, a "rejoin" option to resume a session, and a minimum screen-size check (Rezazade Mehrizi). Desktop browsers only (Agarwal).
- Show the AI's confidence and store it per case, with a warning colour when certainty is low ([Wang 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10531198/)). For CT/MR, show the AI as an extra series the reader can switch on (Kim 2025).

**Measurement**
- Time until the AI was opened, number of answer changes, and heat-map views (Rezazade Mehrizi).
- Pan/zoom clicks, and active time versus total time, stored as a separate click log (Collab-CXR). Time spent in the viewer (Prinster).
- An export that iMRMC can read directly.

**Agreement and QA**
- Blind parallel reads with automatic agreement per mark type ([RedBrick formulas](https://app.redbrickai.com/docs/project-pages/multiple-labeling/consensus/agreement-calculation.md)):
  - overlap score for boxes
  - distance-based score for points
  - exact match for classifications
- Labelbox gives 0–1 agreement scores per feature ([docs](https://docs.labelbox.com/docs/consensus.md)). V7 lets a model act as one of the readers ([docs](https://docs.v7labs.com/docs/mar-9-the-consensus-stage)). Add kappa and ICC yourself; nobody offers them.
- Score each reader against a reference standard, with the reference shown or hidden ([RedBrick labeler evaluation](https://app.redbrickai.com/docs/projects/labeler-evaluation.md), Labelbox Benchmarks). Add an adjudicator role like MD.ai's QA role ([docs](https://docs.md.ai/annotator/ui/admin/assignments/)).
- For intra-observer studies:
  - shuffled case order for each reader (grand-challenge)
  - random case sets for each reader (MD.ai)
  - a washout of at least 4 weeks (Kim 2025)
  - answers carried into a repeated reading (grand-challenge)
- Answer types to support ([grand-challenge model](https://github.com/DIAGNijmegen/rse-grand-challenge/blob/main/app/grandchallenge/reader_studies/models.py)): yes/no, choice, number, point, box, distance, angle, polygon and mask, plus an Accept/Reject control for pre-filled findings.

**Operations**
- De-identify DICOM in the browser before upload (grand-challenge, pacsbin).
- Serve images through short-lived signed links so they never pass through your app server.
- Store screen layouts as JSON files, like Encord's 2×2 mammography layouts ([repo](https://github.com/encord-team/Annotate)).
- Let each project define its own answer-checking rules (RedBrick).
- Give each reader a direct link to their assigned cases (MD.ai).
- An educational mode with instant feedback and a leaderboard (grand-challenge). An RSNA challenge used MD.ai with a public scoreboard to motivate volunteer radiologists ([paper](https://arxiv.org/pdf/2405.19595)).

## Not verified / unknown
- **RedBrick:** the backend programming language. Whether a full on-premises install exists. Which AWS region production uses (the region in the app code is a development placeholder). Its claim that AltaDB loads scans 5–10× faster is marketing.
- **Encord:** whether FastAPI runs the core service. Its database: PostgreSQL + ClickHouse comes only from a third-party job listing. The Cornerstone3D version.
- **MD.ai:** the current backend and database (the evidence is from 2022). Whether an on-premises install is sold. "FDA 510(k)-cleared viewer" is MD.ai's own marketing claim and was not checked.
- **V7:** whether vtk.js also draws plain 2D images.
- **Labelbox:** which library its retired DICOM editor used. A vtk.js fork exists, but that is only a hint.
- **Studies:** the viewer library in Prinster 2024, and the technology behind Rezazade Mehrizi 2023, Wang 2023 and Ewals 2024.
- **grand-challenge:** whether it can run a strict answer-then-reveal-then-revise study. CIRRUS licence terms for self-hosting. Actual prices.
- **Absence findings:** no competitor *documents* kappa/ICC/MRMC, same-reader washout re-reads, or lock-then-reveal. That is "not found in the docs", not proof they lack them.