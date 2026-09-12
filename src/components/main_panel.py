import flet as ft
from src.styles import theme, RADIUS_PANEL, FONT_FAMILY_UI
from src.components.preview_panel import create_preview_panel
from src.components.text_panel import create_text_panel
from src.app_state import state

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

class MainPanel(ft.Container):
    def __init__(self, on_scan_click=None, on_extract_click=None):
        self.preview_panel = create_preview_panel(on_scan_click=on_scan_click)
        self.text_panel = create_text_panel(on_extract_click=on_extract_click)

        # Workspace container holding Document Canvas & Extracted Text
        self.workspace_layout = ft.Row(
            expand=True,
            spacing=16,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                self.preview_panel,
                self.text_panel,
            ],
        )

        super().__init__(
            expand=True,
            bgcolor="transparent",
            content=self.workspace_layout,
        )

        theme.add_listener(self.update_theme_ui)

    def set_stacked(self, stacked: bool):
        if stacked:
            self.workspace_layout.vertical_alignment = ft.CrossAxisAlignment.START
            # Switch controls to vertical column orientation if screen is narrow
            self.content = ft.Column(
                expand=True,
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(content=self.preview_panel, height=360),
                    ft.Container(content=self.text_panel, height=440),
                ],
            )
        else:
            self.workspace_layout.controls = [self.preview_panel, self.text_panel]
            self.content = self.workspace_layout
        safe_update(self)

    def update_theme_ui(self):
        safe_update(self)

def create_main_panel(on_scan_click=None, on_extract_click=None):
    return MainPanel(on_scan_click=on_scan_click, on_extract_click=on_extract_click)
