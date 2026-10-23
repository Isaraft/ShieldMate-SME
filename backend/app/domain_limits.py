import threading
import time
from collections import deque

from app.errors import PublicError


class DomainLimiter:
    """Bounded per-process IP budget; persistent organization budgets live in DomainEvent."""

    def __init__(self) -> None:
        self.entries: dict[str, deque[float]] = {}
        self.lock = threading.Lock()

    def check(self, key: str, limit: int) -> None:
        moment = time.monotonic()
        with self.lock:
            for address in list(self.entries):
                if self.entries[address][-1] <= moment - 900:
                    del self.entries[address]
            if key not in self.entries and len(self.entries) >= 5000:
                raise PublicError(429, "Asset service is busy. Retry later.")
            queue = self.entries.setdefault(key, deque())
            while queue and queue[0] <= moment - 900:
                queue.popleft()
            if len(queue) >= limit:
                raise PublicError(429, "Too many asset requests. Retry in 15 minutes.")
            queue.append(moment)
