import os
import math
import asyncio
import flet as ft
from PIL import Image
from src.styles import theme, RADIUS_PANEL, RADIUS_GLASS, FONT_FAMILY_UI, FONT_FAMILY_MONO, safe_update, unfreeze
from src.app_state import state

def detect_paper_bounds(file_path: str) -> dict:
    """
    Lightweight PIL luminance scan to find paper boundaries [y_min, y_max].
    Runs in < 5ms.
    """
    try:
        with Image.open(file_path) as img:
            thumb = img.convert("L").resize((64, 64))
            pixels = list(thumb.get_flattened_data() if hasattr(thumb, "get_flattened_data") else thumb.getdata())
            w, h = 64, 64
            row_lums = [sum(pixels[y * w : (y + 1) * w]) / w for y in range(h)]
            min_lum = min(row_lums)
            max_lum = max(row_lums)
            if max_lum - min_lum > 30:
                thresh = min_lum + (max_lum - min_lum) * 0.40
                bright_rows = [y for y, lum in enumerate(row_lums) if lum >= thresh]
                if bright_rows and len(bright_rows) >= 8:
                    y_min = max(0.02, bright_rows[0] / 64.0)
                    y_max = min(0.96, bright_rows[-1] / 64.0)
                    return {"ymin": y_min, "ymax": y_max}
            return {"ymin": 0.06, "ymax": 0.92}
    except Exception:
        return {"ymin": 0.06, "ymax": 0.92}

class PreviewPanel(ft.Container):
    def __init__(self, on_scan_click=None):
        self.on_scan_click = on_scan_click
        self.rotation_degrees = 0
        self.is_scanning_anim = False
        self._sweep_task = None
        self._paper_bounds_cache = {}

        # Image control (fills aspect-ratio viewport perfectly)
        self.image_control = ft.Image(
            src="",
            fit=ft.BoxFit.FILL,
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

        # Synchronized Audit Focus Guide overlay
        self.audit_badge_text = ft.Text(
            "LINE 01",
            size=10,
            weight=ft.FontWeight.W_600,
            color=theme.accent,
            font_family=FONT_FAMILY_MONO,
        )
        self.audit_badge = ft.Container(
            content=self.audit_badge_text,
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.accent),
            border_radius=3,
            padding=ft.Padding.symmetric(horizontal=5, vertical=1),
        )
        self.audit_focus_box = ft.Container(
            height=46,
            margin=ft.Margin.symmetric(horizontal=12),
            border_radius=RADIUS_PANEL,
            border=ft.Border.all(1.5, theme.accent),
            bgcolor="rgba(37, 99, 235, 0.10)" if not theme.is_dark else "rgba(75, 136, 240, 0.16)",
            padding=ft.Padding.only(left=8, top=4),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[self.audit_badge],
            ),
        )
        self.audit_overlay_container = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, -0.90),
            animate_align=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            content=self.audit_focus_box,
            visible=False,
        )

        # Image Viewport (constrained strictly to image aspect ratio, zero letterbox drift)
        self.image_viewport = ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Stack(
                expand=True,
                controls=[
                    self.image_control,
                    self.audit_overlay_container,
                ],
            ),
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

        # Inner Canvas Container (uses theme.inset: #F4F4F0 in Light mode, #141414 in Dark mode)
        self.inner_canvas = ft.Container(
            expand=True,
            bgcolor=theme.inset,
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

    def _get_cached_paper_bounds(self, file_path: str) -> dict:
        if file_path in self._paper_bounds_cache:
            return self._paper_bounds_cache[file_path]
        bounds = detect_paper_bounds(file_path)
        self._paper_bounds_cache[file_path] = bounds
        return bounds

    def update_audit_guide(self):
        item = state.selected_item
        has_image = bool(item and item.file_path and os.path.exists(item.file_path))
        if not state.audit_mode or not has_image or state.total_blocks_count <= 0:
            if self.audit_overlay_container.visible:
                self.audit_overlay_container.visible = False
                safe_update(self.audit_overlay_container)
            return

        self.audit_overlay_container.visible = True
        n = state.total_blocks_count
        k = min(n - 1, max(0, state.active_block_index))

        boxes = getattr(item, "block_boxes", None)
        if boxes and k < len(boxes) and isinstance(boxes[k], dict):
            box = boxes[k]
            ymin = box.get("ymin", 0)
            ymax = box.get("ymax", 1000)
            xmin = box.get("xmin", 0)
            xmax = box.get("xmax", 1000)

            cy = (ymin + ymax) / 2000.0
            cx = (xmin + xmax) / 2000.0
            align_y = -1.0 + (2.0 * cy)
            align_x = -1.0 + (2.0 * cx)

            self.audit_overlay_container.alignment = ft.Alignment(align_x, align_y)
            self.audit_focus_box.height = max(36, int((ymax - ymin) / 1000.0 * 500))
        else:
            paper = self._get_cached_paper_bounds(item.file_path)
            y_start = paper.get("ymin", 0.08)
            y_end = paper.get("ymax", 0.90)

            if n > 1:
                fraction = k / (n - 1)
                paper_norm_y = y_start + fraction * (y_end - y_start)
            else:
                paper_norm_y = (y_start + y_end) / 2.0

            align_y = -1.0 + (2.0 * paper_norm_y)
            self.audit_overlay_container.alignment = ft.Alignment(0, align_y)
            self.audit_focus_box.height = 46

        self.audit_badge_text.value = f"LINE {k + 1:02d}"
        safe_update(self.audit_overlay_container)

    def update_preview(self):
        item = state.selected_item
        if not item:
            self.doc_meta.value = "No document loaded"
            self.canvas_content.content = self.empty_placeholder
            self.floating_toolbar.visible = False
            self.stop_scan_animation()
            self.update_audit_guide()
            safe_update(self)
            return

        self.doc_meta.value = f"{item.file_name} ({item.file_size_str})"
        if os.path.exists(item.file_path):
            self.image_control.src = item.file_path
            ar = None
            try:
                with Image.open(item.file_path) as img:
                    if img.height > 0:
                        ar = img.width / img.height
            except Exception:
                pass

            self.image_viewport.aspect_ratio = ar
            self.canvas_content.content = self.image_viewport
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

        self.update_audit_guide()
        safe_update(self)

    def update_theme_ui(self):
        unfreeze(self)
        self.bgcolor = theme.surface
        self.border = ft.Border.all(1, theme.border)
        self.inner_canvas.bgcolor = theme.inset
        self.inner_canvas.border = ft.Border.all(1, theme.border)
        self.empty_icon_box.bgcolor = theme.surface
        self.empty_icon_box.border = ft.Border.all(1, theme.border)
        self.empty_icon.color = theme.text_secondary
        self.empty_text.color = theme.text_secondary

        self.doc_title.color = theme.text_primary
        self.doc_meta.color = theme.text_secondary
        self.scan_line.bgcolor = theme.accent

        self.audit_focus_box.border = ft.Border.all(1.5, theme.accent)
        self.audit_focus_box.bgcolor = "rgba(37, 99, 235, 0.10)" if not theme.is_dark else "rgba(75, 136, 240, 0.16)"
        self.audit_badge.bgcolor = theme.surface
        self.audit_badge.border = ft.Border.all(1, theme.accent)
        self.audit_badge_text.color = theme.accent
        self.update_audit_guide()

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
