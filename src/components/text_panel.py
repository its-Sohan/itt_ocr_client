import flet as ft
from src import styles
from src.components.sidebar import create_badge

def create_text_panel():
    """
    Extracted Text result card.
    Matches Figma #2:50 text-panel.
    """
    return ft.Container(
        expand=True,
        bgcolor=styles.BG_PANEL,
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
                        ft.Text("Extracted text", size=15, weight=ft.FontWeight.W_600, color=styles.TEXT_PRIMARY),
                        create_badge("0 characters"),
                    ],
                ),
                # Inner text preview container
                ft.Container(
                    expand=True,
                    bgcolor=styles.BG_SUBTLE,
                    border=ft.Border.all(1, styles.BORDER_COLOR),
                    border_radius=14,
                    padding=20,
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("No text extracted yet", size=13, weight=ft.FontWeight.W_600, color=styles.TEXT_PRIMARY),
                                    create_badge("Ready to process"),
                                ],
                            ),
                            ft.Text(
                                "Upload an image, click Process, and the extracted text will appear here for review.",
                                size=13,
                                color=styles.TEXT_TERTIARY,
                                selectable=True,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
