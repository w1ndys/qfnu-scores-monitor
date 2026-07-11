import requests
import json
import time
import hmac
import hashlib
import base64
from urllib.parse import quote_plus
from backend.utils.logger import logger


def increment_push_count(user_account, db_connection=None):
    """增加用户的推送计数"""
    from backend.database import DatabaseManager

    try:
        if db_connection is not None:
            db_connection.execute(
                "UPDATE users SET push_count = push_count + 1 WHERE user_account = ?",
                (user_account,),
            )
            return True
        with DatabaseManager() as conn:
            conn.execute(
                "UPDATE users SET push_count = push_count + 1 WHERE user_account = ?",
                (user_account,),
            )
        return True
    except Exception as e:
        logger.error(f"增加推送计数失败: {str(e)}")
        return False


def generate_sign(secret):
    """生成钉钉签名"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode("utf-8")
    string_to_sign = "{}\n{}".format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode("utf-8")
    hmac_code = hmac.new(
        secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
    ).digest()
    sign = quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def send_dingtalk_message(
    webhook_url, secret, message, user_account=None, db_connection=None
):
    """发送钉钉消息"""
    if not webhook_url or not secret:
        return False

    timestamp, sign = generate_sign(secret)
    url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "text", "text": {"content": message}}

    try:
        response = requests.post(
            url, headers=headers, data=json.dumps(data), timeout=10
        )
        if response.status_code == 200 and user_account:
            increment_push_count(user_account, db_connection)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"发送钉钉消息失败: {str(e)}")
        return False


def notify_new_scores(
    webhook_url, secret, new_courses, user_account=None, db_connection=None
):
    """通知新成绩"""
    if not new_courses:
        return True

    # 构建markdown格式的消息
    message = "# 🎉 新成绩通知\n\n"
    message += f"检测到 **{len(new_courses)}** 门新成绩！\n\n"

    for course in new_courses:
        message += "---\n\n"
        message += f"### 📚 {course['课程名称']}\n\n"
        message += f"- **成绩**: {course['成绩']}\n"
        message += f"- **绩点**: {course['绩点']}\n"
        message += f"- **学分**: {course['学分']}\n"
        message += f"- **开课学期**: {course['开课学期']}\n"
        message += f"- **课程编号**: {course['课程编号']}\n"
        message += f"- **成绩标识**: {course['成绩标识']}\n"
        message += f"- **总学时**: {course['总学时']}\n"
        message += f"- **考核方式**: {course['考核方式']}\n"
        message += f"- **考试性质**: {course['考试性质']}\n"
        message += f"- **课程属性**: {course['课程属性']}\n"
        message += f"- **课程性质**: {course['课程性质']}\n"
        message += f"- **课程类别**: {course['课程类别']}\n"
        if course["分组名"]:
            message += f"- **分组名**: {course['分组名']}\n"
        if course["补重学期"]:
            message += f"- **补重学期**: {course['补重学期']}\n"
        message += "\n"

    timestamp, sign = generate_sign(secret)
    url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "markdown", "markdown": {"title": "新成绩通知", "text": message}}

    try:
        response = requests.post(
            url, headers=headers, data=json.dumps(data), timeout=10
        )
        if response.status_code == 200 and user_account:
            logger.info("新成绩通知发送成功")
            increment_push_count(user_account, db_connection)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"发送钉钉消息失败: {str(e)}")
        return False


def notify_session_expired(
    webhook_url, secret, user_account=None, db_connection=None
):
    """通知session过期且自动登录失败"""
    message = "【登录过期提醒】\n您的教务系统登录已过期，自动重新登录失败（验证码识别3次均失败），请手动重新导入账号信息。"
    return send_dingtalk_message(
        webhook_url, secret, message, user_account, db_connection
    )


def notify_init_scores(
    webhook_url, secret, scores, user_account=None, db_connection=None
):
    """初始化时上报当前所有成绩"""
    if not scores:
        message = "【成绩监控初始化成功】\n\n当前暂无成绩记录。\n\n后台将每隔一段时间检测一次是否有新成绩，发现新成绩会自动通过钉钉上报。"
        return send_dingtalk_message(
            webhook_url, secret, message, user_account, db_connection
        )

    # 构建markdown格式的消息
    message = "# 📋 成绩监控初始化成功\n\n"
    message += f"当前共有 **{len(scores)}** 门成绩记录：\n\n"

    for course in scores:
        message += f"- **{course['课程名称']}**: {course['成绩']} (绩点:{course['绩点']}, 学分:{course['学分']})\n"

    message += "\n---\n\n"
    message += "✅ 成绩监控已启动，后台将每隔一段时间检测一次是否有新成绩，发现新成绩会自动通过钉钉上报。"

    timestamp, sign = generate_sign(secret)
    url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {"title": "成绩监控初始化成功", "text": message},
    }

    try:
        response = requests.post(
            url, headers=headers, data=json.dumps(data), timeout=10
        )
        if response.status_code != 200:
            logger.error(
                f"发送钉钉消息失败，状态码: {response.status_code}, 响应内容: {response.text}"
            )
        else:
            logger.info("初始化成绩通知发送成功")
            if user_account:
                increment_push_count(user_account, db_connection)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"发送钉钉消息失败: {str(e)}")
        return False
