# app/db_queue.py

import sqlite3
import json
import logging
import threading
from contextlib import contextmanager

DB_PATH = "offline_queue.db"

class DBQueue:
    """
    Queue that stores payloads in a SQLite database for offline persistence.
    """

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._initialize_db()

    def _initialize_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS offline_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
            """)
            conn.commit()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            yield conn
        finally:
            conn.close()

    def enqueue(self, data):
        """
        Save payload to DB queue.
        """
        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO offline_queue (path, payload) VALUES (?, ?)",
                    (data["path"], json.dumps(data["payload"]))
                )
                conn.commit()
        logging.info(f"💾 Queued offline payload for {data['path']}.")

    def flush(self, post_func):
        """
        Attempt to post and delete all queued payloads.
        """
        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, path, payload FROM offline_queue")
                rows = cursor.fetchall()

                for row in rows:
                    payload_id, path, payload_json = row
                    try:
                        payload_data = json.loads(payload_json)
                        post_func({"path": path, "payload": payload_data})
                        self._delete_by_id(conn, payload_id)
                        logging.info(f"✅ Flushed payload {payload_id} for {path}.")
                    except Exception as e:
                        logging.error(f"⚠️ Failed to flush payload {payload_id}: {e}")
                conn.commit()

    def _delete_by_id(self, conn, payload_id):
        """
        Delete a single payload by ID.
        """
        conn.execute("DELETE FROM offline_queue WHERE id = ?", (payload_id,))
