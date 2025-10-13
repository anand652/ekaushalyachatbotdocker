# backend_api/app/models.py

import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    LargeBinary,
    Enum,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class RoleEnum(str, enum.Enum):
    admin = "admin"
    user = "user"

class StatusEnum(str, enum.Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(RoleEnum), default=RoleEnum.user)
    company_id = Column(Integer, ForeignKey("companies.id"))
    created_at = Column(DateTime, default=datetime.utcnow) # This is the missing piece

    company = relationship("Company", back_populates="users")
    user_queries = relationship("UserQuery", back_populates="user")

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow) # This is the missing piece
    users = relationship("User", back_populates="company")
    documents = relationship("Document", back_populates="company")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    content_type = Column(String)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(StatusEnum), default=StatusEnum.processing)
    file_data = Column(LargeBinary)
    company_id = Column(Integer, ForeignKey("companies.id"))
    source_url = Column(String, nullable=True)

    company = relationship("Company", back_populates="documents")

class UserQuery(Base):
    __tablename__ = "user_queries"
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text)
    response_text = Column(Text)
    query_time = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))

    user = relationship("User", back_populates="user_queries")