import flet as ft
from src import styles
from src.config_store import load_config

def create_dashboard_modal(page: ft.Page) -> ft.AlertDialog:
    config = load_config()
    stats = config.get("usage_stats", {})
    session_user = config.get("session_account", "default_user")
    model_name = config.get("model_name", "gpt-4o-mini")

    total_proc = stats.get("total_processed", 0)
    success = stats.get("successful_runs", 0)
    failed = stats.get("failed_runs", 0)
    chars = stats.get("total_characters_extracted", 0)
    success_rate = f"{(success / total_proc * 100):.1f}%" if total_proc > 0 else "100%"

    def create_metric_card(title: str, value: str, subtitle: str, icon: str):
        return ft.Container(
            expand=True,
            bgcolor=styles.BG_MUTED,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=12,
            padding=16,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(title, size=13, weight=ft.FontWeight.W_500, color=styles.TEXT_SECONDARY),
                            ft.Icon(icon, size=18, color=styles.TEXT_SECONDARY),
                        ],
                    ),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                    ft.Text(subtitle, size=11, color=styles.TEXT_SECONDARY),
                ],
            ),
        )

    def on_close(e):
        page.pop_dialog()

    modal = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.BAR_CHART_ROUNDED, color=styles.TEXT_PRIMARY, size=24),
                        ft.Text("Usage & OCR Metrics Dashboard", size=18, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                    ],
                ),
                ft.IconButton(ft.Icons.CLOSE, on_click=on_close),
            ],
        ),
        content=ft.Container(
            width=540,
            padding=ft.Padding.only(top=10),
            content=ft.Column(
                tight=True,
                spacing=16,
                controls=[
                    # User session strip
                    ft.Container(
                        bgcolor=styles.BG_SUBTLE,
                        border=ft.Border.all(1, styles.BORDER_COLOR),
                        border_radius=10,
                        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(ft.Icons.ACCOUNT_CIRCLE_OUTLINED, size=18, color=styles.TEXT_PRIMARY),
                                        ft.Text(f"Session: {session_user}", size=13, weight=ft.FontWeight.W_600, color=styles.TEXT_PRIMARY),
                                    ],
                                ),
                                ft.Container(
                                    content=ft.Text(f"Model: {model_name}", size=11, weight=ft.FontWeight.W_600, color=styles.TEXT_SECONDARY),
                                    bgcolor=styles.BG_SUBTLE,
                                    border=ft.Border.all(1, styles.BORDER_COLOR),
                                    border_radius=4,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                ),
                            ],
                        ),
                    ),
                    # Metric cards row 1
                    ft.Row(
                        spacing=12,
                        controls=[
                            create_metric_card("Total Processed", str(total_proc), f"{success} successful, {failed} failed", ft.Icons.DOCUMENT_SCANNER_OUTLINED),
                            create_metric_card("Success Rate", success_rate, "Lifetime OCR success", ft.Icons.CHECK_CIRCLE_OUTLINE),
                        ],
                    ),
                    # Metric cards row 2
                    ft.Row(
                        spacing=12,
                        controls=[
                            create_metric_card("Chars Extracted", f"{chars:,}", "Total transcribed characters", ft.Icons.TEXT_FIELDS_ROUNDED),
                            create_metric_card("Est. Words", f"{chars // 5:,}", "Assuming ~5 chars/word", ft.Icons.ANALYTICS_OUTLINED),
                        ],
                    ),
                ],
            ),
        ),
        actions=[
            ft.ElevatedButton(
                "Close",
                style=ft.ButtonStyle(
                    bgcolor=styles.BTN_PRIMARY_BG,
                    color=styles.BTN_PRIMARY_TEXT,
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                on_click=on_close,
            ),
        ],
    )
    return modal
