import asyncio
import os
import flet as ft
from src import styles
from src.app_state import state
from src.components.nav_rail import create_nav_rail
from src.components.sidebar import create_sidebar
from src.components.main_panel import create_main_panel
from src.components.settings_modal import create_settings_modal
from src.components.dashboard_modal import create_dashboard_modal
from src.services.scanner import scan_document
from src.services.ocr_llm import extract_text_with_llm

def main(page: ft.Page):
    page.title = "ITT OCR Client - Image to Text"
    page.bgcolor = styles.BG_APP
    page.padding = 0
    page.window.min_width = 1100
    page.window.min_height = 700
    page.window.width = 1380
    page.window.height = 860

    # In Flet 0.86+, FilePicker is an auto-registered Service, not a UI Control.
    file_picker = ft.FilePicker()

    # Open Settings Modal
    def open_settings(e=None):
        settings_modal = create_settings_modal(page)
        page.show_dialog(settings_modal)

    # Open Dashboard Modal
    def open_dashboard(e=None):
        dashboard_modal = create_dashboard_modal(page)
        page.show_dialog(dashboard_modal)

    # File Browse Handler (pick_files is an async Service method)
    async def on_browse_files_async(e):
        try:
            files = await file_picker.pick_files(
                dialog_title="Select images for OCR extraction",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=True,
            )
            if files:
                for f in files:
                    if f.path:
                        state.add_item(f.path, source="upload")
                page.update()
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"File picker error: {str(ex)}"), bgcolor="#DC2626"))

    def on_browse_files(e):
        page.run_task(on_browse_files_async, e)

    # Scanner Trigger Handler
    def on_scan_device(e):
        try:
            page.show_dialog(ft.SnackBar(ft.Text("Acquiring document from scanner..."), duration=2500))
            scanned_path = scan_document()
            if scanned_path and os.path.exists(scanned_path):
                state.add_item(scanned_path, source="scanner")
                page.show_dialog(ft.SnackBar(ft.Text(f"Scan complete! Added {os.path.basename(scanned_path)} to queue.")))
            else:
                page.show_dialog(ft.SnackBar(ft.Text("Scanner operation cancelled or returned no image.")))
        except Exception as ex:
            page.show_dialog(ft.SnackBar(ft.Text(f"Scan error: {str(ex)}"), bgcolor="#DC2626"))

    # Process Queue with LLM
    async def process_queue_async(e):
        ready_items = state.get_ready_items()
        if not ready_items:
            page.show_dialog(ft.SnackBar(ft.Text("No files in queue ready for processing! Add images first.")))
            return

        sidebar_comp.set_processing(True, f"Processing 1/{len(ready_items)}...")

        for idx, item in enumerate(ready_items, 1):
            state.select_item(item.id)
            item.status = "Processing"
            state.notify()
            page.update()
            sidebar_comp.set_processing(True, f"Processing {idx}/{len(ready_items)}...")

            try:
                extracted = await extract_text_with_llm(item.file_path)
                item.extracted_text = extracted
                item.status = "Done"
                item.error_message = ""
            except Exception as ex:
                item.status = "Failed"
                item.error_message = str(ex)
                page.show_dialog(ft.SnackBar(ft.Text(f"Failed {item.file_name}: {str(ex)}"), bgcolor="#DC2626"))

            state.notify()
            page.update()

        sidebar_comp.set_processing(False)
        page.show_dialog(ft.SnackBar(ft.Text("OCR queue processing finished!")))

    def on_process_click(e):
        page.run_task(process_queue_async, e)

    # Instantiate UI
    nav_rail_comp = create_nav_rail(
        on_settings_click=open_settings,
        on_dashboard_click=open_dashboard,
    )
    sidebar_comp = create_sidebar(
        on_browse_click=on_browse_files,
        on_scan_click=on_scan_device,
        on_process_click=on_process_click,
    )
    main_panel_comp = create_main_panel()

    # Root Landscape View
    root_layout = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            nav_rail_comp,
            ft.Container(
                expand=True,
                padding=ft.Padding.all(20),
                content=ft.Row(
                    expand=True,
                    spacing=20,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        sidebar_comp,
                        main_panel_comp,
                    ],
                ),
            ),
        ],
    )

    page.add(root_layout)

if __name__ == "__main__":
    ft.run(main)
