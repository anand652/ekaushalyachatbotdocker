# backend_api/app/schemas.py

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from .models import RoleEnum, StatusEnum

# --- User Schemas ---
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: RoleEnum

class UserCreate(UserBase):
    password: str
    company_id: int

class User(UserBase):
    id: int
    company_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Document Schemas ---
class DocumentBase(BaseModel):
    filename: str

class Document(DocumentBase):
    id: int
    company_id: int
    status: StatusEnum
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Company Schemas ---
class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    users: list[User] = []
    documents: list[Document] = []

    model_config = ConfigDict(from_attributes=True)

# --- NEW: Simple schema for public company data ---
class CompanyPublic(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# --- Chat Schemas ---
class ChatQuery(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str