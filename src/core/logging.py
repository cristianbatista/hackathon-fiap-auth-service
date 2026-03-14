import json
import logging
import sys
import uuid
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    SERVICE_NAME = "auth-service"

    def format(self, record: logging.LogRecord) -> str:
        trace_id = getattr(record, "trace_id", str(uuid.uuid4()))
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "service": self.SERVICE_NAME,
            "level": record.levelname,
            "message": record.getMessage(),
            "trace_id": trace_id,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level.upper(), handlers=[])
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        root.addHandler(handler)
    root.setLevel(level.upper())
