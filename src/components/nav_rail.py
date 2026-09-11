import flet as ft
from src import styles

def create_nav_rail():
    """Slim left rail navigation matching the 75px Figma strip."""
    return ft.Container(
        width=72,
        bgcolor=styles.NAV_RAIL_BG,
        padding=ft.Padding.symmetric(vertical=24),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
            spacing=20,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.MENU_ROUNDED,
                    icon_color=styles.TEXT_PRIMARY,
                    icon_size=24,
                    tooltip="Menu",
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOUD_UPLOAD_ROUNDED,
                    icon_color=styles.TEXT_PRIMARY,
                    icon_size=24,
                    tooltip="Upload",
                ),
                ft.IconButton(
                    icon=ft.Icons.TEXT_SNIPPET_OUTLINED,
                    icon_color=styles.TEXT_SECONDARY,
                    icon_size=24,
                    tooltip="Extracted Text",
                ),
            ],
        ),
    )
