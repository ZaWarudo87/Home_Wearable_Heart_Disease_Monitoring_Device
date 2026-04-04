from flask import request

import database


def _parse_user_id_token(token: str):
    if not token:
        return None
    try:
        return int(token)
    except (TypeError, ValueError):
        return None


def check_auth(req: request) -> dict:
    auth_header = req.headers.get('Authorization')
    if not auth_header:
        return {"error": (401, 'Missing Authorization Header')}

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer':
            return {"error": (401, 'Invalid Authorization Scheme')}
    except ValueError:
        return {"error": (401, 'Invalid Authorization Header')}

    user_id = _parse_user_id_token(token)
    if user_id is None:
        return {"error": (401, 'Invalid Token')}

    user = database.get_user_by_id(user_id)
    if not user:
        return {"error": (401, 'Invalid Token')}

    return {
        "id": user.id,
        "token": str(user.id),
        "name": user.name,
        "birthday": user.birthday.isoformat(),
        "profile_completed": user.profile_completed
    }


def check_auth_ws(token: str) -> bool:
    user_id = _parse_user_id_token(token)
    if user_id is None:
        return False
    return database.get_user_by_id(user_id) is not None

def check_login(req: request) -> dict:
    payload = req.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    birthday = (payload.get("birthday") or "").strip()

    if not name:
        return {"error": (400, "Missing name")}
    if not birthday:
        return {"error": (400, "Missing birthday")}

    user = database.get_user_by_name_birth(name, birthday)
    is_new_user = user is None

    if is_new_user:
        user = database.create_user(name, birthday)
        print(f"Created new user: {name}")
    else:
        print(f"Existing user logged in: {name}")

    return {
        "id": user.id,
        "token": str(user.id),
        "is_new_user": is_new_user,
        "name": user.name,
        "birthday": user.birthday,
        "profile_completed": user.profile_completed
    }
