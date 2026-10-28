import logging
from collections import deque
from contextvars import ContextVar
from datetime import datetime, timezone

current_user_email: ContextVar[str | None] = ContextVar("current_user_email", default=None)


class UserEmailFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.user_email = current_user_email.get() or "system"
        return True


class InMemoryLogHandler(logging.Handler):
    """
    Keeps the most recent log records in memory so the admin panel can
    display them. Not persisted across restarts - "recent logs" only.
    """

    def __init__(self, capacity: int = 200):
        super().__init__()
        self.buffer = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        self.buffer.append({
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "user_email": getattr(record, "user_email", "system"),
        })

    def get_logs(self) -> list:
        return list(reversed(self.buffer))


log_handler = InMemoryLogHandler()
log_handler.addFilter(UserEmailFilter())
access_logger = logging.getLogger("access")


def setup_logging() -> None:
    root_logger = logging.getLogger()
    if log_handler not in root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(log_handler)
