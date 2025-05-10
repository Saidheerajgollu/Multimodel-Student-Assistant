import os
import uuid
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import re
from typing import List, Dict, Any, Tuple, Optional
import asyncio
import time

from app.db.document_store import DocumentStore
from app.db.vector_store import get_vector_store
from app.models.document import DocumentChunk

# Configure paths for external tools if needed
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

# Performance configuration - optimized for better results with OpenAI
MAX_PAGES_TO_PROCESS = 50  # Limit for very large documents
CHUNK_SIZE = 2000  # Larger chunks for more context
CHUNK_OVERLAP = 200  # Sufficient overlap to maintain context between chunks
BATCH_SIZE = 10  # Process chunks in batches for vector store

# Debug function
def log_debug(message):
    with open("debug.txt", "a") as f:
        f.write(f"{message}\n")

async def process_document(doc_id: str, file_path: str, document_store: DocumentStore):
    """
    Process a document file (PDF or image) and store its content.
    
    Args:
        doc_id: The document ID
        file_path: Path to the document file
        document_store: The document store instance
    """
    try:
        start_time = time.time()
        print(f"Starting processing for document {doc_id}")
        log_debug(f"Starting processing for document {doc_id}, file: {file_path}")
        
        # Update status to processing
        document_store.update_document_status(doc_id, "processing")
        
        # Determine file type
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Process based on file type
        if file_ext == ".pdf":
            chunks = await process_pdf(doc_id, file_path)
        elif file_ext in [".png", ".jpg", ".jpeg"]:
            chunks = await process_image(doc_id, file_path)
        else:
            error_msg = f"Unsupported file format: {file_ext}"
            log_debug(error_msg)
            document_store.update_document_status(doc_id, "error", error_msg)
            return
        
        if not chunks:
            error_msg = "No content extracted from document"
            log_debug(error_msg)
            document_store.update_document_status(doc_id, "error", error_msg)
            return
            
        print(f"Extracted {len(chunks)} chunks from document")
        log_debug(f"Extracted {len(chunks)} chunks from document {doc_id}")
        
        # Store document chunks
        document_chunks = []
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            doc_chunk = DocumentChunk(
                id=chunk_id,
                document_id=doc_id,
                content=chunk["content"],
                page_number=chunk.get("page_number"),
                chunk_index=chunk.get("chunk_index", 0),
                metadata=chunk.get("metadata", {})
            )
            document_chunks.append(doc_chunk)
        
        # Add chunks to document store
        document_store.add_chunks(doc_id, document_chunks)
        
        # Add to vector store in batches
        vector_store = get_vector_store()
        
        print(f"Adding chunks to vector store in batches of {BATCH_SIZE}")
        log_debug(f"Adding {len(document_chunks)} chunks to vector store in batches of {BATCH_SIZE}")
        
        for i in range(0, len(document_chunks), BATCH_SIZE):
            batch = document_chunks[i:i+BATCH_SIZE]
            success = vector_store.add_chunks([
                {
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata
                }
                for chunk in batch
            ])
            
            if not success:
                error_msg = f"Failed to add batch {i//BATCH_SIZE + 1} to vector store"
                print(error_msg)
                log_debug(error_msg)
                # Continue processing other batches even if one fails
        
        # Update status to ready
        document_store.update_document_status(doc_id, "ready")
        
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"Document processing completed in {processing_time:.2f} seconds")
        log_debug(f"Document {doc_id} processing completed in {processing_time:.2f} seconds")
    
    except Exception as e:
        # Update status to error
        error_msg = f"Error processing document: {str(e)}"
        document_store.update_document_status(doc_id, "error", error_msg)
        print(error_msg)
        log_debug(f"Error processing document {doc_id}: {str(e)}")

