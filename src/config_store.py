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
    "auto_extract": True,
    "default_output_mode": "document",
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
        json.dump(config, f, indent=2, ensure_ascii=False)

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

HISTORY_FILE = CONFIG_DIR / "history.json"

def load_history() -> list:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_history(items: list):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    except Exception as ex:
        print(f"Failed to save history: {ex}")

