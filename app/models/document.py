from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    id: str
    filename: str
    status: str = "pending"  # pending, processing, ready, error

class DocumentResponse(DocumentBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class DocumentList(BaseModel):
    documents: List[DocumentResponse]
    
class DocumentChunk(BaseModel):
    id: str
    document_id: str
    content: str
    page_number: Optional[int] = None
    chunk_index: int
    metadata: Dict[str, Any] = {}
