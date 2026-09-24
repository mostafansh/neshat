# Runbook: how to start the site

The site has three modes. The environment variable `NESHAT_MODE` chooses one.
All commands are for Windows PowerShell, run in the repo folder.

## 1. This computer only (dev)

```powershell
uv run python manage.py runserver
```

Open http://127.0.0.1:8000. Dev mode shows detailed error pages, so it refuses every other
device on purpose.

## 2. Phones on the same network (venue)

Use this for checkpoints with radiologists and at the workshop.

1. Check that nothing already uses port 8080. This command must print nothing:

   ```powershell
   Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue
   ```

   If it prints a line, stop the old server first. Windows lets two servers share a port and
   then sends each phone to either one at random.

2. Start the site:

   ```powershell
   $env:NESHAT_MODE = "venue"
   uv run waitress-serve --listen=0.0.0.0:8080 config.wsgi:application
   ```

3. Find this computer's address with `ipconfig` (the IPv4 address of the Wi-Fi or Ethernet
   adapter, for example 192.168.8.10). Phones open `http://<that address>:8080`.

4. If phones cannot connect, Windows Firewall is blocking Python. Allow it for this network
   when Windows asks.

Admin pages (`/admin/`) answer only the laptop itself in venue mode:
http://127.0.0.1:8080/admin/. The Wi-Fi is plain HTTP, so never type the admin password on a
phone. Readers type their own password on their phones to sign up; the sign-up and sign-in
pages warn them to choose a new password that they use nowhere else.

Stop the server with Ctrl+C. After a code update (`git pull`), stop the server, run
`uv run python manage.py migrate`, then start it again. `migrate` adds any new database columns
the update needs; when there are none, it does nothing. In venue mode the server reads the page
templates and the style and script files once, at start.

### The practice study

The practice study has 8 synthetic cases (drawn by code, no patients). Load it once:

```powershell
uv run python manage.py make_synthetic_study
```

If it already exists, the command stops and says so. `--replace` deletes the practice study
**and every answer given to it**, then makes it again.

The MRI practice study has 8 synthetic stacks of 24 slices. It works the same way:

```powershell
uv run python manage.py make_synthetic_stack_study
```

### The UMD MRI study (public data)

The question is "Nabothian cyst?" on sagittal T2 uterine MRI. The source is the local UMD copy
on `D:\UMD`. The script never changes it. It writes only to
`C:\Users\Mahbod\Desktop\datasets\umd-cyst\`, outside this repo:

- `study\`: what the site loads (`study.json`, `cases.csv`, `spares.csv`, one slice folder per
  case).
- `private\`: `map.csv` (case folder to UMD case and answer) and `contact-sheets\` (all slices
  of a case on one image). Never put these in the repo or on the site: UMD case numbers are
  public, so they give the answers away.

1. Prepare the folders. The script prints counts only.

   ```powershell
   uv run --group prep python prep/umd_stack.py
   ```

2. Check every contact sheet by eye (16: 8 study cases and 8 spares). Is the cyst label right?
   Is there any text burned into the image? Each tile has its phone number ("12 / 24") and
   marks: "key" on the key slice, "AI" and a yellow box on the slices of the AI box, "truth"
   and a green box on the slices of the largest expert cyst. The `map.csv` columns
   `key_slice_on_phone` and `ai_slices_on_phone` give the same slice numbers. Check the false
   alarms (category FP in `map.csv`) and the missed cysts (FN) first. For an FP case, look
   under the yellow box for a real cyst that nobody drew. For FN and TP cases, check that the
   green box holds a Nabothian cyst.

3. Optional: open one case in 3D Slicer on this PC. Slicer shows the T2 image, the expert mask
   ("Truth", filled) and the model's answer ("AI", outline only) on the key slice. The view is
   turned to the acquired slice plane, so each arrow-key step shows one phone slice. If Slicer
   is not in its usual folder, set the `SLICER` environment variable to `Slicer.exe`. Replace
   NN with the number of the case folder.

   ```powershell
   uv run --group prep python prep/umd_stack.py slicer case-NN
   ```

4. To replace a case with a spare: move the spare's row from `spares.csv` into `cases.csv`.
   Give it the position and the `ai_confidence` of the row it replaces.

5. Check the folder with the site's loader. It writes nothing. Run `migrate` first (after every
   update).

   ```powershell
   uv run python manage.py migrate
   uv run python manage.py load_study C:\Users\Mahbod\Desktop\datasets\umd-cyst\study --check
   ```

   The expected line: `Check passed for 'umd-cyst': 8 cases, 8 stacks, N slices in the
   stacks. Nothing was written.` N depends on the cases: 188 for the first pick, and it
   changes when you swap in a spare.

6. Load and open it. The site does not show a draft study, so there is nothing to test before
   this step. `--open` freezes the study (rule 3): after that, no case can be swapped under the
   same key.

   ```powershell
   uv run python manage.py load_study C:\Users\Mahbod\Desktop\datasets\umd-cyst\study --open
   ```

7. Read the cases on a phone through the LAN address in venue mode, not only on this computer.

## 3. The online server (online)

Not set up yet. When the server exists, it needs:

- An HTTPS proxy in front (nginx or the host's panel) that sends `X-Forwarded-Proto` and the
  original `Host`, and appends `X-Forwarded-For`.
- Waitress bound to the proxy only, and told to trust it. Without the trust flags, every page
  loops on redirects:

  ```bash
  NESHAT_MODE=online NESHAT_HOSTS=study.example.ir \
    waitress-serve --listen=127.0.0.1:8000 --trusted-proxy=127.0.0.1 \
    --trusted-proxy-headers="x-forwarded-proto x-forwarded-for" config.wsgi:application
  ```

- `NESHAT_SECRET_KEY` set in the service environment (or `data/secret_key.txt` kept private).
- HSTS starts at one hour (`NESHAT_HSTS_SECONDS`). Raise it only after one HTTPS certificate
  renewal has worked on the server.

## Where to look when something breaks

`data/errors.log` records server errors (5xx) and refused requests (4xx, for example "This
page expired") in every mode. A phone that says "The server had a problem" means an entry is
there. A phone that says "Connection lost" got no answer: the Wi-Fi dropped, the server is stopped or
the laptop is asleep, or the answer was too slow. Check that the server still runs, then the
Wi-Fi.
