"""Structured logging setup."""
from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from config.settings import settings

_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

def _build_logger() -> logging.Logger:
    logger = logging.getLogger("nexus")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fh = RotatingFileHandler(settings.LOG_DIR / "app.log",
                             maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(logging.Formatter(_FMT))
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(_FMT))
    logger.addHandler(fh); logger.addHandler(sh)
    return logger

log = _build_logger()