import os
import uuid
from dataclasses import dataclass, asdict
from typing import List, Optional, Callable
from src.config_store import load_history, save_history

@dataclass
class QueueItem:
    id: str
    file_path: str
    file_name: str
    file_size_str: str
    status: str = "Ready"  # "Ready", "Processing", "Done", "Failed"
    extracted_text: str = ""
    error_message: str = ""
    source: str = "upload"  # "upload", "scanner", or "clipboard"
    output_mode: str = "document"  # "document", "spreadsheet", "key_value", "raw_text"
    block_boxes: Optional[List[dict]] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "QueueItem":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            file_path=data.get("file_path", ""),
            file_name=data.get("file_name", ""),
            file_size_str=data.get("file_size_str", "Unknown"),
            status=data.get("status", "Ready"),
            extracted_text=data.get("extracted_text", ""),
            error_message=data.get("error_message", ""),
            source=data.get("source", "upload"),
            output_mode=data.get("output_mode", "document"),
            block_boxes=data.get("block_boxes", None),
        )

def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

class AppState:
    def __init__(self):
        self.queue: List[QueueItem] = []
        self.selected_item_id: Optional[str] = None
        self.active_output_mode: str = "document"
        self.is_processing_all: bool = False
        self.status_message: str = "Ready"
        self.audit_mode: bool = False
        self.active_block_index: int = 0
        self.total_blocks_count: int = 0
        self._listeners: List[Callable[[], None]] = []
        # App starts with clean, empty queue (no mock or cached pages on opening)

    def _load_cached_history(self):
        try:
            cached_data = load_history()
            if cached_data:
                for item_dict in cached_data:
                    # Validate item file path or preserve cached record
                    item = QueueItem.from_dict(item_dict)
                    self.queue.append(item)
                if self.queue:
                    self.selected_item_id = self.queue[0].id
        except Exception as ex:
            print(f"Error loading cached history: {ex}")

    def persist(self):
        try:
            data = [item.to_dict() for item in self.queue]
            save_history(data)
        except Exception as ex:
            print(f"Error persisting history: {ex}")

    def add_listener(self, listener: Callable[[], None]):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def notify(self):
        # Auto-persist state changes (extracted text, status)
        self.persist()
        for listener in self._listeners:
            try:
                listener()
            except Exception as ex:
                print(f"Error in state listener: {ex}")

    @property
    def selected_item(self) -> Optional[QueueItem]:
        if not self.selected_item_id and self.queue:
            return self.queue[0]
        for item in self.queue:
            if item.id == self.selected_item_id:
                return item
        return self.queue[0] if self.queue else None

    def add_item(self, file_path: str, source: str = "upload") -> QueueItem:
        file_name = os.path.basename(file_path)
        try:
            size_bytes = os.path.getsize(file_path)
            size_str = format_file_size(size_bytes)
        except Exception:
            size_str = "Unknown"

        item = QueueItem(
            id=str(uuid.uuid4())[:8],
            file_path=file_path,
            file_name=file_name,
            file_size_str=size_str,
            source=source,
            output_mode=self.active_output_mode,
        )
        self.queue.append(item)
        if not self.selected_item_id:
            self.selected_item_id = item.id
        self.notify()
        return item

    def set_active_output_mode(self, mode: str):
        if mode in ("document", "spreadsheet", "key_value", "raw_text"):
            self.active_output_mode = mode
            self.notify()

    def select_item(self, item_id: str):
        self.selected_item_id = item_id
        self.notify()

    def remove_item(self, item_id: str):
        self.queue = [item for item in self.queue if item.id != item_id]
        if self.selected_item_id == item_id:
            self.selected_item_id = self.queue[0].id if self.queue else None
        self.notify()

    def clear_completed(self):
        self.queue = [item for item in self.queue if item.status != "Done"]
        if self.queue:
            self.selected_item_id = self.queue[0].id
        else:
            self.selected_item_id = None
        self.notify()

    def get_ready_items(self) -> List[QueueItem]:
        return [item for item in self.queue if item.status in ("Ready", "Failed")]

    def set_audit_mode(self, enabled: bool):
        self.audit_mode = enabled
        self.notify()

    def set_active_block_index(self, index: int):
        self.active_block_index = max(0, index)
        self.notify()

    def next_audit_block(self):
        if self.total_blocks_count > 0:
            self.active_block_index = min(self.total_blocks_count - 1, self.active_block_index + 1)
            self.notify()

    def prev_audit_block(self):
        if self.total_blocks_count > 0:
            self.active_block_index = max(0, self.active_block_index - 1)
            self.notify()

state = AppState()
