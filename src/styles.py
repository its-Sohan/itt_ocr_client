import flet as ft
from typing import Callable, List, Any

# Design Tokens strictly matching specification
# Light mode tokens - Architectural Studio / Swiss precision
# Background: Grounded neutral desktop surface (#ECECE8)
# Surface: Pure elevated white workspace panels (#FFFFFF)
# Inset: Subtle recessed working canvas for document preview & text (#F4F4F0)
# Border: Crisp engineered 1px hairline (#CFCFC9) with clear visual definition
LIGHT_BG = "#ECECE8"
LIGHT_SURFACE = "#FFFFFF"
LIGHT_INSET = "#F4F4F0"
LIGHT_BORDER = "#CFCFC9"
LIGHT_BORDER_SUBTLE = "#DFDFD9"
LIGHT_BUTTON_BG = "#F7F7F5"
LIGHT_TEXT_PRIMARY = "#141412"
LIGHT_TEXT_SECONDARY = "#565650"
LIGHT_ACCENT = "#2563EB"

# Light mode glass spec
LIGHT_GLASS_BG = "#E6FFFFFF"
LIGHT_GLASS_BORDER = "#CFCFC9"
LIGHT_GLASS_SHADOW_COLOR = "#15000000"

# Dark mode tokens - Deep technical workspace
# Background: Deep charcoal desk (#111111)
# Surface: Elevated carbon panels (#1E1E1E)
# Inset: Recessed deep canvas (#141414)
# Border: Crisp separation border (#383835)
DARK_BG = "#111111"
DARK_SURFACE = "#1E1E1E"
DARK_INSET = "#141414"
DARK_BORDER = "#383835"
DARK_BORDER_SUBTLE = "#282826"
DARK_BUTTON_BG = "#262626"
DARK_TEXT_PRIMARY = "#F4F4F0"
DARK_TEXT_SECONDARY = "#A2A29C"
DARK_ACCENT = "#4B88F0"

# Dark mode glass spec
DARK_GLASS_BG = "#B31E1E1E"
DARK_GLASS_BORDER = "#383835"
DARK_GLASS_SHADOW_COLOR = "#70000000"

# Shared Radii Hierarchy
# Larger radius (16-20px) on floating glass elements
RADIUS_GLASS = 18
# Smaller radius (4-8px) on flat structural panels
RADIUS_PANEL = 6

import unicodedata

# Typography tokens
FONT_FAMILY_UI = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
FONT_FAMILY_MONO = "'JetBrains Mono', 'IBM Plex Mono', Menlo, Consolas, monospace"
FONT_FAMILY_BENGALI = "Kalpurush, 'Noto Sans Bengali', sans-serif"

def contains_bengali(text: str) -> bool:
    """Detects whether string contains any Bengali Unicode codepoints (U+0980 - U+09FF)."""
    if not text:
        return False
    return any('\u0980' <= ch <= '\u09FF' for ch in text)

def safe_bengali_normalize(text: str) -> str:
    """
    Applies Unicode NFC normalization to ensure complex Bengali conjuncts (যুক্তাক্ষর)
    and vowel signs (কার) remain canonically composed without decomposition or rendering corruption.
    """
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)

def unfreeze(obj: Any, visited=None) -> Any:
    """
    Recursively removes _frozen marker from an object, its children, and Prop-managed value objects
    to prevent Flet 0.86+ 'RuntimeError: Frozen controls cannot be updated.'
    """
    if obj is None:
        return obj
    if visited is None:
        visited = set()
    oid = id(obj)
    if oid in visited:
        return obj
    visited.add(oid)

    if hasattr(obj, "_frozen"):
        try:
            del obj._frozen
        except Exception:
            try:
                object.__delattr__(obj, "_frozen")
            except Exception:
                pass

    if hasattr(obj, "_values") and isinstance(obj._values, dict):
        for v in list(obj._values.values()):
            unfreeze(v, visited)

    if hasattr(obj, "__dict__"):
        for k, v in list(obj.__dict__.items()):
            if k not in ("_parent", "_page", "page", "session", "_Session__page") and not callable(v):
                unfreeze(v, visited)

    if hasattr(obj, "controls") and isinstance(obj.controls, list):
        for c in list(obj.controls):
            unfreeze(c, visited)

    if hasattr(obj, "content") and obj.content:
        unfreeze(obj.content, visited)

    return obj

def safe_update(control: Any):
    """Safely updates a Flet control, unfreezing if necessary and catching any errors."""
    if control is None:
        return
    try:
        unfreeze(control)
        control.update()
    except Exception:
        pass

class ThemeState:
    def __init__(self):
        self.is_dark: bool = False
        self.reduced_motion: bool = False
        self._listeners: List[Callable[[], None]] = []

    def add_listener(self, listener: Callable[[], None]):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def notify(self):
        for listener in list(self._listeners):
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
    def inset(self) -> str:
        return DARK_INSET if self.is_dark else LIGHT_INSET

    @property
    def border(self) -> str:
        return DARK_BORDER if self.is_dark else LIGHT_BORDER

    @property
    def border_subtle(self) -> str:
        return DARK_BORDER_SUBTLE if self.is_dark else LIGHT_BORDER_SUBTLE

    @property
    def button_bg(self) -> str:
        return DARK_BUTTON_BG if self.is_dark else LIGHT_BUTTON_BG

    @property
    def menu_bg(self) -> str:
        return "#262626" if self.is_dark else "#FFFFFF"

    @property
    def menu_border(self) -> str:
        return "#40403C" if self.is_dark else "#CFCFC9"

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
