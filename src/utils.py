from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Protocol:
    LOGIN_REQUEST = "log"
    LOGIN_INFO = "rlo"
    MSG = "msg"
    USER_LIST = "ele"
    SEPARATOR = "|"


VALID_COMMANDS = {Protocol.LOGIN_REQUEST, Protocol.MSG, Protocol.USER_LIST}

def is_valid_protocol_message(raw_msg: str) -> bool:
    if not raw_msg or not isinstance(raw_msg, str):
        return False

    parts = raw_msg.strip().split(Protocol.SEPARATOR)
    if not parts:
        return False

    cmd = parts[0]
    if cmd not in VALID_COMMANDS:
        return False

    match cmd:
        case Protocol.LOGIN_REQUEST:
            return len(parts) == 3 and bool(parts[1].strip())

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

        case Protocol.USER_LIST:
            return len(parts) == 2

    return False

def parse_password_file(filepath: str) -> dict[str, str]:
    result = {}
    path = Path(filepath)

    if not path.exists():
        logger.warning(f"Password file not found: {filepath}")
        return result

    try:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                name, pwd = line.split(":", 1)
                name, pwd = name.strip(), pwd.strip()
                if name:
                    result[name] = pwd
    except Exception as e:
        logger.error(f"Error reading password file {filepath}: {e}")

    return result

def build_login_response(success: bool) -> str:
    status = "login eseguito" if success else "login errato"
    return f"{Protocol.LOGIN_INFO}{Protocol.SEPARATOR}{status}"

def build_users_list_payload(connected_users: dict[str, object]) -> str:
    users = ",".join(connected_users.keys())
    return f"{Protocol.USER_LIST}{Protocol.SEPARATOR}{users}"
