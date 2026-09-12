import flet as ft
from src.styles import (
    theme,
    RADIUS_PANEL,
    FONT_FAMILY_UI,
    FONT_FAMILY_MONO,
    FONT_FAMILY_BENGALI,
    contains_bengali,
)
from src.app_state import state
from src.services.clipboard import copy_text_to_clipboard
from src.services.text_transforms import (
    convert_digits_to_english,
    convert_digits_to_bengali,
    unwrap_broken_lines,
    clean_whitespace_and_margins,
    clean_table_formatting,
    check_invoice_math,
)

import os
import time

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

def get_page(control: ft.Control):
    try:
        return control.page
    except Exception:
        return None

def get_export_dir() -> str:
    desktop = os.path.expanduser("~/Desktop")
    if os.path.isdir(desktop):
        return desktop
    docs = os.path.expanduser("~/Documents")
    if os.path.isdir(docs):
        return docs
    return os.path.expanduser("~")

def text_to_csv_string(text: str) -> str:
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    lines = text.strip().splitlines()
    table_lines = [l.strip() for l in lines if l.strip().startswith("|") and l.strip().endswith("|")]
    if table_lines:
        for line in table_lines:
            inner = line.strip("|")
            cells = [c.strip() for c in inner.split("|")]
            if all(set(c).issubset({"-", ":", " "}) for c in cells if c):
                continue
            writer.writerow(cells)
    else:
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if "\t" in line_str:
                writer.writerow([c.strip() for c in line_str.split("\t")])
            elif "," in line_str:
                writer.writerow([c.strip() for c in line_str.split(",")])
            else:
                writer.writerow([line_str])
    return output.getvalue()

def text_to_tsv_string(text: str) -> str:
    lines = text.strip().splitlines()
    table_lines = [l.strip() for l in lines if l.strip().startswith("|") and l.strip().endswith("|")]
    if table_lines:
        tsv_rows = []
        for line in table_lines:
            inner = line.strip("|")
            cells = [c.strip() for c in inner.split("|")]
            # Skip divider rows like |---|---|
            if all(set(c).issubset({"-", ":", " "}) for c in cells if c):
                continue
            tsv_rows.append("\t".join(cells))
        return "\n".join(tsv_rows)
    else:
        tsv_rows = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if "\t" in line_str:
                tsv_rows.append(line_str)
            elif "," in line_str:
                cells = [c.strip() for c in line_str.split(",")]
                tsv_rows.append("\t".join(cells))
            else:
                tsv_rows.append(line_str)
        return "\n".join(tsv_rows)

class ParagraphBlock(ft.Container):
    def __init__(self, text: str, block_index: int = 0, is_active: bool = False, on_copy=None, on_select=None):
        self.block_text = text
        self.block_index = block_index
        self.is_active = is_active
        self.on_copy = on_copy
        self.on_select = on_select

        is_bengali = contains_bengali(self.block_text)

        self.index_badge = ft.Text(
            f"{self.block_index + 1:02d}",
            size=10,
            weight=ft.FontWeight.W_600,
            color=theme.accent if self.is_active else theme.text_secondary,
            font_family=FONT_FAMILY_MONO,
        )
        self.index_container = ft.Container(
            content=self.index_badge,
            padding=ft.Padding.only(top=3, right=4),
        )

        self.copy_icon = ft.Icon(
            ft.Icons.CONTENT_COPY_ROUNDED,
            size=12,
            color=theme.text_secondary,
        )
        self.copy_label = ft.Text(
            "Copy",
            size=11,
            weight=ft.FontWeight.W_500,
            color=theme.text_secondary,
            font_family=FONT_FAMILY_UI,
        )
        self.copy_badge = ft.Container(
            content=ft.Row(
                spacing=4,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.copy_icon,
                    self.copy_label,
                ],
            ),
            bgcolor=theme.button_bg,
            border=ft.Border.all(1, theme.border),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            opacity=0.0,
            animate_opacity=150,
            ink=True,
            on_click=self._handle_copy_click,
            tooltip="Copy block",
        )

        self.text_content = ft.Text(
            self.block_text,
            size=14 if is_bengali else 13,
            font_family=FONT_FAMILY_BENGALI if is_bengali else FONT_FAMILY_MONO,
            color=theme.text_primary,
            selectable=True,
            expand=True,
        )

        active_border = ft.Border.all(2, theme.accent)
        normal_border = ft.Border.all(1, theme.border)
        active_bg = "rgba(37, 99, 235, 0.05)" if not theme.is_dark else "rgba(75, 136, 240, 0.10)"

        super().__init__(
            key=f"block_{self.block_index}",
            bgcolor=active_bg if self.is_active else theme.surface,
            border=active_border if self.is_active else normal_border,
            border_radius=RADIUS_PANEL,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            on_hover=self._on_hover,
            on_click=self._handle_block_click,
            ink=True,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
                controls=[
                    ft.Row(
                        spacing=8,
                        expand=True,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            self.index_container,
                            self.text_content,
                        ],
                    ),
                    self.copy_badge,
                ],
            ),
        )

    def _handle_block_click(self, e):
        if self.on_select:
            self.on_select(self.block_index)

    def _handle_copy_click(self, e):
        self.copy_icon.icon = ft.Icons.CHECK_ROUNDED
        self.copy_icon.name = ft.Icons.CHECK_ROUNDED
        self.copy_icon.color = "#10B981" if not theme.is_dark else "#34D399"
        self.copy_label.value = "Copied"
        self.copy_label.color = "#10B981" if not theme.is_dark else "#34D399"
        safe_update(self)
        p = getattr(e, "page", None) or getattr(getattr(e, "control", None), "page", None) or get_page(self)
        if self.on_copy:
            self.on_copy(self.block_text, page=p)

    def _on_hover(self, e: ft.HoverEvent):
        is_hovered = (e.data == "true")
        self.copy_badge.opacity = 1.0 if is_hovered else 0.0
        if not is_hovered:
            self.copy_icon.icon = ft.Icons.CONTENT_COPY_ROUNDED
            self.copy_icon.name = ft.Icons.CONTENT_COPY_ROUNDED
            self.copy_label.value = "Copy"
            self.copy_label.color = theme.text_secondary
        if not self.is_active:
            self.border = ft.Border.all(1, theme.accent if is_hovered else theme.border)
        safe_update(self)

    def update_theme(self):
        active_border = ft.Border.all(2, theme.accent)
        normal_border = ft.Border.all(1, theme.border)
        active_bg = "rgba(37, 99, 235, 0.05)" if not theme.is_dark else "rgba(75, 136, 240, 0.10)"

        self.bgcolor = active_bg if self.is_active else theme.surface
        self.border = active_border if self.is_active else normal_border
        self.text_content.color = theme.text_primary
        self.copy_badge.bgcolor = theme.button_bg
        self.copy_badge.border = ft.Border.all(1, theme.border)
        self.copy_icon.color = theme.text_secondary
        self.copy_label.color = theme.text_secondary
        self.index_badge.color = theme.accent if self.is_active else theme.text_secondary
        safe_update(self)

