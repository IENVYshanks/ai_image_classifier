from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from src.models.token import DriveToken
from sqlalchemy.orm import Session
import io
from PIL import Image


def get_drive_service(user_id, db: Session):
    """
    Authenticate with Google Drive using stored token
    """
    drive_token = db.query(DriveToken).filter(DriveToken.user_id == user_id).first()
    if not drive_token:
        raise ValueError("No Drive token found for user")
    
    # Use stored access token (should be decrypted if encrypted)
    credentials = Credentials(token=drive_token.access_token_enc)
    return build('drive', 'v3', credentials=credentials)


def list_images_in_folder(folder_id: str, user_id, db: Session):
    """
    List all image files in a Google Drive folder
    """
    service = get_drive_service(user_id, db)
    
    query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType)',
        pageSize=1000
    ).execute()
    
    return results.get('files', [])


def download_image_from_drive(file_id: str, user_id, db: Session):
    """
    Download image from Google Drive and return as PIL Image
    """
    service = get_drive_service(user_id, db)
    request = service.files().get_media(fileId=file_id)
    file_content = request.execute()
    
    image = Image.open(io.BytesIO(file_content))
    return image


def create_person_folder(person_label: str, parent_folder_id: str, user_id, db: Session):
    """
    Create a new folder in Google Drive for a person cluster
    """
    service = get_drive_service(user_id, db)
    
    file_metadata = {
        'name': f"Person - {person_label}",
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')


def copy_file_in_drive(file_id: str, destination_folder_id: str, user_id, db: Session):
    """
    Copy an image file to a person folder in Google Drive
    """
    service = get_drive_service(user_id, db)
    metadata = {'parents': [destination_folder_id]}
    service.files().copy(fileId=file_id, body=metadata).execute()
