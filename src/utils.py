from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ============================
# Protocollo messaggi
# ============================
class Protocol:
    #Definisce comandi e separatore per protocollo chat
    LOGIN_REQUEST = "log"  # richiesta login
    LOGIN_INFO = "rlo"     # risposta login
    MSG = "msg"            # messaggio chat
    USER_LIST = "ele"      # lista utenti online
    SEPARATOR = "|"        # separatore campi

VALID_COMMANDS = {Protocol.LOGIN_REQUEST, Protocol.MSG, Protocol.USER_LIST}

# ============================
# Controlli messaggi
# ============================
def is_valid_protocol_message(raw_msg: str) -> bool:
    #Controlla se il messaggio ricevuto rispetta il protocollo
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
            # deve avere 3 campi: comando, username, password
            return len(parts) == 3 and bool(parts[1].strip())
        case Protocol.MSG:
            # deve avere almeno 4 campi: comando, username, timestamp, messaggio
            if len(parts) < 4:
                return False
            username, date_str, message = parts[1].strip(), parts[2].strip(), parts[3].strip()
            if not username or not message:
                return False
            try:
                datetime.fromisoformat(date_str)  # verifica validità timestamp
            except ValueError:
                return False
            return True
        case Protocol.USER_LIST:
            # lista utenti deve avere 2 campi: comando + lista utenti
            return len(parts) == 2

    return False

# ============================
# Gestione utenti autorizzati
# ============================
def parse_password_file(filepath: str) -> dict[str, str]:
    #Legge file username:password e ritorna dizionario
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

# ============================
# Costruzione payload
# ============================
def build_login_response(success: bool) -> str:
    #Crea messaggio di risposta al login
    status = "login eseguito" if success else "login errato"
    return f"{Protocol.LOGIN_INFO}{Protocol.SEPARATOR}{status}"

def build_users_list_payload(connected_users: dict[str, object]) -> str:
    #Crea messaggio con lista utenti online
    users = ",".join(connected_users.keys())
    return f"{Protocol.USER_LIST}{Protocol.SEPARATOR}{users}"
