#!/usr/bin/env python3
"""
Captures high-resolution interface screenshots of Leddro via Chrome DevTools Protocol (CDP).
"""

import sys
import os
import json
import base64
import time
import asyncio
import subprocess
from pathlib import Path
import httpx
import websockets

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

async def cdp_call(ws, method, params=None, msg_id=[1]):
    mid = msg_id[0]
    msg_id[0] += 1
    req = {"id": mid, "method": method}
    if params:
        req["params"] = params
    await ws.send(json.dumps(req))
    while True:
        raw = await ws.recv()
        resp = json.loads(raw)
        if resp.get("id") == mid:
            return resp

async def capture_page_screenshot(ws, output_path: Path, delay: float = 2.5):
    print(f"[shot] Waiting {delay}s for animations/render to settle...")
    await asyncio.sleep(delay)
    res = await cdp_call(ws, "Page.captureScreenshot", {"format": "png"})
    if "result" in res and "data" in res["result"]:
        img_data = base64.b64decode(res["result"]["data"])
        output_path.write_bytes(img_data)
        print(f"[shot] Saved -> {output_path} ({len(img_data):,} bytes)")
    else:
        print(f"[error] Failed to capture screenshot for {output_path}: {res}")

async def navigate_and_capture(ws, url: str, output_path: Path, delay: float = 2.5):
    print(f"[shot] Navigating to {url}...")
    await cdp_call(ws, "Page.navigate", {"url": url})
    await capture_page_screenshot(ws, output_path, delay=delay)

async def main():
    chrome_exe = None
    for p in CHROME_PATHS:
        if Path(p).exists():
            chrome_exe = p
            break

    if not chrome_exe:
        print("[error] Chrome executable not found.")
        sys.exit(1)

    port = 9222
    output_dir = Path("docs/screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)

    temp_profile = Path(os.environ.get("TEMP", ".")) / "chrome_shot_profile"
    cmd = [
        chrome_exe,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={temp_profile}",
        "--window-size=1440,900",
        "http://localhost:5173/"
    ]

    print("[shot] Launching Chrome CDP...")
    proc = subprocess.Popen(cmd)
    try:
        ws_url = None
        async with httpx.AsyncClient() as client:
            for _ in range(30):
                try:
                    resp = await client.get(f"http://127.0.0.1:{port}/json/list")
                    tabs = resp.json()
                    page_tabs = [t for t in tabs if t.get("type") == "page"]
                    if page_tabs:
                        ws_url = page_tabs[0]["webSocketDebuggerUrl"]
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.3)

        if not ws_url:
            print("[error] Could not find page target via CDP /json/list.")
            sys.exit(1)

        print(f"[shot] Connected to CDP WebSocket: {ws_url}")
        async with websockets.connect(ws_url, max_size=25_000_000) as ws:
            # Enable domains
            await cdp_call(ws, "Page.enable")
            await cdp_call(ws, "Runtime.enable")

            # 1. Capture Overview: Tactical Radar Matrix
            print("[shot] Step 1: Capturing Overview Command Center (Radar Mode)...")
            await capture_page_screenshot(ws, output_dir / "overview-command-center.png", delay=3.5)

            # 2. Switch to Relationship Graph Mode and capture
            print("[shot] Step 2: Switching to Relationship Graph...")
            click_graph_expr = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const btn = buttons.find(b => b.textContent && (b.textContent.includes('Relationship Graph') || b.textContent.includes('MiroFish Graph')));
                if (btn) {
                    btn.click();
                    return 'clicked Relationship Graph';
                }
                return 'button not found';
            })()
            """
            click_res = await cdp_call(ws, "Runtime.evaluate", {"expression": click_graph_expr})
            res_val = click_res.get("result", {}).get("result", {}).get("value")
            print(f"[shot] Click response: {res_val}")
            await capture_page_screenshot(ws, output_dir / "relationship-graph.png", delay=4.0)
            await capture_page_screenshot(ws, output_dir / "mirofish-knowledge-graph.png", delay=0.5)

            # 3. Capture Prospects Page
            await navigate_and_capture(ws, "http://localhost:5173/prospects", output_dir / "prospect-management.png", delay=2.5)

            # 4. Open Draft Generation Modal on Prospects Page
            print("[shot] Step 4: Generating Draft Modal screenshot...")
            open_modal_expr = """
            (() => {
                const modalBtn = document.querySelector('button[title*="Generate AI email draft"]') ||
                                 document.querySelector('button[title*="draft"]');
                if (modalBtn) {
                    modalBtn.click();
                    return 'opened draft modal';
                }
                return 'modal button not found';
            })()
            """
            modal_click_res = await cdp_call(ws, "Runtime.evaluate", {"expression": open_modal_expr})
            modal_val = modal_click_res.get("result", {}).get("result", {}).get("value")
            print(f"[shot] Modal click response: {modal_val}")
            if modal_val == "opened draft modal":
                await capture_page_screenshot(ws, output_dir / "ai-draft-generation-modal.png", delay=2.0)

            # 5. Capture Audits Page
            await navigate_and_capture(ws, "http://localhost:5173/audits", output_dir / "technical-audits.png", delay=2.5)

            # 6. Capture Drafts Studio Page
            await navigate_and_capture(ws, "http://localhost:5173/drafts", output_dir / "ai-draft-studio.png", delay=2.5)

            # 7. Capture Integrations Settings Page
            await navigate_and_capture(ws, "http://localhost:5173/integrations", output_dir / "integrations-settings.png", delay=2.5)

        print("[shot] All screenshots captured successfully!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        print("[shot] Chrome closed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
