import os
import subprocess
import tempfile
from typing import Optional, Tuple

import requests
from packaging import version

GITHUB_REPO = "Rusya665/Solar_cells_measurements_plotting"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def check_for_updates(
    current_version: str,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Checks GitHub for a newer release.

    :param current_version: The version string currently running (e.g. '1.0.0').
    :return: (update_available, new_version_string, download_url)
    """
    try:
        response = requests.get(RELEASES_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        latest_tag = data.get("tag_name", "").lstrip("v")
        if not latest_tag:
            return False, None, None

        if version.parse(latest_tag) > version.parse(current_version.lstrip("v")):
            # Find the setup installer asset first, fall back to bare .exe
            download_url = None
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if "Setup" in name and name.endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    break
            if download_url is None:
                for asset in data.get("assets", []):
                    if asset.get("name", "").endswith(".exe"):
                        download_url = asset.get("browser_download_url")
                        break

            if download_url:
                return True, latest_tag, download_url

        return False, None, None
    except Exception:
        # Silently fail — network errors must not crash the app
        return False, None, None


def download_and_install_update(download_url: str) -> None:
    """
    Downloads the update installer and launches a batch script that:
      1. Waits for Python to exit
      2. Runs the installer silently
      3. Cleans up the downloaded file and the batch script itself
    """
    try:
        temp_dir = tempfile.gettempdir()
        exe_path = os.path.join(temp_dir, "JVProcessor_Update.exe")

        with requests.get(download_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(exe_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        bat_content = f"""@echo off
echo Installing JV Processor Update...
timeout /t 2 /nobreak > nul
start /wait "" "{exe_path}" /SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
del "{exe_path}"
del "%~f0"
"""
        bat_path = os.path.join(temp_dir, "jv_processor_install_update.bat")
        with open(bat_path, "w", encoding="ansi") as f:
            f.write(bat_content)

        # Strip PyInstaller env vars so the restarted app doesn't use stale paths
        env = os.environ.copy()
        for k in [k for k in env if k.upper().startswith(("_PYI_", "_MEI"))]:
            env.pop(k)

        # CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen([bat_path], creationflags=0x08000000, env=env)

    except Exception as e:
        print(f"Error downloading or installing update: {e}")
