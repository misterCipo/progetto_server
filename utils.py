# utils.py
from datetime import datetime

class Protocol:
    LOGIN_REQUEST = "log"
    LOGIN_INFO = "rlo"
    MSG = "msg"
    USER_LIST = "ele"
    SEPARATOR = "|"

VALID_COMMANDS = {Protocol.LOGIN_REQUEST, Protocol.MSG, Protocol.USER_LIST}

def is_valid_protocol_message(raw_msg: str) -> bool:
    parts = raw_msg.strip().split(Protocol.SEPARATOR)
    if not parts:
        return False
    cmd = parts[0]
    if cmd not in VALID_COMMANDS:
        return False

    match cmd:
        case Protocol.LOGIN_REQUEST:
            if len(parts) != 3:
                return False
            username = parts[1].strip()
            return bool(username)

        case Protocol.MSG:
            if len(parts) < 4:
                return False
            username, date_str, message = parts[1].strip(), parts[2].strip(), parts[3].strip()
            if not username or not message:
                return False
            try:
                datetime.fromisoformat(date_str)
            except ValueError:
                return False
            return True

        case _:
            return False

def parse_password_file(filepath):
    result = {}
    with open(filepath, "r") as file:
        for line in file:
            line = line.strip()
            if not line or ":" not in line:
                continue
            name, pwd = line.split(":", 1)
            result[name] = pwd
    return result

def build_login_response(success: bool) -> str:
    return f"{Protocol.LOGIN_INFO}{Protocol.SEPARATOR}{'login effettuato' if success else 'login errato'}"

def build_users_list_payload(connected_users):
    return f"{Protocol.USER_LIST}{Protocol.SEPARATOR}{','.join(connected_users.keys())}"