async def process_pdf(doc_id: str, file_path: str) -> List[Dict[str, Any]]:
    """
    Process a PDF file and extract text content.
    
    Args:
        doc_id: The document ID
        file_path: Path to the PDF file
        
    Returns:
        List of content chunks with metadata
    """
    chunks = []
    
    # Open the PDF
    try:
        doc = fitz.open(file_path)
        
        # Limit pages for very large documents
        total_pages = len(doc)
        pages_to_process = min(total_pages, MAX_PAGES_TO_PROCESS)
        
        if total_pages > MAX_PAGES_TO_PROCESS:
            log_debug(f"Document {doc_id} has {total_pages} pages, processing first {MAX_PAGES_TO_PROCESS} pages only")
            print(f"Document has {total_pages} pages, processing first {MAX_PAGES_TO_PROCESS} pages only")
        
        # Process each page
        for page_num in range(pages_to_process):
            page = doc[page_num]
            text = page.get_text()
            
            # Skip empty pages
            if not text.strip():
                continue
            
            # Clean the text to remove excessive whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Split into chunks with optimized parameters
            text_chunks = chunk_text(text, max_chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
            
            # Add chunks with metadata
            for i, chunk_content in enumerate(text_chunks):
                chunks.append({
                    "content": chunk_content,
                    "page_number": page_num + 1,
                    "chunk_index": i,
                    "metadata": {
                        "source": "pdf",
                        "page": page_num + 1,
                        "total_pages": total_pages
                    }
                })
        
        doc.close()
        return chunks
        
    except Exception as e:
        error_msg = f"Error processing PDF {file_path}: {e}"
        print(error_msg)
        log_debug(error_msg)
        return []

async def process_image(doc_id: str, file_path: str) -> List[Dict[str, Any]]:
    """
    Process an image file and extract text using OCR.
    
    Args:
        doc_id: The document ID
        file_path: Path to the image file
        
    Returns:
        List of content chunks with metadata
    """
    chunks = []
    
    try:
        # Open the image
        image = Image.open(file_path)
        
        # Extract text using Tesseract OCR with improved configuration
        # Use --psm 3 (fully automatic page segmentation) for better results
        text = pytesseract.image_to_string(
            image,
            config='--psm 3 --oem 3'
        )
        
        # Skip empty images
        if not text.strip():
            log_debug(f"No text extracted from image {file_path}")
            return []
        
        # Clean the text to remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split into chunks with optimized parameters
        text_chunks = chunk_text(text, max_chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        
        # Add chunks with metadata
        for i, chunk_content in enumerate(text_chunks):
            chunks.append({
                "content": chunk_content,
                "chunk_index": i,
                "metadata": {
                    "source": "image",
                    "filename": os.path.basename(file_path)
                }
            })
        
        return chunks
        
    except Exception as e:
        error_msg = f"Error processing image {file_path}: {e}"
        print(error_msg)
        log_debug(error_msg)
        return []

def chunk_text(text: str, max_chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks of approximately max_chunk_size characters.
    
    Args:
        text: The text to split
        max_chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    # If text is short enough, return it as a single chunk
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Find a good breakpoint slightly before max_chunk_size
        end = start + max_chunk_size
        
        if end >= len(text):
            # Last chunk
            chunks.append(text[start:])
            break
        
        # Try to find a good sentence boundary to break on
        # First look for periods followed by space or newline
        breakpoint = text.rfind('. ', start, end)
        if breakpoint == -1:
            # Try other sentence terminators
            breakpoint = text.rfind('! ', start, end)
            if breakpoint == -1:
                breakpoint = text.rfind('? ', start, end)
                if breakpoint == -1:
                    # Try to find paragraph breaks
                    breakpoint = text.rfind('\n\n', start, end)
                    if breakpoint == -1:
                        # Try to find a newline
                        breakpoint = text.rfind('\n', start, end)
                        if breakpoint == -1:
                            # Try to find a space
                            breakpoint = text.rfind(' ', start, end)
                            if breakpoint == -1:
                                # No good breakpoint, just use max size
                                breakpoint = end
                            else:
                                breakpoint += 1  # Include the space
                        else:
                            breakpoint += 1  # Include the newline
                    else:
                        breakpoint += 2  # Include the paragraph break
                else:
                    breakpoint += 2  # Include the question mark and space
            else:
                breakpoint += 2  # Include the exclamation mark and space
        else:
            breakpoint += 2  # Include the period and space
        
        # Add the chunk
        chunks.append(text[start:breakpoint])
        
        # Start next chunk with overlap
        start = max(0, breakpoint - overlap)
    
    return chunks
