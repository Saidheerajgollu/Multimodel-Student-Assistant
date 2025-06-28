from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class QuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None  # If None, search across all documents

class QuestionResponse(BaseModel):
    question: str
    answer: str
    document_id: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None  # Source chunks used for the answer

class Flashcard(BaseModel):
    front: str  # Question or concept
    back: str   # Answer or explanation

class FlashcardRequest(BaseModel):
    document_id: str
    count: int = 5  # Number of flashcards to generate
    topic: Optional[str] = None  # Specific topic to focus on

class FlashcardResponse(BaseModel):
    document_id: str
    flashcards: List[Flashcard]

class SummaryRequest(BaseModel):
    document_id: str
    max_length: Optional[int] = 500  # Maximum length of summary in words

class SummaryResponse(BaseModel):
    document_id: str
    summary: str
