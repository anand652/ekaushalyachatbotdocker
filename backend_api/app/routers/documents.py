#backend_api/app/routers/documents.py

import os
import uuid
import requests
import chromadb
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Body
from fastapi.responses import Response
from sqlalchemy.orm import Session
from .. import models, security
from ..database import SessionLocal
from ..processing import delete_document_from_chroma

# Initialize ChromaDB client and collection
db_client = chromadb.PersistentClient(path="chroma_db")
collection = db_client.get_or_create_collection(name="company_documents")

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# Upload file endpoint
# -----------------------
@router.post("/upload")
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_admin: dict = Depends(security.get_current_admin_user),
    db: Session = Depends(get_db)
):
    company_id = current_admin["company_id"]
    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file upload.")

    db_document = models.Document(
        filename=file.filename,
        content_type=getattr(file, "content_type", None) or "application/pdf",
        file_size=len(file_bytes),
        file_data=file_bytes,
        company_id=company_id,
        status=models.StatusEnum.processing,
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    safe_name = file.filename.replace(os.sep, "_")
    temp_file_path = f"temp_{db_document.id}_{uuid.uuid4().hex}_{safe_name}"
    with open(temp_file_path, "wb") as f:
        f.write(file_bytes)

    from ..processing import process_and_store_document
    background_tasks.add_task(
        process_and_store_document,
        file_path=temp_file_path,
        filename=file.filename,
        company_id=company_id,
        document_id=db_document.id
    )

    return {
        "message": "File uploaded and processing has started.",
        "document_id": db_document.id,
        "filename": file.filename
    }

# -----------------------
# Upload from URL endpoint
# -----------------------
@router.post("/upload_url")
def upload_url_document(
    background_tasks: BackgroundTasks,
    url: str = Body(..., embed=True),
    current_admin: dict = Depends(security.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin-only: fetch a document from URL, save it, and process it in background.
    """
    company_id = current_admin["company_id"]

    # Fetch the file from URL
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    file_bytes = response.content
    content_type = response.headers.get("Content-Type", "application/pdf")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="URL returned empty content.")

    # Generate filename from URL
    filename = url.split("/")[-1] or f"url_doc_{uuid.uuid4().hex}"

    db_document = models.Document(
        filename=filename,
        content_type=content_type,
        file_size=len(file_bytes),
        file_data=file_bytes,
        company_id=company_id,
        status=models.StatusEnum.processing,
        source_url=url
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    temp_file_path = f"temp_{db_document.id}_{uuid.uuid4().hex}_{filename}"
    with open(temp_file_path, "wb") as f:
        f.write(file_bytes)

    from ..processing import process_and_store_document
    background_tasks.add_task(
        process_and_store_document,
        file_path=temp_file_path,
        filename=filename,
        company_id=company_id,
        document_id=db_document.id
    )

    return {
        "message": "URL content fetched and processing started.",
        "document_id": db_document.id,
        "filename": filename
    }

# -----------------------
# Download endpoint
# -----------------------
@router.get("/download/{document_id}")
def download_document(
    document_id: int,
    current_admin: dict = Depends(security.get_current_admin_user),
    db: Session = Depends(get_db)
):
    company_id = current_admin["company_id"]
    doc = (
        db.query(models.Document)
        .filter(models.Document.id == document_id, models.Document.company_id == company_id)
        .first()
    )
    if not doc or not doc.file_data:
        raise HTTPException(status_code=404, detail="Document not found or no file stored.")

    return Response(
        content=doc.file_data,
        media_type=doc.content_type or "application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{doc.filename}"'
        },
    )

# -----------------------
# List uploaded documents
# -----------------------
@router.get("/")
def list_documents(
    current_admin: dict = Depends(security.get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin-only: list all documents uploaded for the admin's company
    """
    company_id = current_admin["company_id"]
    docs = db.query(models.Document).filter(models.Document.company_id == company_id).all()

    if not docs:
        return []

    # Return minimal info for frontend display, including content_type and source_url
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "status": d.status.value,
            "uploaded_at": d.uploaded_at,
            "content_type": d.content_type,
            "source_url": getattr(d, 'source_url', None) # Safely get the new attribute
        }
        for d in docs
    ]

# -----------------------
# Delete document endpoint
# -----------------------
@router.delete("/delete/{document_id}")
def delete_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    current_admin: dict = Depends(security.get_current_admin_user),
    db: Session = Depends(get_db)
):
    company_id = current_admin["company_id"]
    db_document = (
        db.query(models.Document)
        .filter(models.Document.id == document_id, models.Document.company_id == company_id)
        .first()
    )

    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    # Delete from PostgreSQL
    db.delete(db_document)
    db.commit()

    # Add background task to delete from ChromaDB
    background_tasks.add_task(delete_document_from_chroma, document_id)

    return {"message": f"Document {document_id} and its embeddings are scheduled for deletion."}