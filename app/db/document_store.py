from datetime import datetime
from typing import Dict, List, Optional
import uuid

from app.models.document import DocumentResponse, DocumentChunk

class DocumentStore:
    def __init__(self):
        self.documents: Dict[str, DocumentResponse] = {}
        self.chunks: Dict[str, List[DocumentChunk]] = {}
    
    def add_document(self, id: str, filename: str, file_path: str) -> DocumentResponse:
        """Add a new document to the store."""
        now = datetime.now()
        document = DocumentResponse(
            id=id,
            filename=filename,
            status="processing",
            created_at=now,
            updated_at=now
        )
        self.documents[id] = document
        return document
    
    def get_document(self, doc_id: str) -> Optional[DocumentResponse]:
        """Get a document by ID."""
        return self.documents.get(doc_id)
    
    def get_all_documents(self) -> List[DocumentResponse]:
        """Get all documents."""
        return list(self.documents.values())
    
    def update_document_status(self, doc_id: str, status: str, error_message: Optional[str] = None) -> Optional[DocumentResponse]:
        """Update the status of a document."""
        if doc_id not in self.documents:
            return None
        
        document = self.documents[doc_id]
        document.status = status
        document.updated_at = datetime.now()
        
        if error_message:
            document.error_message = error_message
        
        return document
    
    def add_chunks(self, doc_id: str, chunks: List[DocumentChunk]) -> bool:
        """Add chunks for a document."""
        if doc_id not in self.documents:
            return False
        
        self.chunks[doc_id] = chunks
        self.update_document_status(doc_id, "ready")
        return True
    
    def get_chunks(self, doc_id: str) -> List[DocumentChunk]:
        """Get all chunks for a document."""
        return self.chunks.get(doc_id, [])
    
    def get_all_chunks(self) -> List[DocumentChunk]:
        """Get all chunks across all documents."""
        all_chunks = []
        for chunks in self.chunks.values():
            all_chunks.extend(chunks)
        return all_chunks

# Singleton instance for dependency injection
_document_store = None

def get_document_store() -> DocumentStore:
    """Get the document store singleton instance."""
    global _document_store
    if _document_store is None:
        _document_store = DocumentStore()
    return _document_store
