from __future__ import annotations

import logging
import re
from typing import Any


PATTERNS = (
    (re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~-]+"), "Bearer [REDACTED]"),
    (
        re.compile(r"(?i)(refresh_token|access_token|password|cvc)\s*[=:]\s*[^\s,}]+"),
        r"\1=[REDACTED]",
    ),
    (re.compile(r"(?<!\d)(?:\d[ -]?){15,18}\d(?!\d)"), "[CARD_REDACTED]"),
    (re.compile(r"(?<!\d)01[016789][ -]?\d{3,4}[ -]?\d{4}(?!\d)"), "[PHONE_REDACTED]"),
)


def mask_sensitive_text(value: str) -> str:
    masked = value
    for pattern, replacement in PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked


def _mask(value: Any) -> Any:
    if isinstance(value, str):
        return mask_sensitive_text(value)
    if isinstance(value, tuple):
        return tuple(_mask(item) for item in value)
    if isinstance(value, dict):
        return {key: _mask(item) for key, item in value.items()}
    return value


class SensitiveDataLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_sensitive_text(record.msg)
        record.args = _mask(record.args)
        return True


def install_sensitive_data_log_filter() -> None:
    log_filter = SensitiveDataLogFilter()
    loggers = [logging.getLogger()]
    loggers.extend(
        logger
        for logger in logging.Logger.manager.loggerDict.values()
        if isinstance(logger, logging.Logger)
    )
    for logger in loggers:
        for handler in logger.handlers:
            if not any(
                isinstance(item, SensitiveDataLogFilter)
                for item in handler.filters
            ):
                handler.addFilter(log_filter)
