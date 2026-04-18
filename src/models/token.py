from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.db import Base

class DriveToken(Base):
    __tablename__ = "drive_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    access_token_enc = Column(String, nullable=False)   # Fernet-encrypted
    refresh_token_enc = Column(String, nullable=False)  # Fernet-encrypted
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    scopes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="drive_tokens")