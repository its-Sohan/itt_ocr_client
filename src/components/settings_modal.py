import flet as ft
from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI
from src.config_store import load_config, save_config

def create_settings_modal(page: ft.Page, on_saved=None) -> ft.AlertDialog:
    config = load_config()

    initial_api_key = config.get("api_key", "").strip()
    initial_base_url = config.get("base_url", "https://api.openai.com/v1").strip()

    session_field = ft.TextField(
        label="Session account",
        value=config.get("session_account", "default_user"),
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=13,
        dense=True,
    )

    api_key_field = ft.TextField(
        label="API key",
        value=initial_api_key,
        hint_text="sk-...",
        password=True,
        can_reveal_password=True,
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=13,
        dense=True,
    )

    base_url_field = ft.TextField(
        label="API base URL",
        value=initial_base_url,
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=13,
        dense=True,
    )

    model_field = ft.TextField(
        label="Vision model",
        value=config.get("model_name", "gpt-4o-mini"),
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=13,
        dense=True,
    )

    system_prompt_field = ft.TextField(
        label="OCR system prompt",
        value=config.get("system_prompt", ""),
        multiline=True,
        min_lines=2,
        max_lines=3,
        border_color=theme.border,
        focused_border_color=theme.accent,
        text_size=12,
    )

    reduced_motion_switch = ft.Switch(
        label="Reduce motion",
        value=theme.reduced_motion,
        active_color=theme.accent,
        on_change=lambda e: theme.set_reduced_motion(e.control.value),
    )

    def on_close(e):
        page.pop_dialog()

    def commit_save():
        config["session_account"] = session_field.value.strip()
        config["api_key"] = api_key_field.value.strip()
        config["base_url"] = base_url_field.value.strip()
        config["model_name"] = model_field.value.strip()
        config["system_prompt"] = system_prompt_field.value.strip()
        config["reduced_motion"] = reduced_motion_switch.value
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

    def on_save_click(e):
        new_api_key = api_key_field.value.strip()
        new_base_url = base_url_field.value.strip()

        has_api_changed = (new_api_key != initial_api_key)
        has_url_changed = (new_base_url != initial_base_url)

        # Take explicit confirmation for API Key and Endpoint URL changes
        if has_api_changed or has_url_changed:
            change_notes = []
            if has_api_changed:
                change_notes.append("• API Key credential updated")
            if has_url_changed:
                change_notes.append(f"• API Base URL changed to: {new_base_url}")

            confirm_box = ft.Container(
                width=460,
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
                            "You are updating API connection settings. Future text extraction calls will use these new credentials.",
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
                                    style=ft.ButtonStyle(
                                        bgcolor=theme.accent,
                                        color="#FFFFFF",
                                        shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                                        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                                        side=ft.BorderSide(2, theme.accent),
                                    ),
                                    on_click=lambda ev: (page.pop_dialog(), commit_save()),
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
            commit_save()

    title_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(
                "Settings",
                size=16,
                weight=ft.FontWeight.W_600,
                color=theme.text_primary,
                font_family=FONT_FAMILY_UI,
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

    content_box = ft.Container(
        width=520,
        bgcolor=theme.glass_bg,
        blur=theme.glass_blur,
        border=theme.glass_border,
        border_radius=RADIUS_GLASS,
        shadow=theme.glass_shadow,
        padding=20,
        content=ft.Column(
            tight=True,
            spacing=14,
            controls=[
                title_row,
                ft.Text(
                    "Configure vision model API credentials and accessibility preferences.",
                    size=12,
                    color=theme.text_secondary,
                    font_family=FONT_FAMILY_UI,
                ),
                session_field,
                api_key_field,
                base_url_field,
                model_field,
                system_prompt_field,
                reduced_motion_switch,
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
                            on_click=on_close,
                        ),
                        ft.ElevatedButton(
                            "Save",
                            style=ft.ButtonStyle(
                                bgcolor=theme.accent,
                                color="#FFFFFF",
                                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                                padding=ft.Padding.symmetric(horizontal=18, vertical=10),
                                side=ft.BorderSide(2, theme.accent),
                            ),
                            on_click=on_save_click,
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
