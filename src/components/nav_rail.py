import flet as ft
from src import styles

def create_nav_rail(on_settings_click=None, on_dashboard_click=None):
    """
    Swiss Minimalist Tactical Left Rail (64px).
    Features crisp geometric iconography, active indicators, and subtle divider rules.
    """
    def create_nav_btn(icon, tooltip, on_click=None, active=False):
        return ft.Container(
            width=42,
            height=42,
            border_radius=10,
            bgcolor=styles.BG_PANEL if active else "transparent",
            border=ft.Border.all(1, styles.BORDER_COLOR if active else "transparent"),
            alignment=ft.Alignment.CENTER,
            content=ft.IconButton(
                icon=icon,
                icon_color=styles.TEXT_PRIMARY if active else styles.TEXT_SECONDARY,
                icon_size=20,
                tooltip=tooltip,
                on_click=on_click,
            ),
        )

    return ft.Container(
        width=68,
        bgcolor=styles.NAV_RAIL_BG,
        border=ft.Border(right=ft.BorderSide(1, styles.NAV_RAIL_BORDER)),
        padding=ft.Padding.symmetric(vertical=20, horizontal=12),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                # Top brand + primary shortcuts
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        # Minimalist Monogram Brand Anchor
                        ft.Container(
                            width=42,
                            height=42,
                            border_radius=8,
                            bgcolor=styles.BTN_PRIMARY_BG,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text("OCR", size=11, weight=ft.FontWeight.W_800, color=styles.BG_PANEL),
                            tooltip="ITT OCR Client — Swiss Edition",
                        ),
                        ft.Container(height=1, width=28, bgcolor=styles.BORDER_COLOR),
                        create_nav_btn(ft.Icons.DASHBOARD_ROUNDED, "Usage Dashboard", on_click=on_dashboard_click),
                    ],
                ),
                # Bottom settings shortcut
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        ft.Container(height=1, width=28, bgcolor=styles.BORDER_COLOR),
                        create_nav_btn(ft.Icons.TUNE_ROUNDED, "Configuration & API Credentials", on_click=on_settings_click),
                    ],
                ),
            ],
        ),
    )
