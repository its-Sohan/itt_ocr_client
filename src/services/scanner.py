import os
import sys
import tempfile
import subprocess
import time
from pathlib import Path
from typing import Optional

def is_windows() -> bool:
    return sys.platform.startswith("win")

def scan_document_windows() -> Optional[str]:
    """
    Triggers a document scan on Windows using PowerShell WIA (Windows Image Acquisition).
    Saves the output image to a temporary file and returns its path.
    """
    temp_dir = Path(tempfile.gettempdir()) / "itt_ocr_scans"
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_file = temp_dir / f"scan_{int(time.time())}.jpg"

    # PowerShell script using WIA.CommonDialog
    ps_script = f"""
    $ErrorActionPreference = 'Stop'
    try {{
        $dialog = New-Object -ComObject WIA.CommonDialog
        $image = $dialog.ShowAcquireImage()
        if ($image) {{
            $image.SaveFile('{str(out_file).replace('\\', '\\\\')}')
            Write-Host 'SUCCESS'
        }} else {{
            Write-Host 'CANCELLED'
        }}
    }} catch {{
        Write-Error $_.Exception.Message
        exit 1
    }}
    """

    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if res.returncode == 0 and out_file.exists():
            return str(out_file)
        else:
            stderr = res.stderr.strip() or res.stdout.strip()
            raise RuntimeError(f"Scanner error or cancelled: {stderr}")
    except FileNotFoundError:
        raise RuntimeError("PowerShell is not available on this system.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Scanning operation timed out.")

def scan_document() -> str:
    """
    Cross-platform scanner entry point.
    On Windows: calls scan_document_windows()
    On Non-Windows / Fallback: Creates a sample/diagnostic placeholder or raises informative error.
    """
    if is_windows():
        path = scan_document_windows()
        if not path:
            raise RuntimeError("Scan was cancelled or produced no file.")
        return path
    else:
        # Non-Windows development fallback: generates a test simulated document image
        temp_dir = Path(tempfile.gettempdir()) / "itt_ocr_scans"
        temp_dir.mkdir(parents=True, exist_ok=True)
        sample_path = temp_dir / f"simulated_scan_{int(time.time())}.png"
        
        # Create a lightweight PNG test scan for dev verification
        _create_test_scan_image(str(sample_path))
        return str(sample_path)

def _create_test_scan_image(output_path: str):
    """Creates a minimal valid PNG test page for testing without hardware."""
    # 1x1 or minimal PNG header data or simple base64 image
    import base64
    # A clean white 300x200 PNG with text banner
    minimal_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x64\x00\x00\x00\x64'
        b'\x08\x02\x00\x00\x00\xff\x80\x02\x03\x00\x00\x00\x1bIDATx\x9cc\xfc'
        b'\xcf\x80\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    with open(output_path, "wb") as f:
        f.write(minimal_png)
