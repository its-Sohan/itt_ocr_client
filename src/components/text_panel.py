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

import os
import time

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

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

class ParagraphBlock(ft.Container):
    def __init__(self, text: str, on_copy):
        self.block_text = text
        self.on_copy = on_copy

        is_bengali = contains_bengali(self.block_text)

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
            bgcolor=theme.surface,
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

        super().__init__(
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            on_hover=self._on_hover,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
                controls=[
                    self.text_content,
                    self.copy_badge,
                ],
            ),
        )

    def _handle_copy_click(self, e):
        self.copy_icon.name = ft.Icons.CHECK_ROUNDED
        self.copy_icon.color = "#10B981" if not theme.is_dark else "#34D399"
        self.copy_label.value = "Copied"
        self.copy_label.color = "#10B981" if not theme.is_dark else "#34D399"
        safe_update(self)
        self.on_copy(self.block_text)

    def _on_hover(self, e: ft.HoverEvent):
        is_hovered = (e.data == "true")
        self.copy_badge.opacity = 1.0 if is_hovered else 0.0
        if not is_hovered:
            self.copy_icon.name = ft.Icons.CONTENT_COPY_ROUNDED
            self.copy_icon.color = theme.text_secondary
            self.copy_label.value = "Copy"
            self.copy_label.color = theme.text_secondary
        self.border = ft.Border.all(1, theme.accent if is_hovered else theme.border)
        safe_update(self)

    def update_theme(self):
        self.bgcolor = theme.surface
        self.border = ft.Border.all(1, theme.border)
        self.text_content.color = theme.text_primary
        self.copy_badge.bgcolor = theme.surface
        self.copy_badge.border = ft.Border.all(1, theme.border)
        self.copy_icon.color = theme.text_secondary
        self.copy_label.color = theme.text_secondary
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
            "0 characters",
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
            bgcolor=theme.bg,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=8,
            content=self.blocks_column,
        )

        # Copy Entire Document button
        self.copy_icon = ft.Icon(ft.Icons.CONTENT_COPY_ROUNDED, size=14, color=theme.text_primary)
        self.copy_text = ft.Text("Copy all", size=12, weight=ft.FontWeight.W_500, color=theme.text_primary, font_family=FONT_FAMILY_UI)
        self.copy_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=6,
                controls=[self.copy_icon, self.copy_text],
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                side=ft.BorderSide(1, theme.border),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                bgcolor=theme.surface,
            ),
            on_click=self.on_copy_all_click,
            tooltip="Copy entire extracted text to clipboard",
        )

        # View Mode Toggle Segment: Blocks / Raw / Markdown
        self.mode_label = ft.Text("View: Blocks", size=12, weight=ft.FontWeight.W_500, color=theme.text_primary, font_family=FONT_FAMILY_UI)
        self.view_mode_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.VIEW_AGENDA_OUTLINED, size=14, color=theme.text_primary),
                    self.mode_label,
                ],
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                side=ft.BorderSide(1, theme.border),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                bgcolor=theme.surface,
            ),
            on_click=self.cycle_view_mode,
            tooltip="Cycle view mode: Paragraph Blocks, Raw Monospace, Markdown Preview",
        )

        # Export button
        self.export_icon = ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=14, color=theme.text_primary)
        self.export_text = ft.Text("Export", size=12, weight=ft.FontWeight.W_500, color=theme.text_primary, font_family=FONT_FAMILY_UI)
        self.export_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=6,
                controls=[self.export_icon, self.export_text],
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                side=ft.BorderSide(1, theme.border),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                bgcolor=theme.surface,
            ),
            on_click=self.on_export_click,
            tooltip="Export extracted text to file",
        )

        # Primary Action Button: 'Extract text'
        self.extract_progress = ft.ProgressRing(width=14, height=14, stroke_width=2, color="#FFFFFF", visible=False)
        self.extract_label = ft.Text(
            "Extract text",
            size=13,
            weight=ft.FontWeight.W_500,
            color="#FFFFFF",
            font_family=FONT_FAMILY_UI,
        )
        self.extract_btn = ft.ElevatedButton(
            content=ft.Row(
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    self.extract_progress,
                    self.extract_label,
                ],
            ),
            style=ft.ButtonStyle(
                bgcolor=theme.accent,
                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                side=ft.BorderSide(2, theme.accent),
            ),
            on_click=self.on_extract_click,
            tooltip="Extract text from selected image",
        )

        header_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[self.header_title, self.char_count_text],
                ),
                self.status_label,
            ],
        )

        bottom_bar = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        self.copy_btn,
                        self.view_mode_btn,
                        self.export_btn,
                    ],
                ),
                self.extract_btn,
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
            self.char_count_text.value = f"{len(item.extracted_text):,} characters"
            is_bengali = contains_bengali(item.extracted_text)
            self.raw_output_field.text_style.font_family = FONT_FAMILY_BENGALI if is_bengali else FONT_FAMILY_MONO
            self.raw_output_field.text_size = 14 if is_bengali else 13
            # Rebuild blocks from edited text
            self._rebuild_blocks(item.extracted_text)

    def cycle_view_mode(self, e):
        if self.view_mode == "blocks":
            self.view_mode = "raw"
            self.mode_label.value = "View: Raw"
            self.text_canvas.content = self.raw_output_field
        elif self.view_mode == "raw":
            self.view_mode = "markdown"
            self.mode_label.value = "View: Markdown"
            self.text_canvas.content = self.markdown_output_view
        else:
            self.view_mode = "blocks"
            self.mode_label.value = "View: Blocks"
            self.text_canvas.content = self.blocks_column
        safe_update(self)

    def on_copy_block(self, block_text: str):
        if block_text and self.page:
            try:
                self.page.set_clipboard(block_text)
                self.page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Copied paragraph", size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=1500,
                    )
                )
            except Exception:
                pass

    def on_copy_all_click(self, e):
        item = state.selected_item
        text_to_copy = self.raw_output_field.value or (item.extracted_text if item else "")
        if text_to_copy and self.page:
            try:
                self.page.set_clipboard(text_to_copy)
                self.page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("Copied", size=13, weight=ft.FontWeight.W_500, color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=1800,
                    )
                )
            except Exception:
                pass

    def _rebuild_blocks(self, text: str):
        self.blocks_column.controls.clear()
        if not text:
            self.blocks_column.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text(
                        "No paragraphs extracted yet.",
                        size=13,
                        color=theme.text_secondary,
                        font_family=FONT_FAMILY_UI,
                    ),
                )
            )
            return

        # Split into paragraphs by double newlines or single newlines
        raw_blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        if not raw_blocks:
            raw_blocks = [b.strip() for b in text.split("\n") if b.strip()]
        if not raw_blocks:
            raw_blocks = [text.strip()]

        for block in raw_blocks:
            self.blocks_column.controls.append(
                ParagraphBlock(block, on_copy=self.on_copy_block)
            )

    def on_export_click(self, e):
        item = state.selected_item
        text_content = self.raw_output_field.value or (item.extracted_text if item else "")
        if not text_content and not any(it.extracted_text for it in state.queue):
            if self.page:
                self.page.show_dialog(
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
                self.page.pop_dialog()
                folder_name = os.path.basename(target_dir) or target_dir
                self.page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(f"Saved {fname} to {folder_name}", size=13, color=theme.text_primary),
                        bgcolor=theme.glass_bg,
                        duration=3000,
                    )
                )
            except Exception as ex:
                self.page.show_dialog(
                    ft.SnackBar(content=ft.Text(f"Export failed: {str(ex)}"), bgcolor="#EF4444")
                )

        def export_merged(ext: str):
            completed = [it for it in state.queue if it.extracted_text and it.extracted_text.strip()]
            if not completed:
                self.page.show_dialog(
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
                ft.TextButton("Cancel", on_click=lambda ev: self.page.pop_dialog()),
            ],
        )
        self.page.show_dialog(export_dialog)

    def set_processing(self, is_processing: bool):
        self.extract_progress.visible = is_processing
        self.extract_label.value = "Extracting text..." if is_processing else "Extract text"
        self.extract_btn.disabled = is_processing
        safe_update(self)

    def update_text_view(self):
        item = state.selected_item
        if not item:
            self.char_count_text.value = "0 characters"
            self.status_label.value = "No document loaded"
            self.status_label.color = theme.text_secondary
            self.raw_output_field.value = ""
            self.markdown_output_view.value = "*Drop an image or PDF here to extract its text.*"
            self._rebuild_blocks("")
            safe_update(self)
            return

        text = item.extracted_text or ""
        self.char_count_text.value = f"{len(text):,} characters"
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

        safe_update(self)

    def update_theme_ui(self):
        self.bgcolor = theme.surface
        self.border = ft.Border.all(1, theme.border)
        self.header_title.color = theme.text_primary
        self.char_count_text.color = theme.text_secondary
        self.text_canvas.bgcolor = theme.bg
        self.text_canvas.border = ft.Border.all(1, theme.border)

        self.raw_output_field.text_style.color = theme.text_primary
        self.raw_output_field.cursor_color = theme.accent

        self.copy_btn.style.bgcolor = theme.surface
        self.copy_btn.style.side = ft.BorderSide(1, theme.border)
        self.copy_icon.color = theme.text_primary
        self.copy_text.color = theme.text_primary

        self.view_mode_btn.style.bgcolor = theme.surface
        self.view_mode_btn.style.side = ft.BorderSide(1, theme.border)
        self.mode_label.color = theme.text_primary

        self.export_btn.style.bgcolor = theme.surface
        self.export_btn.style.side = ft.BorderSide(1, theme.border)
        self.export_icon.color = theme.text_primary
        self.export_text.color = theme.text_primary

        self.extract_btn.style.bgcolor = theme.accent
        self.extract_btn.style.side = ft.BorderSide(2, theme.accent)

        for block_ctrl in self.blocks_column.controls:
            if isinstance(block_ctrl, ParagraphBlock):
                block_ctrl.update_theme()

        self.update_text_view()

def create_text_panel(on_extract_click=None):
    return TextPanel(on_extract_click=on_extract_click)
