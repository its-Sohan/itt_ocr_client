"""Update prompt dialog: check -> download w/ progress -> verify -> relaunch.

User flow (kept simple for non-technical users):
  press "Install & Restart" -> see progress bar -> app closes itself ->
  helper swaps the .exe -> fresh app opens. Any failure leaves the current
  version untouched and shows a calm message plus a Retry button.

Separation: this file is UI only. All network / filesystem work lives in
src/services/updater.py (main-app code) plus the runtime-generated .bat
helper (updater helper script). This dialog only orchestrates them.
"""

import platform
import re
import tempfile
import time
from pathlib import Path

import flet as ft

from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI, primary_button_style
from src.services.updater import (
    download_update,
    fetch_expected_sha256,
    stage_and_launch_replacer,
    verify_sha256,
)


def _safe_asset_name(name: str, fallback: str) -> str:
    """Sanitize the release asset name for use as a temp filename."""
    base = (name or fallback).strip() or fallback
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    if not safe.lower().endswith(".exe"):
        safe += ".exe"
    return safe


def create_update_dialog(page: ft.Page, update_info: dict) -> ft.AlertDialog:
    latest_ver = update_info.get("latest_version", "unknown")
    current_ver = update_info.get("current_version", "")
    release_notes = update_info.get("release_notes", "No details provided for this release.")
    release_page = update_info.get("release_page_url") or ""

    # -- progress + status widgets (hidden until download starts) ----------
    status_text = ft.Text(
        "Your files and settings will stay safe.",
        size=12,
        color=theme.text_secondary,
        font_family=FONT_FAMILY_UI,
    )
    progress_bar = ft.ProgressBar(
        value=0,
        visible=False,
        color=theme.accent,
        bgcolor=theme.border,
        height=6,
    )

    def set_busy(busy: bool, label: str = ""):
        """Toggle button/progress state; always call before page.update()."""
        update_button.disabled = busy
        later_button.disabled = busy
        close_button.disabled = busy
        progress_bar.visible = busy or progress_bar.visible
        if label:
            status_text.value = label
            status_text.color = theme.text_secondary

    def show_error(message: str):
        """Failure state: calm message + Retry affordance, no stack trace."""
        status_text.value = message
        status_text.color = theme.error
        progress_bar.visible = False
        update_button.disabled = False
        update_button.text = "Try again"
        update_button.icon = ft.Icons.REFRESH_ROUNDED
        later_button.disabled = False
        close_button.disabled = False
        page.update()

    def on_close(e=None):
        # X / Later: never touch the filesystem, just dismiss.
        try:
            dialog.open = False
            page.update()
        except Exception:
            pass

    async def on_update_click(e=None):
        # Guard: portable auto-replace is a Windows-only flow in this build.
        if platform.system().lower() != "windows":
            show_error("Automatic install works on Windows in this build.")
            if release_page:
                try:
                    page.launch_url(release_page)
                except Exception:
                    pass
            return

        sha256_url = update_info.get("sha256_url")
        if not sha256_url:
            # NEVER skip verification: abort rather than install blind.
            show_error("This update is missing its safety check, so we kept your current version.")
            return

        set_busy(True, "Getting ready…")
        update_button.text = "Updating…"
        update_button.icon = ft.Icons.DOWNLOAD_ROUNDED
        page.update()

        # Stage into %TEMP%, never next to (or over) the running .exe.
        asset_name = _safe_asset_name(
            update_info.get("asset_name") or "",
            f"ITT-OCR-v{latest_ver}.exe",
        )
        dest = Path(tempfile.gettempdir()) / f"itt-ocr-{latest_ver}-{asset_name}"
        last_ui_push = 0.0

        def on_progress(downloaded: int, total: int):
            # Throttle UI pushes: per-64KB-chunk updates would flood Flet.
            nonlocal last_ui_push
            now = time.monotonic()
            if total and total > 0:
                frac = max(0.0, min(1.0, downloaded / total))
                progress_bar.value = frac
                pct = int(frac * 100)
                # Windows quirk note: Content-Length may be absent on some
                # mirrors; then we fall through to the indeterminate branch.
                status_text.value = f"Downloading update… {pct}%"
            else:
                progress_bar.value = None  # indeterminate activity bar
                mb = downloaded / (1024 * 1024)
                status_text.value = f"Downloading update… {mb:.1f} MB so far"
            if now - last_ui_push >= 0.15:
                last_ui_push = now
                try:
                    progress_bar.update()
                    status_text.update()
                except Exception:
                    pass

        try:
            # 1. Safety-check file first (small, fast fail before big .exe).
            set_busy(True, "Checking update safety…")
            page.update()
            expected = await fetch_expected_sha256(sha256_url)

            # 2. Download to temp with live progress.
            set_busy(True, "Downloading update… 0%")
            progress_bar.value = 0
            progress_bar.visible = True
            page.update()
            await download_update(update_info, dest, on_progress=on_progress)

            # 3. Verify completeness BEFORE touching the installed copy.
            status_text.value = "Making sure the download is complete…"
            try:
                status_text.update()
            except Exception:
                pass
            ok = verify_sha256(dest, expected)
            if not ok:
                try:
                    dest.unlink(missing_ok=True)
                except Exception:
                    pass
                show_error("The download didn't match its safety check. Your current version is untouched — tap Try again.")
                return

            # 4. Hand off to the .bat replacer, then exit so it can swap.
            # Windows quirk: the running .exe is file-locked; only the
            # helper (running after we exit) may move/overwrite it.
            status_text.value = "Closing the app to finish… Opening the new version in a moment."
            try:
                status_text.update()
            except Exception:
                pass
            stage_and_launch_replacer(dest)

            try:
                dialog.open = False
                page.update()
            except Exception:
                pass
            try:
                page.window.close()
            except Exception:
                # Fallback: ask OS to terminate if window handle is gone.
                import os as _os

                _os._exit(0)
        except RuntimeError as exc:
            # All updater errors are already user-readable; show verbatim.
            show_error(str(exc) or "Something went wrong. Your current version is untouched — tap Try again.")
        except Exception:
            # Last-resort guard: never leak a traceback to end users.
            show_error("Something went wrong. Your current version is untouched — tap Try again.")

    # -- static content ------------------------------------------------------
    notes_box = ft.Container(
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
            controls=[
                ft.Markdown(
                    release_notes,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                )
            ],
        ),
        bgcolor=theme.bg,
        border=ft.Border.all(1, theme.border),
        border_radius=8,
        padding=12,
    )
    # Fixed height via parent container so long changelogs scroll internally.
    notes_box.height = 180

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.SYSTEM_UPDATE_ROUNDED, color=theme.accent, size=20),
                    ft.Text(
                        "Update Available",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=theme.text_primary,
                        font_family=FONT_FAMILY_UI,
                    ),
                ],
            ),
            close_button := ft.IconButton(
                icon=ft.Icons.CLOSE_ROUNDED,
                icon_size=16,
                icon_color=theme.text_secondary,
                on_click=on_close,
            ),
        ],
    )

    version_chips = ft.Row(
        spacing=8,
        controls=[
            ft.Container(
                content=ft.Text(f"Current: v{current_ver}", size=11, color=theme.text_secondary),
                bgcolor=theme.surface,
                border=ft.Border.all(1, theme.border),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            ),
            ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=12, color=theme.text_secondary),
            ft.Container(
                content=ft.Text(f"New: v{latest_ver}", size=11, weight=ft.FontWeight.W_600, color=theme.accent),
                bgcolor=theme.surface,
                border=ft.Border.all(1, theme.accent),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            ),
        ],
    )

    content_box = ft.Container(
        width=560,
        bgcolor=theme.glass_bg,
        blur=theme.glass_blur,
        border=theme.glass_border,
        border_radius=RADIUS_GLASS,
        shadow=theme.glass_shadow,
        padding=24,
        content=ft.Column(
            tight=True,
            spacing=14,
            controls=[
                header,
                version_chips,
                ft.Text(
                    "What's new in this version:",
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=theme.text_primary,
                    font_family=FONT_FAMILY_UI,
                ),
                notes_box,
                ft.Column(spacing=6, controls=[status_text, progress_bar]),
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    spacing=8,
                    controls=[
                        later_button := ft.TextButton(
                            "Later",
                            style=ft.ButtonStyle(
                                color=theme.text_secondary,
                                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                            ),
                            on_click=on_close,
                        ),
                        update_button := ft.ElevatedButton(
                            "Install & Restart",
                            icon=ft.Icons.DOWNLOAD_ROUNDED,
                            style=primary_button_style(),
                            on_click=on_update_click,
                        ),
                    ],
                ),
            ],
        ),
    )

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor="transparent",
        shape=ft.RoundedRectangleBorder(radius=RADIUS_GLASS),
        content_padding=0,
        content=content_box,
    )
    return dialog
