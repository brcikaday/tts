from services.auth import register_user, authenticate_user
from db.session import get_db
from fastapi import APIRouter, Depends
from schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from sqlalchemy.orm import Session
from core.dependencies import get_current_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=TokenResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return register_user(user_data, db)

@auth_router.post("/login", response_model= TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):

    return authenticate_user(user_data, db)


@auth_router.get("/me", response_model=UserResponse)
def read_current_user(current_user: UserResponse = Depends(get_current_user)):
    return current_user



