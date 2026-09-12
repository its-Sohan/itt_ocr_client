import asyncio
import os
import flet as ft
from src.styles import theme, FONT_FAMILY_UI
from src.app_state import state
from src.components.top_bar import create_top_bar
from src.components.sidebar import create_sidebar
from src.components.main_panel import create_main_panel
from src.components.settings_modal import create_settings_modal
from src.components.dashboard_modal import create_dashboard_modal
from src.components.command_palette import create_command_palette
from src.services.scanner import scan_document
from src.services.ocr_llm import extract_text_with_llm

def main(page: ft.Page):
    page.title = "ITT OCR"
    page.bgcolor = theme.bg
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK if theme.is_dark else ft.ThemeMode.LIGHT

    # Set up Typography
    page.fonts = {
        "Inter": "assets/fonts/Inter-Regular.ttf",
        "JetBrains Mono": "assets/fonts/JetBrainsMono-Regular.ttf",
        "Noto Sans Bengali": "assets/fonts/NotoSansBengali-Regular.ttf",
        "Kalpurush": "assets/fonts/kalpurush.ttf",
    }
    page.theme = ft.Theme(font_family=FONT_FAMILY_UI)

    # Window constraints
    page.window.min_width = 800
    page.window.min_height = 600
    page.window.width = 1380
    page.window.height = 860
    page.window.icon = "assets/app_icon.png"

    file_picker = ft.FilePicker()

    # Modals
    def open_settings(e=None):
        settings_modal = create_settings_modal(page)
        page.show_dialog(settings_modal)

    def open_dashboard(e=None):
        dashboard_modal = create_dashboard_modal(page)
        page.show_dialog(dashboard_modal)

    def open_command_palette(e=None):
        palette = create_command_palette(
            page,
            on_browse_files=on_browse_files,
            on_scan_device=on_scan_device,
            on_extract_text=on_extract_click,
            on_open_settings=open_settings,
            on_open_dashboard=open_dashboard,
        )
        page.show_dialog(palette)

    # Ingestion Actions
    async def on_browse_files_async(e):
        try:
            files = await file_picker.pick_files(
                dialog_title="Select document or image",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=True,
            )
            if files:
                for f in files:
                    if f.path:
                        state.add_item(f.path, source="upload")
                page.update()
        except Exception as ex:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"File picker error: {str(ex)}"),
                    bgcolor="#EF4444",
                )
            )

    def on_browse_files(e):
        page.run_task(on_browse_files_async, e)

    def on_scan_device(e):
        try:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("Scanning document from hardware device...", color=theme.text_primary),
                    bgcolor=theme.glass_bg,
                    duration=2000,
                )
            )
            scanned_path = scan_document()
            if scanned_path and os.path.exists(scanned_path):
                state.add_item(scanned_path, source="scanner")
                page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"Added {os.path.basename(scanned_path)} to queue", color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=2000,
                    )
                )
            else:
                page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Scan produced no image.", color=theme.text_secondary),
                        bgcolor=theme.glass_bg,
                    )
                )
        except Exception as ex:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Scan error: {str(ex)}"),
                    bgcolor="#EF4444",
                )
            )

    # OCR Extraction Handler
    async def extract_item_async(item):
        if not item or not item.file_path:
            return

        item.status = "Processing"
        state.notify()
        main_panel_comp.text_panel.set_processing(True)
        main_panel_comp.preview_panel.start_scan_animation()
        page.update()

        try:
            extracted = await extract_text_with_llm(item.file_path)
            item.extracted_text = extracted
            item.status = "Done"
            item.error_message = ""
        except Exception as ex:
            item.status = "Failed"
            item.error_message = str(ex)
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(
                        f"Extraction failed: {str(ex)[:120]}",
                        size=13,
                        color="#FFFFFF",
                    ),
                    bgcolor="#EF4444",
                    duration=5000,
                )
            )
        finally:
            main_panel_comp.text_panel.set_processing(False)
            main_panel_comp.preview_panel.stop_scan_animation()
            state.notify()
            page.update()

    def on_extract_click(e):
        item = state.selected_item
        if not item:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("Drop an image or PDF here to extract its text.", color=theme.text_primary),
                    bgcolor=theme.glass_bg,
                )
            )
            return
        page.run_task(extract_item_async, item)

    # Toggle history rail
    def toggle_history(e=None):
        sidebar_comp.toggle_collapse()

    # Instantiate UI components
    top_bar_comp = create_top_bar(
        on_toggle_history=toggle_history,
        on_command_palette=open_command_palette,
        on_settings=open_settings,
        on_dashboard=open_dashboard,
    )

    sidebar_comp = create_sidebar(
        on_browse_click=on_browse_files,
        on_scan_click=on_scan_device,
    )

    main_panel_comp = create_main_panel(
        on_scan_click=on_scan_device,
        on_extract_click=on_extract_click,
    )

    # Workspace row: History rail (left) + Main Panel (right)
    workspace_row = ft.Row(
        expand=True,
        spacing=16,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            sidebar_comp,
            main_panel_comp,
        ],
    )

    # Main container
    app_container = ft.Container(
        expand=True,
        bgcolor=theme.bg,
        padding=ft.Padding.only(left=16, top=14, right=16, bottom=16),
        content=ft.Column(
            expand=True,
            spacing=12,
            controls=[
                top_bar_comp,
                workspace_row,
            ],
        ),
    )

    # Reactive theme synchronization
    def on_theme_change():
        page.bgcolor = theme.bg
        page.theme_mode = ft.ThemeMode.DARK if theme.is_dark else ft.ThemeMode.LIGHT
        app_container.bgcolor = theme.bg
        page.update()

    theme.add_listener(on_theme_change)

    # Responsive breakpoint handling (< 768px)
    def on_page_resize(e):
        width = page.width or 1200
        if width < 768:
            # Narrow screen: collapse history by default, stack canvas and text panel
            if sidebar_comp.visible:
                sidebar_comp.visible = False
            main_panel_comp.set_stacked(True)
        else:
            main_panel_comp.set_stacked(False)
        page.update()

    page.on_resized = on_page_resize

    # Global keyboard shortcuts: Ctrl+K / Cmd+K, Ctrl+Enter, Ctrl+O
    def on_keyboard(e: ft.KeyboardEvent):
        if e.key.lower() == "k" and (e.ctrl or e.meta):
            open_command_palette()
        elif e.key.lower() == "enter" and (e.ctrl or e.meta):
            on_extract_click(None)
        elif e.key.lower() == "o" and (e.ctrl or e.meta):
            on_browse_files(None)

    page.on_keyboard_event = on_keyboard

    page.add(app_container)

if __name__ == "__main__":
    ft.run(main, assets_dir="src/assets")
