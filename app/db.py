import sqlite3
from typing import Optional, Tuple
from .config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_strikes (
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        strikes INTEGER NOT NULL DEFAULT 0,
        last_reason TEXT,
        updated_at INTEGER NOT NULL,
        PRIMARY KEY (chat_id, user_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_settings (
        chat_id INTEGER PRIMARY KEY,
        welcome_text TEXT,
        rules_text TEXT
    );
    """)

    conn.commit()
    conn.close()

def get_chat_settings(chat_id: int) -> Tuple[Optional[str], Optional[str]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT welcome_text, rules_text FROM chat_settings WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None, None
    return row["welcome_text"], row["rules_text"]

def set_welcome(chat_id: int, text: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chat_settings(chat_id, welcome_text, rules_text)
        VALUES(?, ?, COALESCE((SELECT rules_text FROM chat_settings WHERE chat_id=?), NULL))
        ON CONFLICT(chat_id) DO UPDATE SET welcome_text=excluded.welcome_text
    """, (chat_id, text, chat_id))
    conn.commit()
    conn.close()

def set_rules(chat_id: int, text: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chat_settings(chat_id, welcome_text, rules_text)
        VALUES(?, COALESCE((SELECT welcome_text FROM chat_settings WHERE chat_id=?), NULL), ?)
        ON CONFLICT(chat_id) DO UPDATE SET rules_text=excluded.rules_text
    """, (chat_id, chat_id, text))
    conn.commit()
    conn.close()

def get_strikes(chat_id: int, user_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT strikes FROM user_strikes WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    row = cur.fetchone()
    conn.close()
    return int(row["strikes"]) if row else 0

def set_strikes(chat_id: int, user_id: int, strikes: int, reason: str, ts: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_strikes(chat_id, user_id, strikes, last_reason, updated_at)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(chat_id, user_id) DO UPDATE SET
            strikes=excluded.strikes,
            last_reason=excluded.last_reason,
            updated_at=excluded.updated_at
    """, (chat_id, user_id, strikes, reason, ts))
    conn.commit()
    conn.close()

def forgive_user(chat_id: int, user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_strikes WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    conn.commit()
    conn.close()
