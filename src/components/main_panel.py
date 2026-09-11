import flet as ft
from src import styles
from src.components.sidebar import create_badge
from src.components.preview_panel import create_preview_panel
from src.components.text_panel import create_text_panel

def create_main_panel():
    """
    Main Content Panel holding Title/Subtitle and the dual Workspace (Preview + Extracted Text).
    Matches Figma #2:32 main-panel.
    """
    # Header
    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Column(
                spacing=4,
                controls=[
                    ft.Text("Image to Text", size=28, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                    ft.Text(
                        "Review extracted text, correct errors, and export the final result.",
                        size=13,
                        color=styles.TEXT_SECONDARY,
                    ),
                ],
            ),
            create_badge("0 / 1 page", bg_color=styles.BG_PILL, text_color=styles.TEXT_MUTED),
        ],
    )

    # Workspace row: preview-panel + text-panel
    workspace = ft.Row(
        expand=True,
        spacing=20,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            create_preview_panel(),
            create_text_panel(),
        ],
    )

    return ft.Container(
        expand=True,
        bgcolor=styles.BG_PANEL,
        border=ft.Border.all(1, styles.BORDER_COLOR),
        border_radius=20,
        padding=24,
        content=ft.Column(
            expand=True,
            spacing=20,
            controls=[
                header,
                workspace,
            ],
        ),
    )
