from backend.database import DatabaseManager, get_timestamp


class UserRepository:
    @staticmethod
    def list_all() -> list[dict]:
        with DatabaseManager() as conn:
            rows = conn.execute(
                "SELECT user_account, enabled, session_expired, push_count, "
                "last_check_at, created_at, updated_at FROM users ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def save(user_account, encrypted_password, encrypted_session, encryption_key, webhook, secret):
        timestamp = get_timestamp()
        with DatabaseManager() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO users
                (user_account, encrypted_password, encrypted_session, encryption_key,
                 dingtalk_webhook, dingtalk_secret, enabled, session_expired, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?, ?)
                """,
                (user_account, encrypted_password, encrypted_session, encryption_key,
                 webhook, secret, timestamp, timestamp),
            )

    @staticmethod
    def delete(user_account: str):
        with DatabaseManager() as conn:
            conn.execute("DELETE FROM users WHERE user_account = ?", (user_account,))
            conn.execute("DELETE FROM scores WHERE user_account = ?", (user_account,))

    @staticmethod
    def toggle(user_account: str) -> bool:
        with DatabaseManager() as conn:
            cursor = conn.execute(
                "UPDATE users SET enabled = 1 - enabled, updated_at = ? WHERE user_account = ?",
                (get_timestamp(), user_account),
            )
        return cursor.rowcount > 0
