"""Help Center: About, Terms of Service, Privacy Policy, Bug Report.

All dialogs reuse the app's existing glass-card style and the single
version source (APP_VERSION in src/services/updater.py).

Legal texts below are plain-language TEMPLATES, not legal advice.
Have a lawyer review them before a public release, especially if data
collection ever changes.
"""

import urllib.parse

import flet as ft

from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI, primary_button_style, secondary_button_style
from src.services.updater import APP_VERSION
from src.services.bug_report import build_bug_report, SUPPORT_CONTACT_EMAIL
from src.services.clipboard import copy_text_to_clipboard

APP_NAME = "ITT OCR"
APP_TAGLINE = "Fast text extraction for scanned pages and photos."

# ---------------------------------------------------------------------------
# Legal copy (templates — see module docstring)
# ---------------------------------------------------------------------------

TOS_TEXT = """1. Acceptance of Terms
By installing or using ITT OCR you agree to these terms. If you do not agree, do not use the app.

2. Use of the App
ITT OCR converts images and scans into text using a vision-model service you configure yourself. You are responsible for having the right to process any document you load, and for complying with the terms of your chosen model provider.

3. Your Content and API Keys
Your documents, API keys, and settings stay on your own computer. The app never sees your API key after you save it (it is stored masked on your device). You are responsible for keeping your own keys safe.

4. Updates
The app can check a public releases page for new versions. Installing an update replaces only the app file; your settings and files are left untouched.

5. Limitations of Liability
The app is provided "as is", without warranties of any kind. Text extraction is AI-assisted and can make mistakes — always check important results yourself. To the maximum extent allowed by law, the developer is not liable for indirect or consequential damages.

6. Termination
You may stop using the app at any time by deleting it. Any terms that should reasonably survive (such as liability limits) continue to apply.

7. Changes to Terms
If these terms change, the new version will ship with the app and take effect when you install that update.

8. Contact
For questions about these terms, use Report a bug in the app's Settings and mention "Terms question"."""

PRIVACY_TEXT = """1. What We Collect
Almost nothing, and everything stays on your device:
- Your settings (API endpoint, model name, preferences) in a local config file.
- Basic usage counts (documents processed, characters extracted, successes/failures) in the same local file, so the dashboard can show them.
- Short-lived temporary files (scans, clipboard images, downloads) in your system temp folder.

2. How We Use It
Local data is used only to run the app (remember your settings, show your history and stats). It is never uploaded, sold, or shared by the app itself.

3. Data Storage and Security
Settings and history live in a folder on your computer (~/.itt_ocr_client). Your API key is stored masked and is never displayed again after saving. No account, no password, no cloud sync is built into the app.

4. Third Parties
Two things leave your computer, both only when you ask:
- Update checks contact the public GitHub releases page (which, like any website, can see your IP address and the app version being checked).
- Text extraction sends the current image to the vision-model endpoint YOU configured, using YOUR key, under YOUR provider's privacy policy. Choose a provider you trust, especially for sensitive documents.

5. User Rights and Choices
- You can clear your history in the app, turn off auto-extract, and turn off update checks in Settings.
- Bug reports are created as a file on your computer and only shared if you choose to send it.
- To erase everything, delete the app and the ~/.itt_ocr_client folder.

6. Contact
For privacy questions, use Report a bug in the app's Settings and mention "Privacy question"."""


# ---------------------------------------------------------------------------
# Shared dialog shell
# ---------------------------------------------------------------------------

