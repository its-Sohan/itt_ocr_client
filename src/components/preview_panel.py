import os
import math
import asyncio
import flet as ft
from src.styles import theme, RADIUS_PANEL, RADIUS_GLASS, FONT_FAMILY_UI
from src.app_state import state

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

class PreviewPanel(ft.Container):
    def __init__(self, on_scan_click=None):
        self.on_scan_click = on_scan_click
        self.rotation_degrees = 0
        self.is_scanning_anim = False
        self._sweep_task = None

        # Flat Document Canvas container
        self.image_control = ft.Image(
            src="",
            fit=ft.BoxFit.CONTAIN,
            border_radius=RADIUS_PANEL,
            rotate=ft.Rotate(angle=0),
        )

        # Empty state invitation
        self.empty_icon = ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, size=24, color=theme.text_secondary)
        self.empty_icon_box = ft.Container(
            width=52,
            height=52,
            border_radius=RADIUS_PANEL,
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            alignment=ft.Alignment.CENTER,
            content=self.empty_icon,
        )
        self.empty_text = ft.Text(
            "Drop an image or PDF here to extract its text.",
            size=13,
            weight=ft.FontWeight.W_400,
            color=theme.text_secondary,
            text_align=ft.TextAlign.CENTER,
            font_family=FONT_FAMILY_UI,
        )

        self.empty_placeholder = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                self.empty_icon_box,
                self.empty_text,
            ],
        )

        # Canvas content layer
        self.canvas_content = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=self.empty_placeholder,
        )

        # Signature Motion: Precision Scan-line
        self.scan_line = ft.Container(
            top=0,
            left=0,
            right=0,
            height=2,
            bgcolor=theme.accent,
            shadow=[
                ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=theme.accent,
                    offset=ft.Offset(0, 0),
                )
            ],
            visible=False,
        )

        # Floating Glass Toolbar (16px radius, 20px blur, translucent fill, glass shadow)
        self.rotate_btn = ft.IconButton(
            icon=ft.Icons.ROTATE_RIGHT_ROUNDED,
            icon_size=16,
            icon_color=theme.text_primary,
            tooltip="Rotate 90° clockwise",
            on_click=self.rotate_image,
        )
        self.reset_rotate_btn = ft.IconButton(
            icon=ft.Icons.REPLAY_ROUNDED,
            icon_size=16,
            icon_color=theme.text_secondary,
            tooltip="Reset rotation",
            on_click=self.reset_rotation,
        )
        self.rescan_btn = ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            icon_size=16,
            icon_color=theme.text_secondary,
            tooltip="Re-scan document",
            on_click=lambda e: self.on_scan_click(e) if self.on_scan_click else None,
        )
        self.fit_btn = ft.IconButton(
            icon=ft.Icons.ASPECT_RATIO_ROUNDED,
            icon_size=16,
            icon_color=theme.text_secondary,
            tooltip="Toggle image fit mode",
            on_click=self.toggle_fit,
        )

        self.toolbar_controls = ft.Row(
            spacing=2,
            controls=[
                self.rotate_btn,
                self.reset_rotate_btn,
                self.fit_btn,
                self.rescan_btn,
            ],
        )

        self.floating_toolbar = ft.Container(
            bottom=14,
            right=14,
            content=self.toolbar_controls,
            bgcolor=theme.glass_bg,
            blur=theme.glass_blur,
            border=theme.glass_border,
            border_radius=16,
            shadow=theme.glass_shadow,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            visible=False,
            animate_opacity=150,
        )

        # Document Canvas Stack
        self.canvas_stack = ft.Stack(
            expand=True,
            controls=[
                self.canvas_content,
                self.scan_line,
                self.floating_toolbar,
            ],
        )

        # Inner Canvas Container (uses theme.bg: #FAFAF9 in Light mode, #121212 in Dark mode)
        self.inner_canvas = ft.Container(
            expand=True,
            bgcolor=theme.bg,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=self.canvas_stack,
            on_hover=self._on_canvas_hover,
        )

        # Header metadata
        self.doc_title = ft.Text(
            "Document canvas",
            size=14,
            weight=ft.FontWeight.W_500,
            color=theme.text_primary,
            font_family=FONT_FAMILY_UI,
        )
        self.doc_meta = ft.Text(
            "No document loaded",
            size=12,
            color=theme.text_secondary,
            font_family=FONT_FAMILY_UI,
        )

        header_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[self.doc_title, self.doc_meta],
        )

        main_column = ft.Column(
            expand=True,
            spacing=10,
            controls=[
                header_row,
                self.inner_canvas,
            ],
        )

        super().__init__(
            expand=True,
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            border_radius=RADIUS_PANEL,
            padding=16,
            content=main_column,
        )

        state.add_listener(self.update_preview)
        theme.add_listener(self.update_theme_ui)
        self.update_preview()

    def _on_canvas_hover(self, e: ft.HoverEvent):
        if state.selected_item and os.path.exists(state.selected_item.file_path):
            self.floating_toolbar.visible = True
            safe_update(self.floating_toolbar)

    def rotate_image(self, e):
        self.rotation_degrees = (self.rotation_degrees + 90) % 360
        radians = self.rotation_degrees * (math.pi / 180.0)
        self.image_control.rotate = ft.Rotate(angle=radians)
        safe_update(self.image_control)

    def reset_rotation(self, e):
        self.rotation_degrees = 0
        self.image_control.rotate = ft.Rotate(angle=0)
        safe_update(self.image_control)

    def toggle_fit(self, e):
        if self.image_control.fit == ft.BoxFit.CONTAIN:
            self.image_control.fit = ft.BoxFit.FIT_WIDTH
        else:
            self.image_control.fit = ft.BoxFit.CONTAIN
        safe_update(self.image_control)

    def start_scan_animation(self):
        self.is_scanning_anim = True
        self.scan_line.visible = True
        safe_update(self.scan_line)

        if theme.reduced_motion:
            self.scan_line.top = 0
            safe_update(self.scan_line)
            return

        async def _sweep():
            pos = 0.0
            step = 0.02
            forward = True
            while self.is_scanning_anim:
                if forward:
                    pos += step
                    if pos >= 0.95:
                        forward = False
                else:
                    pos -= step
                    if pos <= 0.02:
                        forward = True
                
                self.scan_line.top = int(pos * 500)
                safe_update(self.scan_line)
                await asyncio.sleep(0.04)

        if self.page:
            self.page.run_task(_sweep)

    def stop_scan_animation(self):
        self.is_scanning_anim = False
        self.scan_line.visible = False
        safe_update(self.scan_line)

    def update_preview(self):
        item = state.selected_item
        if not item:
            self.doc_meta.value = "No document loaded"
            self.canvas_content.content = self.empty_placeholder
            self.floating_toolbar.visible = False
            self.stop_scan_animation()
            safe_update(self)
            return

        self.doc_meta.value = f"{item.file_name} ({item.file_size_str})"
        if os.path.exists(item.file_path):
            self.image_control.src = item.file_path
            self.canvas_content.content = self.image_control
            self.floating_toolbar.visible = True
        else:
            self.canvas_content.content = self.empty_placeholder
            self.floating_toolbar.visible = False

        if item.status == "Processing":
            if not self.is_scanning_anim:
                self.start_scan_animation()
        else:
            if self.is_scanning_anim:
                self.stop_scan_animation()

        safe_update(self)

    def update_theme_ui(self):
        self.bgcolor = theme.surface
        self.border = ft.Border.all(1, theme.border)
        self.inner_canvas.bgcolor = theme.bg
        self.inner_canvas.border = ft.Border.all(1, theme.border)
        self.empty_icon_box.bgcolor = theme.surface
        self.empty_icon_box.border = ft.Border.all(1, theme.border)
        self.empty_icon.color = theme.text_secondary
        self.empty_text.color = theme.text_secondary

        self.doc_title.color = theme.text_primary
        self.doc_meta.color = theme.text_secondary
        self.scan_line.bgcolor = theme.accent

        self.floating_toolbar.bgcolor = theme.glass_bg
        self.floating_toolbar.border = theme.glass_border
        self.floating_toolbar.shadow = theme.glass_shadow
        self.rotate_btn.icon_color = theme.text_primary
        self.reset_rotate_btn.icon_color = theme.text_secondary
        self.fit_btn.icon_color = theme.text_secondary
        self.rescan_btn.icon_color = theme.text_secondary
        safe_update(self)

def create_preview_panel(on_scan_click=None):
    return PreviewPanel(on_scan_click=on_scan_click)
