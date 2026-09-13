"""Self-update engine for the portable Windows .exe build.

Main-app code only. The actual file replacement is performed by a tiny
Windows batch helper generated at runtime (see build_replacer_batch() /
stage_and_launch_replacer()) because a running .exe cannot overwrite
itself on Windows (file lock).

Version source: APP_VERSION constant below (bumped by hand per release).
Release source: public GitHub Releases repo, e.g. its-Sohan/itt-ocr-release,
queried via the releases/latest API. Each release must contain:
  - ITT-OCR-vX.Y.Z.exe          (the portable app)
  - ITT-OCR-vX.Y.Z.exe.sha256   (plain text file holding the SHA256 hex)

User data lives in ~/.itt_ocr_client (see config_store.py) and is never
touched by this module -- only the .exe file itself is replaced, plus a
one-generation .bak backup next to it.

Windows quirks handled here (see inline notes):
  1. Running .exe is locked -- replacer waits on our PID via tasklist.
  2. Frozen exe path is sys.executable, NOT __file__ (PyInstaller/Flet
     unpacks to a _MEI temp dir; __file__ would point there).
  3. Unsigned downloads may trip SmartScreen/AV -- we never bypass it,
     we only show a calm message telling the user what the dialog means.
  4. Console flash -- replacer is launched with CREATE_NO_WINDOW.
  5. Batch (.bat) is used instead of PowerShell to avoid ExecutionPolicy
     prompts for non-technical users.
"""

import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx
from packaging import version as pkg_version

# ---------------------------------------------------------------------------
# Version + release location (both maintained by hand, no automation assumed)
# ---------------------------------------------------------------------------

# Current running version. Bump this string by hand for every release.
APP_VERSION = "1.0.0"

# Default public releases repo ("owner/repo"). Overridable per-user via
# config.json -> releases_repo (see config_store.py).
DEFAULT_RELEASE_REPO = "its-Sohan/itt-ocr-release"

# How long the replacer waits for the main app to exit before giving up.
REPLACER_WAIT_SECONDS = 30

# Matches a bare SHA256 hex digest inside a .sha256 sidecar file, which may
# look like "<hex>  <filename>" (certutil/sha256sum style) or just "<hex>".
_SHA256_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")


def get_platform_asset_keyword() -> str:
    """File keyword identifying the installer asset for this OS."""
    system = platform.system().lower()
    if "windows" in system:
        return ".exe"
    if "darwin" in system:
        return ".dmg"
    return "linux"


def _friendly_network_error(exc: Exception) -> str:
    """Map low-level network errors to calm, non-technical messages."""
    # httpx timeout / DNS / refused all mean the same thing to end users.
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if "timeout" in name or "timeout" in text or "timed out" in text:
        return "The update check took too long. Check your connection and try again."
    if "connect" in name or "dns" in text or "getaddrinfo" in text or "refused" in text:
        return "You're not connected to the internet. Connect and try again."
    return "Couldn't reach the update server. Check your internet and try again."


def _safe_parse(v: str):
    """Parse a version string, returning None instead of raising."""
    try:
        return pkg_version.parse(v.strip())
    except Exception:
        return None


