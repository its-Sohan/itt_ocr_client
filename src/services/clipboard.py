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