def _shell(title: str, icon, body: list, width: int = 560) -> tuple:
    """Glass-card dialog shell. Returns (dialog, close_fn) pieces."""
    title_text = ft.Text(
        title, size=16, weight=ft.FontWeight.W_700,
        color=theme.text_primary, font_family=FONT_FAMILY_UI,
    )
    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=18, color=theme.accent),
                    title_text,
                ],
            ),
            ft.IconButton(
                icon=ft.Icons.CLOSE_ROUNDED, icon_size=16,
                icon_color=theme.text_secondary, tooltip="Close",
            ),
        ],
    )
    close_btn = header.controls[1]

    box = ft.Container(
        width=width,
        bgcolor=theme.glass_bg,
        blur=theme.glass_blur,
        border=theme.glass_border,
        border_radius=RADIUS_GLASS,
        shadow=theme.glass_shadow,
        padding=20,
        content=ft.Column(tight=True, spacing=14, controls=[header, *body]),
    )
    dialog = ft.AlertDialog(
        modal=True,
        bgcolor="transparent",
        shape=ft.RoundedRectangleBorder(radius=RADIUS_GLASS),
        content_padding=0,
        content=box,
    )
    return dialog, close_btn


def _bind_close(page: ft.Page, dialog: ft.AlertDialog, close_btn: ft.IconButton):
    close_btn.on_click = lambda e: page.pop_dialog()


def _legal_body(text: str) -> list:
    return [
        ft.Container(
            height=320,
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=14,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                spacing=8,
                controls=[
                    ft.Text(
                        text, size=12, color=theme.text_primary,
                        font_family=FONT_FAMILY_UI, selectable=True,
                    ),
                ],
            ),
        ),
        ft.Text(
            "Plain-language template — not legal advice. "
            "Have it reviewed before public release.",
            size=11, color=theme.text_secondary, font_family=FONT_FAMILY_UI,
        ),
    ]


# ---------------------------------------------------------------------------
# Public dialogs
# ---------------------------------------------------------------------------

def create_about_dialog(page: ft.Page) -> ft.AlertDialog:
    def _open(make):
        page.show_dialog(make(page))

    body = [
        ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=44, height=44, border_radius=12,
                    bgcolor=theme.accent,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.DOCUMENT_SCANNER_ROUNDED,
                        color="#FFFFFF", size=24,
                    ),
                ),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(
                            APP_NAME, size=17, weight=ft.FontWeight.W_700,
                            color=theme.text_primary, font_family=FONT_FAMILY_UI,
                        ),
                        ft.Text(
                            f"Version v{APP_VERSION}",
                            size=12, weight=ft.FontWeight.W_600,
                            color=theme.accent, font_family=FONT_FAMILY_UI,
                        ),
                    ],
                ),
            ],
        ),
        ft.Text(APP_TAGLINE, size=13, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
        ft.Container(
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=12,
            content=ft.Text(
                "Your files and settings stay on your computer. "
                "Text extraction uses the vision service you configure in Settings.",
                size=12, color=theme.text_secondary, font_family=FONT_FAMILY_UI,
            ),
        ),
        ft.Row(
            spacing=4,
            controls=[
                ft.TextButton(
                    "Terms of Service",
                    style=ft.ButtonStyle(color=theme.accent),
                    on_click=lambda e: _open(create_terms_dialog),
                ),
                ft.TextButton(
                    "Privacy Policy",
                    style=ft.ButtonStyle(color=theme.accent),
                    on_click=lambda e: _open(create_privacy_dialog),
                ),
                ft.TextButton(
                    "Report a bug",
                    style=ft.ButtonStyle(color=theme.accent),
                    on_click=lambda e: _open(create_bug_report_dialog),
                ),
            ],
        ),
        ft.Text(
            "Built with Flet (Python).",
            size=11, color=theme.text_secondary, font_family=FONT_FAMILY_UI,
        ),
    ]
    dialog, close_btn = _shell("About", ft.Icons.INFO_OUTLINED, body, width=480)
    _bind_close(page, dialog, close_btn)
    return dialog


def create_terms_dialog(page: ft.Page) -> ft.AlertDialog:
    dialog, close_btn = _shell(
        "Terms of Service", ft.Icons.DESCRIPTION_OUTLINED, _legal_body(TOS_TEXT),
    )
    _bind_close(page, dialog, close_btn)
    return dialog


