from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from app.db.document_store import get_document_store, DocumentStore
from app.core.rag_engine import answer_question, generate_flashcards, generate_summary
from app.models.question import QuestionRequest, QuestionResponse, FlashcardRequest, FlashcardResponse, SummaryRequest, SummaryResponse

router = APIRouter()

@router.post("/questions/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    document_store: DocumentStore = Depends(get_document_store)
):
    """
    Answer a question based on the uploaded documents.
    """
    # Check if document exists
    if request.document_id:
        document = document_store.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
    
    # Get answer using RAG
    answer = await answer_question(
        question=request.question,
        document_id=request.document_id,
        document_store=document_store
    )
    
    return {
        "question": request.question,
        "answer": answer,
        "document_id": request.document_id
    }

@router.post("/questions/flashcards", response_model=FlashcardResponse)
async def create_flashcards(
    request: FlashcardRequest,
    document_store: DocumentStore = Depends(get_document_store)
):
    """
    Generate flashcards based on a document or section.
    """
    # Check if document exists
    document = document_store.get_document(request.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Generate flashcards
    flashcards = await generate_flashcards(
        document_id=request.document_id,
        count=request.count,
        topic=request.topic,
        document_store=document_store
    )
    
    return {
        "document_id": request.document_id,
        "flashcards": flashcards
    }

@router.post("/questions/summary", response_model=SummaryResponse)
async def create_summary(
    request: SummaryRequest,
    document_store: DocumentStore = Depends(get_document_store)
):
    """
    Generate a summary of a document or section.
    """
    # Check if document exists
    document = document_store.get_document(request.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Generate summary
    summary = await generate_summary(
        document_id=request.document_id,
        max_length=request.max_length,
        document_store=document_store
    )
    
    return {
        "document_id": request.document_id,
        "summary": summary
    }
