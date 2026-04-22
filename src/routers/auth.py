import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.users import User

from src.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def build_token_response(user: User) -> TokenResponse:
    subject = str(user.id)
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return build_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return build_token_response(user)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest) -> AccessTokenResponse:
    try:
        token_payload = decode_jwt(payload.refresh_token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    if token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    subject = token_payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
        )

    return AccessTokenResponse(access_token=create_access_token(subject))


@router.get("/google/login")
async def google_login():
    from src.services.google_auth import get_oauth_client
    client = get_oauth_client()
    authorization_url, state = client.create_authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        scope=["openid", "email", "profile"],
    )
    return {"authorization_url": authorization_url, "state": state}


@router.get("/google/callback")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    from src.services.google_auth import get_oauth_client
    client = get_oauth_client()
    token = await client.fetch_token(
        "https://oauth2.googleapis.com/token",
        code=code,
    )
    # Fetch user info
    user_info = await client.get("https://www.googleapis.com/oauth2/v2/userinfo")
    user_data = user_info.json()
    
    # Check if user exists, else create
    user = db.query(User).filter(User.email == user_data["email"]).first()
    if not user:
        user = User(email=user_data["email"], hashed_password="")  # No password for OAuth
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate JWT tokens
    return build_token_response(user)
