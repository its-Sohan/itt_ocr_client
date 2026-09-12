import os
import flet as ft
from src import styles
from src.app_state import state

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

class PreviewPanel(ft.Container):
    def __init__(self):
        super().__init__(
            width=380,
            bgcolor=styles.BG_PANEL,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=12,
            padding=16,
        )
        self.size_badge = ft.Container(
            content=ft.Text("0 KB", size=11, weight=ft.FontWeight.W_600, color=styles.TEXT_SECONDARY),
            bgcolor=styles.BG_SUBTLE,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )
        self.filename_text = ft.Text("NO FILE LOADED", size=12, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY)
        self.status_text = ft.Text("Select or add an image from queue", size=11, color=styles.TEXT_TERTIARY)
        
        # Inner canvas for the preview image
        self.image_display_container = ft.Container(
            expand=True,
            bgcolor=styles.BG_SUBTLE,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=8,
            padding=12,
            alignment=ft.Alignment.CENTER,
            content=self._build_empty_placeholder(),
        )

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.START,
            spacing=12,
            controls=[
                # Precision Header
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(width=6, height=6, border_radius=3, bgcolor=styles.TEXT_PRIMARY),
                                ft.Text("SOURCE DOCUMENT", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                            ],
                        ),
                        self.size_badge,
                    ],
                ),
                self.image_display_container,
                # Micro metadata footer
                ft.Container(
                    bgcolor=styles.BG_SUBTLE,
                    border=ft.Border.all(1, styles.BORDER_COLOR),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            self.filename_text,
                            self.status_text,
                        ],
                    ),
                ),
            ],
        )

        state.add_listener(self.update_preview)
        self.update_preview()

    def _build_empty_placeholder(self):
        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Container(
                    width=64,
                    height=64,
                    border_radius=8,
                    bgcolor=styles.BG_PANEL,
                    border=ft.Border.all(1, styles.BORDER_DASHED),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.IMAGE_OUTLINED, size=28, color=styles.TEXT_MUTED),
                ),
                ft.Text("AWAITING DOCUMENT INPUT", size=10, weight=ft.FontWeight.BOLD, color=styles.TEXT_MUTED),
            ],
        )

    def update_preview(self):
        item = state.selected_item
        if not item:
            self.filename_text.value = "NO FILE LOADED"
            self.status_text.value = "Awaiting selection"
            self.size_badge.content.value = "0 KB"
            self.image_display_container.content = self._build_empty_placeholder()
            safe_update(self)
            return

        self.filename_text.value = item.file_name.upper()
        self.status_text.value = f"{item.source.upper()} • {item.status.upper()}"
        self.size_badge.content.value = item.file_size_str

        if os.path.exists(item.file_path):
            self.image_display_container.content = ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=ft.Image(
                    src=item.file_path,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=6,
                ),
            )
        else:
            self.image_display_container.content = self._build_empty_placeholder()

        safe_update(self)

def create_preview_panel():
    return PreviewPanel()
