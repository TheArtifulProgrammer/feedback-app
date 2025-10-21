"""Database operations"""
import sqlite3
import logging
from typing import List, Optional
from contextlib import contextmanager
from app.models import Feedback
from app.config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite database manager"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
        logger.info("Database initialized")

    def create_feedback(self, feedback: Feedback) -> Feedback:
        """Create new feedback"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                'INSERT INTO feedback (message, created_at, updated_at) VALUES (?, ?, ?)',
                (feedback.message, feedback.created_at, feedback.updated_at)
            )
            feedback.id = cursor.lastrowid
        logger.info(f"Created feedback: {feedback.id}")
        return feedback

    def get_all_feedback(self) -> List[Feedback]:
        """Get all feedback"""
        with self._get_connection() as conn:
            rows = conn.execute('SELECT * FROM feedback ORDER BY created_at DESC').fetchall()
            return [Feedback(**dict(row)) for row in rows]

    def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """Get feedback by ID"""
        with self._get_connection() as conn:
            row = conn.execute('SELECT * FROM feedback WHERE id = ?', (feedback_id,)).fetchone()
            return Feedback(**dict(row)) if row else None

    def update_feedback(self, feedback_id: int, message: str, updated_at: str) -> bool:
        """Update feedback"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                'UPDATE feedback SET message = ?, updated_at = ? WHERE id = ?',
                (message, updated_at, feedback_id)
            )
            success = cursor.rowcount > 0
        if success:
            logger.info(f"Updated feedback: {feedback_id}")
        return success

    def delete_feedback(self, feedback_id: int) -> bool:
        """Delete feedback"""
        with self._get_connection() as conn:
            cursor = conn.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
            success = cursor.rowcount > 0
        if success:
            logger.info(f"Deleted feedback: {feedback_id}")
        return success

    def count_feedback(self) -> int:
        """Count total feedback"""
        with self._get_connection() as conn:
            result = conn.execute('SELECT COUNT(*) as count FROM feedback').fetchone()
            return result['count'] if result else 0
