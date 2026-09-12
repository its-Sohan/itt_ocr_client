import flet as ft
from src import styles
from src.app_state import state, QueueItem

def create_badge(text: str, bg_color=styles.BG_SUBTLE, text_color=styles.TEXT_SECONDARY):
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=text_color),
        bgcolor=bg_color,
        border=ft.Border.all(1, styles.BORDER_COLOR),
        border_radius=4,
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
    )

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

class Sidebar(ft.Container):
    def __init__(self, on_browse_click=None, on_scan_click=None, on_process_click=None):
        super().__init__(
            width=390,
            bgcolor=styles.BG_PANEL,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=12,
            padding=20,
        )
        self.on_browse_click = on_browse_click
        self.on_scan_click = on_scan_click
        self.on_process_click = on_process_click

        # Swiss Header: Architectural hierarchy with small caps category label
        self.header = ft.Column(
            spacing=4,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(width=6, height=6, border_radius=3, bgcolor=styles.TEXT_PRIMARY),
                        ft.Text("DOCUMENT ACQUISITION", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                    ],
                ),
                ft.Text(
                    "Feed documents via scanner hardware or local file explorer into the processing queue.",
                    size=12,
                    color=styles.TEXT_SECONDARY,
                ),
            ],
        )

        # Tactical Dropzone: Dual primary actions with high-contrast buttons
        self.dropzone = ft.Container(
            height=160,
            bgcolor=styles.BG_SUBTLE,
            border=ft.Border.all(1, styles.BORDER_DASHED),
            border_radius=8,
            padding=16,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Text("DRAG & DROP OR CHOOSE SOURCE", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_SECONDARY),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.ElevatedButton(
                                content=ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, size=15, color=styles.BTN_PRIMARY_TEXT),
                                        ft.Text("BROWSE FILES", size=11, weight=ft.FontWeight.BOLD, color=styles.BTN_PRIMARY_TEXT),
                                    ],
                                ),
                                style=ft.ButtonStyle(
                                    bgcolor=styles.BTN_PRIMARY_BG,
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                    padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                                ),
                                on_click=self.on_browse_click,
                            ),
                            ft.OutlinedButton(
                                content=ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(ft.Icons.DOCUMENT_SCANNER_OUTLINED, size=15, color=styles.TEXT_PRIMARY),
                                        ft.Text("ACQUIRE SCAN", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_PRIMARY),
                                    ],
                                ),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                    padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                                    side=ft.BorderSide(1, styles.BORDER_COLOR),
                                ),
                                on_click=self.on_scan_click,
                            ),
                        ],
                    ),
                    ft.Text("PDF, PNG, JPG, BMP • Max 50MB", size=10, color=styles.TEXT_MUTED),
                ],
            ),
        )

        # Queue card header
        self.queue_count_badge = ft.Container(
            content=ft.Text("0 ITEMS", size=10, weight=ft.FontWeight.BOLD, color=styles.TEXT_SECONDARY),
            bgcolor=styles.BG_SUBTLE,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )
        self.queue_header_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(width=6, height=6, border_radius=3, bgcolor=styles.TEXT_SECONDARY),
                        ft.Text("QUEUE", size=11, weight=ft.FontWeight.BOLD, color=styles.TEXT_SECONDARY),
                    ],
                ),
                self.queue_count_badge,
            ],
        )

        # Dynamic Queue items column
        self.queue_list_column = ft.Column(
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Queue wrapper card
        self.queue_card = ft.Container(
            expand=True,
            bgcolor=styles.BG_SUBTLE,
            border=ft.Border.all(1, styles.BORDER_COLOR),
            border_radius=8,
            padding=12,
            content=ft.Column(
                expand=True,
                spacing=8,
                controls=[
                    self.queue_header_row,
                    ft.Divider(height=1, color=styles.BORDER_COLOR),
                    self.queue_list_column,
                ],
            ),
        )

        # Process button
        self.process_button_text = ft.Text("PROCESS QUEUE", size=13, weight=ft.FontWeight.BOLD, color=styles.BTN_PRIMARY_TEXT)
        self.process_progress = ft.ProgressRing(width=16, height=16, stroke_width=2, color=styles.BTN_PRIMARY_TEXT, visible=False)
        self.process_btn = ft.ElevatedButton(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    self.process_progress,
                    self.process_button_text,
                ],
            ),
            style=ft.ButtonStyle(
                bgcolor=styles.BTN_PRIMARY_BG,
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding.symmetric(vertical=16),
            ),
            on_click=self.on_process_click,
        )

        # Full layout
        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=14,
            controls=[
                self.header,
                self.dropzone,
                self.queue_card,
                ft.Container(
                    content=self.process_btn,
                    alignment=ft.Alignment.CENTER,
                ),
            ],
        )

        state.add_listener(self.update_queue_ui)
        self.update_queue_ui()

    def set_processing(self, is_processing: bool, text: str = "PROCESSING..."):
        self.process_progress.visible = is_processing
        self.process_button_text.value = text if is_processing else "PROCESS QUEUE"
        self.process_btn.disabled = is_processing
        safe_update(self)

    def _render_item_row(self, item: QueueItem) -> ft.Container:
        is_selected = (state.selected_item_id == item.id)

        # Status badge
        if item.status == "Done":
            status_badge = ft.Container(
                content=ft.Text("DONE", size=9, weight=ft.FontWeight.BOLD, color=styles.STATUS_SUCCESS_TEXT),
                bgcolor=styles.STATUS_SUCCESS_BG,
                border=ft.Border.all(1, styles.STATUS_SUCCESS_BORDER),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            )
        elif item.status == "Processing":
            status_badge = ft.Container(
                content=ft.Text("RUNNING", size=9, weight=ft.FontWeight.BOLD, color=styles.STATUS_PROC_TEXT),
                bgcolor=styles.STATUS_PROC_BG,
                border=ft.Border.all(1, styles.STATUS_PROC_BORDER),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            )
        elif item.status == "Failed":
            status_badge = ft.Container(
                content=ft.Text("ERROR", size=9, weight=ft.FontWeight.BOLD, color=styles.STATUS_ERR_TEXT),
                bgcolor=styles.STATUS_ERR_BG,
                border=ft.Border.all(1, styles.STATUS_ERR_BORDER),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            )
        else:
            status_badge = ft.Container(
                content=ft.Text("READY", size=9, weight=ft.FontWeight.BOLD, color=styles.TEXT_SECONDARY),
                bgcolor=styles.BG_PANEL,
                border=ft.Border.all(1, styles.BORDER_COLOR),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            )

        icon_type = ft.Icons.DOCUMENT_SCANNER_OUTLINED if item.source == "scanner" else ft.Icons.IMAGE_OUTLINED

        row_container = ft.Container(
            bgcolor=styles.BG_PANEL if is_selected else "transparent",
            border=ft.Border.all(1, styles.TEXT_PRIMARY if is_selected else styles.BORDER_COLOR),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            ink=True,
            on_click=lambda e, iid=item.id: state.select_item(iid),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                        controls=[
                            ft.Icon(icon_type, size=15, color=styles.TEXT_PRIMARY if is_selected else styles.TEXT_MUTED),
                            ft.Column(
                                spacing=1,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        item.file_name,
                                        size=12,
                                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_500,
                                        color=styles.TEXT_PRIMARY,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(f"{item.file_size_str} • {item.source.upper()}", size=10, color=styles.TEXT_MUTED),
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            status_badge,
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_size=13,
                                icon_color=styles.TEXT_MUTED,
                                tooltip="Remove",
                                on_click=lambda e, iid=item.id: state.remove_item(iid),
                            ),
                        ],
                    ),
                ],
            ),
        )
        return row_container

    def update_queue_ui(self):
        items_count = len(state.queue)
        self.queue_count_badge.content.value = f"{items_count} ITEM{'S' if items_count != 1 else ''}"

        self.queue_list_column.controls.clear()
        if not state.queue:
            self.queue_list_column.controls.append(
                ft.Container(
                    padding=24,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=24, color=styles.TEXT_MUTED),
                            ft.Text("QUEUE EMPTY", size=10, weight=ft.FontWeight.BOLD, color=styles.TEXT_MUTED),
                            ft.Text("Use browse or scan to queue documents", size=10, color=styles.TEXT_TERTIARY),
                        ],
                    ),
                )
            )
        else:
            for item in state.queue:
                self.queue_list_column.controls.append(self._render_item_row(item))

        safe_update(self)

def create_sidebar(on_browse_click=None, on_scan_click=None, on_process_click=None):
    return Sidebar(on_browse_click=on_browse_click, on_scan_click=on_scan_click, on_process_click=on_process_click)
