from urllib.parse import urlparse

from backend.repositories.settings_repository import SettingsRepository


class SettingsService:
    @staticmethod
    def get() -> dict:
        return SettingsRepository.get()

    @staticmethod
    def update(data: dict) -> dict:
        ocr_url = str(data.get("ocr_url", "")).strip().rstrip("/")
        parsed = urlparse(ocr_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return {"success": False, "message": "OCR 地址必须是有效的 HTTP/HTTPS URL"}
        try:
            interval = int(data.get("check_interval_minutes", 5))
        except (TypeError, ValueError):
            return {"success": False, "message": "监控间隔必须是整数"}
        if not 1 <= interval <= 1440:
            return {"success": False, "message": "监控间隔必须在 1 到 1440 分钟之间"}

        settings = {"ocr_url": ocr_url, "check_interval_minutes": interval}
        SettingsRepository.save(settings)

        from scheduler import update_check_interval

        update_check_interval(interval)
        return {"success": True, "message": "系统配置已保存并生效", "settings": settings}
