import flet as ft
from typing import Callable, List

# Design Tokens strictly matching specification
# Light mode tokens
LIGHT_BG = "#FAFAF9"
LIGHT_SURFACE = "#FFFFFF"
LIGHT_BORDER = "#E4E4E1"
LIGHT_TEXT_PRIMARY = "#1C1C1A"
LIGHT_TEXT_SECONDARY = "#6B6B66"
LIGHT_ACCENT = "#2F6FED"

# Light mode glass spec (using 0xAARRGGBB hex for robust Flutter parsing)
# background: rgba(255, 255, 255, 0.72) -> #B8FFFFFF
# border: 1px solid rgba(255, 255, 255, 0.4) -> #66FFFFFF or clean hairline #E4E4E1
# box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08) -> #14000000
LIGHT_GLASS_BG = "#B8FFFFFF"
LIGHT_GLASS_BORDER = "#E4E4E1"
LIGHT_GLASS_SHADOW_COLOR = "#14000000"

# Dark mode tokens
DARK_BG = "#121212"
DARK_SURFACE = "#1B1B1B"
DARK_BORDER = "#2E2E2C"
DARK_TEXT_PRIMARY = "#F2F2EF"
DARK_TEXT_SECONDARY = "#9A9A94"
DARK_ACCENT = "#5B8DEF"

# Dark mode glass spec
# background: rgba(24, 24, 24, 0.6) -> #99181818
# border: 1px solid rgba(255, 255, 255, 0.08) -> #14FFFFFF
# box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) -> #66000000
DARK_GLASS_BG = "#99181818"
DARK_GLASS_BORDER = "#2E2E2C"
DARK_GLASS_SHADOW_COLOR = "#66000000"

# Shared Radii Hierarchy
# Larger radius (16-20px) on floating glass elements
RADIUS_GLASS = 18
# Smaller radius (4-8px) on flat structural panels
RADIUS_PANEL = 6

# Typography tokens
FONT_FAMILY_UI = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
FONT_FAMILY_MONO = "'JetBrains Mono', 'IBM Plex Mono', Menlo, Consolas, monospace"

class ThemeState:
    def __init__(self):
        self.is_dark: bool = False
        self.reduced_motion: bool = False
        self._listeners: List[Callable[[], None]] = []

    def add_listener(self, listener: Callable[[], None]):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def notify(self):
        for listener in self._listeners:
            try:
                listener()
            except Exception as ex:
                print(f"Error in theme listener: {ex}")

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.notify()

    def set_reduced_motion(self, enabled: bool):
        self.reduced_motion = enabled
        self.notify()

    # Active dynamic tokens
    @property
    def bg(self) -> str:
        return DARK_BG if self.is_dark else LIGHT_BG

    @property
    def surface(self) -> str:
        return DARK_SURFACE if self.is_dark else LIGHT_SURFACE

    @property
    def border(self) -> str:
        return DARK_BORDER if self.is_dark else LIGHT_BORDER

    @property
    def text_primary(self) -> str:
        return DARK_TEXT_PRIMARY if self.is_dark else LIGHT_TEXT_PRIMARY

    @property
    def text_secondary(self) -> str:
        return DARK_TEXT_SECONDARY if self.is_dark else LIGHT_TEXT_SECONDARY

    @property
    def accent(self) -> str:
        return DARK_ACCENT if self.is_dark else LIGHT_ACCENT

    @property
    def glass_bg(self) -> str:
        return DARK_GLASS_BG if self.is_dark else LIGHT_GLASS_BG

    @property
    def glass_border_color(self) -> str:
        return DARK_GLASS_BORDER if self.is_dark else LIGHT_GLASS_BORDER

    @property
    def glass_border(self) -> ft.Border:
        return ft.Border.all(1, self.glass_border_color)

    @property
    def glass_blur(self) -> ft.Blur:
        return ft.Blur(20, 20)

    @property
    def glass_shadow(self) -> List[ft.BoxShadow]:
        color = DARK_GLASS_SHADOW_COLOR if self.is_dark else LIGHT_GLASS_SHADOW_COLOR
        blur_rad = 32 if self.is_dark else 20
        offset_y = 8 if self.is_dark else 4
        return [
            ft.BoxShadow(
                spread_radius=0,
                blur_radius=blur_rad,
                color=color,
                offset=ft.Offset(0, offset_y),
            )
        ]

theme = ThemeState()

# Compatibility constants
BG_APP = LIGHT_BG
BG_PANEL = LIGHT_SURFACE
BORDER_COLOR = LIGHT_BORDER
TEXT_PRIMARY = LIGHT_TEXT_PRIMARY
TEXT_SECONDARY = LIGHT_TEXT_SECONDARY
ACCENT = LIGHT_ACCENT
