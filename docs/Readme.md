# Docker Status Page

A minimal, self-hosted status dashboard that shows the running/stopped state of all Docker containers on a host — dark-themed, mobile-friendly, and installable as a PWA in Edge/Chrome.

## How it works

```
GitHub push (app/**)
    │
    │  self-hosted runner on the Docker host
    ▼
/opt/docker/<host>_statuspage/config/
    │
    │  systemd.path watcher (inotify)
    ▼
Container restart (docker compose restart)
```

The app itself is a tiny Python HTTP server (`app/app.py`) that reads the local Docker socket (`/var/run/docker.sock`) and renders a live grid of containers. No database, no external dependencies beyond the `docker` Python SDK.

## Repository structure

```
.github/
  workflows/
    deploy.yml       # deploys app/ to every docker_host runner in the matrix
app/
  app.py             # HTTP server + HTML/PWA rendering
  style.css          # responsive dark theme
docs/
  README.md          # this file
```

## Deployment

Deployment is handled entirely by the `deploy.yml` workflow — pushing to `main` with changes under `app/` triggers a copy of `app.py` and `style.css` to every Docker host listed in the workflow's runner matrix. Each host's `systemd.path` watcher (set up via the `linux_systemd_path_watcher` Ansible role) detects the change and restarts the container automatically.

Adding a new Docker host:

1. Register a self-hosted GitHub Actions org runner on the host (see the infrastructure repo's `docker_host` role and `setup_github_runners.yml` playbook)
2. Deploy the `hau-app01_statuspage`-style stack via the `docker_stack` Ansible role (see `host_vars` example in the infrastructure repo)
3. Add the new runner's name to the `matrix.runner` list in `.github/workflows/deploy.yml`

## Configuration

The container reads its display settings from environment variables, set in the Ansible `host_vars` for each host — not from this repo:

| Variable | Description |
|---|---|
| `HOST_NAME` | Displayed as the page title and PWA name |
| `HOST_INITIALS` | Shown in the logo placeholder (1–3 characters) |
| `REFRESH_INTERVAL` | Auto-refresh interval in seconds (default: 10) |

## Local testing

```bash
cd app
pip install docker
python app.py
# open http://localhost:8080
```

Requires access to a Docker socket at `/var/run/docker.sock`.

## PWA installation

Once the page loads in Edge or Chrome, an install icon appears in the address bar — the app can be added as a standalone desktop/mobile app. The manifest and icon are generated dynamically by `app.py`, no static assets required.
