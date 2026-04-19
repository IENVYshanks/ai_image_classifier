from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.db.database import get_db
from src.dependencies import get_current_user
from src.models.users import User
from src.models.person import Person
from src.models.image_face import ImageFace

router = APIRouter(prefix="/images", tags=["images"])


class ProcessFolderRequest(BaseModel):
    folder_id: str


class PersonResponse(BaseModel):
    id: str
    label: str
    image_count: int
    
    class Config:
        from_attributes = True


class ImageFaceResponse(BaseModel):
    id: str
    drive_file_id: str
    drive_file_name: str
    person_id: str
    confidence_score: float
    
    class Config:
        from_attributes = True


@router.post("/process-folder")
async def process_folder(
    request: ProcessFolderRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger background task to process images in a Google Drive folder
    
    - Detects faces in all images
    - Clusters them using DeepFace embeddings
    - Creates Drive folders for each person
    - Stores results in database
    """
    from src.services.classification_service import process_folder_and_cluster
    
    if not request.folder_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="folder_id is required"
        )
    
    background_tasks.add_task(
        process_folder_and_cluster,
        request.folder_id,
        current_user.id,
        db
    )
    
    return {
        "message": "Image processing started in background",
        "folder_id": request.folder_id,
        "status": "processing"
    }


@router.get("/persons", response_model=list[PersonResponse])
async def get_user_persons(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all detected persons (face clusters) for the current user
    """
    persons = db.query(Person).filter(Person.user_id == current_user.id).all()
    return persons


@router.get("/persons/{person_id}/images", response_model=list[ImageFaceResponse])
async def get_person_images(
    person_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all images for a specific person (face cluster)
    """
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == current_user.id
    ).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    images = db.query(ImageFace).filter(
        ImageFace.person_id == person_id,
        ImageFace.user_id == current_user.id
    ).all()
    
    return images


@router.get("/images", response_model=list[ImageFaceResponse])
async def get_all_user_images(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all detected face images for the current user
    """
    images = db.query(ImageFace).filter(
        ImageFace.user_id == current_user.id
    ).all()
    
    return images
