import sqlite3
from pathlib import Path
from .config import DB_FILE, BUDDY_DIR


def get_conn() -> sqlite3.Connection:
    BUDDY_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            role      TEXT    NOT NULL,
            content   TEXT    NOT NULL,
            session   TEXT,
            ts        DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS facts (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            content   TEXT    NOT NULL,
            category  TEXT    DEFAULT 'general',
            ts        DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            description TEXT,
            status      TEXT    DEFAULT 'pending',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS file_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT    NOT NULL,
            operation TEXT    NOT NULL,
            status    TEXT    DEFAULT 'success',
            details   TEXT,
            ts        DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


# ── Conversations ──────────────────────────────────────────────────────────────

def add_message(role: str, content: str, session: str = None) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO conversations (role, content, session) VALUES (?,?,?)",
        (role, content, session),
    )
    conn.commit()
    conn.close()


def get_recent_history(limit: int = 20) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return list(reversed([{"role": r["role"], "content": r["content"]} for r in rows]))


# ── Facts ─────────────────────────────────────────────────────────────────────

def add_fact(content: str, category: str = "general") -> None:
    conn = get_conn()
    conn.execute("INSERT INTO facts (content, category) VALUES (?,?)", (content, category))
    conn.commit()
    conn.close()


def get_facts() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM facts ORDER BY ts DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_fact(fact_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM facts WHERE id=?", (fact_id,))
    conn.commit()
    conn.close()


# ── Tasks ─────────────────────────────────────────────────────────────────────

def add_task(title: str, description: str = None) -> None:
    conn = get_conn()
    conn.execute("INSERT INTO tasks (title, description) VALUES (?,?)", (title, description))
    conn.commit()
    conn.close()


def get_tasks(status: str = None) -> list[dict]:
    conn = get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_task_status(task_id: int, status: str) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE tasks SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, task_id),
    )
    conn.commit()
    conn.close()


def delete_task(task_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


# ── File history ──────────────────────────────────────────────────────────────

def add_file_history(file_path: str, operation: str, status: str = "success", details: str = None) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO file_history (file_path, operation, status, details) VALUES (?,?,?,?)",
        (file_path, operation, status, details),
    )
    conn.commit()
    conn.close()


def get_file_history(limit: int = 10) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM file_history ORDER BY ts DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