def create_privacy_dialog(page: ft.Page) -> ft.AlertDialog:
    dialog, close_btn = _shell(
        "Privacy Policy", ft.Icons.PRIVACY_TIP_OUTLINED, _legal_body(PRIVACY_TEXT),
    )
    _bind_close(page, dialog, close_btn)
    return dialog


def create_bug_report_dialog(page: ft.Page) -> ft.AlertDialog:
    desc_field = ft.TextField(
        label="What went wrong?",
        hint_text="Example: extraction fails on my invoice photo with…",
        multiline=True, min_lines=3, max_lines=5, autofocus=True,
        border_color=theme.border, focused_border_color=theme.accent,
        text_size=13,
    )
    steps_field = ft.TextField(
        label="Steps to reproduce (optional)",
        hint_text="1. Open… 2. Click… 3. See…",
        multiline=True, min_lines=2, max_lines=4,
        border_color=theme.border, focused_border_color=theme.accent,
        text_size=13,
    )
    contact_field = ft.TextField(
        label="Your email (optional, only if you want a reply)",
        border_color=theme.border, focused_border_color=theme.accent,
        text_size=13, dense=True,
    )
    logs_switch = ft.Switch(
        label="Attach diagnostic info (recommended, API key removed)",
        value=True, active_color=theme.accent,
    )
    status_text = ft.Text(
        "Saves a file on your computer. Nothing is sent automatically.",
        size=11, color=theme.text_secondary, font_family=FONT_FAMILY_UI,
    )

    def _fail(message: str):
        status_text.value = message
        status_text.color = theme.error
        try:
            status_text.update()
        except Exception:
            pass

    def on_save(e):
        desc = (desc_field.value or "").strip()
        if len(desc) < 10:
            _fail("Please describe the problem in a sentence or two so we can help.")
            return
        try:
            path = build_bug_report(
                description=desc,
                steps=(steps_field.value or "").strip(),
                contact=(contact_field.value or "").strip(),
                include_logs=logs_switch.value,
            )
        except Exception:
            _fail("Couldn't save the report file. Please try again.")
            return
        try:
            copy_text_to_clipboard(str(path), page=page)
        except Exception:
            pass
        page.pop_dialog()
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(
                    f"Report saved. Its location is copied: {path}",
                    size=13, color=theme.text_primary,
                ),
                bgcolor=theme.glass_bg,
                duration=6000,
            )
        )

    def on_email(e):
        if not SUPPORT_CONTACT_EMAIL:
            _fail("Email support isn't set up yet — please use “Save report file” instead.")
            return
        desc = (desc_field.value or "").strip() or "(no description)"
        steps = (steps_field.value or "").strip()
        subject = urllib.parse.quote(f"{APP_NAME} bug report v{APP_VERSION}")
        body = urllib.parse.quote(f"{desc}\n\nSteps:\n{steps}"[:1500])
        try:
            page.launch_url(f"mailto:{SUPPORT_CONTACT_EMAIL}?subject={subject}&body={body}")
        except Exception:
            _fail("Couldn't open your email app. Please use “Save report file” instead.")

    actions = [
        ft.TextButton(
            "Cancel",
            style=ft.ButtonStyle(color=theme.text_secondary),
            on_click=lambda e: page.pop_dialog(),
        ),
    ]
    if SUPPORT_CONTACT_EMAIL:
        actions.append(
            ft.OutlinedButton(
                "Open email app",
                icon=ft.Icons.EMAIL_OUTLINED,
                style=secondary_button_style(),
                on_click=on_email,
            )
        )
    actions.append(
        ft.ElevatedButton(
            "Save report file",
            icon=ft.Icons.SAVE_OUTLINED,
            style=primary_button_style(),
            on_click=on_save,
        )
    )

    body = [
        desc_field,
        steps_field,
        contact_field,
        logs_switch,
        status_text,
        ft.Row(alignment=ft.MainAxisAlignment.END, spacing=8, controls=actions),
    ]
    dialog, close_btn = _shell("Report a bug", ft.Icons.BUG_REPORT_OUTLINED, body)
    _bind_close(page, dialog, close_btn)
    return dialog
