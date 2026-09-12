import flet as ft
from src import styles

def create_nav_rail(on_settings_click=None, on_dashboard_click=None):
    """
    Modern vertical icon dock matching the Figma design.
    """
    return ft.Container(
        width=56,
        bgcolor=styles.BG_PANEL,
        border=ft.Border.all(1, styles.BORDER_COLOR),
        border_radius=16,
        shadow=styles.PANEL_SHADOW,
        padding=ft.Padding.symmetric(vertical=16, horizontal=6),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                # Top icons
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        ft.Container(
                            width=38,
                            height=38,
                            border_radius=10,
                            bgcolor=styles.BTN_PRIMARY_BG,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.DOCUMENT_SCANNER_ROUNDED, color=styles.BG_PANEL, size=20),
                            tooltip="ITT OCR Client",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ANALYTICS_OUTLINED,
                            icon_color=styles.TEXT_SECONDARY,
                            icon_size=20,
                            tooltip="Usage Dashboard",
                            on_click=on_dashboard_click,
                        ),
                    ],
                ),
                # Bottom icons
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS_OUTLINED,
                            icon_color=styles.TEXT_SECONDARY,
                            icon_size=20,
                            tooltip="Configuration & API Key",
                            on_click=on_settings_click,
                        ),
                    ],
                ),
            ],
        ),
    )
