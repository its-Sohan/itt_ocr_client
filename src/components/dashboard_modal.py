import flet as ft
from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI
from src.config_store import load_config

def create_dashboard_modal(page: ft.Page) -> ft.AlertDialog:
    config = load_config()
    stats = config.get("usage_stats", {})
    session_user = config.get("session_account", "default_user")

    total_proc = stats.get("total_processed", 0)
    success = stats.get("successful_runs", 0)
    failed = stats.get("failed_runs", 0)
    chars = stats.get("total_characters_extracted", 0)
    success_rate = f"{(success / total_proc * 100):.1f}%" if total_proc > 0 else "100%"

    def create_metric_card(title: str, value: str, subtitle: str):
        return ft.Container(
            expand=True,
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=14,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text(title, size=12, weight=ft.FontWeight.W_500, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
                    ft.Text(value, size=20, weight=ft.FontWeight.W_600, color=theme.text_primary, font_family=FONT_FAMILY_UI),
                    ft.Text(subtitle, size=11, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
                ],
            ),
        )

    def on_close(e):
        page.pop_dialog()

    title_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(
                "Usage metrics",
                size=16,
                weight=ft.FontWeight.W_600,
                color=theme.text_primary,
                font_family=FONT_FAMILY_UI,
            ),
            ft.IconButton(
                icon=ft.Icons.CLOSE_ROUNDED,
                icon_size=16,
                icon_color=theme.text_secondary,
                tooltip="Close",
                on_click=on_close,
            ),
        ],
    )

    session_strip = ft.Container(
        bgcolor=theme.surface,
        border=ft.Border.all(1, theme.border),
        border_radius=RADIUS_PANEL,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(f"Session: {session_user}", size=12, weight=ft.FontWeight.W_500, color=theme.text_primary, font_family=FONT_FAMILY_UI),
                ft.Container(
                    content=ft.Text("Active", size=11, weight=ft.FontWeight.W_500, color="#10B981" if not theme.is_dark else "#34D399"),
                    bgcolor=theme.bg,
                    border=ft.Border.all(1, theme.border),
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                ),
            ],
        ),
    )

    content_box = ft.Container(
        width=520,
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
                title_row,
                session_strip,
                ft.Row(
                    spacing=10,
                    controls=[
                        create_metric_card("Processed", str(total_proc), f"{success} successful, {failed} failed"),
                        create_metric_card("Success rate", success_rate, "Overall transcription rate"),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        create_metric_card("Characters", f"{chars:,}", "Total transcribed characters"),
                        create_metric_card("Estimated words", f"{chars // 5:,}", "Assuming ~5 chars per word"),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.ElevatedButton(
                            "Close",
                            style=ft.ButtonStyle(
                                bgcolor=theme.accent,
                                color="#FFFFFF",
                                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                                side=ft.BorderSide(2, theme.accent),
                            ),
                            on_click=on_close,
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
