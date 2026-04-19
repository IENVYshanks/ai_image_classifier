import numpy as np
from deepface import DeepFace
from sklearn.cluster import DBSCAN
from src.models.person import Person
from src.models.image_face import ImageFace
from sqlalchemy.orm import Session
from datetime import datetime, timezone


def extract_face_embedding(image):
    """
    Extract face embedding using DeepFace
    Returns embedding vector or None if no face detected
    """
    try:
        embedding = DeepFace.represent(
            image,
            model_name="Facenet512",
            enforce_detection=False
        )
        return embedding[0]['embedding']
    except Exception as e:
        print(f"Error extracting embedding: {e}")
        return None


def cluster_faces(embeddings, eps=0.5, min_samples=1):
    """
    Cluster face embeddings using DBSCAN
    Returns cluster labels for each embedding
    
    eps: maximum distance between two samples
    min_samples: minimum number of samples in a cluster
    """
    if len(embeddings) < 2:
        return [0]
    
    embedding_array = np.array(embeddings)
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(embedding_array)
    return clustering.labels_


def process_folder_and_cluster(folder_id: str, user_id, db: Session):
    """
    Main function: Download images from Drive, detect faces, cluster, and organize
    
    Steps:
    1. List all images in folder
    2. Extract face embeddings
    3. Cluster faces using DBSCAN
    4. Create Person records and Drive folders
    5. Copy images to corresponding person folders
    """
    from src.services.drive_service import (
        list_images_in_folder,
        download_image_from_drive,
        create_person_folder,
        copy_file_in_drive
    )
    
    try:
        # Step 1: List images in folder
        images = list_images_in_folder(folder_id, user_id, db)
        if not images:
            return {"message": "No images found in folder"}
        
        print(f"Found {len(images)} images")
        
        # Step 2: Extract embeddings
        embeddings = []
        image_data = []
        
        for img_file in images:
            try:
                print(f"Processing: {img_file['name']}")
                image = download_image_from_drive(img_file['id'], user_id, db)
                embedding = extract_face_embedding(image)
                
                if embedding:
                    embeddings.append(embedding)
                    image_data.append((img_file['id'], img_file['name'], embedding))
            except Exception as e:
                print(f"Error processing {img_file['name']}: {e}")
        
        if not embeddings:
            return {"message": "No faces detected in any images"}
        
        print(f"Extracted embeddings from {len(embeddings)} faces")
        
        # Step 3: Cluster faces
        cluster_labels = cluster_faces([e for _, _, e in image_data])
        unique_clusters = len(set(cluster_labels))
        print(f"Created {unique_clusters} clusters")
        
        # Step 4 & 5: Create persons and organize in Drive
        person_folders = {}
        
        for idx, (file_id, file_name, embedding) in enumerate(image_data):
            cluster_id = cluster_labels[idx]
            
            # Create person if new cluster
            if cluster_id not in person_folders:
                person_label = f"Person {cluster_id + 1}"
                person = Person(
                    user_id=user_id,
                    label=person_label,
                    image_count=0
                )
                db.add(person)
                db.commit()
                db.refresh(person)
                
                print(f"Created Person: {person_label} (ID: {person.id})")
                
                # Create folder in Drive
                drive_folder_id = create_person_folder(
                    person_label,
                    folder_id,
                    user_id,
                    db
                )
                person_folders[cluster_id] = (person.id, drive_folder_id)
            
            person_id, drive_folder_id = person_folders[cluster_id]
            
            # Copy file to person folder in Drive
            copy_file_in_drive(file_id, drive_folder_id, user_id, db)
            
            # Store in DB
            image_face = ImageFace(
                user_id=user_id,
                person_id=person_id,
                drive_file_id=file_id,
                drive_file_name=file_name,
                confidence_score=0.9,
                classified_at=datetime.now(timezone.utc)
            )
            db.add(image_face)
        
        db.commit()
        
        result = {
            "message": "Processing completed successfully",
            "total_images": len(image_data),
            "total_clusters": len(person_folders),
            "folder_id": folder_id
        }
        print(f"Result: {result}")
        return result
        
    except Exception as e:
        print(f"Error in process_folder_and_cluster: {e}")
        db.rollback()
        return {"error": str(e)}
