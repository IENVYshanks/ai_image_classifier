import requests


DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"


def list_drive_files(access_token: str, page_size: int = 10) -> list[dict]:
    """
    List files from the authenticated user's Google Drive.
    """
    response = requests.get(
        DRIVE_FILES_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "pageSize": page_size,
            "fields": "files(id,name,mimeType,webViewLink)",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("files", [])
