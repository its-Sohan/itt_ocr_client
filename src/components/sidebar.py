import flet as ft
from src import styles

def create_badge(text: str, bg_color=styles.BG_PILL, text_color=styles.TEXT_MUTED):
    return ft.Container(
        content=ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=text_color),
        bgcolor=bg_color,
        border_radius=999,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )

def create_sidebar(on_browse_click=None, on_process_click=None):
    """
    Left upload and queue panel (Width: ~390px).
    Matches Figma #2:8 sidebar.
    """
    # Header
    header = ft.Column(
        spacing=6,
        controls=[
            ft.Text("Upload your files", size=26, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
            ft.Text(
                "Add images to extract text, organize uploads, and review processing status.",
                size=13,
                color=styles.TEXT_SECONDARY,
            ),
        ],
    )

    # Upload Dropzone
    dropzone = ft.Container(
        height=210,
        bgcolor=styles.BG_MUTED,
        border=ft.Border.all(1, styles.BORDER_DASHED),
        border_radius=16,
        padding=16,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Container(
                    width=52,
                    height=52,
                    border_radius=26,
                    bgcolor=styles.BG_PILL,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=26, color=styles.TEXT_PRIMARY),
                ),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    controls=[
                        ft.Text("Drag and drop files here", size=15, weight=ft.FontWeight.W_600, color=styles.TEXT_PRIMARY),
                        ft.Text("PNG, JPG, or PDF up to 50 MB", size=12, color=styles.TEXT_SECONDARY),
                    ],
                ),
                ft.ElevatedButton(
                    content=ft.Text("Browse files", size=13, weight=ft.FontWeight.W_600, color=styles.BG_PANEL),
                    style=ft.ButtonStyle(
                        bgcolor=styles.TEXT_PRIMARY,
                        shape=ft.RoundedRectangleBorder(radius=999),
                        padding=ft.Padding.symmetric(horizontal=18, vertical=10),
                    ),
                    on_click=on_browse_click,
                ),
            ],
        ),
    )

    # Queue Card
    queue_card = ft.Container(
        bgcolor=styles.BG_PANEL,
        border=ft.Border.all(1, styles.BORDER_COLOR),
        border_radius=16,
        padding=16,
        content=ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Upload queue", size=15, weight=ft.FontWeight.W_600, color=styles.TEXT_PRIMARY),
                        create_badge("1 file"),
                    ],
                ),
                # File row
                ft.Container(
                    bgcolor=styles.BG_MUTED,
                    border_radius=12,
                    padding=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(
                                        width=40,
                                        height=40,
                                        border_radius=10,
                                        bgcolor=styles.BG_PILL,
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Icon(ft.Icons.IMAGE_OUTLINED, size=20, color=styles.TEXT_SECONDARY),
                                    ),
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text("img-001654here.png", size=13, weight=ft.FontWeight.W_600, color=styles.TEXT_PRIMARY),
                                            ft.Text("397.8 KB", size=11, color=styles.TEXT_SECONDARY),
                                        ],
                                    ),
                                ],
                            ),
                            create_badge("Ready", bg_color=styles.BG_SUCCESS_PILL, text_color=styles.TEXT_SUCCESS),
                        ],
                    ),
                ),
            ],
        ),
    )

    # Process Action Button
    process_btn = ft.ElevatedButton(
        content=ft.Text("Process", size=16, weight=ft.FontWeight.W_600, color=styles.BTN_PRIMARY_TEXT),
        style=ft.ButtonStyle(
            bgcolor=styles.BTN_PRIMARY_BG,
            shape=ft.RoundedRectangleBorder(radius=14),
            padding=ft.Padding.symmetric(vertical=16),
        ),
        on_click=on_process_click,
    )

    # Full Sidebar Container
    return ft.Container(
        width=380,
        bgcolor=styles.BG_PANEL,
        border=ft.Border.all(1, styles.BORDER_COLOR),
        border_radius=20,
        padding=24,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=20,
                    controls=[
                        header,
                        dropzone,
                        queue_card,
                    ],
                ),
                ft.Container(
                    content=process_btn,
                    alignment=ft.Alignment.CENTER,
                ),
            ],
        ),
    )
