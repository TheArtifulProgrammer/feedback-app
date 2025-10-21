"""Data models for feedback application"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Feedback:
    """Feedback model"""
    id: Optional[int]
    message: str
    created_at: str
    updated_at: str

    @staticmethod
    def create(message: str) -> 'Feedback':
        """Create new feedback instance"""
        now = datetime.utcnow().isoformat()
        return Feedback(
            id=None,
            message=message,
            created_at=now,
            updated_at=now
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'message': self.message,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
