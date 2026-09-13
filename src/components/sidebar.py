import flet as ft
from src.styles import theme, RADIUS_PANEL, FONT_FAMILY_UI, safe_update, unfreeze, secondary_button_style
from src.app_state import state, QueueItem

class Sidebar(ft.Container):
    def __init__(
        self,
        on_browse_click=None,
        on_scan_click=None,
        on_paste_click=None,
        on_run_all_click=None,
    ):
        self.on_browse_click = on_browse_click
        self.on_scan_click = on_scan_click
        self.on_paste_click = on_paste_click
        self.on_run_all_click = on_run_all_click
        self.is_collapsed = False
        self.search_filter = ""

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

        self.run_all_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE_ROUNDED,
            icon_size=17,
            icon_color=theme.accent,
            tooltip="Extract all pending (batch)",
            on_click=self._on_run_all_click,
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
                ft.Row(
                    spacing=2,
                    controls=[
                        self.run_all_btn,
                        self.clear_btn,
                    ],
                ),
            ],
        )

        # Ingestion Dropzone
        self.dropzone_text = ft.Text(
            "Drop image or PDF",
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

        self.browse_icon = ft.Icon(ft.Icons.FOLDER_OPEN_OUTLINED, size=13, color=theme.text_primary)
        self.browse_text = ft.Text("Browse", size=11, weight=ft.FontWeight.W_500, color=theme.text_primary)
        self.browse_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
                controls=[self.browse_icon, self.browse_text],
            ),
            style=secondary_button_style(),
            expand=True,
            on_click=self.on_browse_click,
            tooltip="Browse image files (Ctrl+O)",
        )

        self.scan_icon = ft.Icon(ft.Icons.DOCUMENT_SCANNER_ROUNDED, size=13, color=theme.text_primary)
        self.scan_text = ft.Text("Scan", size=11, weight=ft.FontWeight.W_500, color=theme.text_primary)
        self.scan_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
                controls=[self.scan_icon, self.scan_text],
            ),
            style=secondary_button_style(),
            expand=True,
            on_click=self.on_scan_click,
            tooltip="Scan from hardware device",
        )

        self.paste_icon = ft.Icon(ft.Icons.CONTENT_PASTE_ROUNDED, size=13, color=theme.text_primary)
        self.paste_text = ft.Text("Paste", size=11, weight=ft.FontWeight.W_500, color=theme.text_primary)
        self.paste_btn = ft.OutlinedButton(
            content=ft.Row(
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
                controls=[self.paste_icon, self.paste_text],
            ),
            style=secondary_button_style(),
            expand=True,
            on_click=self.on_paste_click,
            tooltip="Paste image from clipboard (Ctrl+V)",
        )

        self.dropzone_container = ft.Container(
            bgcolor=theme.inset,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=12,
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
                        spacing=6,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[self.browse_btn, self.scan_btn, self.paste_btn],
                    ),
                ],
            ),
        )

        # Search filter field
        self.search_field = ft.TextField(
            hint_text="Search history...",
            hint_style=ft.TextStyle(size=12, color=theme.text_secondary, font_family=FONT_FAMILY_UI),
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            dense=True,
            text_size=12,
            border_color=theme.border,
            focused_border_color=theme.accent,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            on_change=self._on_search_changed,
        )

        # Queue list column
        self.queue_list_column = ft.Column(
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.body_content = ft.Column(
            spacing=10,
            expand=True,
            controls=[
                header_row,
                self.dropzone_container,
                self.search_field,
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

    def _on_run_all_click(self, e):
        # While a batch is running this button becomes Stop.
        if state.is_processing_all:
            state.is_processing_all = False
            state.notify()
        elif self.on_run_all_click:
            self.on_run_all_click(e)

    def _render_item(self, item: QueueItem) -> ft.Container:
        is_selected = (state.selected_item_id == item.id)

        if item.status == "Done":
            status_color = theme.success
            status_label = "Done"
        elif item.status == "Processing":
            status_color = theme.accent
            status_label = "Processing"
        elif item.status == "Failed":
            status_color = theme.error
            status_label = "Failed"
        else:
            status_color = theme.text_secondary
            status_label = "Ready"

        source_icon = ft.Icons.CONTENT_PASTE_ROUNDED if item.source == "clipboard" else (
            ft.Icons.DOCUMENT_SCANNER_ROUNDED if item.source == "scanner" else ft.Icons.IMAGE_OUTLINED
        )

        item_container = ft.Container(
            bgcolor=theme.inset if is_selected else theme.surface,
            border=ft.Border.all(1.5 if is_selected else 1, theme.accent if is_selected else theme.border),
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
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(source_icon, size=11, color=theme.text_secondary),
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

    def _on_search_changed(self, e):
        self.search_filter = (e.control.value or "").strip().lower()
        self.update_queue_ui()

    def update_queue_ui(self):
        all_items = state.queue
        count = len(all_items)
        self.count_text.value = f"{count} item{'s' if count != 1 else ''}"

        # Batch affordance: play becomes stop while a batch is running.
        if state.is_processing_all:
            self.run_all_btn.icon = ft.Icons.STOP_CIRCLE_OUTLINED
            self.run_all_btn.tooltip = "Stop batch extraction"
        else:
            self.run_all_btn.icon = ft.Icons.PLAY_CIRCLE_OUTLINE_ROUNDED
            self.run_all_btn.tooltip = "Extract all pending (batch)"

        # Apply search filter
        if self.search_filter:
            display_items = [
                item for item in all_items
                if self.search_filter in item.file_name.lower()
                or self.search_filter in (item.extracted_text or "").lower()
            ]
        else:
            display_items = all_items

        self.queue_list_column.controls.clear()
        if not display_items:
            empty_msg = "No matching documents found" if self.search_filter else "No documents in history"
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
                                empty_msg,
                                size=12,
                                weight=ft.FontWeight.W_500,
                                color=theme.text_secondary,
                                font_family=FONT_FAMILY_UI,
                            ),
                            ft.Text(
                                "Use Browse, Scan or Paste above to add your first document.",
                                size=11,
                                color=theme.text_secondary,
                                text_align=ft.TextAlign.CENTER,
                                font_family=FONT_FAMILY_UI,
                            ),
                        ],
                    ),
                )
            )
        else:
            for item in display_items:
                self.queue_list_column.controls.append(self._render_item(item))

        safe_update(self)

    def update_theme_ui(self):
        unfreeze(self)
        self.bgcolor = theme.surface
        self.border = ft.Border.all(1, theme.border)
        self.title_text.color = theme.text_primary
        self.count_text.color = theme.text_secondary
        self.run_all_btn.icon_color = theme.accent
        self.clear_btn.icon_color = theme.text_secondary
        self.dropzone_text.color = theme.text_primary
        self.dropzone_subtext.color = theme.text_secondary
        self.dropzone_container.bgcolor = theme.inset
        self.dropzone_container.border = ft.Border.all(1, theme.border)

        self.browse_btn.style = secondary_button_style()
        self.browse_icon.color = theme.text_primary
        self.browse_text.color = theme.text_primary

        self.scan_btn.style = secondary_button_style()
        self.scan_icon.color = theme.text_primary
        self.scan_text.color = theme.text_primary

        self.paste_btn.style = secondary_button_style()
        self.paste_icon.color = theme.text_primary
        self.paste_text.color = theme.text_primary

        self.search_field.border_color = theme.border
        self.search_field.focused_border_color = theme.accent
        self.search_field.hint_style = ft.TextStyle(
            size=12,
            color=theme.text_secondary,
            font_family=FONT_FAMILY_UI,
        )

        self.update_queue_ui()

def create_sidebar(
    on_browse_click=None,
    on_scan_click=None,
    on_paste_click=None,
    on_run_all_click=None,
):
    return Sidebar(
        on_browse_click=on_browse_click,
        on_scan_click=on_scan_click,
        on_paste_click=on_paste_click,
        on_run_all_click=on_run_all_click,
    )
