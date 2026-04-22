from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.db.config import get_settings
from src.models.image import Image
from src.models.ingestion_job import IngestionJob
from src.models.user_folder import UserFolder
from src.services import drive_service
from src.services.face_service import (
    assign_qdrant_point_ids,
    extract_faces_and_embeddings,
    replace_image_faces,
)
from src.services.folder_service import (
    increment_folder_failed,
    increment_folder_processed,
    mark_folder_done,
    mark_folder_failed,
    mark_folder_processing,
    set_folder_total_images,
    upsert_user_folder,
)
from src.services.image_service import (
    mark_image_done,
    mark_image_failed,
    mark_image_processing,
    set_image_storage_location,
)
from src.services.storage_service import (
    storage_is_configured,
    upload_image,
)
from src.services.job_service import (
    create_ingestion_job,
    increment_job_failed,
    increment_job_processed,
    mark_job_done,
    mark_job_failed,
    mark_job_running,
    set_job_total,
)
from src.services.vector_service import upsert_face_embeddings

logger = logging.getLogger(__name__)


def create_or_update_folder(
    db: Session,
    *,
    user_id,
    drive_folder_id: str,
    folder_name: str | None = None,
) -> UserFolder:
    return upsert_user_folder(
        db,
        user_id=user_id,
        drive_folder_id=drive_folder_id,
        folder_name=folder_name,
    )


def start_ingestion_job(
    db: Session,
    *,
    user_id,
    folder_id,
    job_type: str = "full",
) -> IngestionJob:
    return create_ingestion_job(db, user_id=user_id, folder_id=folder_id, job_type=job_type)


def get_folder_for_user(db: Session, *, folder_id, user_id) -> UserFolder | None:
    return (
        db.query(UserFolder)
        .filter(UserFolder.id == folder_id, UserFolder.user_id == user_id)
        .first()
    )


def get_job_for_user(db: Session, *, job_id, user_id) -> IngestionJob | None:
    return (
        db.query(IngestionJob)
        .filter(IngestionJob.id == job_id, IngestionJob.user_id == user_id)
        .first()
    )


def get_all_images_for_user(db: Session, *, user_id) -> list[Image]:
    return (
        db.query(Image)
        .filter(Image.user_id == user_id)
        .order_by(Image.ingested_at.desc(), Image.drive_file_name.asc())
        .all()
    )


