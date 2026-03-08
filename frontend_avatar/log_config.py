# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
# Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
# Commercial use requires prior written consent from all copyright holders.
# See LICENSE for full terms. Thank you for keeping the rules.
# https://github.com/monjyu1101
# -------------------------------------------------------------------------

"""frontend_avatar 用ログ設定モジュール"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

_logging_configured = False
_current_log_path: Path | None = None


class ByteAlignedFormatter(logging.Formatter):
    def __init__(self, fmt: str, datefmt: str | None = None, name_width_bytes: int = 24, encoding: str = "shift_jis"):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.name_width_bytes = max(0, int(name_width_bytes))
        self.encoding = encoding

    def _byte_width(self, text: str) -> int:
        try:
            return len(text.encode(self.encoding, errors="replace"))
        except Exception:
            return len(text.encode("shift_jis", errors="replace"))

    def _pad_name_by_width(self, name: str) -> str:
        text = str(name)
        width = self._byte_width(text)
        if width >= self.name_width_bytes:
            return text
        return text + (" " * (self.name_width_bytes - width))

    def format(self, record: logging.LogRecord) -> str:
        record.name_aligned = self._pad_name_by_width(record.name)
        return super().format(record)


class DailyDateFileHandler(logging.FileHandler):
    def __init__(self, log_dir: str, prefix: str = "frontend_avatar", encoding: str = "utf-8"):
        self.log_dir = log_dir
        self.prefix = prefix
        self._current_datetime = datetime.now().strftime("%Y%m%d.%H0000")
        os.makedirs(self.log_dir, exist_ok=True)
        super().__init__(self._build_filename(self._current_datetime), mode="a", encoding=encoding, delay=True)

    def _build_filename(self, datetime_str: str) -> str:
        return os.path.join(self.log_dir, f"{datetime_str}.{self.prefix}.log")

    def emit(self, record: logging.LogRecord) -> None:
        global _current_log_path
        try:
            current_datetime = datetime.now().strftime("%Y%m%d.%H0000")
            if current_datetime != self._current_datetime:
                self._current_datetime = current_datetime
                self.baseFilename = os.path.abspath(self._build_filename(current_datetime))
                if self.stream:
                    self.stream.close()
                    self.stream = None
            _current_log_path = Path(self.baseFilename)
            super().emit(record)
        except Exception:
            self.handleError(record)


def setup_logging(instance_name: str = "frontend_avatar") -> None:
    global _logging_configured, _current_log_path

    if _logging_configured:
        return

    log_dir = Path(__file__).resolve().parent / "temp" / "logs"
    formatter = ByteAlignedFormatter(
        "%(asctime)s - %(name_aligned)s - %(levelname)-8s - %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    file_handler = DailyDateFileHandler(log_dir=str(log_dir), prefix=instance_name)
    file_handler.setFormatter(formatter)
    _current_log_path = Path(file_handler.baseFilename)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler],
        force=True,
    )

    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("websocket").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)

    _logging_configured = True
    logging.getLogger("log_config").info("ログ設定を初期化しました (instance=%s)", instance_name)


def get_logger(module_name: str) -> logging.Logger:
    if not _logging_configured:
        setup_logging()
    return logging.getLogger(module_name)


def get_current_log_path() -> Path | None:
    return _current_log_path

