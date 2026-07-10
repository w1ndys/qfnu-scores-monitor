from backend.repositories import UserRepository
from main import simulate_login
from scheduler import check_all_users, check_single_user
from utils.crypto import encrypt_session, generate_key
from utils.dingtalk import notify_init_scores
from utils.logger import logger
from utils.score_monitor import fetch_scores, serialize_session
from utils.session_manager import get_session, reset_session


class UserService:
    @staticmethod
    def list_users() -> list[dict]:
        return UserRepository.list_all()

    @staticmethod
    def import_user(text: str) -> dict:
        lines = [line.strip() for line in text.splitlines() if line.strip()][:4]
        if len(lines) < 4:
            return {"success": False, "message": f"需要4行有效数据，当前只有 {len(lines)} 行"}
        account, password, webhook, secret = lines
        try:
            reset_session()
            if not simulate_login(account, password):
                return {"success": False, "message": "登录失败，请检查学号和密码"}
            session = get_session()
            key = generate_key()
            UserRepository.save(
                account,
                encrypt_session(password, key),
                encrypt_session(serialize_session(session), key),
                key,
                webhook,
                secret,
            )
            try:
                _, scores, expired = fetch_scores(session)
                if not expired:
                    notify_init_scores(webhook, secret, scores or [], account)
            except Exception as error:
                logger.error(f"用户 {account} 初始化获取成绩失败: {error}")
            return {"success": True, "message": f"用户 {account} 导入成功，已开始监控"}
        except Exception as error:
            logger.exception(f"导入用户 {account} 失败")
            return {"success": False, "message": str(error)}

    @staticmethod
    def delete_user(account: str) -> dict:
        UserRepository.delete(account)
        return {"success": True, "message": f"用户 {account} 已删除"}

    @staticmethod
    def toggle_user(account: str) -> dict:
        if not UserRepository.toggle(account):
            return {"success": False, "message": "用户不存在"}
        return {"success": True, "message": "用户状态已更新"}

    @staticmethod
    def check_user(account: str) -> dict:
        return check_single_user(account)

    @staticmethod
    def check_all() -> dict:
        check_all_users()
        return {"success": True, "message": "全部用户检测完成"}
