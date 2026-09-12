import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

def get_clipboard_image() -> Optional[str]:
    """
    Grabs an image from the system clipboard if present.
    Saves to a local temporary file and returns its absolute path.
    Returns None if the clipboard does not contain image data.
    """
    temp_dir = Path(tempfile.gettempdir()) / "itt_ocr_scans"
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_file = temp_dir / f"clip_{int(time.time() * 1000)}.png"

    # 1. Try Pillow ImageGrab (fast in-memory extraction)
    try:
        from PIL import ImageGrab, Image
        grabbed = ImageGrab.grabclipboard()
        if isinstance(grabbed, Image.Image):
            grabbed.save(str(out_file), "PNG")
            if out_file.exists():
                return str(out_file)
        elif isinstance(grabbed, list) and grabbed:
            first_path = str(grabbed[0])
            if os.path.exists(first_path) and first_path.lower().endswith(
                (".png", ".jpg", ".jpeg", ".webp", ".bmp")
            ):
                return first_path
    except Exception:
        pass

    # 2. Windows Fallback: Native .NET System.Windows.Forms.Clipboard
    if sys.platform.startswith("win"):
        target_path = str(out_file).replace("\\", "\\\\")
        ps_script = f"""
        Add-Type -AssemblyName System.Windows.Forms
        $clip = [System.Windows.Forms.Clipboard]::GetImage()
        if ($clip -ne $null) {{
            $dest = '{target_path}'
            $clip.Save($dest, [System.Drawing.Imaging.ImageFormat]::Png)
            [Console]::Out.WriteLine("SUCCESS")
        }} else {{
            [Console]::Out.WriteLine("NO_IMAGE")
        }}
        """
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if "SUCCESS" in res.stdout and out_file.exists():
                return str(out_file)
        except Exception:
            pass

    # 3. Linux Fallback: wl-paste (Wayland) or xclip (X11)
    else:
        # Check Wayland wl-paste
        try:
            res = subprocess.run(
                ["wl-paste", "--type", "image/png"],
                capture_output=True,
                timeout=5,
            )
            if res.returncode == 0 and len(res.stdout) > 50:
                with open(out_file, "wb") as f:
                    f.write(res.stdout)
                return str(out_file)
        except Exception:
            pass

        # Check X11 xclip
        try:
            res = subprocess.run(
                ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
                capture_output=True,
                timeout=5,
            )
            if res.returncode == 0 and len(res.stdout) > 50:
                with open(out_file, "wb") as f:
                    f.write(res.stdout)
                return str(out_file)
        except Exception:
            pass

    return None


def _copy_win_ctypes(text: str) -> bool:
    """Copies UTF-16 Unicode text to Windows clipboard using standard Win32 API via ctypes."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        if not user32.OpenClipboard(None):
            return False
        try:
            user32.EmptyClipboard()
            encoded = text.encode("utf-16-le") + b"\x00\x00"
            h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
            if not h_mem:
                return False
            ptr = kernel32.GlobalLock(h_mem)
            if not ptr:
                kernel32.GlobalFree(h_mem)
                return False
            ctypes.memmove(ptr, encoded, len(encoded))
            kernel32.GlobalUnlock(h_mem)
            if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
                kernel32.GlobalFree(h_mem)
                return False
            return True
        finally:
            user32.CloseClipboard()
    except Exception:
        return False


def _copy_win_powershell(text: str) -> bool:
    """PowerShell fallback for setting clipboard on Windows."""
    try:
        cmd = (
            "$OutputEncoding = [Console]::InputEncoding = [System.Text.Encoding]::UTF8; "
            "[Console]::In.ReadToEnd() | Set-Clipboard"
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-STA", "-Command", cmd],
            input=text.encode("utf-8"),
            creationflags=0x08000000 if sys.platform.startswith("win") else 0,
            check=False,
            timeout=5,
        )
        return res.returncode == 0
    except Exception:
        return False


def _copy_linux(text: str) -> bool:
    """Copies text to Linux clipboard trying Wayland (wl-copy) then X11 (xclip, xsel)."""
    # 1. Wayland
    try:
        res = subprocess.run(
            ["wl-copy"],
            input=text.encode("utf-8"),
            check=False,
            timeout=5,
        )
        if res.returncode == 0:
            return True
    except Exception:
        pass

    # 2. X11 xclip
    try:
        res = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode("utf-8"),
            check=False,
            timeout=5,
        )
        if res.returncode == 0:
            return True
    except Exception:
        pass

    # 3. X11 xsel
    try:
        res = subprocess.run(
            ["xsel", "-b", "-i"],
            input=text.encode("utf-8"),
            check=False,
            timeout=5,
        )
        if res.returncode == 0:
            return True
    except Exception:
        pass

    return False


def _copy_macos(text: str) -> bool:
    """Copies text to macOS clipboard using pbcopy."""
    try:
        res = subprocess.run(
            ["pbcopy"],
            input=text.encode("utf-8"),
            check=False,
            timeout=5,
        )
        return res.returncode == 0
    except Exception:
        return False


def copy_text_to_clipboard(text: str, page: Optional[object] = None) -> bool:
    """
    Copies text to the system clipboard across platforms (Windows, Linux, macOS)
    with safe Unicode encoding for Bengali and other non-ASCII scripts.

    Order of evaluation:
    1. pyperclip (cross-platform standard)
    2. Native Win32 API via ctypes (Windows UTF-16, zero dependencies)
    3. PowerShell Set-Clipboard (Windows fallback)
    4. wl-copy / xclip / xsel (Linux Wayland / X11)
    5. pbcopy (macOS)
    6. Synchronizes with Flet page.clipboard service if page is provided.
    """
    if not text:
        return False

    success = False

    # 1. pyperclip
    try:
        import pyperclip
        pyperclip.copy(text)
        success = True
    except Exception:
        pass

    # 2. Windows ctypes fallback
    if not success and sys.platform.startswith("win"):
        success = _copy_win_ctypes(text)
        if not success:
            success = _copy_win_powershell(text)

    # 3. Linux fallback
    if not success and not sys.platform.startswith(("win", "darwin")):
        success = _copy_linux(text)

    # 4. macOS fallback
    if not success and sys.platform == "darwin":
        success = _copy_macos(text)

    # 5. Flet internal service sync
    if page:
        try:
            if hasattr(page, "run_task") and hasattr(page, "clipboard"):
                page.run_task(page.clipboard.set, text)
            elif hasattr(page, "set_clipboard"):
                page.set_clipboard(text)
        except Exception:
            pass

    return success