class TextPanel(ft.Container):
    def __init__(self, on_extract_click=None):
        self.on_extract_click = on_extract_click
        # View modes: "blocks", "raw", "markdown"
        self.view_mode = "blocks"

        # Header labels
        self.header_title = ft.Text(
            "Extracted text",
            size=14,
            weight=ft.FontWeight.W_500,
            color=theme.text_primary,
            font_family=FONT_FAMILY_UI,
        )

        self.char_count_text = ft.Text(
            "0 chars",
            size=12,
            color=theme.text_secondary,
            font_family=FONT_FAMILY_UI,
        )

        self.status_label = ft.Text(
            "Ready",
            size=12,
            weight=ft.FontWeight.W_500,
            color=theme.text_secondary,
            font_family=FONT_FAMILY_UI,
        )

        # Local format transforms undo stack
        self._undo_stack = []

        # Local Invoice Math Validation Chip
        self.math_chip_icon = ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=12, color="#10B981")
        self.math_chip_text = ft.Text("", size=11, weight=ft.FontWeight.W_500, color="#10B981", font_family=FONT_FAMILY_UI)
        self.math_chip = ft.Container(
            visible=False,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            border_radius=RADIUS_PANEL,
            content=ft.Row(
                spacing=5,
                tight=True,
                controls=[
                    self.math_chip_icon,
                    self.math_chip_text,
                ],
            ),
        )

        # 1. Blocks View: paragraph-by-paragraph with hover-copy button
        self.blocks_column = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # 2. Raw Monospace Editor View
        self.raw_output_field = ft.TextField(
            value="",
            read_only=False,
            multiline=True,
            border=ft.InputBorder.NONE,
            text_size=13,
            text_style=ft.TextStyle(
                font_family=FONT_FAMILY_MONO,
                color=theme.text_primary,
                letter_spacing=0.2,
            ),
            cursor_color=theme.accent,
            expand=True,
            content_padding=ft.Padding.all(14),
            hint_text="Extracted text will appear here in monospace.",
            hint_style=ft.TextStyle(font_family=FONT_FAMILY_UI, color=theme.text_secondary, size=13),
            on_change=self._on_text_edited,
        )

        # 3. Formatted Markdown View
        self.markdown_output_view = ft.Markdown(
            value="*No text extracted yet.*",
            selectable=True,
            expand=True,
            soft_line_break=True,
        )

        # Central Text Canvas holding current view mode
        self.text_canvas = ft.Container(
            expand=True,
            bgcolor=theme.inset,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=8,
            content=self.blocks_column,
        )

        # 1. Copy All icon button
        self.copy_icon = ft.Icon(ft.Icons.CONTENT_COPY_ROUNDED, size=16, color=theme.text_primary)
        self.copy_text = ft.Text("Copy all", visible=False)
        self.copy_btn = ft.Container(
            content=self.copy_icon,
            width=36,
            height=34,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            bgcolor=theme.button_bg,
            ink=True,
            on_click=self.on_copy_all_click,
            tooltip="Copy all text (Ctrl+C)",
        )

        # 2. Export icon button
        self.export_icon = ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=16, color=theme.text_primary)
        self.export_text = ft.Text("Export", visible=False)
        self.export_btn = ft.Container(
            content=self.export_icon,
            width=36,
            height=34,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            bgcolor=theme.button_bg,
            ink=True,
            on_click=self.on_export_click,
            tooltip="Export extracted text to file",
        )

        # 3. Local Formatting & Tools Menu icon button
        self.tools_icon = ft.Icon(ft.Icons.TUNE_ROUNDED, size=16, color=theme.text_primary)
        self.tools_text = ft.Text("Tools", visible=False)
        self.tools_container = ft.Container(
            content=self.tools_icon,
            width=36,
            height=34,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            bgcolor=theme.button_bg,
        )
        self.tools_menu_btn = ft.PopupMenuButton(
            content=self.tools_container,
            bgcolor=theme.menu_bg,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
            tooltip="Tools (Audit, convert digits, unwrap, math, AI alignment)",
            items=self._build_tools_menu_items(),
        )

        # 4. Side-by-Side Audit Mode Toggle icon button
        self.audit_icon = ft.Icon(
            ft.Icons.SAVED_SEARCH_ROUNDED if state.audit_mode else ft.Icons.FIND_IN_PAGE_OUTLINED,
            size=16,
            color=theme.accent if state.audit_mode else theme.text_primary,
        )
        self.audit_text = ft.Text("Audit: ON" if state.audit_mode else "Audit: OFF", visible=False)
        audit_init_bg = (
            "rgba(37, 99, 235, 0.10)" if (state.audit_mode and not theme.is_dark)
            else ("rgba(75, 136, 240, 0.16)" if state.audit_mode else theme.button_bg)
        )
        self.audit_btn = ft.Container(
            content=self.audit_icon,
            width=36,
            height=34,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1.5 if state.audit_mode else 1, theme.accent if state.audit_mode else theme.border),
            border_radius=RADIUS_PANEL,
            bgcolor=audit_init_bg,
            ink=True,
            on_click=self.toggle_audit_mode,
            tooltip=f"Side-by-Side Audit Mode: {'ON' if state.audit_mode else 'OFF'} (Alt+A)",
        )

        # 5. View Mode Toggle icon button (Blocks / Raw / Markdown)
        self.view_mode_icon = ft.Icon(ft.Icons.VIEW_AGENDA_OUTLINED, size=16, color=theme.text_primary)
        self.mode_label = ft.Text("View: Blocks", visible=False)
        self.view_mode_btn = ft.Container(
            content=self.view_mode_icon,
            width=36,
            height=34,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            bgcolor=theme.button_bg,
            ink=True,
            on_click=self.cycle_view_mode,
            tooltip="View mode: Blocks (Click to cycle Raw/Markdown)",
        )

        # 6. Output Mode Toggle icon button
        self.MODE_KEYS = ["document", "spreadsheet", "key_value", "raw_text"]
        self.MODE_ICONS = {
            "document": ft.Icons.DESCRIPTION_OUTLINED,
            "spreadsheet": ft.Icons.TABLE_CHART_OUTLINED,
            "key_value": ft.Icons.LABEL_OUTLINED,
            "raw_text": ft.Icons.NOTES_ROUNDED,
        }
        self.MODE_LABELS = {
            "document": "Document",
            "spreadsheet": "Spreadsheet",
            "key_value": "Key-Value",
            "raw_text": "Raw Text",
        }
        self.MODE_DESCRIPTIONS = {
            "document": "Standard prose & headings",
            "spreadsheet": "Invoices, tables & Excel TSV",
            "key_value": "IDs, forms & key-value pairs",
            "raw_text": "Unformatted continuous plain text",
        }

        initial_mode = state.active_output_mode
        self.output_mode_icon = ft.Icon(
            self.MODE_ICONS.get(initial_mode, ft.Icons.DESCRIPTION_OUTLINED),
            size=16,
            color=theme.accent,
        )
        self.output_mode_text = ft.Text(
            f"Format: {self.MODE_LABELS.get(initial_mode, 'Document')}",
            visible=False,
        )
        self.output_mode_btn = ft.Container(
            content=self.output_mode_icon,
            width=36,
            height=34,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            bgcolor=theme.button_bg,
            ink=True,
            on_click=self.cycle_output_mode,
            tooltip=f"Format: {self.MODE_LABELS.get(initial_mode, 'Document')} (Click to cycle)",
        )

        # Primary Action Button: 'Extract text' (prominently in top header)
        self.extract_progress = ft.ProgressRing(width=13, height=13, stroke_width=2, color="#FFFFFF", visible=False)
        self.extract_icon = ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=15, color="#FFFFFF")
        self.extract_label = ft.Text("Extract text", size=12, weight=ft.FontWeight.W_600, color="#FFFFFF", font_family=FONT_FAMILY_UI)
        self.extract_btn = ft.ElevatedButton(
            content=ft.Row(
                spacing=5,
                tight=True,
                controls=[
                    self.extract_icon,
                    self.extract_progress,
                    self.extract_label,
                ],
            ),
            style=ft.ButtonStyle(
                bgcolor=theme.accent,
                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                side=ft.BorderSide(2, theme.accent),
            ),
            on_click=self.on_extract_click,
            tooltip="Extract text from document (Ctrl+Enter)",
        )

        header_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
            run_spacing=6,
            spacing=8,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                    controls=[self.header_title, self.char_count_text, self.math_chip],
                ),
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                    controls=[
                        self.status_label,
                        self.extract_btn,
                    ],
                ),
            ],
        )

        # Crisp hairline divider between document actions and view/format controls
        self.toolbar_divider = ft.Container(
            width=1,
            height=20,
            bgcolor=theme.border,
            margin=ft.Margin.symmetric(horizontal=3),
        )

        # Strictly horizontal icon-only toolbar: saves space, eliminates list-view wrapping, allows easy feature expansion
        bottom_bar = ft.Row(
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            wrap=False,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self.copy_btn,
                self.export_btn,
                self.tools_menu_btn,
                self.audit_btn,
                self.toolbar_divider,
                self.view_mode_btn,
                self.output_mode_btn,
            ],
        )

        main_column = ft.Column(
            expand=True,
            spacing=10,
            controls=[
                header_row,
                self.text_canvas,
                bottom_bar,
            ],
        )

        super().__init__(
            expand=True,
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=16,
            content=main_column,
        )

        state.add_listener(self.update_text_view)
        theme.add_listener(self.update_theme_ui)
        self.update_text_view()

    def _on_text_edited(self, e):
        item = state.selected_item
        if item:
            item.extracted_text = self.raw_output_field.value
            self.markdown_output_view.value = item.extracted_text
            self.char_count_text.value = f"{len(item.extracted_text):,} chars"
            is_bengali = contains_bengali(item.extracted_text)
            self.raw_output_field.text_style.font_family = FONT_FAMILY_BENGALI if is_bengali else FONT_FAMILY_MONO
            self.raw_output_field.text_size = 14 if is_bengali else 13
            self._rebuild_blocks(item.extracted_text)
            self._update_math_status(item.extracted_text)

    def _build_tools_menu_items(self):
        text_color = theme.text_primary
        icon_color = theme.accent
        divider_color = theme.border
        sec_text_color = theme.text_secondary
        green_color = "#34D399" if theme.is_dark else "#059669"
        undo_color = "#FBBF24" if theme.is_dark else "#D97706"
        is_audit = state.audit_mode
        audit_tag_bg = theme.accent if is_audit else "transparent"
        audit_tag_color = "#FFFFFF" if is_audit else sec_text_color
        audit_tag_border = theme.accent if is_audit else theme.border

        return [
            ft.PopupMenuItem(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=10,
                            tight=True,
                            controls=[
                                ft.Icon(ft.Icons.SAVED_SEARCH_ROUNDED if is_audit else ft.Icons.FIND_IN_PAGE_OUTLINED, size=16, color=theme.accent if is_audit else icon_color),
                                ft.Text("Side-by-Side Audit Mode", size=12, color=theme.accent if is_audit else text_color, font_family=FONT_FAMILY_UI, weight=ft.FontWeight.W_600 if is_audit else ft.FontWeight.W_500),
                            ],
                        ),
                        ft.Container(
                            bgcolor=audit_tag_bg,
                            border=ft.Border.all(1, audit_tag_border),
                            border_radius=3,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=1),
                            content=ft.Text("ON" if is_audit else "OFF", size=10, weight=ft.FontWeight.W_600, color=audit_tag_color, font_family=FONT_FAMILY_MONO),
                        ),
                    ],
                ),
                on_click=lambda e: self.toggle_audit_mode(e),
            ),
            ft.PopupMenuItem(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.AUTO_FIX_HIGH_ROUNDED, size=16, color=theme.accent),
                        ft.Text("Audit: Align lines with AI (Bounding boxes)", size=12, color=text_color, font_family=FONT_FAMILY_UI, weight=ft.FontWeight.W_500),
                    ],
                ),
                on_click=lambda e: self.run_ai_audit_alignment(e),
            ),
            ft.PopupMenuItem(ft.Divider(height=1, color=divider_color)),
            ft.PopupMenuItem(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.NUMBERS_ROUNDED, size=16, color=icon_color),
                        ft.Text("Convert digits to English (১ ➔ 1)", size=12, color=text_color, font_family=FONT_FAMILY_UI, weight=ft.FontWeight.W_500),
                    ],
                ),
                on_click=lambda e: self.apply_transform(convert_digits_to_english, "Converted digits to English (123)", e),
            ),
            ft.PopupMenuItem(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.FORMAT_LIST_NUMBERED_ROUNDED, size=16, color=icon_color),
                        ft.Text("Convert digits to Bengali (1 ➔ ১)", size=12, color=text_color, font_family=FONT_FAMILY_UI, weight=ft.FontWeight.W_500),
                    ],
                ),
                on_click=lambda e: self.apply_transform(convert_digits_to_bengali, "Converted digits to Bengali (১২৩)", e),
            ),
            ft.PopupMenuItem(ft.Divider(height=1, color=divider_color)),
            ft.PopupMenuItem(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.WRAP_TEXT_ROUNDED, size=16, color=text_color),
                        ft.Text("Unwrap broken lines (join paragraphs)", size=12, color=text_color, font_family=FONT_FAMILY_UI, weight=ft.FontWeight.W_500),
                    ],
                ),
                on_click=lambda e: self.apply_transform(unwrap_broken_lines, "Unwrapped broken column lines", e),
            ),
            ft.PopupMenuItem(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.SPACE_BAR_ROUNDED, size=16, color=text_color),
                        ft.Text("Trim excess spaces & blank lines", size=12, color=text_color, font_family=FONT_FAMILY_UI, weight=ft.FontWeight.W_500),
                    ],
                ),
                on_click=lambda e: self.apply_transform(clean_whitespace_and_margins, "Cleaned spacing & blank lines", e),
            ),
            ft.PopupMenuItem(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.TABLE_ROWS_ROUNDED, size=16, color=text_color),
                        ft.Text("Clean & align table columns", size=12, color=text_color, font_family=FONT_FAMILY_UI, weight=ft.FontWeight.W_500),
                    ],
                ),
                on_click=lambda e: self.apply_transform(clean_table_formatting, "Aligned table grid", e),
            ),
            ft.PopupMenuItem(ft.Divider(height=1, color=divider_color)),
            ft.PopupMenuItem(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.CALCULATE_OUTLINED, size=16, color=green_color),
                        ft.Text("Verify invoice table math", size=12, color=text_color, font_family=FONT_FAMILY_UI, weight=ft.FontWeight.W_500),
                    ],
                ),
                on_click=lambda e: self.run_math_verification(e),
            ),
            ft.PopupMenuItem(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.UNDO_ROUNDED, size=16, color=undo_color if self._undo_stack else sec_text_color),
                        ft.Text(
                            f"Undo last tool action ({len(self._undo_stack)})" if self._undo_stack else "Undo last tool action",
                            size=12,
                            color=text_color if self._undo_stack else sec_text_color,
                            font_family=FONT_FAMILY_UI,
                        ),
                    ],
                ),
                on_click=lambda e: self.undo_transform(e),
            ),
        ]

    def apply_transform(self, func, action_name: str, e=None):
        p = (e.page if e and hasattr(e, "page") and e.page else None) or get_page(self)
        item = state.selected_item
        curr_text = self.raw_output_field.value or (item.extracted_text if item else "")
        if not curr_text:
            if p:
                p.show_dialog(
                    ft.SnackBar(content=ft.Text("No text to format", size=13, color=theme.text_secondary), bgcolor=theme.glass_bg)
                )
            return

        new_text = func(curr_text)
        if new_text == curr_text:
            if p:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("No changes needed: text is already in target format.", size=13, color=theme.text_secondary),
                        bgcolor=theme.glass_bg,
                        duration=2000,
                    )
                )
            return

        # Save previous text for undo
        self._undo_stack.append(curr_text)

        self.raw_output_field.value = new_text
        self.markdown_output_view.value = new_text
        if item:
            item.extracted_text = new_text
            state.persist()
            state.notify()
        else:
            self.char_count_text.value = f"{len(new_text):,} chars"
            self._rebuild_blocks(new_text)
            self._update_math_status(new_text)
            safe_update(self)

        # Refresh undo status in menu items
        self.tools_menu_btn.items = self._build_tools_menu_items()
        safe_update(self.tools_menu_btn)

        if p:
            p.update()
            p.show_dialog(
                ft.SnackBar(
                    content=ft.Text(action_name, size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                    bgcolor=theme.glass_bg,
                    duration=2000,
                )
            )

    def undo_transform(self, e=None):
        p = (e.page if e and hasattr(e, "page") and e.page else None) or get_page(self)
        if not self._undo_stack:
            if p:
                p.show_dialog(
                    ft.SnackBar(content=ft.Text("Nothing to undo", size=13, color=theme.text_secondary), bgcolor=theme.glass_bg)
                )
            return

        prev_text = self._undo_stack.pop()
        item = state.selected_item
        self.raw_output_field.value = prev_text
        self.markdown_output_view.value = prev_text
        if item:
            item.extracted_text = prev_text
            state.persist()
            state.notify()
        else:
            self.char_count_text.value = f"{len(prev_text):,} characters"
            self._rebuild_blocks(prev_text)
            self._update_math_status(prev_text)
            safe_update(self)

        # Refresh undo status in menu items
        self.tools_menu_btn.items = self._build_tools_menu_items()
        safe_update(self.tools_menu_btn)

        if p:
            p.update()
            p.show_dialog(
                ft.SnackBar(content=ft.Text("Undid formatting change", size=13, color=theme.text_primary), bgcolor=theme.glass_bg)
            )

    def _update_math_status(self, text: str):
        if not text:
            self.math_chip.visible = False
            return

        res = check_invoice_math(text)
        if not res:
            self.math_chip.visible = False
            return

        if res["matched"]:
            self.math_chip.bgcolor = "rgba(16, 185, 129, 0.12)"
            self.math_chip.border = ft.Border.all(1, "#10B981")
            self.math_chip_icon.icon = ft.Icons.CHECK_CIRCLE_ROUNDED
            self.math_chip_icon.name = ft.Icons.CHECK_CIRCLE_ROUNDED
            self.math_chip_icon.color = "#10B981"
            self.math_chip_text.value = f"Math verified ({res['total']:,.0f})"
            self.math_chip_text.color = "#10B981"
            self.math_chip.tooltip = f"Invoice total {res['total']:,.2f} matches sum of items"
            self.math_chip.visible = True
        else:
            self.math_chip.bgcolor = "rgba(245, 158, 11, 0.12)"
            self.math_chip.border = ft.Border.all(1, "#F59E0B")
            self.math_chip_icon.icon = ft.Icons.WARNING_AMBER_ROUNDED
            self.math_chip_icon.name = ft.Icons.WARNING_AMBER_ROUNDED
            self.math_chip_icon.color = "#F59E0B"
            self.math_chip_text.value = f"Math diff: {res['difference']:,.0f}"
            self.math_chip_text.color = "#F59E0B"
            self.math_chip.tooltip = f"Calculated sum ({res['calculated']:,.2f}) does not match stated total ({res['total']:,.2f})"
            self.math_chip.visible = True

    def run_math_verification(self, e=None):
        p = (e.page if e and hasattr(e, "page") and e.page else None) or get_page(self)
        item = state.selected_item
        text = self.raw_output_field.value or (item.extracted_text if item else "")
        if not text:
            if p:
                p.show_dialog(
                    ft.SnackBar(content=ft.Text("No text to verify", size=13, color=theme.text_secondary), bgcolor=theme.glass_bg)
                )
            return

        res = check_invoice_math(text)
        if not res:
            if p:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("No invoice table or total rows found in document.", size=13, color=theme.text_secondary),
                        bgcolor=theme.glass_bg,
                        duration=2200,
                    )
                )
            return

        self._update_math_status(text)
        safe_update(self)

        if p:
            p.update()
            if res["matched"]:
                msg = f"✓ Verified! All items sum up to total: {res['total']:,.2f}"
                color = "#10B981" if not theme.is_dark else "#34D399"
            else:
                msg = f"⚠ Mismatch: Items sum ({res['calculated']:,.2f}) vs Stated total ({res['total']:,.2f})"
                color = "#F59E0B" if not theme.is_dark else "#FBBF24"
            p.show_dialog(
                ft.SnackBar(
                    content=ft.Text(msg, size=13, weight=ft.FontWeight.W_500, color=color),
                    bgcolor=theme.glass_bg,
                    duration=3000,
                )
            )

    def cycle_view_mode(self, e):
        p = getattr(e, "page", None) or get_page(self)
        if self.view_mode == "blocks":
            self.view_mode = "raw"
            self.mode_label.value = "View: Raw"
            self.view_mode_icon.icon = ft.Icons.CODE_ROUNDED
            self.view_mode_icon.name = ft.Icons.CODE_ROUNDED
            self.view_mode_btn.tooltip = "View mode: Raw Editor (Click to switch to Markdown)"
            self.text_canvas.content = self.raw_output_field
            toast_text = "Switched to Raw Text editor"
        elif self.view_mode == "raw":
            self.view_mode = "markdown"
            self.mode_label.value = "View: Markdown"
            self.view_mode_icon.icon = ft.Icons.PREVIEW_ROUNDED
            self.view_mode_icon.name = ft.Icons.PREVIEW_ROUNDED
            self.view_mode_btn.tooltip = "View mode: Markdown Preview (Click to switch to Blocks)"
            self.text_canvas.content = self.markdown_output_view
            toast_text = "Switched to Markdown preview"
        else:
            self.view_mode = "blocks"
            self.mode_label.value = "View: Blocks"
            self.view_mode_icon.icon = ft.Icons.VIEW_AGENDA_OUTLINED
            self.view_mode_icon.name = ft.Icons.VIEW_AGENDA_OUTLINED
            self.view_mode_btn.tooltip = "View mode: Interactive Blocks (Click to switch to Raw)"
            self.text_canvas.content = self.blocks_column
            toast_text = "Switched to Interactive Blocks"
        self.view_mode_btn.content = self.view_mode_icon
        safe_update(self.view_mode_icon)
        safe_update(self.view_mode_btn)
        safe_update(self.text_canvas)
        if p:
            try:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(toast_text, size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=1500,
                    )
                )
            except Exception:
                pass

    def toggle_audit_mode(self, e=None):
        new_state = not state.audit_mode
        state.set_audit_mode(new_state)
        self._update_audit_btn_ui(new_state)
        if new_state and self.view_mode != "blocks":
            self.view_mode = "blocks"
            self.mode_label.value = "View: Blocks"
            self.view_mode_icon.icon = ft.Icons.VIEW_AGENDA_OUTLINED
            self.view_mode_icon.name = ft.Icons.VIEW_AGENDA_OUTLINED
            self.view_mode_btn.content = self.view_mode_icon
            self.view_mode_btn.tooltip = "View mode: Interactive Blocks (Click to switch to Raw)"
            self.text_canvas.content = self.blocks_column
            safe_update(self.view_mode_icon)
            safe_update(self.view_mode_btn)
            safe_update(self.text_canvas)

        p = (e.page if e and hasattr(e, "page") and e.page else None) or get_page(self)
        if p:
            msg = "Audit Mode ON: Navigate with Up/Down or J/K to cross-check scan" if new_state else "Audit Mode OFF"
            p.show_dialog(
                ft.SnackBar(
                    content=ft.Text(msg, size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                    bgcolor=theme.glass_bg,
                    duration=2000,
                )
            )

    def _update_audit_btn_ui(self, is_on: bool):
        icon_name = ft.Icons.SAVED_SEARCH_ROUNDED if is_on else ft.Icons.FIND_IN_PAGE_OUTLINED
        self.audit_icon.icon = icon_name
        self.audit_icon.name = icon_name
        self.audit_icon.color = theme.accent if is_on else theme.text_primary
        self.audit_text.value = f"Audit: {'ON' if is_on else 'OFF'}"
        self.audit_text.color = theme.accent if is_on else theme.text_primary
        self.audit_btn.bgcolor = (
            "rgba(37, 99, 235, 0.10)" if (is_on and not theme.is_dark)
            else ("rgba(75, 136, 240, 0.16)" if is_on else theme.button_bg)
        )
        self.audit_btn.border = ft.Border.all(1.5 if is_on else 1, theme.accent if is_on else theme.border)
        self.audit_btn.tooltip = f"Side-by-Side Audit Mode: {'ON' if is_on else 'OFF'} (Alt+A)"
        self.audit_btn.content = self.audit_icon
        safe_update(self.audit_icon)
        safe_update(self.audit_btn)
        self.tools_menu_btn.items = self._build_tools_menu_items()
        safe_update(self.tools_menu_btn)

    def run_ai_audit_alignment(self, e=None):
        p = (e.page if e and hasattr(e, "page") and e.page else None) or get_page(self)
        item = state.selected_item
        if not item or not item.file_path or not os.path.exists(item.file_path):
            if p:
                p.show_dialog(
                    ft.SnackBar(content=ft.Text("No image document loaded to align.", color=theme.text_secondary), bgcolor=theme.glass_bg)
                )
            return

        text = item.extracted_text or self.raw_output_field.value
        if not text:
            if p:
                p.show_dialog(
                    ft.SnackBar(content=ft.Text("Extract text first before aligning with AI.", color=theme.text_secondary), bgcolor=theme.glass_bg)
                )
            return

        if "\n\n" in text:
            raw_blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        elif "\n" in text:
            raw_blocks = [b.strip() for b in text.split("\n") if b.strip()]
        else:
            raw_blocks = [text.strip()]

        if p:
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
                    if p:
                        p.show_dialog(
                            ft.SnackBar(
                                content=ft.Text(f"AI aligned {len(boxes)} paragraph coordinates with pinpoint accuracy!", size=13, color="#10B981"),
                                bgcolor=theme.glass_bg,
                                duration=2500,
                            )
                        )
                else:
                    if p:
                        p.show_dialog(
                            ft.SnackBar(
                                content=ft.Text("AI returned no boxes, using paper bounds.", size=13, color=theme.text_secondary),
                                bgcolor=theme.glass_bg,
                            )
                        )
            except Exception as ex:
                if p:
                    p.show_dialog(
                        ft.SnackBar(
                            content=ft.Text(f"AI alignment failed: {str(ex)}", size=13, color="#EF4444"),
                            bgcolor=theme.glass_bg,
                        )
                    )

        if p:
            p.run_task(_align_task)

    def on_select_block(self, block_index: int):
        state.set_active_block_index(block_index)
        if not state.audit_mode:
            state.audit_mode = True
            self._update_audit_btn_ui(True)
        state.notify()

    def cycle_output_mode(self, e):
        curr = state.active_output_mode if state.active_output_mode in self.MODE_KEYS else "document"
        curr_idx = self.MODE_KEYS.index(curr)
        next_mode = self.MODE_KEYS[(curr_idx + 1) % len(self.MODE_KEYS)]
        self.set_output_mode(next_mode)

    def set_output_mode(self, mode: str):
        state.set_active_output_mode(mode)
        item = state.selected_item
        if item:
            item.output_mode = mode
        icon_name = self.MODE_ICONS.get(mode, ft.Icons.DESCRIPTION_OUTLINED)
        self.output_mode_icon.icon = icon_name
        self.output_mode_icon.name = icon_name
        self.output_mode_btn.content = self.output_mode_icon
        self.output_mode_text.value = f"Format: {self.MODE_LABELS.get(mode, 'Document')}"
        label = self.MODE_LABELS.get(mode, mode)
        desc = self.MODE_DESCRIPTIONS.get(mode, "")
        self.output_mode_btn.tooltip = f"Format: {label} ({desc}) - Click to cycle"
        safe_update(self.output_mode_icon)
        safe_update(self.output_mode_btn)
        p = get_page(self)
        if p:
            try:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"Format: {label} ({desc})", size=13, color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=1800,
                    )
                )
            except Exception:
                pass

    def on_copy_block(self, block_text: str, page=None):
        p = page or get_page(self)
        if not block_text:
            return

        is_table = state.active_output_mode == "spreadsheet" or ("|" in block_text and "\n|" in block_text)
        if is_table:
            tsv_data = text_to_tsv_string(block_text)
            text_to_send = tsv_data if tsv_data else block_text
            toast_msg = "Copied table (Excel-ready TSV)"
        else:
            text_to_send = block_text
            toast_msg = "Copied paragraph"

        copy_text_to_clipboard(text_to_send, page=p)

        if p:
            try:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(toast_msg, size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=1500,
                    )
                )
            except Exception:
                pass

    def on_copy_all_click(self, e):
        p = getattr(e, "page", None) or get_page(self) or getattr(getattr(e, "control", None), "page", None)
        item = state.selected_item
        text_to_copy = ""
        if self.raw_output_field and self.raw_output_field.value:
            text_to_copy = self.raw_output_field.value
        elif item and item.extracted_text:
            text_to_copy = item.extracted_text

        if not text_to_copy:
            if p:
                try:
                    p.show_dialog(
                        ft.SnackBar(
                            content=ft.Text("No extracted text to copy", size=13, color=theme.text_secondary),
                            bgcolor=theme.glass_bg,
                            duration=1800,
                        )
                    )
                except Exception:
                    pass
            return

        is_table = state.active_output_mode == "spreadsheet" or ("|" in text_to_copy and "\n|" in text_to_copy)
        if is_table:
            tsv_data = text_to_tsv_string(text_to_copy)
            final_text = tsv_data if tsv_data else text_to_copy
            toast_msg = "Copied (Spreadsheet TSV table ready for Excel/Sheets)"
        else:
            final_text = text_to_copy
            toast_msg = "Copied to clipboard"

        copy_text_to_clipboard(final_text, page=p)

        # Inline button visual feedback
        self.copy_icon.icon = ft.Icons.CHECK_ROUNDED
        self.copy_icon.name = ft.Icons.CHECK_ROUNDED
        self.copy_icon.color = "#10B981" if not theme.is_dark else "#34D399"
        self.copy_text.value = "Copied!"
        self.copy_text.color = "#10B981" if not theme.is_dark else "#34D399"
        self.copy_btn.content = self.copy_icon
        safe_update(self.copy_icon)
        safe_update(self.copy_btn)

        def _reset_btn():
            time.sleep(1.5)
            self.copy_icon.icon = ft.Icons.CONTENT_COPY_ROUNDED
            self.copy_icon.name = ft.Icons.CONTENT_COPY_ROUNDED
            self.copy_icon.color = theme.text_primary
            self.copy_text.value = "Copy all"
            self.copy_text.color = theme.text_primary
            self.copy_btn.content = self.copy_icon
            safe_update(self.copy_icon)
            safe_update(self.copy_btn)

        import threading
        threading.Thread(target=_reset_btn, daemon=True).start()

        if p:
            try:
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(toast_msg, size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=2000,
                    )
                )
            except Exception:
                pass

    def _rebuild_blocks(self, text: str):
        self.blocks_column.controls.clear()
        if not text:
            state.total_blocks_count = 0
            self.blocks_column.controls.append(
                ft.Container(
                    padding=40,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=28, color=theme.text_secondary),
                            ft.Text(
                                "No text extracted from this document yet.",
                                size=13,
                                color=theme.text_secondary,
                                font_family=FONT_FAMILY_UI,
                            ),
                            ft.ElevatedButton(
                                content=ft.Row(
                                    spacing=6,
                                    tight=True,
                                    controls=[
                                        ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=15, color="#FFFFFF"),
                                        ft.Text("Extract text from document", size=12, weight=ft.FontWeight.W_600, color="#FFFFFF", font_family=FONT_FAMILY_UI),
                                    ],
                                ),
                                style=ft.ButtonStyle(
                                    bgcolor=theme.accent,
                                    shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                                    side=ft.BorderSide(2, theme.accent),
                                ),
                                on_click=self.on_extract_click,
                                tooltip="Extract text with vision model (Ctrl+Enter)",
                            ),
                        ],
                    ),
                )
            )
            return

        # Split into paragraphs by double newlines or single newlines
        if "\n\n" in text:
            raw_blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        elif "\n" in text:
            raw_blocks = [b.strip() for b in text.split("\n") if b.strip()]
        else:
            raw_blocks = [text.strip()] if text.strip() else []

        state.total_blocks_count = len(raw_blocks)
        for idx, block in enumerate(raw_blocks):
            is_act = (idx == state.active_block_index and state.audit_mode)
            self.blocks_column.controls.append(
                ParagraphBlock(
                    block,
                    block_index=idx,
                    is_active=is_act,
                    on_copy=self.on_copy_block,
                    on_select=self.on_select_block,
                )
            )

    def on_export_click(self, e):
        p = get_page(self)
        if not p:
            return
        item = state.selected_item
        text_content = self.raw_output_field.value or (item.extracted_text if item else "")
        if not text_content and not any(it.extracted_text for it in state.queue):
            p.show_dialog(
                ft.SnackBar(content=ft.Text("No extracted text to export.", color=theme.text_primary), bgcolor=theme.glass_bg)
            )
            return

        def save_file(ext: str, content: str, filename_override: str = None):
            target_dir = get_export_dir()
            if filename_override:
                fname = filename_override
            else:
                base = os.path.splitext(item.file_name)[0] if item else "extracted_text"
                fname = f"{base}.{ext}"
            export_path = os.path.join(target_dir, fname)
            try:
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(content)
                p.pop_dialog()
                folder_name = os.path.basename(target_dir) or target_dir
                p.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"Saved {fname} to {folder_name}", size=13, color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=3000,
                    )
                )
            except Exception as ex:
                p.show_dialog(
                    ft.SnackBar(content=ft.Text(f"Export failed: {str(ex)}"), bgcolor="#EF4444")
                )

        def export_merged(ext: str):
            completed = [it for it in state.queue if it.extracted_text and it.extracted_text.strip()]
            if not completed:
                p.show_dialog(
                    ft.SnackBar(content=ft.Text("No completed documents with text in queue.", color=theme.text_primary), bgcolor=theme.glass_bg)
                )
                return
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            merged_lines = [
                f"# ITT OCR - Batch Export ({len(completed)} documents)",
                f"Exported on: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "=" * 40,
                "",
            ]
            for idx, it in enumerate(completed, 1):
                merged_lines.append(f"## Document {idx}: {it.file_name}")
                merged_lines.append("")
                merged_lines.append(it.extracted_text.strip())
                merged_lines.append("")
                merged_lines.append("-" * 30)
                merged_lines.append("")

            merged_text = "\n".join(merged_lines)
            save_file(ext, merged_text, filename_override=f"batch_export_{timestamp}.{ext}")

        export_dialog = ft.AlertDialog(
            bgcolor=theme.glass_bg,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Text("Export Extracted Text", size=16, weight=ft.FontWeight.W_600, color=theme.text_primary),
            content=ft.Column(
                tight=True,
                spacing=6,
                controls=[
                    ft.Text("Current Document", size=12, weight=ft.FontWeight.W_600, color=theme.text_secondary),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color=theme.text_primary, size=20),
                        title=ft.Text("Plain text (.txt)", size=13, color=theme.text_primary),
                        on_click=lambda ev: save_file("txt", text_content),
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CODE_OUTLINED, color=theme.text_primary, size=20),
                        title=ft.Text("Markdown (.md)", size=13, color=theme.text_primary),
                        on_click=lambda ev: save_file("md", text_content),
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.TABLE_CHART_OUTLINED, color=theme.text_primary, size=20),
                        title=ft.Text("CSV / Spreadsheet (.csv)", size=13, color=theme.text_primary),
                        subtitle=ft.Text("Converts markdown tables or row data", size=11, color=theme.text_secondary),
                        on_click=lambda ev: save_file("csv", text_to_csv_string(text_content)),
                    ),
                    ft.Divider(height=1, color=theme.border),
                    ft.Text("Batch Queue Export", size=12, weight=ft.FontWeight.W_600, color=theme.text_secondary),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.FOLDER_ZIP_OUTLINED, color=theme.accent, size=20),
                        title=ft.Text("Merge All Queue Documents (.txt)", size=13, color=theme.text_primary),
                        subtitle=ft.Text("Combines all queue transcriptions", size=11, color=theme.text_secondary),
                        on_click=lambda ev: export_merged("txt"),
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ARTICLE_OUTLINED, color=theme.accent, size=20),
                        title=ft.Text("Merge All Queue Documents (.md)", size=13, color=theme.text_primary),
                        subtitle=ft.Text("Formatted markdown document with headers", size=11, color=theme.text_secondary),
                        on_click=lambda ev: export_merged("md"),
                    ),
                ],
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda ev: p.pop_dialog()),
            ],
        )
        p.show_dialog(export_dialog)

    def set_processing(self, is_processing: bool):
        self.extract_progress.visible = is_processing
        self.extract_label.value = "Extracting text..." if is_processing else "Extract text"
        self.extract_btn.disabled = is_processing
        safe_update(self)

    def update_text_view(self):
        item = state.selected_item
        if not item:
            self.char_count_text.value = "0 chars"
            self.status_label.value = "Ready"
            self.status_label.color = theme.text_secondary
            self.raw_output_field.value = ""
            self.markdown_output_view.value = "*Drop an image or PDF here to extract its text.*"
            self._rebuild_blocks("")
            safe_update(self)
            return

        text = item.extracted_text or ""
        self.char_count_text.value = f"{len(text):,} chars"
        is_bengali = contains_bengali(text)
        self.raw_output_field.text_style.font_family = FONT_FAMILY_BENGALI if is_bengali else FONT_FAMILY_MONO
        self.raw_output_field.text_size = 14 if is_bengali else 13

        if item.status == "Processing":
            self.status_label.value = "Extracting text"
            self.status_label.color = theme.accent
            self.raw_output_field.value = "Extracting document text with vision model..."
            self.markdown_output_view.value = "*Extracting document text with vision model...*"
            self._rebuild_blocks("Extracting document text with vision model...")
        elif item.status == "Done":
            self.status_label.value = "Done"
            self.status_label.color = "#10B981" if not theme.is_dark else "#34D399"
            self.raw_output_field.value = text
            self.markdown_output_view.value = text
            self._rebuild_blocks(text)
        elif item.status == "Failed":
            self.status_label.value = "Error"
            self.status_label.color = "#EF4444" if not theme.is_dark else "#F87171"
            err_msg = "Couldn't read this image. Try a sharper photo or a higher-resolution scan."
            if item.error_message:
                err_msg += f"\n\nDetails: {item.error_message}"
            self.raw_output_field.value = err_msg
            self.markdown_output_view.value = f"**Couldn't read this image. Try a sharper photo or a higher-resolution scan.**\n\n`{item.error_message}`"
            self._rebuild_blocks(err_msg)
        else:
            self.status_label.value = "Ready"
            self.status_label.color = theme.text_secondary
            self.raw_output_field.value = text
            self.markdown_output_view.value = text or "*Click 'Extract text' below to begin.*"
            self._rebuild_blocks(text)

        self._update_math_status(text)
        self._update_audit_btn_ui(state.audit_mode)

        # Synchronize format mode icon and tooltip to reflect active format
        curr_mode = state.active_output_mode or "document"
        icon_name = self.MODE_ICONS.get(curr_mode, ft.Icons.DESCRIPTION_OUTLINED)
        self.output_mode_icon.icon = icon_name
        self.output_mode_icon.name = icon_name
        self.output_mode_btn.content = self.output_mode_icon
        label = self.MODE_LABELS.get(curr_mode, "Document")
        desc = self.MODE_DESCRIPTIONS.get(curr_mode, "")
        self.output_mode_btn.tooltip = f"Format: {label} ({desc}) - Click to cycle"

        safe_update(self)

        if state.audit_mode and get_page(self.blocks_column):
            try:
                self.blocks_column.scroll_to(scroll_key=f"block_{state.active_block_index}", duration=150)
            except Exception:
                pass

    def update_theme_ui(self):
        self.bgcolor = theme.surface
        self.border = ft.Border.all(1, theme.border)
        self.header_title.color = theme.text_primary
        self.char_count_text.color = theme.text_secondary
        self.text_canvas.bgcolor = theme.inset
        self.text_canvas.border = ft.Border.all(1, theme.border)

        self.raw_output_field.text_style.color = theme.text_primary
        self.raw_output_field.cursor_color = theme.accent

        self.copy_btn.bgcolor = theme.button_bg
        self.copy_btn.border = ft.Border.all(1, theme.border)
        self.copy_icon.color = theme.text_primary
        self.copy_text.color = theme.text_primary

        self.view_mode_btn.bgcolor = theme.button_bg
        self.view_mode_btn.border = ft.Border.all(1, theme.border)
        self.view_mode_icon.color = theme.text_primary
        self.mode_label.color = theme.text_primary

        audit_bg = (
            "rgba(37, 99, 235, 0.10)" if (state.audit_mode and not theme.is_dark)
            else ("rgba(75, 136, 240, 0.16)" if state.audit_mode else theme.button_bg)
        )
        self.audit_btn.bgcolor = audit_bg
        self.audit_btn.border = ft.Border.all(1.5 if state.audit_mode else 1, theme.accent if state.audit_mode else theme.border)
        self.audit_icon.color = theme.accent if state.audit_mode else theme.text_primary
        self.audit_text.color = theme.accent if state.audit_mode else theme.text_primary

        self.tools_menu_btn.bgcolor = theme.menu_bg
        self.tools_menu_btn.items = self._build_tools_menu_items()
        self.tools_container.bgcolor = theme.button_bg
        self.tools_container.border = ft.Border.all(1, theme.border)
        self.tools_icon.color = theme.text_primary
        self.tools_text.color = theme.text_primary

        self.export_btn.bgcolor = theme.button_bg
        self.export_btn.border = ft.Border.all(1, theme.border)
        self.export_icon.color = theme.text_primary
        self.export_text.color = theme.text_primary

        if hasattr(self, "toolbar_divider"):
            self.toolbar_divider.bgcolor = theme.border

        self.extract_btn.style.bgcolor = theme.accent
        self.extract_btn.style.side = ft.BorderSide(2, theme.accent)

        self.output_mode_btn.bgcolor = theme.button_bg
        self.output_mode_btn.border = ft.Border.all(1, theme.border)
        self.output_mode_icon.color = theme.accent
        self.output_mode_text.color = theme.text_primary

        for block_ctrl in self.blocks_column.controls:
            if isinstance(block_ctrl, ParagraphBlock):
                block_ctrl.update_theme()

        self.update_text_view()

def create_text_panel(on_extract_click=None):
    return TextPanel(on_extract_click=on_extract_click)
