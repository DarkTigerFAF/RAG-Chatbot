from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text, Index
from sqlalchemy.orm import relationship
from ..core.database import Base


class History(Base):
    __tablename__ = "history"
    __table_args__ = (
        # Speeds up per-user recent history lookups used in chat/history and context build
        Index("ix_history_user_id_timestamp", "user_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="history")
