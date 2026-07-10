import re
from pathlib import Path


class LogService:
    LOG_NAME = re.compile(r"^app_\d{8}_\d{6}\.log$")

    @classmethod
    def list_logs(cls) -> list[dict]:
        files = sorted(Path("logs").glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
        return [
            {"name": path.name, "size": path.stat().st_size, "mtime": int(path.stat().st_mtime)}
            for path in files
            if cls.LOG_NAME.fullmatch(path.name)
        ]

    @classmethod
    def read_log(cls, name: str, lines: int) -> dict:
        if not cls.LOG_NAME.fullmatch(name):
            return {"success": False, "message": "无效的日志文件名"}
        path = Path("logs") / name
        if not path.exists():
            return {"success": False, "message": "日志文件不存在"}
        limit = max(1, min(lines, 1000))
        content = path.read_text(encoding="utf-8").splitlines(keepends=True)[-limit:]
        return {"success": True, "content": "".join(content), "total_lines": len(content)}
