from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import create_access_token, get_current_user
from ..models import User
from ..schemas import UserCreate, Login
from ..crud import get_user_by_username, get_user_by_email, create_user
from ..security import verify_password
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    current_user = get_current_user(db=db) if "Authorization" in router.dependencies else None
    if user.role != "user" and (not current_user or current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Only admin can assign other roles")
    new_user = create_user(db, user.dict(exclude_unset=True))
    access_token = create_access_token({"user_id": new_user.user_id, "username": new_user.username}, timedelta(minutes=30))
    return {"token": access_token, "user_id": new_user.user_id}

@router.post("/login")
async def login(login_data: Login, db: Session = Depends(get_db)):
    user = get_user_by_username(db, login_data.username)
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        {"user_id": user.user_id, "username": user.username, "role": user.role},
        timedelta(minutes=30)
    )
    return {
        "token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "role": user.role
    } 