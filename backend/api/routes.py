from flask import Blueprint, jsonify, request

from backend.services.log_service import LogService
from backend.services.settings_service import SettingsService
from backend.services.user_service import UserService

api = Blueprint("api", __name__)


@api.route("/import", methods=["POST", "OPTIONS"])
def import_user():
    if request.method == "OPTIONS":
        return "", 204
    return jsonify(UserService.import_user((request.get_json(silent=True) or {}).get("text", "")))


@api.get("/users")
def users():
    return jsonify({"success": True, "users": UserService.list_users()})


@api.delete("/users/<user_account>")
def delete_user(user_account: str):
    return jsonify(UserService.delete_user(user_account))


@api.post("/users/<user_account>/toggle")
def toggle_user(user_account: str):
    return jsonify(UserService.toggle_user(user_account))


@api.post("/users/<user_account>/check")
def check_user(user_account: str):
    return jsonify(UserService.check_user(user_account))


@api.post("/check")
def check_all():
    return jsonify(UserService.check_all())


@api.get("/logs")
def logs():
    return jsonify({"success": True, "logs": LogService.list_logs()})


@api.get("/logs/<log_name>")
def log_content(log_name: str):
    return jsonify(LogService.read_log(log_name, request.args.get("lines", 200, type=int)))


@api.get("/settings")
def get_settings():
    return jsonify({"success": True, "settings": SettingsService.get()})


@api.put("/settings")
def update_settings():
    return jsonify(SettingsService.update(request.get_json(silent=True) or {}))
