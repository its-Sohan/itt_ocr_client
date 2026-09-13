"""Local bug-report bundle builder.

Design choice (simplest reliable option): the app writes a redacted
diagnostic file on the user's own disk and tells them where it is.
No backend, no account, works offline. The user can then email it,
attach it anywhere, or delete it. Nothing ever leaves the machine
unless the user sends it themselves.

Privacy rules for the bundle (do not weaken these):
  - NEVER include the API key (replaced with "***set***" / "").
  - Strip query strings / embedded credentials from the endpoint URL.
  - NEVER include document contents (extracted_text) or local file
    paths (they leak OS usernames, e.g. /home/<name>/...).
  - Only metadata: file names, sizes, statuses, error messages.
"""

import platform
import re
import sys
from datetime import datetime
from pathlib import Path

from src.config_store import CONFIG_DIR, load_config, load_history
from src.services.updater import APP_VERSION, get_update_error_log_path

# TODO (before release): set your public support address. When empty, the
# in-app dialog hides the "Open email app" button and offers "Save file".
SUPPORT_CONTACT_EMAIL = ""


def _redact_url(url: str) -> str:
    """Remove query strings, fragments, and userinfo from an endpoint URL."""
    url = (url or "").strip()
    if not url:
        return ""
    had_secret = ("?" in url) or ("#" in url)
    url = re.sub(r"[?#].*$", "", url)
    url = re.sub(r"://[^/@]*@", "://***@", url)
    if had_secret:
        url += "?<redacted>"
    return url


def _redacted_config_snapshot() -> dict:
    config = load_config()
    api_key = (config.get("api_key") or "").strip()
    return {
        "session_account": config.get("session_account", ""),
        "api_key": "***set***" if api_key else "",
        "base_url": _redact_url(config.get("base_url", "")),
        "model_name": config.get("model_name", ""),
        "auto_extract": config.get("auto_extract", True),
        "default_output_mode": config.get("default_output_mode", ""),
        "quality": config.get("quality", ""),
        "releases_repo": config.get("releases_repo", ""),
        "check_updates_on_startup": config.get("check_updates_on_startup", True),
        "usage_stats": config.get("usage_stats", {}),
    }


def _history_snapshot(limit: int = 50) -> list:
    """Metadata only: names, sizes, statuses, error snippets. No contents."""
    try:
        items = load_history()
    except Exception:
        return []
    snapshot = []
    for entry in items[-limit:]:
        if not isinstance(entry, dict):
            continue
        snapshot.append(
            {
                "file_name": entry.get("file_name", ""),
                "file_size": entry.get("file_size_str", ""),
                "status": entry.get("status", ""),
                "source": entry.get("source", ""),
                "output_mode": entry.get("output_mode", ""),
                "error": str(entry.get("error_message", "") or "")[:300],
            }
        )
    return snapshot


def _updater_log_snapshot() -> str:
    """Read (without clearing) the replacer helper's error log, if any."""
    try:
        log = get_update_error_log_path()
        if log.exists():
            return log.read_text(encoding="utf-8", errors="replace").strip()[:2000]
    except Exception:
        pass
    return ""


def build_bug_report(
    description: str,
    steps: str = "",
    contact: str = "",
    include_logs: bool = True,
) -> Path:
    """Write a redacted bug-report markdown file. Returns its path.

    Raises OSError if the file cannot be written.
    """
    reports_dir = CONFIG_DIR / "bug-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = reports_dir / f"itt-ocr-bug-report-{stamp}.md"

    lines = [
        "# ITT OCR — Bug report",
        "",
        f"App version: v{APP_VERSION}",
        f"Platform: {platform.system()} {platform.release()} ({platform.machine()})",
        f"Python: {sys.version.split()[0]}",
        f"Created: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## What went wrong",
        (description or "").strip() or "(no description given)",
        "",
        "## Steps to reproduce",
        (steps or "").strip() or "(not provided)",
        "",
        "## Contact (optional)",
        (contact or "").strip() or "(not provided)",
        "",
    ]
    if include_logs:
        lines += [
            "## Diagnostic info (automatic, redacted)",
            "",
            "### Settings snapshot (API key removed)",
            "```",
            _format_snapshot(_redacted_config_snapshot()),
            "```",
            "",
            "### Recent documents (names only, no contents)",
            _format_history(_history_snapshot()),
            "",
            "### Last updater message",
            _updater_log_snapshot() or "(none)",
            "",
        ]
    else:
        lines += ["## Diagnostic info", "(excluded at the user's request)", ""]
    lines += [
        "---",
        "This file was created on your computer by ITT OCR. "
        "Nothing was sent anywhere — attach it to a support message only if you want to.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _format_snapshot(snapshot: dict) -> str:
    import json

    try:
        return json.dumps(snapshot, indent=2, ensure_ascii=False)
    except Exception:
        return str(snapshot)


def _format_history(items: list) -> str:
    if not items:
        return "(no recent documents)"
    rows = []
    for it in items:
        rows.append(
            f"- {it.get('file_name', '?')} "
            f"[{it.get('file_size', '?')}, {it.get('status', '?')}, "
            f"{it.get('source', '?')}]"
            + (f" — error: {it['error']}" if it.get("error") else "")
        )
    return "\n".join(rows)
