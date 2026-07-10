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
        SettingsRepository.save({"ocr_url": ocr_url})
        return {"success": True, "message": "OCR 配置已保存", "settings": {"ocr_url": ocr_url}}
