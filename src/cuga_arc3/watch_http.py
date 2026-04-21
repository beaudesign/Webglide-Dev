from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


def build_snapshot_payload(artifact_path: Path, *, game_id: str | None = None) -> dict[str, Any]:
    """Load a run artifact JSON and shape it for the browser side panel."""
    path = artifact_path.resolve()
    if not path.is_file():
        return {"ok": False, "error": f"artifact not found: {path}"}

    raw = json.loads(path.read_text(encoding="utf-8"))
    mtime_ms = int(path.stat().st_mtime * 1000)

    game_traces = raw.get("game_traces")
    traces: list[dict[str, Any]] = [
        t for t in (game_traces if isinstance(game_traces, list) else []) if isinstance(t, dict)
    ]

    master_prompt = ""
    if isinstance(raw.get("summary"), dict):
        mp = raw["summary"].get("master_prompt")
        if isinstance(mp, str) and mp.strip():
            master_prompt = mp.strip()

    parsed: list[tuple[str, list[Any]]] = []
    for trace in traces:
        gid = trace.get("game_id")
        if not isinstance(gid, str) or not gid:
            continue
        events = trace.get("events")
        event_list: list[Any] = events if isinstance(events, list) else []
        if not master_prompt:
            master_prompt = _master_prompt_from_events(event_list)
        parsed.append((gid, event_list))

    game_ids = [gid for gid, _ in parsed]
    selected = game_id if game_id and game_id in game_ids else (game_ids[0] if game_ids else None)

    games_summary: list[dict[str, Any]] = []
    selected_events: list[Any] = []
    for gid, event_list in parsed:
        stop_reason = _last_stop_reason(event_list)
        games_summary.append(
            {
                "game_id": gid,
                "event_count": len(event_list),
                "stop_reason": stop_reason,
            }
        )
        if gid == selected:
            selected_events = event_list

    return {
        "ok": True,
        "artifact_path": str(path),
        "mtime_ms": mtime_ms,
        "meta": {
            "run_id": raw.get("run_id"),
            "stage": raw.get("stage"),
            "manifest_path": raw.get("manifest_path"),
            "created_at": raw.get("created_at"),
            "summary": raw.get("summary") if isinstance(raw.get("summary"), dict) else {},
        },
        "master_prompt": master_prompt,
        "game_ids": game_ids,
        "selected_game_id": selected,
        "games_summary": games_summary,
        "events": selected_events,
    }


def _last_stop_reason(events: list[Any]) -> str | None:
    for event in reversed(events):
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "episode_end":
            continue
        payload = event.get("payload")
        if isinstance(payload, dict) and "stop_reason" in payload:
            return str(payload.get("stop_reason"))
    return None


def _master_prompt_from_events(events: list[Any]) -> str:
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "test_session":
            continue
        payload = event.get("payload")
        if isinstance(payload, dict):
            mp = payload.get("master_prompt")
            if isinstance(mp, str) and mp.strip():
                return mp.strip()
    return ""


