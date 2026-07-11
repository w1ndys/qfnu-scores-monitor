"""系统配置的文件持久化工具。"""

import json
import os
from pathlib import Path


class SettingsStore:
    PATH = Path(os.getenv("APP_CONFIG_PATH", "settings.json"))

    @classmethod
    def get(cls) -> dict:
        settings = {
            "ocr_url": os.getenv("OCR_URL", ""),
            "check_interval_minutes": int(os.getenv("CHECK_INTERVAL_MINUTES", "5")),
        }
        if cls.PATH.exists():
            settings.update(json.loads(cls.PATH.read_text(encoding="utf-8")))
        return settings

    @classmethod
    def save(cls, settings: dict) -> dict:
        cls.PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.PATH.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
        return settings
