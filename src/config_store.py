import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".itt_ocr_client"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "session_account": "default_user",
    "api_key": "",
    "base_url": "https://api.openai.com/v1",
    "model_name": "gpt-4o-mini",
    "system_prompt": "You are an expert OCR engine. Extract and transcribe all visible text from the image accurately. Maintain all structural elements such as headings, lists, tables, and paragraphs where applicable. Output clean text or Markdown only without introductory pleasantries or commentary.",
    "usage_stats": {
        "total_scanned_or_uploaded": 0,
        "total_processed": 0,
        "total_characters_extracted": 0,
        "successful_runs": 0,
        "failed_runs": 0,
    },
}

def load_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all default keys exist
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            stats = DEFAULT_CONFIG["usage_stats"].copy()
            stats.update(data.get("usage_stats", {}))
            merged["usage_stats"] = stats
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def update_usage_stats(characters: int = 0, success: bool = True):
    config = load_config()
    stats = config.get("usage_stats", {})
    stats["total_processed"] = stats.get("total_processed", 0) + 1
    if success:
        stats["successful_runs"] = stats.get("successful_runs", 0) + 1
        stats["total_characters_extracted"] = stats.get("total_characters_extracted", 0) + characters
    else:
        stats["failed_runs"] = stats.get("failed_runs", 0) + 1
    config["usage_stats"] = stats
    save_config(config)
    return stats
