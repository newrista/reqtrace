"""In-memory storage for captured trace entries."""

from collections import deque
from threading import Lock
from typing import Deque, Iterator, List, Optional

from reqtrace.models import TraceEntry


class TraceStore:
    """Thread-safe, bounded in-memory store for TraceEntry objects."""

    def __init__(self, max_entries: int = 1000) -> None:
        self._max_entries = max_entries
        self._entries: Deque[TraceEntry] = deque(maxlen=max_entries)
        self._lock = Lock()

    def add(self, entry: TraceEntry) -> None:
        with self._lock:
            self._entries.append(entry)

    def get_all(self) -> List[TraceEntry]:
        with self._lock:
            return list(self._entries)

    def get_by_id(self, trace_id: str) -> Optional[TraceEntry]:
        with self._lock:
            for entry in self._entries:
                if entry.trace_id == trace_id:
                    return entry
        return None

    def filter_by_method(self, method: str) -> List[TraceEntry]:
        method = method.upper()
        with self._lock:
            return [e for e in self._entries if e.request.method.upper() == method]

    def filter_by_status(self, status_code: int) -> List[TraceEntry]:
        with self._lock:
            return [e for e in self._entries if e.response.status_code == status_code]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def __iter__(self) -> Iterator[TraceEntry]:
        return iter(self.get_all())


# Module-level default store instance
default_store = TraceStore()
