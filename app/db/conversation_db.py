import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional


class ConversationDB:
    def __init__(self, db_path: str = "conversations.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                escalated BOOLEAN DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
            );
        """)
        self.conn.commit()

    def save_message(self, conversation_id: str, role: str, content: str, confidence: float = None):
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute("""
            INSERT OR IGNORE INTO conversations (conversation_id, created_at, updated_at)
            VALUES (?, ?, ?)
        """, (conversation_id, now, now))
        self.conn.execute("""
            INSERT INTO messages (conversation_id, role, content, confidence, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (conversation_id, role, content, confidence, now))
        self.conn.execute("""
            UPDATE conversations SET updated_at = ?, message_count = message_count + 1
            WHERE conversation_id = ?
        """, (now, conversation_id))
        self.conn.commit()

    def get_conversation_history(self, conversation_id: str, max_turns: int = 10) -> List[Dict]:
        cursor = self.conn.execute("""
            SELECT role, content FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (conversation_id, max_turns * 2))
        messages = [dict(row) for row in cursor.fetchall()]
        return list(reversed(messages))

    def close(self):
        self.conn.close()


conversation_db = ConversationDB()