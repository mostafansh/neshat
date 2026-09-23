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
http://127.0.0.1:8080/admin/. The Wi-Fi is plain HTTP, so never type a password on a phone.

Stop the server with Ctrl+C.

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

`data/errors.log` records server errors and refused requests in every mode.
