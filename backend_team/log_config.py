# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
from pathlib import Path

_configured = False


def setup_logging(instance_name: str = "team_main") -> None:
    global _configured
    if _configured:
        return
    log_dir = Path(__file__).resolve().parent / "temp" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        logging.FileHandler(log_dir / f"{instance_name}.log", encoding="utf-8"),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
