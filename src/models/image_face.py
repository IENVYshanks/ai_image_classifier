from sqlalchemy import Column, String, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from src.db import Base

class ImageFace(Base):
    __tablename__ = "image_faces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True)
    drive_file_id = Column(String, nullable=False)   # Google Drive file ID
    drive_file_name = Column(String, nullable=True)
    s3_image_key = Column(String, nullable=True)     # copy stored in S3
    confidence_score = Column(Float, nullable=True)  # DeepFace cluster confidence
    face_bbox = Column(JSONB, nullable=True)          # {"x": 10, "y": 20, "w": 80, "h": 90}
    classified_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="image_faces")
    person = relationship("Person", back_populates="image_faces")