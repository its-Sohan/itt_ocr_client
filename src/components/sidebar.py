import flet as ft
from src.styles import theme, RADIUS_PANEL, FONT_FAMILY_UI
from src.app_state import state, QueueItem

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

class Sidebar(ft.Container):
    def __init__(self, on_browse_click=None, on_scan_click=None):
        self.on_browse_click = on_browse_click
        self.on_scan_click = on_scan_click
        self.is_collapsed = False

        # Header
        self.title_text = ft.Text(
            "History",
            size=15,
            weight=ft.FontWeight.W_600,
            color=theme.text_primary,
            font_family=FONT_FAMILY_UI,
        )

        self.count_text = ft.Text(
            "0 items",
            size=12,
            weight=ft.FontWeight.W_400,
            color=theme.text_secondary,
            font_family=FONT_FAMILY_UI,
        )

        self.clear_btn = ft.IconButton(
            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
            icon_size=16,
            icon_color=theme.text_secondary,
            tooltip="Clear completed",
            on_click=lambda e: state.clear_completed(),
        )

        header_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[self.title_text, self.count_text],
                ),
                self.clear_btn,
            ],
        )

        # Ingestion Dropzone
        self.dropzone_text = ft.Text(
            "Drop an image or PDF here",
            size=13,
            weight=ft.FontWeight.W_500,
            color=theme.text_primary,
            font_family=FONT_FAMILY_UI,
        )
        self.dropzone_subtext = ft.Text(
            "PNG, JPG, WebP up to 50 MB",
            size=11,
            color=theme.text_secondary,
            font_family=FONT_FAMILY_UI,
        )

        self.browse_icon = ft.Icon(ft.Icons.FOLDER_OPEN_OUTLINED, size=14, color=theme.text_primary)
        self.browse_text = ft.Text("Browse files", size=12, weight=ft.FontWeight.W_500, color=theme.text_primary)
        self.browse_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[self.browse_icon, self.browse_text],
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                side=ft.BorderSide(1, theme.border),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                bgcolor=theme.surface,
            ),
            on_click=self.on_browse_click,
        )

        self.scan_icon = ft.Icon(ft.Icons.DOCUMENT_SCANNER_OUTLINED, size=14, color=theme.text_primary)
        self.scan_text = ft.Text("Scan document", size=12, weight=ft.FontWeight.W_500, color=theme.text_primary)
        self.scan_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[self.scan_icon, self.scan_text],
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=RADIUS_PANEL),
                side=ft.BorderSide(1, theme.border),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                bgcolor=theme.surface,
            ),
            on_click=self.on_scan_click,
        )

        self.dropzone_container = ft.Container(
            bgcolor=theme.bg,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=14,
            content=ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[self.dropzone_text, self.dropzone_subtext],
                    ),
                    ft.Row(
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[self.browse_btn, self.scan_btn],
                    ),
                ],
            ),
        )

        # Queue list column
        self.queue_list_column = ft.Column(
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.body_content = ft.Column(
            spacing=12,
            expand=True,
            controls=[
                header_row,
                self.dropzone_container,
                ft.Text(
                    "Documents",
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=theme.text_secondary,
                    font_family=FONT_FAMILY_UI,
                ),
                self.queue_list_column,
            ],
        )

        super().__init__(
            width=300,
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=14,
            content=self.body_content,
            visible=True,
        )

        state.add_listener(self.update_queue_ui)
        theme.add_listener(self.update_theme_ui)
        self.update_queue_ui()

    def toggle_collapse(self):
        self.visible = not self.visible
        safe_update(self)

    def _render_item(self, item: QueueItem) -> ft.Container:
        is_selected = (state.selected_item_id == item.id)

        if item.status == "Done":
            status_color = "#10B981" if not theme.is_dark else "#34D399"
            status_label = "Done"
        elif item.status == "Processing":
            status_color = theme.accent
            status_label = "Processing"
        elif item.status == "Failed":
            status_color = "#EF4444" if not theme.is_dark else "#F87171"
            status_label = "Failed"
        else:
            status_color = theme.text_secondary
            status_label = "Ready"

        item_container = ft.Container(
            bgcolor=theme.bg if is_selected else theme.surface,
            border=ft.Border.all(1, theme.accent if is_selected else theme.border),
            border_radius=RADIUS_PANEL,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            ink=True,
            on_click=lambda e, iid=item.id: state.select_item(iid),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(
                                item.file_name,
                                size=13,
                                weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.W_400,
                                color=theme.text_primary,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                font_family=FONT_FAMILY_UI,
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text(item.file_size_str, size=11, color=theme.text_secondary),
                                    ft.Text(status_label, size=11, weight=ft.FontWeight.W_500, color=status_color),
                                ],
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE_ROUNDED,
                        icon_size=14,
                        icon_color=theme.text_secondary,
                        tooltip="Remove",
                        on_click=lambda e, iid=item.id: state.remove_item(iid),
                    ),
                ],
            ),
        )
        return item_container

    def update_queue_ui(self):
        count = len(state.queue)
        self.count_text.value = f"{count} item{'s' if count != 1 else ''}"

        self.queue_list_column.controls.clear()
        if not state.queue:
            self.queue_list_column.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=20, color=theme.text_secondary),
                            ft.Text(
                                "No documents in history",
                                size=12,
                                weight=ft.FontWeight.W_500,
                                color=theme.text_secondary,
                                font_family=FONT_FAMILY_UI,
                            ),
                        ],
                    ),
                )
            )
        else:
            for item in state.queue:
                self.queue_list_column.controls.append(self._render_item(item))

        safe_update(self)

    def update_theme_ui(self):
        self.bgcolor = theme.surface
        self.border = ft.Border.all(1, theme.border)
        self.title_text.color = theme.text_primary
        self.count_text.color = theme.text_secondary
        self.clear_btn.icon_color = theme.text_secondary
        self.dropzone_text.color = theme.text_primary
        self.dropzone_subtext.color = theme.text_secondary
        self.dropzone_container.bgcolor = theme.bg
        self.dropzone_container.border = ft.Border.all(1, theme.border)

        self.browse_btn.style.bgcolor = theme.surface
        self.browse_btn.style.side = ft.BorderSide(1, theme.border)
        self.browse_icon.color = theme.text_primary
        self.browse_text.color = theme.text_primary

        self.scan_btn.style.bgcolor = theme.surface
        self.scan_btn.style.side = ft.BorderSide(1, theme.border)
        self.scan_icon.color = theme.text_primary
        self.scan_text.color = theme.text_primary

        self.update_queue_ui()

def create_sidebar(on_browse_click=None, on_scan_click=None):
    return Sidebar(on_browse_click=on_browse_click, on_scan_click=on_scan_click)
