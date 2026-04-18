from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.db import Base

class Person(Base):
    __tablename__ = "persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=True)           # e.g. "Person 1" or "Alice"
    embedding_s3_key = Column(String, nullable=True)  # mean embedding vector stored in S3
    thumbnail_s3_key = Column(String, nullable=True)  # representative face crop
    image_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="persons")
    image_faces = relationship("ImageFace", back_populates="person", cascade="all, delete")
    access_grants = relationship("AccessGrant", back_populates="person", cascade="all, delete")