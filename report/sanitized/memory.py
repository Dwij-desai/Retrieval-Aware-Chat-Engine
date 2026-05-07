import sqlite3
from contextlib import closing

try:
    from backend.config import settings
except ModuleNotFoundError as exc:
    if exc.name not in {"backend", "backend.config"}:
        raise
    from config import settings


def _connect():
    return sqlite3.connect(settings.memory_db_path)


def init_db() -> None:
    """Create the chat memory table if it doesn't exist."""
    with closing(_connect()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id ON chat_messages(chat_id)"
        )
        conn.commit()


def add_message(chat_id: str, role: str, content: str) -> None:
    """Persist a single chat message."""
    if not chat_id or not role or content is None:
        return
    with closing(_connect()) as conn:
        conn.execute(
            "INSERT INTO chat_messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        conn.commit()


def get_history(chat_id: str, limit: int | None = None) -> list[tuple[str, str]]:
    """Return the most recent messages for a chat_id, oldest-first."""
    if not chat_id:
        return []
    max_messages = limit if limit is not None else settings.memory_max_messages
    with closing(_connect()) as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (chat_id, max_messages),
        ).fetchall()
    return list(reversed(rows))


def clear_history(chat_id: str) -> None:
    """Delete all messages for a chat_id (optional utility)."""
    if not chat_id:
        return
    with closing(_connect()) as conn:
        conn.execute("DELETE FROM chat_messages WHERE chat_id = ?", (chat_id,))
        conn.commit()
