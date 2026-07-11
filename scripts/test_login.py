#!/usr/bin/env python3
import argparse
import getpass
import os
import sys
from textwrap import shorten
from urllib.parse import urlsplit, urlunsplit

import ddddocr
import requests

BASE_URL = "http://zhjw.qfnu.edu.cn"
VERIFY_URL = f"{BASE_URL}/jsxsd/framework/xsMain.jsp"
USER_AGENT = "Mozilla/5.0"
TIMEOUT = 30


def encode_credentials(username: str, password: str, scode: str, sxh: str) -> str:
    code = f"{username}%%%{password}"
    result: list[str] = []
    scode_index = 0
    for index, character in enumerate(code):
        result.append(character)
        if index >= 20:
            continue
        if index >= len(sxh) or not sxh[index].isdigit():
            raise RuntimeError("sxh 格式无效")
        length = int(sxh[index])
        result.append(scode[scode_index:scode_index + length])
        scode_index += length
    return "".join(result)


def response_text(response: requests.Response) -> str:
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def page_summary(response: requests.Response) -> str:
    text = " ".join(response_text(response).split())
    return shorten(text, width=1000, placeholder=" …[已截断]")


def safe_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "[已隐藏]" if parts.query else "", ""))


def run_login(username: str, password: str, attempts: int) -> bool:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    ocr = ddddocr.DdddOcr(show_ad=False)

    print(f"[1/5] 初始化会话：GET {BASE_URL}")
    response = session.get(BASE_URL, timeout=TIMEOUT)
    print(f"      HTTP {response.status_code}，Cookie 数量：{len(session.cookies)}")
    response.raise_for_status()

    for attempt in range(1, attempts + 1):
        print(f"\n--- 登录尝试 {attempt}/{attempts} ---")
        captcha_response = session.get(f"{BASE_URL}/verifycode.servlet", timeout=TIMEOUT)
        captcha_response.raise_for_status()
        captcha = ocr.classification(captcha_response.content).strip().replace(" ", "")
        print(f"[2/5] 验证码：{captcha!r}（图片 {len(captcha_response.content)} bytes）")

        token_response = session.post(
            f"{BASE_URL}/Logon.do?method=logon&flag=sess",
            data={},
            timeout=TIMEOUT,
        )
        token_response.raise_for_status()
        token_value = response_text(token_response).strip()
        if not token_value or token_value.lower() == "no" or "#" not in token_value:
            print(f"[3/5] scode/sxh 获取失败，页面内容：{page_summary(token_response)}")
            continue
        scode, sxh = token_value.split("#", 1)
        print(f"[3/5] scode/sxh 获取成功（长度：{len(scode)}/{len(sxh)}）")

        encoded = encode_credentials(username, password, scode, sxh)
        login_response = session.post(
            f"{BASE_URL}/Logon.do?method=logonLdap",
            data={"userAccount": "", "userPassword": "", "RANDOMCODE": captcha, "encoded": encoded},
            timeout=TIMEOUT,
            allow_redirects=False,
        )
        login_body = response_text(login_response)
        print(
            f"[4/5] 提交登录：HTTP {login_response.status_code}，"
            f"Location={safe_url(login_response.headers.get('Location'))!r}，Cookie 数量：{len(session.cookies)}"
        )
        if login_body.strip():
            print(f"      页面内容：{page_summary(login_response)}")

        redirect_url = login_response.headers.get("Location")
        if login_response.is_redirect and redirect_url:
            redirect_response = session.get(redirect_url, timeout=TIMEOUT, allow_redirects=True)
            print(
                f"      跟随登录票据：HTTP {redirect_response.status_code}，"
                f"最终地址={safe_url(redirect_response.url)!r}，Cookie 数量：{len(session.cookies)}"
            )

        verify_response = session.get(VERIFY_URL, timeout=TIMEOUT, allow_redirects=False)
        verify_body = response_text(verify_response)
        success = verify_response.status_code == 200 and (
            "教学一体化服务平台" in verify_body
            or "glyphicon-class" in verify_body
            or "xsMain" in verify_body
        )
        print(
            f"[5/5] 验证会话：HTTP {verify_response.status_code}，"
            f"Location={safe_url(verify_response.headers.get('Location'))!r}，结果={'成功' if success else '失败'}"
        )
        if success:
            print("登录流程验证成功。")
            return True
        print(f"      页面内容：{page_summary(verify_response)}")

    print("登录流程验证失败。", file=sys.stderr)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="本地验证曲师大教务系统登录流程")
    parser.add_argument("--account", required=True, help="教务系统学号")
    parser.add_argument("--attempts", type=int, default=3, choices=range(1, 6))
    args = parser.parse_args()
    password = os.getenv("LOGIN_TEST_PASSWORD") or getpass.getpass("教务系统密码：")
    return 0 if run_login(args.account, password, args.attempts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
