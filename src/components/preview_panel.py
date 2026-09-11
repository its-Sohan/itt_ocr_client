import flet as ft
from src import styles
from src.components.sidebar import create_badge

def create_preview_panel():
    """
    Original Image preview card (Width: ~360px).
    Matches Figma #2:39 preview-panel.
    """
    return ft.Container(
        width=360,
        bgcolor=styles.BG_SUBTLE,
        border=ft.Border.all(1, styles.BORDER_COLOR),
        border_radius=16,
        padding=18,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.START,
            spacing=16,
            controls=[
                # Header row
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Original image", size=15, weight=ft.FontWeight.W_600, color=styles.TEXT_PRIMARY),
                        create_badge("397.8 KB"),
                    ],
                ),
                # Dashed container with centered preview
                ft.Container(
                    expand=True,
                    bgcolor=styles.BG_MUTED,
                    border=ft.Border.all(1, styles.BORDER_COLOR),
                    border_radius=14,
                    padding=16,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            ft.Container(
                                width=180,
                                height=180,
                                bgcolor=styles.BG_PANEL,
                                border=ft.Border.all(1, styles.BORDER_DASHED),
                                border_radius=12,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(
                                    ft.Icons.IMAGE_ROUNDED,
                                    size=48,
                                    color=styles.TEXT_SECONDARY,
                                ),
                            ),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                                controls=[
                                    ft.Text("img-001654here.png", size=13, weight=ft.FontWeight.W_600, color=styles.TEXT_PRIMARY),
                                    ft.Text("Waiting for processing", size=11, color=styles.TEXT_SECONDARY),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
