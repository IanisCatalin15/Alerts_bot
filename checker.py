from datetime import datetime, timedelta

from config import ALERT_THRESHOLD_MINUTES, ALLOWED_ASSIGNEES
from state import clear_alert, get_alerted_assignee, mark_alerted

IT_DISPACHER_ALIASES = ["IT Dispatcher"]


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _is_unknown_assignee(value: str) -> bool:
    v = _norm(value)
    return v in {"", "n/a", "neidentificat", "necunoscut", "-"}


def _name_matches(needle_list: list[str], assignee: str) -> bool:
    a = _norm(assignee)
    return any(_norm(n) in a for n in needle_list if _norm(n))


def _is_it_dispacher(assignee: str) -> bool:
    return _name_matches(IT_DISPACHER_ALIASES, assignee)


def _should_send_for_key(key: str, assignee: str) -> bool:
    """
    Send alert if:
    - ticket was never alerted, or
    - assignee changed since previous alert (re-alert on reassignment).
    """
    prev = get_alerted_assignee(key)
    if prev is None:
        return True
    return _norm(prev) != _norm(assignee)


def check_wrong_assignee_tickets(tickets: list[dict]) -> list[dict]:
    alerts = []
    now = datetime.now()
    threshold = timedelta(minutes=ALERT_THRESHOLD_MINUTES)

    for ticket in tickets:
        ticket_id = str(ticket.get("id", "")).strip()
        if not ticket_id or ticket_id.startswith("template_"):
            continue

        assignee = (ticket.get("assignee") or "").strip()
        assigned_at = ticket.get("assigned_at")
        key = f"it_core:{ticket_id}"
        if _is_unknown_assignee(assignee):
            continue

        is_allowed = _name_matches(ALLOWED_ASSIGNEES, assignee)
        is_dispacher = _is_it_dispacher(assignee)
        should_notify = is_dispacher or (not is_allowed)

        if not should_notify:
            clear_alert(key)
            continue

        if assigned_at is None:
            if _should_send_for_key(key, assignee):
                mark_alerted(key, assignee)
                alerts.append({**ticket, "duration_minutes": -1})  # NECUNOSCUT
            continue

        minutes_since_assign = int((now - assigned_at).total_seconds() / 60)
        if minutes_since_assign < 0:
            minutes_since_assign = 0

        if (now - assigned_at) >= threshold and _should_send_for_key(key, assignee):
            mark_alerted(key, assignee)
            alerts.append({**ticket, "duration_minutes": minutes_since_assign})

    return alerts


def check_group3_presence_tickets(tickets: list[dict]) -> list[dict]:
    watch_list = ALLOWED_ASSIGNEES + IT_DISPACHER_ALIASES

    alerts = []
    now = datetime.now()

    for ticket in tickets:
        ticket_id = str(ticket.get("id", "")).strip()
        if not ticket_id or ticket_id.startswith("template_"):
            continue

        assignee = (ticket.get("assignee") or "").strip()
        assigned_at = ticket.get("assigned_at")
        key = f"it_departament:{ticket_id}"

        if _is_unknown_assignee(assignee):
            continue

        should_notify = _name_matches(watch_list, assignee)

        if should_notify:
            if _should_send_for_key(key, assignee):
                mark_alerted(key, assignee)

                if assigned_at is None:
                    duration_minutes = -1
                else:
                    duration_minutes = int((now - assigned_at).total_seconds() / 60)
                    if duration_minutes < 0:
                        duration_minutes = 0

                alerts.append({**ticket, "duration_minutes": duration_minutes})
        else:
            clear_alert(key)

    return alerts