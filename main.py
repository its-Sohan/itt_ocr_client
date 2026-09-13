import asyncio
import os
import flet as ft
from src.styles import theme, FONT_FAMILY_UI, RADIUS_GLASS, RADIUS_PANEL, unfreeze, primary_button_style
from src.app_state import state
from src.config_store import load_config
from src.components.top_bar import create_top_bar
from src.components.sidebar import create_sidebar
from src.components.main_panel import create_main_panel
from src.components.settings_modal import create_settings_modal
from src.components.dashboard_modal import create_dashboard_modal
from src.components.command_palette import create_command_palette
from src.services.scanner import scan_document
from src.services.ocr_llm import extract_text_with_llm
from src.services.clipboard import get_clipboard_image
from src.services.updater import check_for_updates, check_pending_update_result, APP_VERSION, DEFAULT_RELEASE_REPO
from src.components.update_dialog import create_update_dialog

def main(page: ft.Page):
    page.title = "ITT OCR"
    page.bgcolor = theme.bg
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK if theme.is_dark else ft.ThemeMode.LIGHT

    # Set up Typography (paths are relative to assets_dir="src/assets")
    page.fonts = {
        "Inter": "fonts/Inter-Regular.ttf",
        "JetBrains Mono": "fonts/JetBrainsMono-Regular.ttf",
        "Noto Sans Bengali": "fonts/NotoSansBengali-Regular.ttf",
        "Kalpurush": "fonts/kalpurush.ttf",
    }
    page.theme = ft.Theme(font_family=FONT_FAMILY_UI)

    # Window constraints
    page.window.min_width = 800
    page.window.min_height = 600
    page.window.width = 1380
    page.window.height = 860
    page.window.icon = "app_icon.png"

    # Initialize default output mode + quality from saved user settings
    initial_config = load_config()
    state.active_output_mode = initial_config.get("default_output_mode", "document")
    _saved_quality = initial_config.get("quality", "standard")
    if _saved_quality in ("standard", "high"):
        state.active_quality = _saved_quality

    # NOTE: do NOT add this to page.overlay. FilePicker is a Service, not a
    # visual control: constructing it auto-registers it with the page's
    # service registry, and putting it in the visual tree makes the client
    # render a red "Unknown control: FilePicker" error instead.
    # Keep this strong reference alive (closures below capture file_picker);
    # unreferenced services are automatically unregistered.
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
            on_paste_image=lambda ev: on_paste_action(ev, show_feedback_on_empty=True),
            on_run_all_pending=on_run_all_pending,
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
                added_items = []
                for f in files:
                    if f.path:
                        it = state.add_item(f.path, source="upload")
                        if it:
                            added_items.append(it)
                page.update()

                cfg = load_config()
                if cfg.get("auto_extract", True) and added_items:
                    for it in added_items:
                        state.select_item(it.id)
                        await extract_item_async(it)
        except Exception as ex:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("Couldn't open the file picker. Please try again."),
                    bgcolor=theme.error,
                )
            )

    def on_browse_files(e):
        page.run_task(on_browse_files_async, e)

    def show_no_scanner_modal(detail: str = ""):
        def on_browse_from_modal(ev):
            page.pop_dialog()
            on_browse_files(None)

        def on_retry_scan(ev):
            page.pop_dialog()
            on_scan_device(None)

        def on_open_wfs(ev):
            try:
                import subprocess
                import sys as _sys

                _popen_kwargs: dict = {}
                if _sys.platform.startswith("win"):
                    _popen_kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
                    try:
                        _si_cls = getattr(subprocess, "STARTUPINFO", None)
                        _use_show = getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
                        if _si_cls is not None:
                            _si = _si_cls()
                            _si.dwFlags |= _use_show
                            _si.wShowWindow = 0  # SW_HIDE
                            _popen_kwargs["startupinfo"] = _si
                    except Exception:
                        pass
                    _popen_kwargs["close_fds"] = True
                subprocess.Popen(["wfs.exe"], shell=False, **_popen_kwargs)
            except Exception:
                pass

        dialog_content = ft.Container(
            width=480,
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
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.DOCUMENT_SCANNER_ROUNDED, size=20, color=theme.accent),
                                    ft.Text(
                                        "Scanner device not detected",
                                        size=15,
                                        weight=ft.FontWeight.W_600,
                                        color=theme.text_primary,
                                        font_family=FONT_FAMILY_UI,
                                    ),
                                ],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_size=16,
                                icon_color=theme.text_secondary,
                                on_click=lambda ev: page.pop_dialog(),
                            ),
                        ],
                    ),
                    ft.Text(
                        "Windows could not detect an active physical scanner or WIA imaging device.",
                        size=13,
                        color=theme.text_primary,
                        font_family=FONT_FAMILY_UI,
                    ),
                    ft.Container(
                        bgcolor=theme.surface,
                        border=ft.Border.all(1, theme.border),
                        border_radius=RADIUS_PANEL,
                        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                        content=ft.Column(
                            spacing=6,
                            controls=[
                                ft.Text("• Connect and turn on your scanner via USB or Wi-Fi.", size=12, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
                                ft.Text("• Ensure official Windows WIA / scanner drivers are installed.", size=12, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
                                ft.Text("• Or select any scanned document (PNG, JPG, WebP, PDF) from your files.", size=12, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
                            ],
                        ),
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.TextButton(
                                "Open Windows Fax & Scan",
                                style=ft.ButtonStyle(color=theme.text_secondary, padding=ft.Padding.all(0)),
                                on_click=on_open_wfs,
                                tooltip="Launch native Windows Fax and Scan app (wfs.exe)",
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.TextButton(
                                        "Retry scan",
                                        style=ft.ButtonStyle(
                                            color=theme.text_secondary,
                                            shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                                        ),
                                        on_click=on_retry_scan,
                                    ),
                                    ft.ElevatedButton(
                                        "Browse scanned file",
                                        style=primary_button_style(),
                                        on_click=on_browse_from_modal,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        )

        modal = ft.AlertDialog(
            modal=True,
            bgcolor="transparent",
            shape=ft.RoundedRectangleBorder(radius=RADIUS_GLASS),
            content_padding=0,
            content=dialog_content,
        )
        page.show_dialog(modal)

    def on_scan_device(e):
        try:
            status, result = scan_document()
            if status == "SUCCESS" and result and os.path.exists(result):
                new_item = state.add_item(result, source="scanner")
                page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"Added scanned document: {os.path.basename(result)}", color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=2500,
                    )
                )
                cfg = load_config()
                if cfg.get("auto_extract", True) and new_item:
                    page.run_task(extract_item_async, new_item)
                else:
                    page.update()
            elif status == "CANCELLED":
                page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Scan cancelled", color=theme.text_secondary),
                        bgcolor=theme.glass_bg,
                        duration=1500,
                    )
                )
            elif status == "NO_DEVICE":
                show_no_scanner_modal(result or "")
            else:
                show_no_scanner_modal(result or "Scanner error")
        except Exception as ex:
            show_no_scanner_modal(str(ex))

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
            mode = state.active_output_mode
            item.output_mode = mode
            extracted = await extract_text_with_llm(item.file_path, mode=mode, model=state.active_model())
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
                    bgcolor=theme.error,
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

    # Batch extraction for all pending items
    async def run_all_pending_async():
        if state.is_processing_all:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("A batch extraction is already running.", color=theme.text_secondary),
                    bgcolor=theme.glass_bg,
                    duration=2000,
                )
            )
            return
        pending_items = [
            item for item in state.queue
            if item.status in ("Ready", "Failed")
        ]
        if not pending_items:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("No pending documents to extract.", color=theme.text_secondary),
                    bgcolor=theme.glass_bg,
                    duration=2000,
                )
            )
            return

        total = len(pending_items)
        state.is_processing_all = True
        state.notify()
        progress_snack = ft.SnackBar(
            content=ft.Text(
                f"Starting batch extraction for {total} document{'s' if total != 1 else ''}...",
                color=theme.text_primary,
            ),
            bgcolor=theme.glass_bg,
            duration=120000,
        )
        page.show_dialog(progress_snack)

        def _set_progress(message: str):
            try:
                progress_snack.content.value = message
                progress_snack.update()
            except Exception:
                pass

        def _dismiss_progress():
            # Only pop if ours is still on top (never steal another dialog).
            try:
                dialogs = getattr(getattr(page, "_dialogs", None), "controls", [])
                if dialogs and dialogs[-1] is progress_snack:
                    page.pop_dialog()
            except Exception:
                pass

        processed = 0
        try:
            for idx, item in enumerate(pending_items, 1):
                if not state.is_processing_all:
                    break
                state.select_item(item.id)
                _set_progress(f"Extracting {idx} of {total}… (Stop in History to cancel)")
                await extract_item_async(item)
                processed += 1
        finally:
            cancelled = not state.is_processing_all
            state.is_processing_all = False
            state.notify()

        _dismiss_progress()
        if cancelled:
            summary = f"Batch stopped ({processed} of {total} done)"
        else:
            summary = f"Batch extraction complete ({total} processed)"
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(summary, color=theme.text_primary),
                bgcolor=theme.glass_bg,
                duration=3000,
            )
        )

    def on_run_all_pending(e=None):
        page.run_task(run_all_pending_async)

    # Clipboard paste action
    def on_paste_action(e=None, show_feedback_on_empty=True):
        img_path = get_clipboard_image()
        if img_path and os.path.exists(img_path):
            new_item = state.add_item(img_path, source="clipboard")
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Pasted image: {os.path.basename(img_path)}", color=theme.text_primary),
                    bgcolor=theme.glass_bg,
                    duration=2000,
                )
            )
            cfg = load_config()
            if cfg.get("auto_extract", True) and new_item:
                page.run_task(extract_item_async, new_item)
            else:
                page.update()
        elif show_feedback_on_empty:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("Clipboard does not contain an image.", color=theme.text_secondary),
                    bgcolor=theme.glass_bg,
                    duration=2500,
                )
            )

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
        on_paste_click=lambda e: on_paste_action(e, show_feedback_on_empty=True),
        on_run_all_click=on_run_all_pending,
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
        try:
            unfreeze(app_container)
            page.update()
        except Exception as ex:
            print(f"Error updating page on theme change: {ex}")

    theme.add_listener(on_theme_change)

    # Responsive breakpoint handling
    def on_page_resize(e):
        width = page.width or 1200
        if width < 768:
            # Very narrow screen: collapse history and stack canvas + text panel
            if sidebar_comp.visible:
                sidebar_comp.visible = False
                sidebar_comp._auto_hidden = True
            main_panel_comp.set_stacked(True)
        elif width < 980:
            # Medium-narrow: collapse history rail to give side-by-side workspace ample room
            if sidebar_comp.visible:
                sidebar_comp.visible = False
                sidebar_comp._auto_hidden = True
            main_panel_comp.set_stacked(False)
        else:
            # Restore the rail only if WE auto-hid it (never fight a manual toggle).
            if getattr(sidebar_comp, "_auto_hidden", False):
                sidebar_comp.visible = True
                sidebar_comp._auto_hidden = False
            main_panel_comp.set_stacked(False)
        page.update()

    page.on_resized = on_page_resize

    # Global keyboard shortcuts: Ctrl+K / Cmd+K, Ctrl+Enter, Ctrl+O, Ctrl+V, Alt+A, Audit navigation (j/k, Up/Down, Esc)
    def on_keyboard(e: ft.KeyboardEvent):
        key_low = (e.key or "").lower()
        if key_low == "k" and (e.ctrl or e.meta):
            open_command_palette()
        elif key_low == "enter" and (e.ctrl or e.meta):
            on_extract_click(None)
        elif key_low == "o" and (e.ctrl or e.meta):
            on_browse_files(None)
        elif key_low == "v" and (e.ctrl or e.meta):
            on_paste_action(None, show_feedback_on_empty=False)
        elif (key_low == "a" and e.alt) or (key_low == "a" and (e.ctrl or e.meta) and e.shift):
            main_panel_comp.text_panel.toggle_audit_mode()
        elif state.audit_mode:
            dialogs_ctrls = getattr(getattr(page, "_dialogs", None), "controls", [])
            is_dialog_open = any(getattr(dlg, "open", False) for dlg in dialogs_ctrls)
            is_blocks_view = getattr(main_panel_comp.text_panel, "view_mode", "") == "blocks"

            if not is_dialog_open:
                if e.key in ("Escape", "Esc"):
                    state.set_audit_mode(False)
                elif is_blocks_view and not (e.ctrl or e.meta or e.alt):
                    if e.key in ("Arrow Down", "ArrowDown", "Down") or key_low == "j":
                        state.next_audit_block()
                    elif e.key in ("Arrow Up", "ArrowUp", "Up") or key_low == "k":
                        state.prev_audit_block()

    page.on_keyboard_event = on_keyboard

    page.add(app_container)

    # Silent background update check on app launch
    async def check_startup_updates():
        try:
            # Let initial frame render smoothly before checking
            await asyncio.sleep(1.5)
            # Surface a failed replace from the previous run (helper .bat log).
            try:
                last_error = check_pending_update_result()
            except Exception:
                last_error = None
            if last_error:
                try:
                    page.show_dialog(
                        ft.SnackBar(
                            content=ft.Text(
                                "The last update couldn't finish — you're still on your previous version. Try updating again from Settings.",
                                color=theme.text_primary,
                            ),
                            bgcolor=theme.glass_bg,
                            duration=6000,
                        )
                    )
                except Exception:
                    pass
            cfg = load_config()
            if not cfg.get("check_updates_on_startup", True):
                return
            repo = cfg.get("releases_repo", DEFAULT_RELEASE_REPO)
            info = await check_for_updates(repo=repo, current_version=APP_VERSION)
            if info.get("has_update"):
                update_dialog = create_update_dialog(page, info)
                page.show_dialog(update_dialog)
        except Exception:
            pass

    page.run_task(check_startup_updates)

if __name__ == "__main__":
    ft.run(main, assets_dir="src/assets")