def _panel_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ARC-3 watch</title>
  <style>
    :root {
      --bg: #0f1419;
      --surface: #1a2332;
      --text: #e7ecf3;
      --muted: #8b9aaf;
      --accent: #3d8bfd;
      --ok: #3ecf8e;
      --warn: #f0b429;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 13px;
      line-height: 1.45;
      min-height: 100vh;
    }
    header {
      padding: 10px 12px;
      background: var(--surface);
      border-bottom: 1px solid #2a3548;
      position: sticky;
      top: 0;
      z-index: 2;
    }
    header h1 { margin: 0; font-size: 14px; font-weight: 600; }
    header p { margin: 4px 0 0; font-size: 11px; color: var(--muted); }
    .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    select {
      background: var(--bg);
      color: var(--text);
      border: 1px solid #2a3548;
      border-radius: 6px;
      padding: 6px 8px;
      min-width: 140px;
      font-size: 12px;
    }
    .badge {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 2px 6px;
      border-radius: 4px;
      background: #243044;
      color: var(--muted);
    }
    .live { background: #1e3a2f; color: var(--ok); }
    main { padding: 10px 12px 24px; }
    .prompt {
      background: var(--surface);
      border-radius: 8px;
      padding: 10px;
      margin-bottom: 12px;
      border: 1px solid #2a3548;
      max-height: 160px;
      overflow: auto;
      white-space: pre-wrap;
      font-size: 11px;
      color: #c5d0e0;
    }
    .prompt:empty { display: none; }
    .events { display: flex; flex-direction: column; gap: 6px; }
    details {
      background: var(--surface);
      border: 1px solid #2a3548;
      border-radius: 8px;
      overflow: hidden;
    }
    details summary {
      cursor: pointer;
      padding: 8px 10px;
      font-weight: 500;
      list-style: none;
      display: flex;
      justify-content: space-between;
      gap: 8px;
    }
    details summary::-webkit-details-marker { display: none; }
    details[open] summary { border-bottom: 1px solid #2a3548; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, monospace; font-size: 11px; color: var(--muted); }
    pre {
      margin: 0;
      padding: 10px;
      overflow: auto;
      max-height: 220px;
      background: #121820;
    }
    .err { color: #ff6b6b; padding: 12px; }
    footer {
      padding: 8px 12px;
      font-size: 10px;
      color: var(--muted);
      border-top: 1px solid #2a3548;
      position: sticky;
      bottom: 0;
      background: var(--bg);
    }
    a { color: var(--accent); }
  </style>
</head>
<body>
  <header>
    <h1>ARC-3 agent watch</h1>
    <p>Open <a href="https://three.arcprize.org" target="_blank" rel="noreferrer">ARC-3</a> in the main tab; this panel follows your run artifact.</p>
    <div class="row" style="margin-top:8px;">
      <span class="badge" id="stageBadge">—</span>
      <span class="badge" id="mtimeBadge">—</span>
      <select id="gameSelect" title="Game"></select>
      <span class="badge live" id="pollBadge">polling</span>
    </div>
  </header>
  <main>
    <div class="prompt" id="masterPrompt" hidden></div>
    <div id="status"></div>
    <div class="events" id="eventList"></div>
  </main>
  <footer>Local watch server · reloads artifact on interval</footer>
  <script>
    const pollMs = 1500;

    async function fetchSnapshot(gameId) {
      const u = new URL("/api/snapshot", location.origin);
      if (gameId) u.searchParams.set("game_id", gameId);
      const r = await fetch(u.toString(), { cache: "no-store" });
      return r.json();
    }

    function render(data) {
      const st = document.getElementById("status");
      const list = document.getElementById("eventList");
      const sel = document.getElementById("gameSelect");
      const mp = document.getElementById("masterPrompt");
      if (!data.ok) {
        st.innerHTML = '<div class="err">' + (data.error || "Unknown error") + "</div>";
        list.innerHTML = "";
        return;
      }
      st.innerHTML = "";
      document.getElementById("stageBadge").textContent = "stage " + (data.meta && data.meta.stage || "—");
      document.getElementById("mtimeBadge").textContent =
        data.mtime_ms ? "updated " + new Date(data.mtime_ms).toLocaleTimeString() : "—";

      const promptText = data.master_prompt || "";
      if (promptText) {
        mp.textContent = promptText;
        mp.removeAttribute("hidden");
      } else {
        mp.textContent = "";
        mp.setAttribute("hidden", "");
      }

      const ids = data.game_ids || [];
      const prev = sel.value;
      sel.innerHTML = "";
      ids.forEach((id) => {
        const o = document.createElement("option");
        o.value = id;
        const sm = (data.games_summary || []).find((g) => g.game_id === id);
        const extra = sm && sm.stop_reason ? " · " + sm.stop_reason : "";
        o.textContent = id + (sm ? " (" + sm.event_count + " ev)" : "") + extra;
        sel.appendChild(o);
      });
      if (ids.length) {
        if (prev && ids.includes(prev)) sel.value = prev;
        else {
          const p = data.selected_game_id;
          sel.value = p && ids.includes(p) ? p : ids[0];
        }
      }

      const events = data.events || [];
      list.innerHTML = "";
      events.forEach((ev, i) => {
        const d = document.createElement("details");
        d.open = i >= events.length - 4;
        const t = ev.event_type || "?";
        const step = ev.step_idx != null ? ev.step_idx : "";
        d.innerHTML =
          "<summary><span>" +
          (i + 1) +
          ". <code>" +
          t +
          "</code></span><span class='mono'>step " +
          step +
          "</span></summary><pre>" +
          JSON.stringify(ev, null, 2) +
          "</pre>";
        list.appendChild(d);
      });
    }

    async function tick() {
      try {
        const sel = document.getElementById("gameSelect");
        const gid = sel && sel.value ? sel.value : null;
        const data = await fetchSnapshot(gid);
        render(data);
      } catch (e) {
        document.getElementById("status").innerHTML =
          '<div class="err">Cannot reach watch server. Is <code>cuga-arc3 watch-serve</code> running?</div>';
      }
    }

    document.getElementById("gameSelect").addEventListener("change", tick);
    setInterval(tick, pollMs);
    tick();
  </script>
</body>
</html>
"""


def _make_handler_class(artifact_path: Path) -> type[BaseHTTPRequestHandler]:
    path_ref = artifact_path.resolve()

    class WatchHandler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _cors(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self) -> None:  # noqa: PLR0911
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/snapshot":
                qs = urllib.parse.parse_qs(parsed.query)
                gid_list = qs.get("game_id", [])
                game_id = gid_list[0] if gid_list else None
                try:
                    body = build_snapshot_payload(path_ref, game_id=game_id)
                except OSError as exc:
                    body = {"ok": False, "error": str(exc)}
                raw = json.dumps(body).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self._cors()
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(raw)
                return
            if parsed.path in ("/", "/index.html"):
                html = _panel_html().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self._cors()
                self.end_headers()
                self.wfile.write(html)
                return
            self.send_error(404, "Not found")

    return WatchHandler


def run_watch_server(*, artifact_path: Path, host: str, port: int) -> None:
    """Run a threaded HTTP server until interrupted."""
    handler = _make_handler_class(artifact_path)
    server = ThreadingHTTPServer((host, port), handler)
    path = artifact_path.resolve()
    print(f"Serving ARC-3 watch panel at http://{host}:{port}/")
    print(f"  artifact: {path}")
    print("  Chrome: Extensions → Load unpacked → browser/extension/arc3-watch-sidepanel")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
