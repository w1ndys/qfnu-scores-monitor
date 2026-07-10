import datetime
import time

from config import get_user_config
from utils.captcha_ocr import get_ocr_res
from utils.logger import logger
from utils.session_manager import get_session

BASE_URL = "http://zhjw.qfnu.edu.cn"
LOGIN_VERIFY_URL = f"{BASE_URL}/jsxsd/framework/xsMain.jsp"
USER_AGENT = "Mozilla/5.0"
LOGIN_STEP_MAX_RETRIES = 3
MAX_CAPTCHA_RETRIES = 3
LOGIN_VERIFY_MAX_RETRIES = 2
REQUEST_TIMEOUT = 30
PASSWORD_ERRORS = ("密码错误", "用户名或密码错误", "用户名密码错误", "您提供的用户名或者密码有误")
CAPTCHA_ERRORS = ("验证码错误", "验证码不正确")


def _request_with_retry(method: str, url: str, **kwargs):
    session = get_session()
    last_error = None
    for attempt in range(1, LOGIN_STEP_MAX_RETRIES + 1):
        try:
            response = session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
            if response.status_code < 400:
                return response
            last_error = RuntimeError(f"HTTP {response.status_code}")
        except Exception as error:
            last_error = error
        logger.warning(f"请求 {url} 失败（第 {attempt}/{LOGIN_STEP_MAX_RETRIES} 次）：{last_error}")
        if attempt < LOGIN_STEP_MAX_RETRIES:
            time.sleep(1)
    raise RuntimeError(f"请求 {url} 失败：{last_error}")


def initialize_session():
    _request_with_retry("GET", BASE_URL, headers={"User-Agent": USER_AGENT})


def handle_captcha() -> str:
    response = _request_with_retry(
        "GET",
        f"{BASE_URL}/verifycode.servlet",
        headers={"User-Agent": USER_AGENT},
    )
    if not response.content:
        raise RuntimeError("验证码图片为空")
    return get_ocr_res(response.content)


def get_login_tokens() -> tuple[str, str]:
    response = _request_with_retry(
        "POST",
        f"{BASE_URL}/Logon.do?method=logon&flag=sess",
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": USER_AGENT},
        data={},
    )
    value = response.text.strip()
    if not value or value.lower() == "no" or "#" not in value:
        raise RuntimeError("教务系统未返回有效的 scode/sxh")
    return tuple(value.split("#", 1))


def generate_encoded_string(user_account: str, user_password: str, scode: str, sxh: str) -> str:
    code = f"{user_account}%%%{user_password}"
    result: list[str] = []
    scode_index = 0
    for index, character in enumerate(code):
        result.append(character)
        if index >= 20:
            continue
        if index >= len(sxh) or not sxh[index].isdigit():
            raise RuntimeError("教务系统返回的 sxh 格式无效")
        length = int(sxh[index])
        result.append(scode[scode_index:scode_index + length])
        scode_index += length
    return "".join(result)


def submit_login(random_code: str, encoded: str):
    return get_session().post(
        f"{BASE_URL}/Logon.do?method=logonLdap",
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": USER_AGENT},
        data={"userAccount": "", "userPassword": "", "RANDOMCODE": random_code, "encoded": encoded},
        timeout=REQUEST_TIMEOUT,
        allow_redirects=False,
    )


def verify_login() -> bool:
    for attempt in range(1, LOGIN_VERIFY_MAX_RETRIES + 1):
        try:
            response = get_session().get(
                LOGIN_VERIFY_URL,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
            )
            if response.status_code == 200 and (
                "教学一体化服务平台" in response.text or "glyphicon-class" in response.text
            ):
                return True
        except Exception as error:
            logger.warning(f"登录状态验证异常：{error}")
        if attempt < LOGIN_VERIFY_MAX_RETRIES:
            time.sleep(1)
    return False


def simulate_login(user_account: str, user_password: str) -> bool:
    initialize_session()
    for attempt in range(1, MAX_CAPTCHA_RETRIES + 1):
        try:
            random_code = handle_captcha()
            scode, sxh = get_login_tokens()
            response = submit_login(random_code, generate_encoded_string(user_account, user_password, scode, sxh))
            body = response.text
            if any(message in body for message in PASSWORD_ERRORS):
                raise ValueError("用户名或密码错误")
            if any(message in body for message in CAPTCHA_ERRORS):
                logger.warning(f"验证码错误（第 {attempt}/{MAX_CAPTCHA_RETRIES} 次）")
                continue
            if not body.strip() or any(marker in body for marker in ("正在登录", "location", "教学一体化服务平台")):
                if verify_login():
                    return True
            else:
                logger.warning(f"登录响应无法确认成功（第 {attempt}/{MAX_CAPTCHA_RETRIES} 次）")
        except ValueError:
            raise
        except Exception as error:
            logger.warning(f"登录尝试失败（第 {attempt}/{MAX_CAPTCHA_RETRIES} 次）：{error}")
        if attempt < MAX_CAPTCHA_RETRIES:
            time.sleep(1)
    raise RuntimeError("登录失败，验证码识别或教务系统响应异常")


def print_welcome():
    logger.info(f"\n{'*' * 10} 曲阜师范大学模拟登录脚本 {'*' * 10}\n")
    logger.info(f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    user_account, user_password = get_user_config()
    while True:
        try:
            if simulate_login(user_account, user_password):
                logger.info("登录成功!")
                break
        except Exception as error:
            logger.error(f"登录失败：{error}，正在重试...")
            time.sleep(1)


if __name__ == "__main__":
    main()
