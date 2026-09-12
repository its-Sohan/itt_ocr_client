import flet as ft
from src.styles import theme, RADIUS_GLASS, RADIUS_PANEL, FONT_FAMILY_UI
from src.config_store import load_config

def safe_update(control: ft.Control):
    try:
        control.update()
    except Exception:
        pass

class TopBar(ft.Container):
    def __init__(
        self,
        on_toggle_history=None,
        on_command_palette=None,
        on_settings=None,
        on_dashboard=None,
    ):
        self.on_toggle_history = on_toggle_history
        self.on_command_palette = on_command_palette
        self.on_settings = on_settings
        self.on_dashboard = on_dashboard

        # Brand / Logo with European pixel art scan icon
        self.app_icon = ft.Image(
            src="assets/app_icon_dark.svg" if theme.is_dark else "assets/app_icon.svg",
            width=20,
            height=20,
            fit=ft.BoxFit.CONTAIN,
        )

        self.brand_text = ft.Text(
            "ITT OCR",
            size=15,
            weight=ft.FontWeight.W_600,
            color=theme.text_primary,
            font_family=FONT_FAMILY_UI,
        )

        config = load_config()
        model_name = config.get("model_name", "gpt-4o-mini")
        self.model_badge_text = ft.Text(
            model_name,
            size=12,
            weight=ft.FontWeight.W_500,
            color=theme.text_secondary,
            font_family=FONT_FAMILY_UI,
        )
        self.model_badge = ft.Container(
            content=self.model_badge_text,
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            tooltip="Active Vision Engine",
        )

        # Command Palette button
        self.cmd_icon = ft.Icon(ft.Icons.SEARCH_ROUNDED, size=14, color=theme.text_secondary)
        self.cmd_label = ft.Text(
            "Search commands...",
            size=12,
            weight=ft.FontWeight.W_400,
            color=theme.text_secondary,
            font_family=FONT_FAMILY_UI,
        )
        self.cmd_shortcut_text = ft.Text("Ctrl K", size=10, weight=ft.FontWeight.W_500, color=theme.text_secondary)
        self.cmd_shortcut_box = ft.Container(
            content=self.cmd_shortcut_text,
            bgcolor=theme.bg,
            border=ft.Border.all(1, theme.border),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )

        self.cmd_palette_btn = ft.Container(
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.cmd_icon,
                    self.cmd_label,
                    self.cmd_shortcut_box,
                ],
            ),
            bgcolor=theme.surface,
            border=ft.Border.all(1, theme.border),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            ink=True,
            on_click=self.on_command_palette,
            tooltip="Open command palette (Ctrl+K)",
        )

        # History toggle button
        self.history_btn = ft.IconButton(
            icon=ft.Icons.VIEW_SIDEBAR_OUTLINED,
            icon_color=theme.text_secondary,
            icon_size=18,
            tooltip="Toggle history rail",
            on_click=self.on_toggle_history,
        )

        # Dashboard button
        self.dashboard_btn = ft.IconButton(
            icon=ft.Icons.BAR_CHART_ROUNDED,
            icon_color=theme.text_secondary,
            icon_size=18,
            tooltip="Usage metrics",
            on_click=self.on_dashboard,
        )

        # Settings button
        self.settings_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            icon_color=theme.text_secondary,
            icon_size=18,
            tooltip="Settings and credentials",
            on_click=self.on_settings,
        )

        # Theme toggle button
        self.theme_btn = ft.IconButton(
            icon=ft.Icons.DARK_MODE_OUTLINED if not theme.is_dark else ft.Icons.LIGHT_MODE_OUTLINED,
            icon_color=theme.text_secondary,
            icon_size=18,
            tooltip="Toggle theme",
            on_click=self._toggle_theme,
        )

        inner_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Left cluster: Logo and model
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self.history_btn,
                        self.app_icon,
                        self.brand_text,
                        self.model_badge,
                    ],
                ),
                # Center: Command palette shortcut
                self.cmd_palette_btn,
                # Right cluster: actions and theme toggle
                ft.Row(
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self.dashboard_btn,
                        self.settings_btn,
                        self.theme_btn,
                    ],
                ),
            ],
        )

        super().__init__(
            content=inner_row,
            bgcolor=theme.glass_bg,
            blur=theme.glass_blur,
            border=theme.glass_border,
            border_radius=RADIUS_GLASS,
            shadow=theme.glass_shadow,
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            margin=ft.Margin(left=16, top=14, right=16, bottom=8),
            height=54,
        )

        theme.add_listener(self.update_theme_ui)

    def _toggle_theme(self, e):
        theme.toggle_theme()

    def update_theme_ui(self):
        self.bgcolor = theme.glass_bg
        self.border = theme.glass_border
        self.shadow = theme.glass_shadow
        self.brand_text.color = theme.text_primary
        self.app_icon.src = "assets/app_icon_dark.svg" if theme.is_dark else "assets/app_icon.svg"
        
        self.model_badge.bgcolor = theme.surface
        self.model_badge.border = ft.Border.all(1, theme.border)
        self.model_badge_text.color = theme.text_secondary

        self.cmd_palette_btn.bgcolor = theme.surface
        self.cmd_palette_btn.border = ft.Border.all(1, theme.border)
        self.cmd_icon.color = theme.text_secondary
        self.cmd_label.color = theme.text_secondary
        self.cmd_shortcut_box.bgcolor = theme.bg
        self.cmd_shortcut_box.border = ft.Border.all(1, theme.border)
        self.cmd_shortcut_text.color = theme.text_secondary

        self.history_btn.icon_color = theme.text_secondary
        self.dashboard_btn.icon_color = theme.text_secondary
        self.settings_btn.icon_color = theme.text_secondary
        self.theme_btn.icon = ft.Icons.DARK_MODE_OUTLINED if not theme.is_dark else ft.Icons.LIGHT_MODE_OUTLINED
        self.theme_btn.icon_color = theme.text_secondary

        config = load_config()
        self.model_badge_text.value = config.get("model_name", "gpt-4o-mini")

        safe_update(self)

def create_top_bar(on_toggle_history=None, on_command_palette=None, on_settings=None, on_dashboard=None):
    return TopBar(
        on_toggle_history=on_toggle_history,
        on_command_palette=on_command_palette,
        on_settings=on_settings,
        on_dashboard=on_dashboard,
    )
