import flet as ft
from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI
from src.config_store import load_config, save_config

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

    def commit_save(final_api_key: str, final_base_url: str):
        config["session_account"] = session_field.value.strip()
        config["api_key"] = final_api_key
        config["base_url"] = final_base_url
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
                                    style=ft.ButtonStyle(
                                        bgcolor=theme.accent,
                                        color="#FFFFFF",
                                        shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                                        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                                        side=ft.BorderSide(2, theme.accent),
                                    ),
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
                    "Configure vision model API credentials. Stored secrets are masked and uncopyable.",
                    size=12,
                    color=theme.text_secondary,
                    font_family=FONT_FAMILY_UI,
                ),
                session_field,
                api_key_field,
                base_url_field,
                credential_actions_row,
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
