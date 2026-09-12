import flet as ft
from src import styles
from src.app_state import state

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

class TextPanel(ft.Container):
    def __init__(self):
        super().__init__(
            expand=True,
            bgcolor=styles.BG_PANEL,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=12,
            padding=16,
        )
        self.char_badge = ft.Container(
            content=ft.Text("0 CHARS", size=11, weight=ft.FontWeight.W_600, color=styles.TEXT_SECONDARY),
            bgcolor=styles.BG_SUBTLE,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )
        self.status_badge = ft.Container(
            content=ft.Text("IDLE", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_MUTED),
            bgcolor=styles.STATUS_READY_BG,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )

        # Mode toggle: Formatted Markdown View vs Raw Monospace View
        self.is_raw_mode = False
        
        # Raw text editor/viewer
        self.raw_field = ft.TextField(
            value="",
            read_only=True,
            multiline=True,
            border=ft.InputBorder.NONE,
            text_size=13,
            cursor_color=styles.TEXT_PRIMARY,
            expand=True,
        )

        # Markdown formatted viewer
        self.markdown_view = ft.Markdown(
            value="*Extracted text will be rendered here with complete markdown formatting.*",
            selectable=True,
            expand=True,
            soft_line_break=True,
        )

        self.content_area = ft.Container(
            expand=True,
            bgcolor=styles.BG_SUBTLE,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=8,
            padding=16,
            content=self.markdown_view,
        )

        # Action Toolbar buttons
        self.copy_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.COPY_ALL_ROUNDED, size=13, color=styles.TEXT_PRIMARY),
                    ft.Text("COPY", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                ],
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                side=ft.BorderSide(1, styles.BORDER_COLOR),
            ),
            on_click=self.on_copy_click,
            visible=False,
        )

        self.toggle_mode_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.CODE_ROUNDED, size=13, color=styles.TEXT_PRIMARY),
                    ft.Text("RAW", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                ],
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                side=ft.BorderSide(1, styles.BORDER_COLOR),
            ),
            on_click=self.on_toggle_mode_click,
            visible=False,
        )

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.START,
            spacing=12,
            controls=[
                # Top header & precision status
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(width=6, height=6, border_radius=3, bgcolor=styles.TEXT_PRIMARY),
                                ft.Text("EXTRACTED TRANSCRIPTION", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                self.toggle_mode_btn,
                                self.copy_btn,
                                self.char_badge,
                                self.status_badge,
                            ],
                        ),
                    ],
                ),
                self.content_area,
            ],
        )

        state.add_listener(self.update_text_view)
        self.update_text_view()

    def on_toggle_mode_click(self, e):
        self.is_raw_mode = not self.is_raw_mode
        self.toggle_mode_btn.content.controls[1].value = "PREVIEW" if self.is_raw_mode else "RAW"
        self.content_area.content = self.raw_field if self.is_raw_mode else self.markdown_view
        if self.page:
            self.update()

    def on_copy_click(self, e):
        item = state.selected_item
        if item and item.extracted_text and self.page:
            try:
                self.page.set_clipboard(item.extracted_text)
                self.page.show_dialog(ft.SnackBar(ft.Text("Transcription copied to clipboard!")))
            except Exception:
                pass

    def update_text_view(self):
        item = state.selected_item
        if not item:
            self.char_badge.content.value = "0 CHARS"
            self.status_badge.content.value = "NO SELECTION"
            self.status_badge.bgcolor = styles.STATUS_READY_BG
            self.status_badge.content.color = styles.TEXT_MUTED
            self.markdown_view.value = "*No document selected from the queue. Upload or scan an image to begin transcription.*"
            self.raw_field.value = ""
            self.copy_btn.visible = False
            self.toggle_mode_btn.visible = False
            safe_update(self)
            return

        char_len = len(item.extracted_text) if item.extracted_text else 0
        self.char_badge.content.value = f"{char_len:,} CHARS"

        if item.status == "Processing":
            self.status_badge.content.value = "IN PROGRESS"
            self.status_badge.bgcolor = styles.STATUS_PROC_BG
            self.status_badge.border = ft.Border.all(1, styles.STATUS_PROC_BORDER)
            self.status_badge.content.color = styles.STATUS_PROC_TEXT
            self.markdown_view.value = "⏳ **Transcribing document via LLM vision model...**\n\nPreserving typography, tabular alignment, and formatting."
            self.raw_field.value = "Transcribing..."
            self.copy_btn.visible = False
            self.toggle_mode_btn.visible = False
        elif item.status == "Done":
            self.status_badge.content.value = "TRANSCRIBED"
            self.status_badge.bgcolor = styles.STATUS_SUCCESS_BG
            self.status_badge.border = ft.Border.all(1, styles.STATUS_SUCCESS_BORDER)
            self.status_badge.content.color = styles.STATUS_SUCCESS_TEXT
            self.markdown_view.value = item.extracted_text
            self.raw_field.value = item.extracted_text
            self.copy_btn.visible = True
            self.toggle_mode_btn.visible = True
        elif item.status == "Failed":
            self.status_badge.content.value = "ERROR"
            self.status_badge.bgcolor = styles.STATUS_ERR_BG
            self.status_badge.border = ft.Border.all(1, styles.STATUS_ERR_BORDER)
            self.status_badge.content.color = styles.STATUS_ERR_TEXT
            self.markdown_view.value = f"### ⚠️ Extraction Failed\n\n```\n{item.error_message}\n```\n\nPlease check your API key and network connection in Settings."
            self.raw_field.value = item.error_message
            self.copy_btn.visible = False
            self.toggle_mode_btn.visible = False
        else:
            self.status_badge.content.value = "READY"
            self.status_badge.bgcolor = styles.STATUS_READY_BG
            self.status_badge.border = ft.Border.all(1, styles.BORDER_COLOR)
            self.status_badge.content.color = styles.STATUS_READY_TEXT
            self.markdown_view.value = "Ready to transcribe. Click **PROCESS QUEUE** below to extract text from this document."
            self.raw_field.value = ""
            self.copy_btn.visible = False
            self.toggle_mode_btn.visible = False

        safe_update(self)

def create_text_panel():
    return TextPanel()
