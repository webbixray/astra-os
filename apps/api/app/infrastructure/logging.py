import json
import logging
import logging.config
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            data.update(record.extra)
        return json.dumps(data, default=str)


CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": JSONFormatter},
        "simple": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console_json": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
        },
        "console_simple": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "simple",
        },
    },
    "loggers": {
        "astra": {"handlers": [], "level": "INFO", "propagate": True},
        "uvicorn": {"handlers": [], "level": "WARNING", "propagate": True},
        "sqlalchemy.engine": {"handlers": [], "level": "WARNING", "propagate": True},
    },
}


def configure_logging(*, json_format: bool | None = None) -> None:
    if json_format is None:
        json_format = "--json-logs" in sys.argv or "JSON_LOGS" in __import__("os").environ

    handler_name = "console_json" if json_format else "console_simple"
    config = {
        "version": CONFIG["version"],
        "disable_existing_loggers": CONFIG["disable_existing_loggers"],
        "formatters": CONFIG["formatters"],
        "handlers": CONFIG["handlers"],
        "root": {
            "level": "WARNING",
            "handlers": [handler_name],
        },
        "loggers": {},
    }
    for name, cfg in CONFIG["loggers"].items():
        config["loggers"][name] = {**cfg, "handlers": [handler_name]}

    logging.config.dictConfig(config)
