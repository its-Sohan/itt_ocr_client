import platform
import httpx
from packaging import version

APP_VERSION = "1.0.0"

# Default public releases repo. You can change this repo name anytime in this file or config.
DEFAULT_RELEASE_REPO = "its-Sohan/itt-ocr-releases"

def get_platform_asset_keyword() -> str:
    """Returns file extension/keyword to identify installer asset for current operating system."""
    system = platform.system().lower()
    if "windows" in system:
        return ".exe"
    elif "darwin" in system:
        return ".dmg"
    else:
        return "linux"

async def check_for_updates(repo: str = DEFAULT_RELEASE_REPO, current_version: str = APP_VERSION) -> dict:
    """
    Checks the public releases repo on GitHub for a newer version.
    Returns update dictionary with details if a newer version is found, or {"has_update": False}.
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ITT-OCR-Client",
    }
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                return {"has_update": False, "status_code": res.status_code, "error": "No releases found or repo not accessible"}
            
            data = res.json()
            raw_tag = data.get("tag_name", "")
            latest_version_str = raw_tag.lstrip("v").strip()
            
            if not latest_version_str:
                return {"has_update": False, "error": "Invalid release tag"}

            # Semantic version check (e.g. 1.1.0 > 1.0.0)
            if version.parse(latest_version_str) > version.parse(current_version):
                assets = data.get("assets", [])
                keyword = get_platform_asset_keyword()
                
                matched_asset = None
                for asset in assets:
                    name = asset.get("name", "").lower()
                    if keyword in name:
                        matched_asset = asset
                        break
                
                # If no OS-specific asset found, fall back to release page or first asset
                download_url = (
                    matched_asset.get("browser_download_url") 
                    if matched_asset 
                    else data.get("html_url")
                )
                
                return {
                    "has_update": True,
                    "current_version": current_version,
                    "latest_version": latest_version_str,
                    "tag_name": raw_tag,
                    "release_name": data.get("name") or raw_tag,
                    "release_notes": data.get("body", "No release notes provided."),
                    "published_at": data.get("published_at", ""),
                    "download_url": download_url,
                    "release_page_url": data.get("html_url", ""),
                    "asset_name": matched_asset.get("name") if matched_asset else None,
                }
            
            return {
                "has_update": False,
                "current_version": current_version,
                "latest_version": latest_version_str,
            }
    except Exception as exc:
        return {"has_update": False, "error": str(exc)}
