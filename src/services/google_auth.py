from authlib.integrations.httpx_client import AsyncOAuth2Client
from src.services.keys import get_tokens

tokens = get_tokens()

def get_oauth_client():
    return AsyncOAuth2Client(
        client_id=tokens.GOOGLE_CLIENT_ID,
        client_secret=tokens.GOOGLE_CLIENT_SECRET,
        redirect_uri="http://localhost:8000/auth/google/callback",  
    )