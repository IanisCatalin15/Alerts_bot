import sqlite3
from datetime import datetime

DB_PATH = "state.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS alerted_tickets (
            ticket_id TEXT PRIMARY KEY,
            assignee TEXT,
            alerted_at TEXT
        )
    """)
    con.commit()
    con.close()


def get_alerted_assignee(ticket_id: str) -> str | None:
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT assignee FROM alerted_tickets WHERE ticket_id = ?", (ticket_id,)
    ).fetchone()
    con.close()
    if not row:
        return None
    return row[0]


def mark_alerted(ticket_id: str, assignee: str):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR REPLACE INTO alerted_tickets VALUES (?, ?, ?)",
        (ticket_id, assignee, datetime.now().isoformat())
    )
    con.commit()
    con.close()

def clear_alert(ticket_id: str):
    """Sterge alerta daca ticketul a fost reasignat corect."""
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM alerted_tickets WHERE ticket_id = ?", (ticket_id,))
    con.commit()
    con.close()