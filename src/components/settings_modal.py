import flet as ft
from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI, primary_button_style, secondary_button_style
from src.config_store import load_config, save_config
from src.services.updater import check_for_updates, APP_VERSION, DEFAULT_RELEASE_REPO
from src.components.update_dialog import create_update_dialog
from src.components.help_center import (
    create_about_dialog,
    create_terms_dialog,
    create_privacy_dialog,
    create_bug_report_dialog,
)

MASKED_PLACEHOLDER = "••••••••••••••••••••"

def create_settings_modal(page: ft.Page, on_saved=None) -> ft.AlertDialog:
    config = load_config()

    saved_api_key = config.get("api_key", "").strip()
    saved_base_url = config.get("base_url", "https://api.openai.com/v1").strip()

    is_api_configured = bool(saved_api_key)
    is_url_configured = bool(saved_base_url)

    session_field = ft.TextField(
        label="Session account",
        value=config.get("session_account", "default_user"),
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=13,
        dense=True,
    )

    # API Key Field: Completely unseeable once configured (password=True, no reveal, value masked)
    api_key_field = ft.TextField(
        label="API key" + (" (configured & locked)" if is_api_configured else ""),
        value=MASKED_PLACEHOLDER if is_api_configured else "",
        hint_text="Enter new API key to update" if is_api_configured else "sk-...",
        password=True,
        can_reveal_password=False,
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=13,
        dense=True,
        helper="Stored key is masked and uncopyable. Type a new key to overwrite." if is_api_configured else None,
        helper_style=ft.TextStyle(size=11, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
    )

    # API Base URL Field: Completely unseeable once configured (password=True, no reveal, value masked)
    base_url_field = ft.TextField(
        label="API base URL / Endpoint" + (" (configured & locked)" if is_url_configured else ""),
        value=MASKED_PLACEHOLDER if is_url_configured else saved_base_url,
        hint_text="Enter new endpoint URL to update" if is_url_configured else "https://api.openai.com/v1",
        password=True,
        can_reveal_password=False,
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=13,
        dense=True,
        helper="Stored endpoint is masked and uncopyable. Type a new URL to overwrite." if is_url_configured else None,
        helper_style=ft.TextStyle(size=11, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
    )

    model_field = ft.TextField(
        label="Vision model",
        value=config.get("model_name", "gpt-4o-mini"),
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=13,
        dense=True,
    )

    default_mode_dropdown = ft.Dropdown(
        label="Default output format",
        value=config.get("default_output_mode", "document"),
        options=[
            ft.dropdown.Option("document", "Document (Standard prose & layout)"),
            ft.dropdown.Option("spreadsheet", "Spreadsheet (Invoices, tables, Excel TSV)"),
            ft.dropdown.Option("key_value", "Key-Value (IDs, forms, certificates)"),
            ft.dropdown.Option("raw_text", "Raw Text (Unformatted plain text)"),
        ],
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=13,
        dense=True,
    )

    auto_extract_switch = ft.Switch(
        label="Auto-extract on ingest (drop, paste, scan)",
        value=config.get("auto_extract", True),
        active_color=theme.accent,
    )

    reduced_motion_switch = ft.Switch(
        label="Reduce motion",
        value=theme.reduced_motion,
        active_color=theme.accent,
        on_change=lambda e: theme.set_reduced_motion(e.control.value),
    )

    theme_switch = ft.Switch(
        label="Dark mode",
        value=theme.is_dark,
        active_color=theme.accent,
        on_change=lambda e: theme.toggle_theme(),
    )

    check_updates_switch = ft.Switch(
        label="Check for updates automatically on startup",
        value=config.get("check_updates_on_startup", True),
        active_color=theme.accent,
    )

    releases_repo_field = ft.TextField(
        label="Releases Repository (GitHub owner/repo)",
        value=config.get("releases_repo", DEFAULT_RELEASE_REPO),
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=12,
        dense=True,
        helper="Point to your public releases repository (e.g. its-Sohan/itt-ocr-release)",
        helper_style=ft.TextStyle(size=11, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
    )

    update_status_text = ft.Text(
        f"Installed version: v{APP_VERSION}",
        size=11,
        color=theme.text_secondary,
        font_family=FONT_FAMILY_UI,
    )

    async def on_check_update_click(e):
        # Friendly, jargon-free status flow: checking -> ready / all-set / calm error.
        check_update_btn.disabled = True
        update_status_text.value = "Checking for updates…"
        update_status_text.color = theme.text_secondary
        try:
            update_status_text.update()
        except Exception:
            pass
        try:
            repo = releases_repo_field.value.strip() or DEFAULT_RELEASE_REPO
            info = await check_for_updates(repo=repo, current_version=APP_VERSION)
        except Exception:
            # check_for_updates never raises, but stay safe: no traceback to users.
            info = {"has_update": False, "error": "Couldn't check just now. Please try again."}
        try:
            if info.get("has_update"):
                update_status_text.value = f"A new version (v{info.get('latest_version')}) is ready."
                update_status_text.color = theme.accent
                update_status_text.update()
                update_dlg = create_update_dialog(page, info)
                page.show_dialog(update_dlg)
            elif info.get("error"):
                # Error strings from updater.py are already plain-English.
                update_status_text.value = str(info.get("error"))
                update_status_text.color = theme.text_secondary
                update_status_text.update()
            else:
                update_status_text.value = "You're all set — you have the newest version."
                update_status_text.color = theme.accent
                update_status_text.update()
        finally:
            check_update_btn.disabled = False
            try:
                check_update_btn.update()
            except Exception:
                pass

    check_update_btn = ft.OutlinedButton(
        "Check Now",
        icon=ft.Icons.REFRESH_ROUNDED,
        style=secondary_button_style(),
        on_click=on_check_update_click,
    )

    update_section = ft.Container(
        bgcolor=theme.surface,
        border=ft.Border.all(1, theme.border),
        border_radius=RADIUS_PANEL,
        padding=16,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "App Updates",
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=theme.text_primary,
                                    font_family=FONT_FAMILY_UI,
                                ),
                                update_status_text,
                            ],
                        ),
                        check_update_btn,
                    ],
                ),
                releases_repo_field,
                check_updates_switch,
            ],
        ),
    )

    def _open_help(make):
        page.show_dialog(make(page))

    help_section = ft.Container(
        bgcolor=theme.surface,
        border=ft.Border.all(1, theme.border),
        border_radius=RADIUS_PANEL,
        padding=16,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text(
                    "HELP & LEGAL",
                    size=10,
                    weight=ft.FontWeight.W_600,
                    color=theme.text_secondary,
                    font_family=FONT_FAMILY_UI,
                ),
                ft.Text(
                    f"ITT OCR v{APP_VERSION} — help, policies, and support live here.",
                    size=12,
                    color=theme.text_secondary,
                    font_family=FONT_FAMILY_UI,
                ),
                ft.Row(
                    spacing=8,
                    wrap=True,
                    controls=[
                        ft.OutlinedButton(
                            "About",
                            icon=ft.Icons.INFO_OUTLINED,
                            style=secondary_button_style(),
                            on_click=lambda e: _open_help(create_about_dialog),
                        ),
                        ft.OutlinedButton(
                            "Terms",
                            icon=ft.Icons.DESCRIPTION_OUTLINED,
                            style=secondary_button_style(),
                            on_click=lambda e: _open_help(create_terms_dialog),
                        ),
                        ft.OutlinedButton(
                            "Privacy",
                            icon=ft.Icons.PRIVACY_TIP_OUTLINED,
                            style=secondary_button_style(),
                            on_click=lambda e: _open_help(create_privacy_dialog),
                        ),
                        ft.OutlinedButton(
                            "Report a bug",
                            icon=ft.Icons.BUG_REPORT_OUTLINED,
                            style=secondary_button_style(),
                            on_click=lambda e: _open_help(create_bug_report_dialog),
                        ),
                    ],
                ),
            ],
        ),
    )

    def on_close(e):
        page.pop_dialog()

    def commit_save(final_api_key: str, final_base_url: str):
        config["session_account"] = session_field.value.strip()
        config["api_key"] = final_api_key
        config["base_url"] = final_base_url
        config["model_name"] = model_field.value.strip()
        config["default_output_mode"] = default_mode_dropdown.value or "document"
        config["auto_extract"] = auto_extract_switch.value
        config["reduced_motion"] = reduced_motion_switch.value
        config["releases_repo"] = releases_repo_field.value.strip() or DEFAULT_RELEASE_REPO
        config["check_updates_on_startup"] = check_updates_switch.value
        save_config(config)
        theme.set_reduced_motion(reduced_motion_switch.value)
        if on_saved:
            on_saved()
        page.pop_dialog()
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text("Settings saved", size=13, color=theme.text_primary),
                bgcolor=theme.glass_bg,
                duration=1800,
            )
        )

    def reset_url_to_default(e):
        base_url_field.value = "https://api.openai.com/v1"
        base_url_field.label = "API base URL / Endpoint"
        base_url_field.password = False
        base_url_field.update()

    def clear_api_key(e):
        api_key_field.value = ""
        api_key_field.label = "API key"
        api_key_field.update()

    credential_actions_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.TextButton(
                "Clear API key",
                style=ft.ButtonStyle(
                    color=theme.text_secondary,
                    padding=ft.Padding.symmetric(horizontal=4, vertical=2),
                ),
                on_click=clear_api_key,
                tooltip="Erase stored API key",
            ),
            ft.TextButton(
                "Reset endpoint to OpenAI default",
                style=ft.ButtonStyle(
                    color=theme.accent,
                    padding=ft.Padding.symmetric(horizontal=4, vertical=2),
                ),
                on_click=reset_url_to_default,
                tooltip="Set URL back to https://api.openai.com/v1",
            ),
        ],
    )

    def on_save_click(e):
        entered_api_key = api_key_field.value.strip()
        entered_base_url = base_url_field.value.strip()

        # If user left the masked placeholder, preserve the previously configured secret
        if entered_api_key == MASKED_PLACEHOLDER:
            final_api_key = saved_api_key
            has_api_changed = False
        else:
            final_api_key = entered_api_key
            has_api_changed = (final_api_key != saved_api_key)

        if entered_base_url == MASKED_PLACEHOLDER:
            final_base_url = saved_base_url
            has_url_changed = False
        else:
            final_base_url = entered_base_url or "https://api.openai.com/v1"
            has_url_changed = (final_base_url != saved_base_url)

        # Take explicit confirmation for API Key and Endpoint URL modifications
        if has_api_changed or has_url_changed:
            change_notes = []
            if has_api_changed:
                if final_api_key:
                    change_notes.append("• API Key credential will be replaced with new value")
                else:
                    change_notes.append("• API Key credential will be cleared")
            if has_url_changed:
                change_notes.append("• Endpoint URL will be updated with new destination")

            confirm_box = ft.Container(
                width=520,
                bgcolor=theme.glass_bg,
                blur=theme.glass_blur,
                border=theme.glass_border,
                border_radius=RADIUS_GLASS,
                shadow=theme.glass_shadow,
                padding=20,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "Confirm credential changes",
                                    size=15,
                                    weight=ft.FontWeight.W_600,
                                    color=theme.text_primary,
                                    font_family=FONT_FAMILY_UI,
                                ),
                                ft.Icon(ft.Icons.SECURITY_ROUNDED, size=18, color=theme.accent),
                            ],
                        ),
                        ft.Text(
                            "You are modifying the API Key or Endpoint URL. Confirm that you want to overwrite your connection settings.",
                            size=12,
                            color=theme.text_secondary,
                            font_family=FONT_FAMILY_UI,
                        ),
                        ft.Container(
                            bgcolor=theme.surface,
                            border=ft.Border.all(1, theme.border),
                            border_radius=RADIUS_PANEL,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(note, size=12, color=theme.text_primary, font_family=FONT_FAMILY_UI)
                                    for note in change_notes
                                ],
                            ),
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            spacing=8,
                            controls=[
                                ft.TextButton(
                                    "Cancel",
                                    style=ft.ButtonStyle(
                                        color=theme.text_secondary,
                                        shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                                    ),
                                    on_click=lambda ev: page.pop_dialog(),
                                ),
                                ft.ElevatedButton(
                                    "Confirm & Save",
                                    style=primary_button_style(),
                                    on_click=lambda ev: (page.pop_dialog(), commit_save(final_api_key, final_base_url)),
                                ),
                            ],
                        ),
                    ],
                ),
            )

            confirm_dialog = ft.AlertDialog(
                modal=True,
                bgcolor="transparent",
                shape=ft.RoundedRectangleBorder(radius=RADIUS_GLASS),
                content_padding=0,
                content=confirm_box,
            )
            page.show_dialog(confirm_dialog)
        else:
            commit_save(final_api_key, final_base_url)

    _is_configured = bool(saved_api_key)
    _status_color = theme.success if _is_configured else theme.text_secondary
    title_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text("SETTINGS", size=10, weight=ft.FontWeight.W_600, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "Settings",
                                size=16,
                                weight=ft.FontWeight.W_700,
                                color=theme.text_primary,
                                font_family=FONT_FAMILY_UI,
                            ),
                            ft.Container(
                                content=ft.Row(
                                    spacing=6,
                                    tight=True,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(width=8, height=8, border_radius=4, bgcolor=_status_color),
                                        ft.Text(
                                            "Connected" if _is_configured else "Not configured",
                                            size=11,
                                            weight=ft.FontWeight.W_600,
                                            color=_status_color,
                                            font_family=FONT_FAMILY_UI,
                                        ),
                                    ],
                                ),
                                bgcolor=theme.inset,
                                border=ft.Border.all(1, _status_color if _is_configured else theme.border),
                                border_radius=20,
                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                            ),
                        ],
                    ),
                ],
            ),
            ft.IconButton(
                icon=ft.Icons.CLOSE_ROUNDED,
                icon_size=16,
                icon_color=theme.text_secondary,
                tooltip="Close",
                on_click=on_close,
            ),
        ],
    )

    def _section_label(text: str):
        return ft.Text(text, size=10, weight=ft.FontWeight.W_600, color=theme.text_secondary, font_family=FONT_FAMILY_UI)

    credentials_card = ft.Container(
        expand=True,
        bgcolor=theme.surface,
        border=ft.Border.all(1, theme.border),
        border_radius=RADIUS_PANEL,
        padding=16,
        content=ft.Column(
            spacing=12,
            controls=[
                _section_label("CONNECTION"),
                session_field,
                api_key_field,
                base_url_field,
                credential_actions_row,
            ],
        ),
    )

    behavior_card = ft.Container(
        expand=True,
        bgcolor=theme.surface,
        border=ft.Border.all(1, theme.border),
        border_radius=RADIUS_PANEL,
        padding=16,
        content=ft.Column(
            spacing=12,
            controls=[
                _section_label("BEHAVIOR"),
                model_field,
                default_mode_dropdown,
                auto_extract_switch,
                reduced_motion_switch,
                theme_switch,
            ],
        ),
    )

    # Two-column top row: connection left, behavior right. Cards top-align
    # (they differ in height) and split the width via expand=True.
    cards_row = ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            credentials_card,
            behavior_card,
        ],
    )

    footer_row = ft.Row(
        alignment=ft.MainAxisAlignment.END,
        spacing=8,
        controls=[
            ft.TextButton(
                "Cancel",
                style=ft.ButtonStyle(
                    color=theme.text_secondary,
                    shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                ),
                on_click=on_close,
            ),
            ft.ElevatedButton(
                "Save",
                style=primary_button_style(),
                on_click=on_save_click,
            ),
        ],
    )

    # Scrollable body with a pinned footer: the dialog never overflows short
    # windows, and Cancel/Save stay visible without scrolling.
    body_scroll = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=16,
        controls=[
            title_row,
            ft.Text(
                "Configure vision model API credentials. Stored secrets are masked and uncopyable.",
                size=12,
                color=theme.text_secondary,
                font_family=FONT_FAMILY_UI,
            ),
            cards_row,
            update_section,
            help_section,
        ],
    )

    content_box = ft.Container(
        width=720,
        height=600,
        bgcolor=theme.glass_bg,
        blur=theme.glass_blur,
        border=theme.glass_border,
        border_radius=RADIUS_GLASS,
        shadow=theme.glass_shadow,
        padding=24,
        content=ft.Column(
            spacing=16,
            controls=[
                body_scroll,
                footer_row,
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
