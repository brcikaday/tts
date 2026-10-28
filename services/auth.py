from core.security import hash_password, verify_password, create_access_token
from models.user import User
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from schemas.user import UserCreate, UserLogin
from services.system_log_service import log_system_event

def register_user(user_data: UserCreate, db: Session) -> dict:
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = hash_password(user_data.password)
    new_user = User(name=user_data.name, email=user_data.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email})
    log_system_event(db, new_user.id, "USER_REGISTERED", "Registered account")
    return {'access_token': access_token, 'token_type': 'bearer', 'user': new_user}


def authenticate_user(user_data: UserLogin, db: Session) -> str:
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    log_system_event(db, user.id, "USER_LOGGED_IN", "Logged in successfully")
    return  {'access_token': access_token, 'token_type': 'bearer', 'user': user}


    
