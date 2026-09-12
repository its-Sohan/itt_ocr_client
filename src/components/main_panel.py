import flet as ft
from src import styles
from src.components.sidebar import create_badge
from src.components.preview_panel import create_preview_panel
from src.components.text_panel import create_text_panel
from src.app_state import state

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

class MainPanel(ft.Container):
    def __init__(self):
        super().__init__(
            expand=True,
            bgcolor=styles.BG_PANEL,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=12,
            padding=20,
        )
        self.page_badge = ft.Container(
            content=ft.Text("PAGE 0 OF 0", size=10, weight=ft.FontWeight.BOLD, color=styles.TEXT_SECONDARY),
            bgcolor=styles.BG_SUBTLE,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )
        self.preview_panel = create_preview_panel()
        self.text_panel = create_text_panel()

        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(width=6, height=6, border_radius=3, bgcolor=styles.TEXT_PRIMARY),
                                ft.Text("WORKSPACE — TRANSCRIPTION STUDIO", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                            ],
                        ),
                        ft.Text(
                            "High-precision document extraction engine with real-time markdown transcription and syntax review.",
                            size=12,
                            color=styles.TEXT_SECONDARY,
                        ),
                    ],
                ),
                self.page_badge,
            ],
        )

        workspace = ft.Row(
            expand=True,
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                self.preview_panel,
                self.text_panel,
            ],
        )

        self.content = ft.Column(
            expand=True,
            spacing=20,
            controls=[
                header,
                workspace,
            ],
        )

        state.add_listener(self.update_header)
        self.update_header()

    def update_header(self):
        total = len(state.queue)
        current_idx = 0
        if state.selected_item and total > 0:
            try:
                current_idx = state.queue.index(state.selected_item) + 1
            except ValueError:
                current_idx = 1
        self.page_badge.content.value = f"PAGE {current_idx} OF {total}"
        safe_update(self)

def create_main_panel():
    return MainPanel()
