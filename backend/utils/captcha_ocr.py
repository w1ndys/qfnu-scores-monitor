import base64

import requests

from backend.utils.settings_store import SettingsStore


def get_ocr_res(image_bytes: bytes) -> str:
    ocr_url = SettingsStore.get().get("ocr_url", "").strip().rstrip("/")
    if not ocr_url:
        raise RuntimeError("未配置 OCR 接口，请先在管理面板中设置")
    response = requests.post(
        f"{ocr_url}/ocr",
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"},
        data={"image": base64.b64encode(image_bytes).decode("ascii")},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if str(payload.get("code")) not in {"0", "200"}:
        raise RuntimeError(payload.get("message") or "OCR 服务识别失败")
    result = str(payload.get("data", "")).replace(" ", "").strip()
    if not result:
        raise RuntimeError("OCR 服务返回了空验证码")
    return result
