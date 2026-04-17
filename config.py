# ===== config.py =====
import os
from dotenv import load_dotenv

load_dotenv()

CRM_URL = os.getenv("CRM_URL")
CRM_URL_GROUP3 = os.getenv("CRM_URL_GROUP3")
CRM_URL_RETAIL_WAREHOUSE = os.getenv("CRM_URL_RETAIL_WAREHOUSE")
CRM_LOGIN_URL = os.getenv("CRM_LOGIN_URL")
CRM_USERNAME = os.getenv("CRM_USERNAME")
CRM_PASSWORD = os.getenv("CRM_PASSWORD")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_DESTINATIONS_RAW = os.getenv("TELEGRAM_DESTINATIONS", "")

CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", 5))
ALERT_THRESHOLD_MINUTES = int(os.getenv("ALERT_THRESHOLD_MINUTES", 30))


def _parse_chat_id(raw_chat_id: str) -> int:
    value = (raw_chat_id or "").strip()
    if not value:
        raise ValueError("chat_id gol in configurarea Telegram.")
    if value.startswith("-"):
        numeric = value[1:]
    else:
        numeric = value
    if not numeric.isdigit():
        raise ValueError(f"chat_id invalid: '{raw_chat_id}'. chat_id trebuie sa fie numeric.")
    return int(value)


def get_telegram_destinations() -> list[dict]:
    """
    Parseaza lista de destinatii Telegram.

    Format recomandat in .env:
    TELEGRAM_DESTINATIONS=-1001234567890,-1001234567890:12,-1009999999999:5
    unde:
      - chat_id simplu => mesaj in chat-ul principal
      - chat_id:thread_id => mesaj in topic/canal (forum topic)
    """
    raw = (TELEGRAM_DESTINATIONS_RAW or "").strip()
    if not raw and TELEGRAM_CHAT_ID:
        return [{"chat_id": _parse_chat_id(TELEGRAM_CHAT_ID), "thread_id": None}]

    out: list[dict] = []
    for chunk in raw.replace("\n", ",").replace(";", ",").split(","):
        item = chunk.strip()
        if not item:
            continue
        if ":" in item:
            chat_id, thread_id = item.split(":", 1)
            chat_id = chat_id.strip()
            thread_id = thread_id.strip()
            if not chat_id or not thread_id:
                raise ValueError(
                    f"Destinatie Telegram invalida: '{item}'. Foloseste formatul chat_id:thread_id."
                )
            if not thread_id.isdigit():
                raise ValueError(
                    f"Thread ID invalid pentru destinatia '{item}'. Thread ID trebuie sa fie numeric."
                )
            out.append({"chat_id": _parse_chat_id(chat_id), "thread_id": int(thread_id)})
        else:
            out.append({"chat_id": _parse_chat_id(item), "thread_id": None})

    if not out:
        raise ValueError(
            "Nu s-au gasit destinatii Telegram valide. Seteaza TELEGRAM_DESTINATIONS sau TELEGRAM_CHAT_ID."
        )
    return out

# Lista persoanelor PERMISE sa aiba tickete
# Orice ticket pe altcineva -> alerta
ALLOWED_ASSIGNEES = [
    "Edi Florean",
    "Razvan Munteanu",
    "Razvan Bucur",
    "Alexandru Nedelcu",
    "Cosmin Mititescu",
    "Vitalii Hrinchenko",
    "Andrei Palade",
    "Valentin Dicu",
    "Ianis Avram",
    "Cristian Vladu",
    "Cristian Farcas",
    "Catalin Suciu",
    "Ilona Poliukhovych",
    "Ілона Полюхович",  # NUME UCRAINEAN ILONA
]