async def check_for_updates(
    repo: str = DEFAULT_RELEASE_REPO,
    current_version: str = APP_VERSION,
) -> dict:
    """Ask GitHub for the latest release and compare it to this build.

    Never raises: all failures return {"has_update": False, "error": ...}
    with an additional "error_kind" hint ("network" | "not_found" |
    "invalid" | "unknown") so the UI can pick a reassuring message.
    """
    repo = (repo or DEFAULT_RELEASE_REPO).strip().strip("/")
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ITT-OCR-Client",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            res = await client.get(url, headers=headers)
    except Exception as exc:  # DNS down, wifi off, captive portal, ...
        return {"has_update": False, "error": _friendly_network_error(exc), "error_kind": "network"}

    if res.status_code == 404:
        return {
            "has_update": False,
            "error": "No updates published yet. Please try again later.",
            "error_kind": "not_found",
            "status_code": 404,
        }
    if res.status_code == 403 and "rate limit" in res.text.lower():
        return {
            "has_update": False,
            "error": "Too many update checks right now. Please wait a few minutes.",
            "error_kind": "network",
            "status_code": 403,
        }
    if res.status_code != 200:
        return {
            "has_update": False,
            "error": "We couldn't check for updates just now. Please try again later.",
            "error_kind": "unknown",
            "status_code": res.status_code,
        }

    try:
        data = res.json()
    except Exception:
        return {"has_update": False, "error": "The update server sent an unclear reply.", "error_kind": "invalid"}

    raw_tag = (data.get("tag_name") or "").strip()
    latest_str = raw_tag.lstrip("vV").strip()
    if not latest_str:
        return {"has_update": False, "error": "This release is missing its version label.", "error_kind": "invalid"}

    current_parsed = _safe_parse(current_version)
    latest_parsed = _safe_parse(latest_str)
    if current_parsed is None or latest_parsed is None:
        return {"has_update": False, "error": "Version check couldn't compare versions.", "error_kind": "invalid"}

    if latest_parsed <= current_parsed:
        return {
            "has_update": False,
            "current_version": current_version,
            "latest_version": latest_str,
        }

    # A newer release exists: locate the Windows .exe + its .sha256 sidecar.
    assets = data.get("assets") or []
    exe_asset = None
    for asset in assets:
        name = (asset.get("name") or "")
        # Windows portable build: ends with .exe (case-insensitive).
        if name.lower().endswith(".exe"):
            exe_asset = asset
            break
    if exe_asset is None:
        return {
            "has_update": False,
            "error": "The newest release has no Windows download yet.",
            "error_kind": "not_found",
        }

    exe_name = exe_asset.get("name") or ""
    download_url = exe_asset.get("browser_download_url") or ""

    # Sidecar is "<exe name>.sha256", e.g. ITT-OCR-v1.1.0.exe.sha256.
    sha256_url = None
    for asset in assets:
        name = (asset.get("name") or "")
        if name == f"{exe_name}.sha256":
            sha256_url = asset.get("browser_download_url")
            break
    # Fallback: any lone .sha256 asset when the release ships exactly one exe.
    if sha256_url is None:
        sha_candidates = [a for a in assets if (a.get("name") or "").lower().endswith(".sha256")]
        if len(sha_candidates) == 1:
            sha256_url = sha_candidates[0].get("browser_download_url")

    if not download_url:
        return {
            "has_update": False,
            "error": "The newest release has no Windows download yet.",
            "error_kind": "not_found",
        }

    return {
        "has_update": True,
        "current_version": current_version,
        "latest_version": latest_str,
        "tag_name": raw_tag,
        "release_name": data.get("name") or raw_tag,
        "release_notes": data.get("body") or "No details provided for this release.",
        "published_at": data.get("published_at") or "",
        "download_url": download_url,
        "sha256_url": sha256_url,  # None when publisher forgot the sidecar.
        "asset_name": exe_name,
        "release_page_url": data.get("html_url") or "",
    }


async def fetch_expected_sha256(sha256_url: str) -> str:
    """Download the .sha256 sidecar and extract the 64-hex digest.

    Raises RuntimeError with a user-readable message on any failure.
    """
    if not sha256_url:
        raise RuntimeError("This update is missing its safety check file. We'll keep your current version.")
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            res = await client.get(sha256_url, headers={"User-Agent": "ITT-OCR-Client"})
            res.raise_for_status()
            text = res.text
    except Exception as exc:
        raise RuntimeError("Couldn't fetch the update safety check. Check your internet and retry.") from exc
    match = _SHA256_RE.search(text or "")
    if not match:
        raise RuntimeError("The update safety check file looks damaged. We'll keep your current version.")
    return match.group(0).lower()


