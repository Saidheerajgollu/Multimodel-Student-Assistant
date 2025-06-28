from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from typing import List
import shutil
import os
from uuid import uuid4
from app.core.document_processor import process_document
from app.db.document_store import get_document_store, DocumentStore
from app.models.document import DocumentResponse, DocumentList

router = APIRouter()

@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_store: DocumentStore = Depends(get_document_store)
):
    """
    Upload a document (PDF or image) for processing and storage.
    """
    # Generate a unique ID for the document
    doc_id = str(uuid4())
    
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Get file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # Validate file type
    if file_ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    # Define storage path
    file_path = f"uploads/{doc_id}{file_ext}"
    
    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Store document metadata
    document = document_store.add_document(
        id=doc_id,
        filename=file.filename,
        file_path=file_path
    )
    
    # Process document in the background
    background_tasks.add_task(
        process_document,
        doc_id=doc_id,
        file_path=file_path,
        document_store=document_store
    )
    
    return {"id": doc_id, "filename": file.filename, "status": "processing"}

@router.get("/documents", response_model=DocumentList)
async def list_documents(document_store: DocumentStore = Depends(get_document_store)):
    """
    List all uploaded documents.
    """
    documents = document_store.get_all_documents()
    return {"documents": documents}

@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, document_store: DocumentStore = Depends(get_document_store)):
    """
    Get details of a specific document.
    """
    document = document_store.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
