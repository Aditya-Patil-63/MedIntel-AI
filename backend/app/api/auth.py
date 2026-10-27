"""
MedIntel AI — Authentication API Endpoints.

Provides registration, login, and profile retrieval endpoints for mobile and web clients.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.session import get_db
from app.models.models import User
from app.schemas.auth import AuthResponse, GoogleLoginRequest, UserLoginRequest, UserRegisterRequest, UserResponse

logger = logging.getLogger("medintel.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Create a new user profile with hashed password and return an access token."""
    normalized_email = request.email.strip().lower()

    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in.",
        )

    new_user = User(
        name=request.name.strip(),
        email=normalized_email,
        hashed_password=hash_password(request.password),
        language_preference=(request.language_preference or "english").strip().lower(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info("New user registered successfully: id=%d, email=%s", new_user.id, new_user.email)

    token = create_access_token(user_id=new_user.id, email=new_user.email)
    return AuthResponse(
        user=UserResponse.model_validate(new_user),
        access_token=token,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate existing user",
)
def login(request: UserLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Validate credentials and return user profile with access token."""
    normalized_email = request.email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials.",
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials.",
        )

    logger.info("User logged in successfully: id=%d, email=%s", user.id, user.email)

    token = create_access_token(user_id=user.id, email=user.email)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=token,
    )


@router.post(
    "/google",
    response_model=AuthResponse,
    summary="Authenticate or register user via Google account",
)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Find or automatically register a user authenticating via Google account."""
    import secrets

    normalized_email = request.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user:
        # Register new Google authenticated user
        user = User(
            name=request.name.strip() or "Google User",
            email=normalized_email,
            hashed_password=hash_password(secrets.token_urlsafe(24)),
            language_preference=(request.language_preference or "english").strip().lower(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("New user registered via Google: id=%d, email=%s", user.id, user.email)
    else:
        logger.info("Existing user signed in via Google: id=%d, email=%s", user.id, user.email)

    token = create_access_token(user_id=user.id, email=user.email)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile information for the currently authenticated user."""
    return UserResponse.model_validate(current_user)
