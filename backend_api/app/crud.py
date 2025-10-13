# backend_api/app/crud.py

from sqlalchemy.orm import Session
from . import models, schemas, security

def get_user_by_email_and_company(db: Session, email: str, company_id: int):
    return db.query(models.User).filter(
        models.User.email == email,
        models.User.company_id == company_id
    ).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_pwd = security.hash_password(user.password)
    db_user = models.User(
        name=user.name,  # NEW
        email=user.email,
        hashed_password=hashed_pwd,
        role=user.role,
        company_id=user.company_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
