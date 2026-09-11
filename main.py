import flet as ft
from src import styles
from src.components.nav_rail import create_nav_rail
from src.components.sidebar import create_sidebar
from src.components.main_panel import create_main_panel

def main(page: ft.Page):
    page.title = "ITT OCR Client - Image to Text"
    page.bgcolor = styles.BG_APP
    page.padding = 0
    page.window.min_width = 1100
    page.window.min_height = 700
    page.window.width = 1380
    page.window.height = 860

    # Handlers for initial scaffolding
    def on_browse(e):
        pass

    def on_process(e):
        pass

    # Root Landscape View
    root_layout = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            create_nav_rail(),
            ft.Container(
                expand=True,
                padding=ft.Padding.all(20),
                content=ft.Row(
                    expand=True,
                    spacing=20,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        create_sidebar(on_browse_click=on_browse, on_process_click=on_process),
                        create_main_panel(),
                    ],
                ),
            ),
        ],
    )

    page.add(root_layout)

if __name__ == "__main__":
    ft.app(target=main)