async def download_update(update_info: dict, dest_path: Path, on_progress=None) -> Path:
    """Stream the new .exe into dest_path (a temp file, never the live exe).

    on_progress(downloaded_bytes, total_bytes) is called per chunk; total
    may be 0 when the server omits Content-Length (then UI shows activity
    instead of a percentage).

    Raises RuntimeError with a calm message; removes any partial file.
    """
    download_url = (update_info or {}).get("download_url") or ""
    if not download_url:
        raise RuntimeError("We couldn't find the download link for this update.")
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    part_path = dest_path.with_suffix(dest_path.suffix + ".part")

    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            async with client.stream("GET", download_url) as res:
                res.raise_for_status()
                total = int(res.headers.get("content-length") or 0)
                # Pre-flight disk-space guard: need the file plus slack.
                if total > 0:
                    try:
                        free = shutil.disk_usage(str(part_path.parent)).free
                        if free < total + (10 * 1024 * 1024):
                            raise RuntimeError(
                                "Not enough space to download the update. "
                                "Free up some space and try again."
                            )
                    except RuntimeError:
                        raise
                    except Exception:
                        pass  # Non-fatal: continue and let the write fail naturally.
                downloaded = 0
                try:
                    with part_path.open("wb") as fh:
                        async for chunk in res.aiter_bytes(chunk_size=64 * 1024):
                            if not chunk:
                                continue
                            fh.write(chunk)
                            downloaded += len(chunk)
                            if on_progress is not None:
                                try:
                                    on_progress(downloaded, total)
                                except Exception:
                                    pass
                except RuntimeError:
                    raise
                except OSError as exc:
                    # ENOSPC = disk filled mid-download.
                    if getattr(exc, "errno", None) == 28:
                        raise RuntimeError(
                            "Your disk filled up during the download. Free space and retry."
                        ) from exc
                    raise RuntimeError("Couldn't save the download. Try again.") from exc
                if total > 0 and downloaded < total:
                    raise RuntimeError("The download stopped early. Tap Retry to try again.")
                if downloaded == 0:
                    raise RuntimeError("The download came back empty. Tap Retry to try again.")
    except RuntimeError:
        try:
            part_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    except Exception as exc:
        try:
            part_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise RuntimeError("The download failed. Check your internet and tap Retry.") from exc

    try:
        # Atomic publish of the temp file: readers never see a half file.
        if dest_path.exists():
            try:
                dest_path.unlink()
            except Exception:
                pass
        part_path.rename(dest_path)
    except OSError as exc:
        try:
            part_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise RuntimeError("Couldn't save the download. Try again.") from exc
    return dest_path


def verify_sha256(file_path: Path, expected_hex: str) -> bool:
    """Return True iff the SHA256 of file_path matches expected_hex."""
    expected = (expected_hex or "").strip().lower()
    if not expected or not _SHA256_RE.fullmatch(expected):
        return False
    digest = hashlib.sha256()
    try:
        with Path(file_path).open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return False
    return digest.hexdigest().lower() == expected


def resolve_current_exe() -> Path:
    """Absolute path of the currently running .exe.

    Windows quirk: when frozen (PyInstaller/Flet), sys.executable IS the
    .exe; __file__/sys.argv[0] would point inside the _MEI temp bundle.
    In dev (python main.py) fall back to argv[0] so the replacer still has
    something sensible to relaunch.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    try:
        candidate = Path(sys.argv[0]).resolve()
        if candidate.is_file():
            return candidate
    except Exception:
        pass
    return Path(sys.executable).resolve()


def get_update_error_log_path() -> Path:
    """Where the batch helper records a failed replace (temp dir)."""
    return Path(tempfile.gettempdir()) / "itt-ocr-update-error.log"


def check_pending_update_result() -> str | None:
    """Return (and clear) the replacer's error message from last launch, if any."""
    log = get_update_error_log_path()
    try:
        if not log.exists():
            return None
        text = log.read_text(encoding="utf-8", errors="replace").strip()
        try:
            log.unlink()
        except Exception:
            pass
        return text or None
    except Exception:
        return None


