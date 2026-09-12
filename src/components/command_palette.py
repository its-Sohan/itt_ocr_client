import flet as ft
from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI
from src.app_state import state

def create_command_palette(
    page: ft.Page,
    on_browse_files=None,
    on_scan_device=None,
    on_extract_text=None,
    on_open_settings=None,
    on_open_dashboard=None,
) -> ft.AlertDialog:
    search_field = ft.TextField(
        hint_text="Type a command or search action...",
        hint_style=ft.TextStyle(size=14, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
        border=ft.InputBorder.NONE,
        autofocus=True,
        text_size=14,
        cursor_color=theme.accent,
        text_style=ft.TextStyle(size=14, color=theme.text_primary, font_family=FONT_FAMILY_UI),
        expand=True,
    )

    commands = [
        {
            "icon": ft.Icons.PLAY_ARROW_ROUNDED,
            "title": "Extract text",
            "desc": "Run vision model OCR extraction on current document",
            "action": lambda: (page.pop_dialog(), on_extract_text(None) if on_extract_text else None),
        },
        {
            "icon": ft.Icons.FOLDER_OPEN_OUTLINED,
            "title": "Browse files",
            "desc": "Open file picker to select image or document",
            "action": lambda: (page.pop_dialog(), on_browse_files(None) if on_browse_files else None),
        },
        {
            "icon": ft.Icons.DOCUMENT_SCANNER_OUTLINED,
            "title": "Scan document",
            "desc": "Acquire image from hardware scanner",
            "action": lambda: (page.pop_dialog(), on_scan_device(None) if on_scan_device else None),
        },
        {
            "icon": ft.Icons.CONTENT_COPY_ROUNDED,
            "title": "Copy extracted text",
            "desc": "Copy active transcription to system clipboard",
            "action": lambda: (page.pop_dialog(), _copy_active_text(page)),
        },
        {
            "icon": ft.Icons.DARK_MODE_OUTLINED,
            "title": "Toggle theme",
            "desc": "Switch between light and dark mode",
            "action": lambda: (page.pop_dialog(), theme.toggle_theme()),
        },
        {
            "icon": ft.Icons.SETTINGS_OUTLINED,
            "title": "Open settings",
            "desc": "Configure API credentials, model name, and preferences",
            "action": lambda: (page.pop_dialog(), on_open_settings(None) if on_open_settings else None),
        },
        {
            "icon": ft.Icons.BAR_CHART_ROUNDED,
            "title": "Open usage dashboard",
            "desc": "View processed document count, character statistics",
            "action": lambda: (page.pop_dialog(), on_open_dashboard(None) if on_open_dashboard else None),
        },
        {
            "icon": ft.Icons.DELETE_SWEEP_OUTLINED,
            "title": "Clear completed",
            "desc": "Remove completed items from history list",
            "action": lambda: (page.pop_dialog(), state.clear_completed()),
        },
    ]

    results_column = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, expand=True)

    def _copy_active_text(p: ft.Page):
        item = state.selected_item
        if item and item.extracted_text:
            p.set_clipboard(item.extracted_text)
            p.show_dialog(
                ft.SnackBar(
                    content=ft.Text("Copied", size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                    bgcolor=theme.glass_bg,
                )
            )

    def render_command_item(cmd):
        return ft.Container(
            border_radius=RADIUS_PANEL,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            ink=True,
            on_click=lambda e: cmd["action"](),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(cmd["icon"], size=18, color=theme.text_secondary),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(cmd["title"], size=13, weight=ft.FontWeight.W_500, color=theme.text_primary, font_family=FONT_FAMILY_UI),
                            ft.Text(cmd["desc"], size=11, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
                        ],
                    ),
                ],
            ),
        )

    def populate(filter_str=""):
        results_column.controls.clear()
        q = filter_str.lower().strip()
        filtered = [c for c in commands if q in c["title"].lower() or q in c["desc"].lower()]
        for cmd in filtered:
            results_column.controls.append(render_command_item(cmd))
        if page:
            page.update()

    def on_search_change(e):
        populate(search_field.value)

    search_field.on_change = on_search_change
    populate("")

    header_bar = ft.Container(
        border=ft.Border(bottom=ft.BorderSide(1, theme.border)),
        padding=ft.Padding.only(bottom=8),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.SEARCH_ROUNDED, size=18, color=theme.text_secondary),
                search_field,
                ft.IconButton(
                    icon=ft.Icons.CLOSE_ROUNDED,
                    icon_size=16,
                    icon_color=theme.text_secondary,
                    tooltip="Close",
                    on_click=lambda e: page.pop_dialog(),
                ),
            ],
        ),
    )

    modal_content = ft.Container(
        width=540,
        height=380,
        padding=16,
        bgcolor=theme.glass_bg,
        blur=theme.glass_blur,
        border=theme.glass_border,
        border_radius=RADIUS_GLASS,
        shadow=theme.glass_shadow,
        content=ft.Column(
            expand=True,
            spacing=10,
            controls=[
                header_bar,
                results_column,
            ],
        ),
    )

    dialog = ft.AlertDialog(
        modal=False,
        bgcolor="transparent",
        shape=ft.RoundedRectangleBorder(radius=RADIUS_GLASS),
        content_padding=0,
        content=modal_content,
    )
    return dialog
