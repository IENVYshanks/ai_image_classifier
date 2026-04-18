from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid, secrets
from src.db import Base

class AccessGrant(Base):
    __tablename__ = "access_grants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    grantee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    share_token = Column(String, unique=True, default=lambda: secrets.token_urlsafe(32), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", foreign_keys=[owner_id], back_populates="grants_given")
    grantee = relationship("User", foreign_keys=[grantee_id], back_populates="grants_received")
    person = relationship("Person", back_populates="access_grants")