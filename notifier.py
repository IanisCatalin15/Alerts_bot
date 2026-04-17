import logging

from telegram import Bot
from telegram.error import TelegramError

from config import TELEGRAM_BOT_TOKEN, get_telegram_destinations


def _severity_dot(duration_minutes: int) -> str:
    if duration_minutes >= 90:
        return "🔴🔴🔴"
    if duration_minutes >= 60:
        return "🔴"
    if duration_minutes >= 30:
        return "🟠"
    return "⚪"


def _duration_label(minutes: int) -> str:
    if minutes < 0:
        return ""
    days, rem = divmod(minutes, 24 * 60)
    h, m = divmod(rem, 60)
    if days > 0:
        return f"{days}d {h}h {m}m"
    if h == 0:
        return f"{m}m"
    return f"{h}h {m}m"


def _safe_title(text: str) -> str:
    t = " ".join((text or "N/A").split()).strip()
    import re
    t = re.sub(r"\b\d+\s*/\s*\d+\b", "", t).strip()  # elimina 0/14
    t = re.sub(r"\s{2,}", " ", t)
    return t or "N/A"


def build_summary_message(tickets: list[dict], title: str) -> str:
    # fara "CRM" in titlu
    clean_title = title.replace("CRM ", "").replace(" CRM", "").strip()

    lines = [f"{clean_title}: {len(tickets)} ticket(e)", ""]

    max_lines = 20
    for t in tickets[:max_lines]:
        duration = int(t.get("duration_minutes", -1))
        dot = _severity_dot(duration)
        duration_text = _duration_label(duration)
        if duration_text:
            lines.append(
                f"- {dot}  #{t.get('id', 'N/A')} | {t.get('assignee', 'N/A')} | {duration_text}"
            )
        else:
            lines.append(f"- {dot}  #{t.get('id', 'N/A')} | {t.get('assignee', 'N/A')}")

        lines.append(f"  {_safe_title(t.get('title', 'N/A'))}")
        if t.get("link"):
            lines.append(f"  {t['link']}")
        lines.append("")

    if len(tickets) > max_lines:
        lines.append(f"... si inca {len(tickets) - max_lines} ticket(e).")

    return "\n".join(lines).strip()


async def send_alerts(tickets: list[dict], title: str = "ALERTA"):
    if not tickets:
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    msg = build_summary_message(tickets, title=title)
    destinations = get_telegram_destinations()
    if not destinations:
        raise RuntimeError(
            "Nu exista destinatii Telegram. Seteaza TELEGRAM_DESTINATIONS sau TELEGRAM_CHAT_ID."
        )

    sent_count = 0
    failed: list[str] = []

    for dest in destinations:
        chat_id = dest["chat_id"]
        thread_id = dest["thread_id"]
        kwargs = {"chat_id": chat_id, "text": msg}
        if thread_id is not None:
            kwargs["message_thread_id"] = thread_id

        try:
            await bot.send_message(**kwargs)
            sent_count += 1
        except TelegramError as exc:
            target = f"{chat_id}:{thread_id}" if thread_id is not None else str(chat_id)
            failed.append(target)
            logging.error("Trimitere esuata pentru destinatia Telegram %s: %s", target, exc)

    if sent_count == 0:
        raise RuntimeError(
            "Nu s-a putut trimite alerta in nicio destinatie Telegram. "
            f"Destinatii esuate: {', '.join(failed) if failed else 'n/a'}"
        )

    if failed:
        logging.warning(
            "Alerte trimise partial: %s reusite, %s esuate (%s).",
            sent_count,
            len(failed),
            ", ".join(failed),
        )
    else:
        logging.info(
            "[NOTIFIER] Rezumat trimis pentru %s ticket(e) in %s destinatie(i).",
            len(tickets),
            sent_count,
        )