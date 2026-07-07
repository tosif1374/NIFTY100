from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..auth import authenticate_user, create_access_token
from ..schemas import Token

router = APIRouter()


@router.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Issue a JWT access token.
    Send as form data: username=analyst&password=nifty100pass
    Token expires after JWT_EXPIRE_MINUTES (default: 60 minutes).
    Include in all subsequent requests:
    Authorization: Bearer <access_token>
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return Token(access_token=token)