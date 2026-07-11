import sqlite3
import sys
import threading
from pathlib import Path

from loguru import logger as _loguru_logger

LOG_DB_PATH = Path("logs.db")
_write_lock = threading.Lock()
_initialized = False


def _initialize_database() -> None:
    with sqlite3.connect(LOG_DB_PATH, timeout=5) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                timestamp REAL NOT NULL,
                level TEXT NOT NULL,
                module TEXT NOT NULL,
                function TEXT NOT NULL,
                line INTEGER NOT NULL,
                message TEXT NOT NULL,
                exception TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC)"
        )


def _database_sink(message) -> None:
    record = message.record
    exception = str(record["exception"]) if record["exception"] else None
    try:
        with _write_lock, sqlite3.connect(LOG_DB_PATH, timeout=5) as connection:
            connection.execute("PRAGMA busy_timeout=5000")
            connection.execute(
                """
                INSERT INTO logs (
                    created_at, timestamp, level, module, function, line, message, exception
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["time"].strftime("%Y-%m-%d %H:%M:%S"),
                    record["time"].timestamp(),
                    record["level"].name,
                    record["name"],
                    record["function"],
                    record["line"],
                    record["message"],
                    exception,
                ),
            )
    except sqlite3.Error as error:
        print(f"日志写入数据库失败：{error}", file=sys.stderr)


def _setup_logger() -> None:
    global _initialized
    if _initialized:
        return

    try:
        _initialize_database()
    except sqlite3.Error as error:
        print(f"日志数据库初始化失败：{error}", file=sys.stderr)

    _loguru_logger.remove()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    _loguru_logger.add(sys.stderr, format=log_format, level="INFO", colorize=True)
    _loguru_logger.add(_database_sink, level="DEBUG", catch=True)
    _initialized = True


_setup_logger()
logger = _loguru_logger

__all__ = ["LOG_DB_PATH", "logger"]
