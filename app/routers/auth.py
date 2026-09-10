from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    user = AuthService.create_user(db, user_in)
    access_token = create_access_token(user.id)
    # Set HTTP-only cookie for web dashboard convenience
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=86400 * 30,
        samesite="lax"
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, login_in.email, login_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    access_token = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=86400 * 30,
        samesite="lax"
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserOut)
def read_me(current_user = Depends(get_current_user)):
    return current_user
