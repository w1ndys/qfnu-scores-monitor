import sqlite3

from utils.logger import LOG_DB_PATH


class LogService:
    @staticmethod
    def read_logs(lines: int) -> dict:
        limit = max(1, min(lines, 1000))
        try:
            with sqlite3.connect(LOG_DB_PATH, timeout=5) as connection:
                connection.row_factory = sqlite3.Row
                rows = connection.execute(
                    """
                    SELECT created_at, level, module, function, line, message, exception
                    FROM logs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        except sqlite3.Error as error:
            return {"success": False, "message": f"读取日志数据库失败：{error}"}

        entries = [dict(row) for row in reversed(rows)]
        content = "\n".join(
            f"{entry['created_at']} | {entry['level']:<8} | "
            f"{entry['module']}:{entry['function']}:{entry['line']} - "
            f"{entry['message']}{(' | ' + entry['exception']) if entry['exception'] else ''}"
            for entry in entries
        )
        return {
            "success": True,
            "content": content,
            "total_lines": len(entries),
            "logs": entries,
        }
