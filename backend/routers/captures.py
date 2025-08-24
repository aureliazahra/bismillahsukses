# routers/captures.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import platform
import os
import subprocess
import urllib.parse
import time

router = APIRouter(prefix="/api/captures", tags=["captures"])

BACKEND_ROOT = Path(__file__).resolve().parents[1]
CAPTURES_DIR = (BACKEND_ROOT / "captures").resolve()
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)  # ensure folder exists

@router.get("/path")
def get_captures_path():
    return {"ok": True, "captures_dir": str(CAPTURES_DIR), "exists": CAPTURES_DIR.exists()}

@router.post("/open")
def open_captures():
    """
    Windows 11:
      - Open File Explorer at CAPTURES_DIR
      - Bring that window to the foreground (focus)
    macOS/Linux keep the earlier behavior.
    """
    if not CAPTURES_DIR.exists():
        raise HTTPException(status_code=404, detail=f"Folder not found: {CAPTURES_DIR}")
    try:
        system = platform.system()
        path = str(CAPTURES_DIR)

        if system == "Windows":
            # 1) Try open with Explorer (fast & reliable)
            try:
                subprocess.Popen(["explorer", path])
            except Exception:
                # fallback
                os.startfile(path)  # type: ignore[attr-defined]

            # 2) Best-effort: bring the Explorer window to foreground using PowerShell + user32
            #    - Enumerate Shell windows and find the one pointing to our folder
            #    - ShowWindow(SW_RESTORE=9), then SetForegroundWindow
            #    Note: Foreground restrictions by Windows may still prevent focus in some cases.
            pwsh_script = f"""
$ErrorActionPreference = 'SilentlyContinue'
$target = [IO.Path]::GetFullPath('{path}')
$shell  = New-Object -ComObject Shell.Application
# short wait to let Explorer create the window
Start-Sleep -Milliseconds 250
$found = $false
foreach($w in $shell.Windows()) {{
  try {{
    $p = $w.Document.Folder.Self.Path
    if($p -eq $target) {{
      $found = $true
      $hwnd = $w.HWND
      Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {{
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}}
"@
      [Win32]::ShowWindow([intptr]$hwnd, 9) | Out-Null   # SW_RESTORE
      [Win32]::SetForegroundWindow([intptr]$hwnd) | Out-Null
      break
    }}
  }} catch {{ }}
}}
if(-not $found) {{
  # If not found yet, explicitly open, wait, then focus again
  $shell.Open($target)
  Start-Sleep -Milliseconds 350
  foreach($w in $shell.Windows()) {{
    try {{
      if($w.Document.Folder.Self.Path -eq $target) {{
        $hwnd = $w.HWND
        [Win32]::ShowWindow([intptr]$hwnd, 9) | Out-Null
        [Win32]::SetForegroundWindow([intptr]$hwnd) | Out-Null
        break
      }}
    }} catch {{ }}
  }}
}}
"""
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", pwsh_script],
                    check=False,
                    creationflags=subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
                )
            except Exception:
                # If anything fails, we still consider the folder opened.
                pass

            return {"ok": True, "opened": path, "os": system, "focused": True}

        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

        return {"ok": True, "opened": path, "os": system}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open/focus folder: {e}") from e

def _list_dir(p: Path):
    out = []
    for entry in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        out.append({
            "name": entry.name,
            "is_dir": entry.is_dir(),
            "size": entry.stat().st_size if entry.is_file() else None,
            "path": str(entry.resolve()),
            "href": f"/backend/captures/{urllib.parse.quote(entry.name)}"
        })
    return out

@router.get("/list")
def list_captures():
    if not CAPTURES_DIR.exists():
        return {"ok": True, "items": []}
    return {"ok": True, "items": _list_dir(CAPTURES_DIR)}

@router.get("/browse", response_class=HTMLResponse)
def browse_captures():
    if not CAPTURES_DIR.exists():
        return HTMLResponse("<h3>captures folder not found.</h3>", status_code=404)
    items = _list_dir(CAPTURES_DIR)
    rows = []
    for it in items:
        icon = "📁" if it["is_dir"] else "📄"
        rows.append(f'<tr><td style="padding:8px">{icon}</td>'
                    f'<td style="padding:8px"><a href="{it["href"]}" target="_blank" rel="noopener">{it["name"]}</a></td>'
                    f'<td style="padding:8px;text-align:right">{"" if it["is_dir"] else it["size"]}</td></tr>')
    html = f"""
    <!doctype html>
    <meta charset="utf-8" />
    <title>Founded Captures</title>
    <div style="font:14px/1.5 system-ui,Segoe UI,Roboto,Arial;margin:24px;max-width:960px">
      <h2 style="margin:0 0 12px">Founded Captures</h2>
      <div style="color:#666;margin-bottom:16px">
        Directory: <code>{CAPTURES_DIR}</code>
      </div>
      <table style="border-collapse:collapse;width:100%;border:1px solid #ddd">
        <thead>
          <tr style="background:#f6f6f6">
            <th style="text-align:left;padding:8px;width:40px"> </th>
            <th style="text-align:left;padding:8px">Name</th>
            <th style="text-align:right;padding:8px;width:160px">Size</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows) if rows else '<tr><td colspan="3" style="padding:12px;color:#666">Empty</td></tr>'}
        </tbody>
      </table>
      <p style="color:#888;margin-top:12px">Click a name to open the file/folder (served via /backend/captures).</p>
    </div>
    """
    return HTMLResponse(html)
