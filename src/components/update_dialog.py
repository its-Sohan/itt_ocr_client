import flet as ft
from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI

def create_update_dialog(page: ft.Page, update_info: dict) -> ft.AlertDialog:
    latest_ver = update_info.get("latest_version", "unknown")
    current_ver = update_info.get("current_version", "")
    release_notes = update_info.get("release_notes", "No changelog provided.")
    download_url = update_info.get("download_url") or update_info.get("release_page_url")

    def on_close(e=None):
        dialog.open = False
        page.update()

    def on_update_click(e=None):
        if download_url:
            page.launch_url(download_url)
        dialog.open = False
        page.update()

    # Changelog display box
    notes_box = ft.Container(
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
            controls=[
                ft.Markdown(
                    release_notes,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                )
            ],
        ),
        max_height=180,
        bgcolor=theme.bg,
        border=ft.Border.all(1, theme.border),
        border_radius=8,
        padding=12,
    )

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.SYSTEM_UPDATE_ROUNDED, color=theme.accent, size=20),
                    ft.Text(
                        "Update Available",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=theme.text_primary,
                        font_family=FONT_FAMILY_UI,
                    ),
                ],
            ),
            ft.IconButton(
                icon=ft.Icons.CLOSE_ROUNDED,
                icon_size=16,
                icon_color=theme.text_secondary,
                on_click=on_close,
            ),
        ],
    )

    version_chips = ft.Row(
        spacing=8,
        controls=[
            ft.Container(
                content=ft.Text(f"Current: v{current_ver}", size=11, color=theme.text_secondary),
                bgcolor=theme.surface,
                border=ft.Border.all(1, theme.border),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            ),
            ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=12, color=theme.text_secondary),
            ft.Container(
                content=ft.Text(f"New: v{latest_ver}", size=11, weight=ft.FontWeight.W_600, color=theme.accent),
                bgcolor=theme.surface,
                border=ft.Border.all(1, theme.accent),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            ),
        ],
    )

    content_box = ft.Container(
        width=480,
        bgcolor=theme.glass_bg,
        blur=theme.glass_blur,
        border=theme.glass_border,
        border_radius=RADIUS_GLASS,
        shadow=theme.glass_shadow,
        padding=20,
        content=ft.Column(
            tight=True,
            spacing=14,
            controls=[
                header,
                version_chips,
                ft.Text(
                    "What's New in this release:",
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=theme.text_primary,
                    font_family=FONT_FAMILY_UI,
                ),
                notes_box,
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    spacing=8,
                    controls=[
                        ft.TextButton(
                            "Later",
                            style=ft.ButtonStyle(
                                color=theme.text_secondary,
                                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                            ),
                            on_click=on_close,
                        ),
                        ft.ElevatedButton(
                            "Download & Update",
                            icon=ft.Icons.DOWNLOAD_ROUNDED,
                            style=ft.ButtonStyle(
                                bgcolor=theme.accent,
                                color="#FFFFFF",
                                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                            ),
                            on_click=on_update_click,
                        ),
                    ],
                ),
            ],
        ),
    )

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor="transparent",
        shape=ft.RoundedRectangleBorder(radius=RADIUS_GLASS),
        content_padding=0,
        content=content_box,
    )
    return dialog