def run_ingestion_job(db: Session, *, job_id) -> IngestionJob:
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if job is None:
        raise ValueError("Ingestion job not found")

    folder = None
    if job.folder_id:
        folder = db.query(UserFolder).filter(UserFolder.id == job.folder_id).first()
    if folder is None:
        return mark_job_failed(db, job, "Folder not found for ingestion job")

    try:
        logger.info("Starting ingestion job_id=%s user_id=%s", job.id, job.user_id)
        mark_job_running(db, job, auto_commit=False)
        mark_folder_processing(db, folder, auto_commit=False)
        db.commit()

        drive_files = drive_service.list_images_in_folder(
            folder.drive_folder_id,
            job.user_id,
            db,
        )
        set_job_total(db, job, len(drive_files), auto_commit=False)
        set_folder_total_images(db, folder, len(drive_files), auto_commit=False)
        db.commit()
        logger.info(
            "Ingestion job_id=%s discovered %s files for folder_id=%s",
            job.id,
            len(drive_files),
            folder.drive_folder_id,
        )

        for drive_file in drive_files:
            image = None
            try:
                logger.info(
                    "Processing Drive file_id=%s name=%s for job_id=%s",
                    drive_file.get("id"),
                    drive_file.get("name"),
                    job.id,
                )
                image = upsert_image_from_drive_file(
                    db,
                    user_id=job.user_id,
                    folder_id=folder.id,
                    drive_file=drive_file,
                    auto_commit=False,
                )
                mark_image_processing(db, image, auto_commit=False)
                image_bytes = drive_service.download_file_bytes(
                    drive_file["id"],
                    job.user_id,
                    db,
                )
                if storage_is_configured():
                    storage_key = upload_image(
                        user_id=job.user_id,
                        image_id=image.id,
                        image_bytes=image_bytes,
                        mime_type=image.mime_type,
                    )
                    set_image_storage_location(
                        db,
                        image,
                        storage_key=storage_key,
                        storage_bucket=get_settings().SUPABASE_STORAGE_BUCKET or "",
                        auto_commit=False,
                    )
                    logger.info(
                        "Stored image_id=%s in bucket=%s path=%s",
                        image.id,
                        get_settings().SUPABASE_STORAGE_BUCKET,
                        storage_key,
                    )
                faces = extract_faces_and_embeddings(image_bytes)
                logger.info(
                    "Detected %s faces for image_id=%s drive_file_id=%s",
                    len(faces),
                    image.id,
                    drive_file.get("id"),
                )
                face_rows = replace_image_faces(
                    db,
                    user_id=job.user_id,
                    image=image,
                    faces=faces,
                )
                point_ids = upsert_face_embeddings(
                    faces=[
                        {
                            "face_id": face_row.id,
                            "user_id": job.user_id,
                            "image_id": image.id,
                            "cluster_id": face_row.cluster_id,
                            "embedding": face_payload["embedding"],
                        }
                        for face_row, face_payload in zip(face_rows, faces)
                    ]
                )
                assign_qdrant_point_ids(db, face_point_ids=point_ids)
                mark_image_done(db, image, face_count=len(faces), auto_commit=False)
                increment_job_processed(db, job, auto_commit=False)
                increment_folder_processed(db, folder, auto_commit=False)
                db.commit()
                logger.info(
                    "Completed processing image_id=%s job_id=%s",
                    image.id,
                    job.id,
                )
            except Exception as exc:
                db.rollback()
                logger.exception(
                    "Failed processing drive_file_id=%s job_id=%s: %s",
                    drive_file.get("id"),
                    job.id,
                    exc,
                )
                if image is not None:
                    image = db.query(Image).filter(Image.id == image.id).first()
                    if image is not None:
                        mark_image_failed(
                            db,
                            image,
                            error_message=str(exc),
                            auto_commit=False,
                        )
                increment_job_failed(
                    db,
                    job,
                    file_id=drive_file.get("id"),
                    error_message=str(exc),
                    auto_commit=False,
                )
                increment_folder_failed(
                    db,
                    folder,
                    error_message=str(exc),
                    auto_commit=False,
                )
                db.commit()

        job = db.query(IngestionJob).filter(IngestionJob.id == job.id).first()
        folder = db.query(UserFolder).filter(UserFolder.id == folder.id).first()
        if job.failed and job.processed == 0:
            mark_folder_failed(
                db,
                folder,
                job.error_message or "All files failed during ingestion",
                auto_commit=False,
            )
            mark_job_failed(
                db,
                job,
                job.error_message or "All files failed during ingestion",
                auto_commit=False,
            )
            db.commit()
            logger.warning("Ingestion job_id=%s failed for all files", job.id)
            return job

        mark_folder_done(db, folder, auto_commit=False)
        mark_job_done(db, job, auto_commit=False)
        db.commit()
        logger.info(
            "Finished ingestion job_id=%s processed=%s failed=%s",
            job.id,
            job.processed,
            job.failed,
        )
        return job
    except Exception as exc:
        db.rollback()
        logger.exception("Unhandled ingestion failure job_id=%s: %s", job.id, exc)
        if folder is not None:
            mark_folder_failed(db, folder, str(exc), auto_commit=False)
        mark_job_failed(db, job, str(exc), auto_commit=False)
        db.commit()
        return job


def upsert_image_from_drive_file(
    db: Session,
    *,
    user_id,
    folder_id,
    drive_file: dict,
    auto_commit: bool = True,
) -> Image:
    image = (
        db.query(Image)
        .filter(Image.user_id == user_id, Image.drive_file_id == drive_file["id"])
        .first()
    )
    metadata = drive_file.get("imageMediaMetadata") or {}
    taken_at = _parse_drive_datetime(metadata.get("time"))
    file_size = drive_file.get("size")
    file_size_bytes = int(file_size) if file_size is not None else None

    if image is None:
        image = Image(
            user_id=user_id,
            folder_id=folder_id,
            drive_file_id=drive_file["id"],
        )
        db.add(image)

    image.folder_id = folder_id
    image.drive_file_name = drive_file.get("name")
    image.mime_type = drive_file.get("mimeType")
    image.file_size_bytes = file_size_bytes
    image.width = metadata.get("width")
    image.height = metadata.get("height")
    image.taken_at = taken_at
    image.status = "pending"
    image.error_message = None
    image.updated_at = datetime.now(timezone.utc)

    if auto_commit:
        db.commit()
        db.refresh(image)
    else:
        db.flush()
    return image


def _parse_drive_datetime(value: str | None):
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None
