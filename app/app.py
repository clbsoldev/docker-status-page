import docker
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST_NAME = os.environ.get("HOST_NAME", "Docker Host")
HOST_INITIALS = os.environ.get("HOST_INITIALS", "DH")
REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "10"))


def get_containers():
    client = docker.from_env()
    return sorted(client.containers.list(all=True), key=lambda c: c.name)


def render_html(containers):
    running = sum(1 for c in containers if c.status == "running")
    total = len(containers)

    cards = "".join(
        f'<div class="card {"running" if c.status == "running" else "stopped"}">'
        f'<div class="card-name">{c.name}</div>'
        f'<div class="status-badge">{c.status}</div>'
        f"</div>"
        for c in containers
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="{REFRESH_INTERVAL}">
    <title>{HOST_NAME} — Docker Status Page</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0a0e14">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="{HOST_NAME}">
</head>
<body>
    <header>
        <div class="brand">
            <span class="slashes">//</span>
            <span class="initials">{HOST_INITIALS}</span>
            <span class="host-name">{HOST_NAME}</span>
        </div>
        <div class="status-meta">
            <span class="count">{running}/{total} running</span> &middot;
            refresh in <span id="countdown">{REFRESH_INTERVAL}</span>s
        </div>
    </header>
    <main>
        <div class="eyebrow">docker status page</div>
        <div class="grid">{cards}</div>
    </main>
    <footer>Auto-refresh every {REFRESH_INTERVAL}s</footer>
    <script>
        let t = {REFRESH_INTERVAL};
        const el = document.getElementById("countdown");
        setInterval(() => {{ t--; if (t >= 0) el.textContent = t; }}, 1000);
    </script>
</body>
</html>"""


def render_manifest():
    return json.dumps({
        "name": HOST_NAME,
        "short_name": HOST_INITIALS,
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f0f0f",
        "theme_color": "#0f0f0f",
        "icons": [{
            "src": "/icon.svg",
            "sizes": "any",
            "type": "image/svg+xml",
            "purpose": "any maskable"
        }]
    })


def render_icon_svg(initials):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="20" fill="#2563eb"/>
  <text x="50" y="67" font-family="sans-serif" font-size="40"
        font-weight="700" fill="white" text-anchor="middle">{initials}</text>
</svg>"""


class StatusHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/style.css":
            self._serve_file("style.css", "text/css")
            return

        if self.path in ("/", "/index.html"):
            self._respond(render_html(get_containers()), "text/html; charset=utf-8")
        elif self.path == "/manifest.json":
            self._respond(render_manifest(), "application/json")
        elif self.path == "/icon.svg":
            self._respond(render_icon_svg(HOST_INITIALS), "image/svg+xml")
        else:
            self.send_response(404)
            self.end_headers()

    def _respond(self, content, ctype):
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.end_headers()
        self.wfile.write(data)

    def _serve_file(self, filename, content_type):
        try:
            with open(filename, "rb") as f:
                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), StatusHandler)
    print(f"Status server running — {HOST_NAME} on :8080")
    server.serve_forever()
