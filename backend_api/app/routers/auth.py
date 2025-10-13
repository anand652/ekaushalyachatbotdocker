#backend_api/app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import crud, schemas, security
from ..database import SessionLocal
from pydantic import BaseModel

router = APIRouter()

class TokenRequest(BaseModel):
    email: str
    password: str
    company_id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email_and_company(
        db, email=user.email, company_id=user.company_id
    )
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered for this company")
    return crud.create_user(db=db, user=user)

@router.post("/login")
def login_for_access_token(request: TokenRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email_and_company(
        db, email=request.email, company_id=request.company_id
    )
    if not user or not security.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, password, or company selection",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "company_id": user.company_id,
            "name": user.name  # NEW
        }
    )
    return {"access_token": access_token, "token_type": "bearer"}
