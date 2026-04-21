# ARC-3 Agent Watch (Chrome side panel)

This unpacked extension shows the **`cuga-arc3 watch-serve`** UI in Chrome’s **side panel** so you can keep [ARC-3](https://three.arcprize.org) in the main window and watch trace events while a run updates the artifact file.

## Setup

1. Start the local server from the project root (or pass an absolute path to your artifact):

   ```bash
   uv run cuga-arc3 watch-serve --artifact artifacts/stage-s0-smoke.json --port 8765
   ```

2. In Chrome: **⋮ → Extensions → Manage extensions → Developer mode → Load unpacked** and choose this folder (`arc3-watch-sidepanel`).

3. Pin the extension, click it, or use the **Side panel** toolbar menu (puzzle icon → ARC-3 Agent Watch → **Show side panel** / pin to toolbar).

4. If your server is not on `http://127.0.0.1:8765/`, edit the **Watch server** field and click **Apply**. The value is stored in `chrome.storage.local`.

5. Open **https://three.arcprize.org** in a normal tab, sign in, and run your session. In another terminal, run `cuga-arc3 run-stage …` so the artifact JSON updates; the side panel polls the server every ~1.5s.

## Permissions

- **sidePanel** — show this UI in Chrome’s side panel.
- **storage** — remember the watch server origin.
- **127.0.0.1 / localhost** — talk to the local `watch-serve` process only.

## Troubleshooting

- **Blank panel**: confirm `watch-serve` is running and the URL matches (scheme, host, port).
- **CORS**: not required for an `iframe` to `localhost`; the extension also has host permissions for fetches if we switch away from iframe later.
