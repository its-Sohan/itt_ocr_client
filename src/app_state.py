import os
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Callable

@dataclass
class QueueItem:
    id: str
    file_path: str
    file_name: str
    file_size_str: str
    status: str = "Ready"  # "Ready", "Processing", "Done", "Failed"
    extracted_text: str = ""
    error_message: str = ""
    source: str = "upload"  # "upload" or "scanner"

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
        self.is_processing_all: bool = False
        self.status_message: str = "Ready"
        self._listeners: List[Callable[[], None]] = []

    def add_listener(self, listener: Callable[[], None]):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def notify(self):
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
        )
        self.queue.append(item)
        if not self.selected_item_id:
            self.selected_item_id = item.id
        self.notify()
        return item

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

state = AppState()
