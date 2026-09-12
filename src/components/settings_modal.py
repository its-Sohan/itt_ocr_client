import flet as ft
from src import styles
from src.config_store import load_config, save_config

def create_settings_modal(page: ft.Page, on_saved=None) -> ft.AlertDialog:
    config = load_config()

    session_field = ft.TextField(
        label="Session / Account Name",
        value=config.get("session_account", "default_user"),
        hint_text="e.g. user_session_1",
        border_color=styles.BORDER_COLOR,
        focused_border_color=styles.TEXT_PRIMARY,
        text_size=14,
        dense=True,
    )

    api_key_field = ft.TextField(
        label="API Key",
        value=config.get("api_key", ""),
        hint_text="sk-...",
        password=True,
        can_reveal_password=True,
        border_color=styles.BORDER_COLOR,
        focused_border_color=styles.TEXT_PRIMARY,
        text_size=14,
        dense=True,
    )

    base_url_field = ft.TextField(
        label="API Base URL",
        value=config.get("base_url", "https://api.openai.com/v1"),
        hint_text="https://api.openai.com/v1 or https://openrouter.ai/api/v1",
        border_color=styles.BORDER_COLOR,
        focused_border_color=styles.TEXT_PRIMARY,
        text_size=14,
        dense=True,
    )

    model_field = ft.TextField(
        label="Vision Model",
        value=config.get("model_name", "gpt-4o-mini"),
        hint_text="gpt-4o, gpt-4o-mini, or openrouter/google/gemini-flash",
        border_color=styles.BORDER_COLOR,
        focused_border_color=styles.TEXT_PRIMARY,
        text_size=14,
        dense=True,
    )

    system_prompt_field = ft.TextField(
        label="OCR System Prompt",
        value=config.get("system_prompt", ""),
        multiline=True,
        min_lines=3,
        max_lines=4,
        border_color=styles.BORDER_COLOR,
        focused_border_color=styles.TEXT_PRIMARY,
        text_size=13,
    )

    status_text = ft.Text("", size=12, color=styles.STATUS_SUCCESS_TEXT)

    def on_close(e):
        page.pop_dialog()

    def on_save_click(e):
        config["session_account"] = session_field.value.strip()
        config["api_key"] = api_key_field.value.strip()
        config["base_url"] = base_url_field.value.strip()
        config["model_name"] = model_field.value.strip()
        config["system_prompt"] = system_prompt_field.value.strip()
        save_config(config)
        if on_saved:
            on_saved()
        page.pop_dialog()
        page.show_dialog(ft.SnackBar(ft.Text("Settings saved successfully!")))

    modal = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, color=styles.TEXT_PRIMARY, size=24),
                        ft.Text("Configuration & API Credentials", size=18, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                    ],
                ),
                ft.IconButton(ft.Icons.CLOSE, on_click=on_close),
            ],
        ),
        content=ft.Container(
            width=500,
            padding=ft.Padding.only(top=10),
            content=ft.Column(
                tight=True,
                spacing=14,
                controls=[
                    ft.Text("Configure your LLM model credentials and active session.", size=13, color=styles.TEXT_SECONDARY),
                    session_field,
                    api_key_field,
                    base_url_field,
                    model_field,
                    system_prompt_field,
                    status_text,
                ],
            ),
        ),
        actions=[
            ft.TextButton("Cancel", on_click=on_close),
            ft.ElevatedButton(
                "Save Configuration",
                style=ft.ButtonStyle(
                    bgcolor=styles.BTN_PRIMARY_BG,
                    color=styles.BTN_PRIMARY_TEXT,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.Padding.symmetric(horizontal=18, vertical=12),
                ),
                on_click=on_save_click,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return modal
