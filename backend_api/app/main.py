# backend_api/app/main.py

from fastapi import FastAPI
from . import models
from .database import engine
# Import the new chat router
from .routers import auth, documents, chat, companies

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Company Chatbot API")

# Include the routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(companies.router, prefix="/companies", tags=["Companies"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the Chatbot API!"}