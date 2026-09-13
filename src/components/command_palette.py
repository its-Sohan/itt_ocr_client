import os

import flet as ft
from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI
from src.app_state import state
from src.services.clipboard import copy_text_to_clipboard
from src.components.help_center import (
    create_about_dialog,
    create_terms_dialog,
    create_privacy_dialog,
    create_bug_report_dialog,
)
from src.services.text_transforms import (
    convert_digits_to_english,
    convert_digits_to_bengali,
    unwrap_broken_lines,
    clean_whitespace_and_margins,
    clean_table_formatting,
    check_invoice_math,
)

def create_command_palette(
    page: ft.Page,
    on_browse_files=None,
    on_scan_device=None,
    on_paste_image=None,
    on_run_all_pending=None,
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
            "desc": "Run vision model OCR extraction on current document (Ctrl+Enter)",
            "action": lambda: (page.pop_dialog(), on_extract_text(None) if on_extract_text else None),
        },
        {
            "icon": ft.Icons.CONTENT_PASTE_ROUNDED,
            "title": "Paste image from clipboard",
            "desc": "Ingest screenshot or image from clipboard (Ctrl+V)",
            "action": lambda: (page.pop_dialog(), on_paste_image(None) if on_paste_image else None),
        },
        {
            "icon": ft.Icons.PLAY_CIRCLE_OUTLINE_ROUNDED,
            "title": "Run all pending",
            "desc": "Batch extract OCR text for all pending queue items",
            "action": lambda: (page.pop_dialog(), on_run_all_pending(None) if on_run_all_pending else None),
        },
        {
            "icon": ft.Icons.FOLDER_OPEN_OUTLINED,
            "title": "Browse files",
            "desc": "Open file picker to select image or document (Ctrl+O)",
            "action": lambda: (page.pop_dialog(), on_browse_files(None) if on_browse_files else None),
        },
        {
            "icon": ft.Icons.DOCUMENT_SCANNER_OUTLINED,
            "title": "Scan document",
            "desc": "Acquire image from hardware scanner",
            "action": lambda: (page.pop_dialog(), on_scan_device(None) if on_scan_device else None),
        },
        {
            "icon": ft.Icons.TABLE_CHART_OUTLINED,
            "title": "Set mode: Spreadsheet",
            "desc": "Switch OCR output format to tabular line items & Excel-ready tables",
            "action": lambda: (page.pop_dialog(), state.set_active_output_mode("spreadsheet")),
        },
        {
            "icon": ft.Icons.DESCRIPTION_OUTLINED,
            "title": "Set mode: Document",
            "desc": "Switch OCR output format to standard prose & paragraphs",
            "action": lambda: (page.pop_dialog(), state.set_active_output_mode("document")),
        },
        {
            "icon": ft.Icons.LABEL_OUTLINED,
            "title": "Set mode: Key-Value",
            "desc": "Switch OCR output format to structured field-value pairs",
            "action": lambda: (page.pop_dialog(), state.set_active_output_mode("key_value")),
        },
        {
            "icon": ft.Icons.NOTES_ROUNDED,
            "title": "Set mode: Raw Text",
            "desc": "Switch OCR output format to clean unformatted plain text",
            "action": lambda: (page.pop_dialog(), state.set_active_output_mode("raw_text")),
        },
        {
            "icon": ft.Icons.CONTENT_COPY_ROUNDED,
            "title": "Copy extracted text",
            "desc": "Copy active transcription to system clipboard",
            "action": lambda: (page.pop_dialog(), _copy_active_text(page)),
        },
        {
            "icon": ft.Icons.FIND_IN_PAGE_OUTLINED,
            "title": "Toggle Side-by-Side Audit Mode",
            "desc": "Cross-check scan against text blocks with synchronized focus guide (Alt+A)",
            "action": lambda: (page.pop_dialog(), state.set_audit_mode(not state.audit_mode)),
        },
        {
            "icon": ft.Icons.AUTO_FIX_HIGH_ROUNDED,
            "title": "Audit: Align lines with AI (Bounding boxes)",
            "desc": "Detect exact 2D paragraph bounding boxes via vision AI model",
            "action": lambda: (page.pop_dialog(), _trigger_ai_alignment(page)),
        },
        {
            "icon": ft.Icons.NUMBERS_ROUNDED,
            "title": "Format: Convert digits to English (১ ➔ 1)",
            "desc": "Converts all Bengali numeral digits in active document to 0-9",
            "action": lambda: (page.pop_dialog(), _apply_palette_transform(convert_digits_to_english, "Converted digits to English (123)")),
        },
        {
            "icon": ft.Icons.FORMAT_LIST_NUMBERED_ROUNDED,
            "title": "Format: Convert digits to Bengali (1 ➔ ১)",
            "desc": "Converts all English numeral digits in active document to ০-৯",
            "action": lambda: (page.pop_dialog(), _apply_palette_transform(convert_digits_to_bengali, "Converted digits to Bengali (১২৩)")),
        },
        {
            "icon": ft.Icons.WRAP_TEXT_ROUNDED,
            "title": "Format: Unwrap broken lines",
            "desc": "Joins lines wrapped mid-sentence while preserving headings and lists",
            "action": lambda: (page.pop_dialog(), _apply_palette_transform(unwrap_broken_lines, "Unwrapped broken lines")),
        },
        {
            "icon": ft.Icons.TABLE_ROWS_ROUNDED,
            "title": "Format: Align table columns",
            "desc": "Cleans and aligns markdown table columns and pipes",
            "action": lambda: (page.pop_dialog(), _apply_palette_transform(clean_table_formatting, "Aligned table grid")),
        },
        {
            "icon": ft.Icons.SPACE_BAR_ROUNDED,
            "title": "Format: Trim spaces & margins",
            "desc": "Trims trailing spaces and collapses redundant blank lines",
            "action": lambda: (page.pop_dialog(), _apply_palette_transform(clean_whitespace_and_margins, "Cleaned spacing & blank lines")),
        },
        {
            "icon": ft.Icons.CALCULATE_OUTLINED,
            "title": "Tools: Verify invoice math",
            "desc": "Validates invoice line items against stated total locally",
            "action": lambda: (page.pop_dialog(), _verify_palette_math(page)),
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
        {
            "icon": ft.Icons.BUG_REPORT_OUTLINED,
            "title": "Report a bug",
            "desc": "Save a diagnostic file on your computer to send to support",
            "action": lambda: (page.pop_dialog(), page.show_dialog(create_bug_report_dialog(page))),
        },
        {
            "icon": ft.Icons.INFO_OUTLINED,
            "title": "About this app",
            "desc": "Version, policies, and support",
            "action": lambda: (page.pop_dialog(), page.show_dialog(create_about_dialog(page))),
        },
        {
            "icon": ft.Icons.DESCRIPTION_OUTLINED,
            "title": "Terms of Service",
            "desc": "Read the app's terms of use",
            "action": lambda: (page.pop_dialog(), page.show_dialog(create_terms_dialog(page))),
        },
        {
            "icon": ft.Icons.PRIVACY_TIP_OUTLINED,
            "title": "Privacy Policy",
            "desc": "What the app stores and sends",
            "action": lambda: (page.pop_dialog(), page.show_dialog(create_privacy_dialog(page))),
        },
    ]

    results_column = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, expand=True)

    def _apply_palette_transform(func, action_name: str):
        item = state.selected_item
        if item and item.extracted_text:
            new_text = func(item.extracted_text)
            if new_text == item.extracted_text:
                page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("No changes needed: text is already in target format.", size=13, color=theme.text_secondary),
                        bgcolor=theme.glass_bg,
                        duration=2000,
                    )
                )
                return
            item.extracted_text = new_text
            state.notify()
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(action_name, size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                    bgcolor=theme.glass_bg,
                    duration=1800,
                )
            )
        else:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("Nothing to format yet — extract text first.", size=13, color=theme.text_secondary),
                    bgcolor=theme.glass_bg,
                    duration=1500,
                )
            )

    def _verify_palette_math(p: ft.Page):
        item = state.selected_item
        if item and item.extracted_text:
            res = check_invoice_math(item.extracted_text)
            if not res:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("No table with a total found in this document.", size=13, color=theme.text_secondary),
                        bgcolor=theme.glass_bg,
                        duration=2000,
                    )
                )
            elif res["matched"]:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"✓ Verified! All items sum up to total: {res['total']:,.2f}", size=13, weight=ft.FontWeight.W_500, color=theme.success),
                        bgcolor=theme.glass_bg,
                        duration=3000,
                    )
                )
            else:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"⚠ Mismatch: Items sum ({res['calculated']:,.2f}) vs Stated total ({res['total']:,.2f})", size=13, weight=ft.FontWeight.W_500, color=theme.warning),
                        bgcolor=theme.glass_bg,
                        duration=3000,
                    )
                )
        else:
            p.show_dialog(
                ft.SnackBar(content=ft.Text("Nothing to check yet — extract text first.", size=13, color=theme.text_secondary), bgcolor=theme.glass_bg)
            )

    def _copy_active_text(p: ft.Page):
        item = state.selected_item
        if item and item.extracted_text:
            copy_text_to_clipboard(item.extracted_text, page=p)
            try:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Copied to clipboard", size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=1500,
                    )
                )
            except Exception:
                pass
        elif p:
            try:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Nothing to copy yet — extract text first.", size=13, color=theme.text_secondary),
                        bgcolor=theme.glass_bg,
                        duration=1500,
                    )
                )
            except Exception:
                pass

    def _trigger_ai_alignment(p: ft.Page):
        item = state.selected_item
        if not item or not item.file_path or not os.path.exists(item.file_path):
            p.show_dialog(ft.SnackBar(content=ft.Text("No image document loaded to align.", color=theme.text_secondary), bgcolor=theme.glass_bg))
            return

        text = item.extracted_text
        if not text:
            p.show_dialog(ft.SnackBar(content=ft.Text("Extract text first before aligning with AI.", color=theme.text_secondary), bgcolor=theme.glass_bg))
            return

        if "\n\n" in text:
            raw_blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        elif "\n" in text:
            raw_blocks = [b.strip() for b in text.split("\n") if b.strip()]
        else:
            raw_blocks = [text.strip()]

        p.show_dialog(
            ft.SnackBar(
                content=ft.Text("Analyzing image & aligning paragraph bounding boxes with AI...", size=13, color=theme.text_primary),
                bgcolor=theme.glass_bg,
                duration=3000,
            )
        )

        async def _align_task():
            from src.services.ocr_llm import align_blocks_with_ai
            try:
                boxes = await align_blocks_with_ai(item.file_path, raw_blocks)
                if boxes:
                    item.block_boxes = boxes
                    state.set_audit_mode(True)
                    state.notify()
                    p.show_dialog(
                        ft.SnackBar(
                            content=ft.Text(f"Aligned {len(boxes)} paragraphs with the scanned image.", size=13, color=theme.success),
                            bgcolor=theme.glass_bg,
                            duration=2500,
                        )
                    )
                else:
                    p.show_dialog(
                        ft.SnackBar(
                            content=ft.Text("Couldn't pinpoint paragraphs — showing the full page instead.", size=13, color=theme.text_secondary),
                            bgcolor=theme.glass_bg,
                        )
                    )
            except Exception as ex:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Couldn't align paragraphs — showing the full page instead.", size=13, color=theme.error),
                        bgcolor=theme.glass_bg,
                    )
                )

        p.run_task(_align_task)

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
            try:
                page.update()
            except Exception:
                pass

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