def build_replacer_batch(
    current_exe: Path,
    new_exe: Path,
    pid: int,
    log_path: Path,
) -> str:
    """Build the .bat helper that swaps the exe AFTER we exit.

    Why a separate helper: Windows locks the running .exe, so the app
    itself can never overwrite it. The helper polls tasklist until our PID
    disappears, keeps one .bak copy, moves the new file over, relaunches,
    then deletes itself. All paths are quoted (Program Files has spaces).
    """
    cur = str(current_exe)
    new = str(new_exe)
    log = str(log_path)
    wait = int(REPLACER_WAIT_SECONDS)
    # NOTE: batch labels + delayed expansion avoided on purpose to stay
    # readable for the developer hand-editing this in an emergency.
    lines = [
        "@echo off",
        "rem ITT OCR self-update helper -- generated at runtime, deletes itself.",
        "rem Waits for the main app PID to exit, then swaps the .exe.",
        "setlocal",
        f'set "CURRENT_EXE={cur}"',
        f'set "NEW_EXE={new}"',
        f'set "PID={int(pid)}"',
        f'set "LOG={log}"',
        f'set "BACKUP={cur}.bak"',
        'if exist "%LOG%" del /F /Q "%LOG%" >nul 2>&1',
        f"set /a TRIES={wait}",
        ":waitloop",
        'tasklist /FI "PID eq %PID%" 2>nul | find /I "%PID%" >nul',
        'if errorlevel 1 goto doswap',
        "set /a TRIES-=1",
        "if %TRIES% LEQ 0 goto doswap",
        "timeout /T 1 /NOBREAK >nul",
        "goto waitloop",
        ":doswap",
        'rem Keep one backup generation so a bad build can be restored by hand.',
        'copy /Y "%CURRENT_EXE%" "%BACKUP%" >nul 2>&1',
        'rem The actual replacement. move works even across drives.',
        'move /Y "%NEW_EXE%" "%CURRENT_EXE%" >nul 2>&1',
        "if errorlevel 1 goto failed",
        'rem Relaunch the fresh app (empty title arg required by start).',
        'start "" "%CURRENT_EXE%"',
        'rem Best-effort cleanup of the staged download if move left a copy.',
        'if exist "%NEW_EXE%" del /F /Q "%NEW_EXE%" >nul 2>&1',
        "goto selfdel",
        ":failed",
        'echo Update could not replace the app file. Your previous version was left in place.>> "%LOG%"',
        'echo If the app lives in Program Files, reinstall it into your user folder or run once as admin.>> "%LOG%"',
        "exit /b 1",
        ":selfdel",
        'rem Delete this helper itself.',
        '(goto) 2>nul & del /F /Q "%~f0" >nul 2>&1',
    ]
    return "\r\n".join(lines) + "\r\n"


def stage_and_launch_replacer(new_exe_path: Path, current_exe: Path | None = None) -> Path:
    """Write the replacer .bat next to the staged download and launch it.

    Returns the .bat path (mostly for tests). The caller must exit the app
    immediately after this returns so the helper can proceed.

    Raises RuntimeError with a calm message when:
      - staged file is missing,
      - the app folder is not writable (e.g. Program Files w/o admin),
      - we are not on Windows (replace only supported there; the caller
        should have gated on platform already).
    """
    if platform.system().lower() != "windows":
        raise RuntimeError("Automatic install is supported on Windows in this build.")
    staged = Path(new_exe_path)
    if not staged.is_file():
        raise RuntimeError("The downloaded update went missing. Please retry.")
    target = Path(current_exe) if current_exe is not None else resolve_current_exe()
    target_dir = target.parent
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    # Writability probe: Program Files without elevation fails here, before
    # we ask the user to close the app for nothing.
    probe = target_dir / ".itt-ocr-write-test.tmp"
    try:
        with probe.open("wb") as fh:
            fh.write(b"ok")
        try:
            probe.unlink()
        except Exception:
            pass
    except OSError as exc:
        err_no = getattr(exc, "errno", None)
        win_err = getattr(exc, "winerror", None)
        if err_no in (13,) or win_err in (5,):
            raise RuntimeError(
                "Windows blocked the update (this folder needs admin rights). "
                "Your current version is untouched."
            ) from exc
        raise RuntimeError("Couldn't prepare the update folder. Please retry.") from exc

    log_path = get_update_error_log_path()
    bat_text = build_replacer_batch(
        current_exe=target,
        new_exe=staged,
        pid=os.getpid(),
        log_path=log_path,
    )
    bat_path = Path(tempfile.gettempdir()) / f"itt-ocr-apply-{os.getpid()}.bat"
    try:
        bat_path.write_text(bat_text, encoding="utf-8")
    except OSError as exc:
        raise RuntimeError("Couldn't prepare the updater helper. Please retry.") from exc

    # Detached + no console window: no black flash for non-technical users.
    # Windows quirk: CREATE_NO_WINDOW (0x08000000) + DETACHED_PROCESS (0x8).
    creationflags = 0
    startupinfo = None
    try:
        creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        si_cls = getattr(subprocess, "STARTUPINFO", None)
        if si_cls is not None:
            startupinfo = si_cls()
            try:
                startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
                startupinfo.wShowWindow = 0  # SW_HIDE
            except Exception:
                pass
    except Exception:
        pass
    try:
        subprocess.Popen(
            ["cmd.exe", "/c", str(bat_path)],
            close_fds=True,
            creationflags=creationflags,
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    except OSError as exc:
        try:
            bat_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise RuntimeError("Couldn't start the updater helper. Please retry.") from exc
    return bat_path
