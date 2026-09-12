import os
import sys
import tempfile
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

def is_windows() -> bool:
    return sys.platform.startswith("win")

def scan_document_windows() -> Tuple[str, Optional[str]]:
    """
    Triggers a document scan on Windows using PowerShell WIA (Windows Image Acquisition).
    - AlwaysSelectDevice = $true: Prompts Windows to hand over scanner device options.
    - UseDevicePage = $true: Prompts Windows native scanner settings & preview page.
    Returns a tuple (status, result_path_or_message):
    - ("SUCCESS", path)
    - ("CANCELLED", None)
    - ("NO_DEVICE", message)
    - ("ERROR", error_message)
    """
    temp_dir = Path(tempfile.gettempdir()) / "itt_ocr_scans"
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_file = temp_dir / f"scan_{int(time.time())}.jpg"
    target_path = str(out_file).replace("\\", "\\\\")

    # WIA ShowAcquireImage(DeviceType, Intent, Bias, FormatID, AlwaysSelectDevice, UseDevicePage, CancelError)
    # DeviceType: 1 = Scanner, 0 = Unspecified (includes camera/phone/imaging)
    # Intent: 0 = Unspecified (user picks color/bw in prompt)
    # Bias: 131072 = MaximizeQuality
    # FormatID: {B96B3CAE-0728-11D3-9D7B-0000F81EF32E} = JPEG
    ps_script = f"""
    $ErrorActionPreference = 'Stop'
    try {{
        $dialog = New-Object -ComObject WIA.CommonDialog
        $jpgFormat = '{{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}}'
        $image = $null

        # Attempt 1: Look for dedicated scanner hardware with full Windows options prompt
        try {{
            $image = $dialog.ShowAcquireImage(1, 0, 131072, $jpgFormat, $true, $true, $false)
        }} catch {{
            $innerErr = $_.Exception.Message
            # Attempt 2: Fall back to any imaging hardware (document camera, camera, MTP device)
            try {{
                $image = $dialog.ShowAcquireImage(0, 0, 131072, $jpgFormat, $true, $true, $false)
            }} catch {{
                $fallbackErr = $_.Exception.Message
                if ($fallbackErr -match '0x80210015' -or $fallbackErr -match 'No WIA device' -or $fallbackErr -match 'selected type is available') {{
                    [Console]::Out.WriteLine('STATUS:NO_DEVICE:No WIA hardware scanner or imaging device is currently connected to Windows.')
                }} else {{
                    [Console]::Out.WriteLine("STATUS:ERROR:$fallbackErr")
                }}
                exit 0
            }}
        }}

        if ($image -ne $null) {{
            $dest = '{target_path}'
            if (Test-Path $dest) {{ Remove-Item -Force $dest }}
            $image.SaveFile($dest)
            [Console]::Out.WriteLine("STATUS:SUCCESS:$dest")
        }} else {{
            [Console]::Out.WriteLine('STATUS:CANCELLED:Scan prompt was cancelled.')
        }}
    }} catch {{
        $err = $_.Exception.Message
        if ($err -match '0x80210015' -or $err -match 'No WIA device' -or $err -match 'selected type is available') {{
            [Console]::Out.WriteLine('STATUS:NO_DEVICE:No WIA hardware scanner or imaging device is currently connected to Windows.')
        }} else {{
            [Console]::Out.WriteLine("STATUS:ERROR:$err")
        }}
    }}
    """

    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=120,
        )
        stdout = res.stdout.strip()
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("STATUS:SUCCESS:"):
                scanned_path = line[len("STATUS:SUCCESS:"):].strip()
                if os.path.exists(scanned_path):
                    return ("SUCCESS", scanned_path)
            elif line.startswith("STATUS:CANCELLED:"):
                return ("CANCELLED", None)
            elif line.startswith("STATUS:NO_DEVICE:"):
                msg = line[len("STATUS:NO_DEVICE:"):].strip()
                return ("NO_DEVICE", msg)
            elif line.startswith("STATUS:ERROR:"):
                msg = line[len("STATUS:ERROR:"):].strip()
                return ("ERROR", msg)

        if out_file.exists():
            return ("SUCCESS", str(out_file))

        stderr = res.stderr.strip()
        if "No WIA device" in stderr or "0x80210015" in stderr:
            return ("NO_DEVICE", "No WIA hardware scanner is currently connected.")
        return ("NO_DEVICE", stderr or "No scanner device response received from Windows.")
    except FileNotFoundError:
        return ("ERROR", "PowerShell is not available on this system.")
    except subprocess.TimeoutExpired:
        return ("ERROR", "Scanning operation timed out.")
    except Exception as ex:
        return ("ERROR", str(ex))

def scan_document() -> Tuple[str, Optional[str]]:
    """
    Cross-platform scanner entry point.
    Returns tuple: (status, path_or_message)
    status: "SUCCESS" | "CANCELLED" | "NO_DEVICE" | "ERROR"
    """
    if is_windows():
        return scan_document_windows()
    else:
        # Non-Windows development fallback: generates a test simulated document image
        temp_dir = Path(tempfile.gettempdir()) / "itt_ocr_scans"
        temp_dir.mkdir(parents=True, exist_ok=True)
        sample_path = temp_dir / f"simulated_scan_{int(time.time())}.png"
        _create_test_scan_image(str(sample_path))
        return ("SUCCESS", str(sample_path))

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
