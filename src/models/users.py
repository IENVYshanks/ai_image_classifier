from sqlalchemy import Column, String, DateTime, UUID, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.db import Base


class User(Base):
    __tablename__ = "USER"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


    drive_tokens = relationship("DriveToken", back_populates="user", cascade="all, delete")
    persons = relationship("Person", back_populates="user", cascade="all, delete")
    image_faces = relationship("ImageFace", back_populates="user", cascade="all, delete")
    grants_given = relationship("AccessGrant", foreign_keys="AccessGrant.owner_id", back_populates="owner")
    grants_received = relationship("AccessGrant", foreign_keys="AccessGrant.grantee_id", back_populates="grantee")