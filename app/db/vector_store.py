import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import os
import json
import numpy as np
from collections import defaultdict
import inspect

# Helper function to log debug messages
def log_debug(message):
    with open("debug.txt", "a") as f:
        f.write(f"{message}\n")

# Add simple vector store implementation that doesn't require external dependencies
class SimpleDictVectorStore:
    """A lightweight vector store implementation using dictionaries and basic cosine similarity."""
    
    def __init__(self):
        """Initialize the simple vector store."""
        self.documents = {}  # id -> document text
        self.metadatas = {}  # id -> metadata dict
        self.document_ids = defaultdict(list)  # document_id -> list of chunk ids
        print("Using SimpleDictVectorStore - lightweight in-memory vector store")
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of dictionaries with 'id', 'document_id', 'content', and 'metadata'
        
        Returns:
            bool: Success or failure
        """
        try:
            for chunk in chunks:
                chunk_id = chunk["id"]
                self.documents[chunk_id] = chunk["content"]
                self.metadatas[chunk_id] = {
                    "document_id": chunk["document_id"],
                    "page_number": chunk.get("page_number"),
                    "chunk_index": chunk.get("chunk_index", 0),
                    **chunk.get("metadata", {})
                }
                self.document_ids[chunk["document_id"]].append(chunk_id)
            
            return True
            
        except Exception as e:
            print(f"Error adding chunks to simple vector store: {e}")
            return False
    
    def search(self, query: str, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks using basic keyword matching.
        
        Args:
            query: The search query
            filter_dict: Optional filter (e.g., {"document_id": "doc123"})
            limit: Maximum number of results
            
        Returns:
            List of relevant chunks with metadata
        """
        try:
            results = []
            
            # Filter chunks by document_id if specified
            chunk_ids = []
            if filter_dict and "document_id" in filter_dict:
                doc_id = filter_dict["document_id"]
                chunk_ids = self.document_ids.get(doc_id, [])
            else:
                chunk_ids = list(self.documents.keys())
            
            # Simple keyword search
            query_terms = set(query.lower().split())
            
            scored_results = []
            for chunk_id in chunk_ids:
                document = self.documents[chunk_id]
                doc_terms = set(document.lower().split())
                
                # Calculate a simple relevance score (% of query terms in document)
                matching_terms = query_terms.intersection(doc_terms)
                if matching_terms:
                    score = len(matching_terms) / len(query_terms)
                    scored_results.append((chunk_id, score))
            
            # Sort by score (highest first) and limit results
            scored_results.sort(key=lambda x: x[1], reverse=True)
            top_results = scored_results[:limit]
            
            # Format results
            for chunk_id, score in top_results:
                results.append({
                    "content": self.documents[chunk_id],
                    "metadata": self.metadatas[chunk_id],
                    "id": chunk_id,
                    "distance": 1.0 - score  # Convert score to distance (lower is better)
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching simple vector store: {e}")
            return []

class VectorStore:
    def __init__(self, persist_directory: str = "chroma_db"):
        """Initialize the vector store."""
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # First try to use the simple dict-based vector store
        try:
            self.use_simple_store = True
            self._impl = SimpleDictVectorStore()
            print("Using SimpleDictVectorStore for vector storage")
            log_debug("Initialized SimpleDictVectorStore")
            return
        except Exception as e:
            print(f"Failed to initialize simple vector store: {e}")
            self.use_simple_store = False
        
        # Try to initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
        except Exception as e:
            print(f"Failed to initialize ChromaDB: {e}")
            self.use_simple_store = True
            self._impl = SimpleDictVectorStore()
            return
        
        # Use SentenceTransformers for embeddings (Gemini does not provide embeddings)
        try:
            print("Using SentenceTransformers for vector store (Gemini migration)")
            log_debug("Using SentenceTransformers (Gemini migration)")
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            log_debug("Successfully initialized SentenceTransformers")
        except Exception as e:
            print(f"Failed to initialize SentenceTransformers: {e}")
            log_debug(f"Failed to initialize SentenceTransformers: {e}")
            self.use_simple_store = True
            self._impl = SimpleDictVectorStore()
            return
        
        # Create or get collection
        try:
            self.collection = self.client.get_or_create_collection(
                name="document_chunks",
                embedding_function=self.embedding_function
            )
            log_debug("Successfully created or got ChromaDB collection")
        except Exception as e:
            print(f"Failed to create ChromaDB collection: {e}")
            log_debug(f"Failed to create ChromaDB collection: {e}")
            self.use_simple_store = True
            self._impl = SimpleDictVectorStore()
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of dictionaries with 'id', 'document_id', 'content', and 'metadata'
        
        Returns:
            bool: Success or failure
        """
        if self.use_simple_store:
            return self._impl.add_chunks(chunks)
            
        try:
            # Format data for ChromaDB
            ids = [chunk["id"] for chunk in chunks]
            documents = [chunk["content"] for chunk in chunks]
            metadatas = [
                {
                    "document_id": chunk["document_id"],
                    "page_number": chunk.get("page_number"),
                    "chunk_index": chunk.get("chunk_index", 0),
                    **chunk.get("metadata", {})
                }
                for chunk in chunks
            ]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            return True
            
        except Exception as e:
            print(f"Error adding chunks to vector store: {e}")
            return False
    
    def search(self, query: str, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.
        
        Args:
            query: The search query
            filter_dict: Optional filter (e.g., {"document_id": "doc123"})
            limit: Maximum number of results
            
        Returns:
            List of relevant chunks with metadata
        """
        if self.use_simple_store:
            return self._impl.search(query, filter_dict, limit)
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter_dict
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "id": results["ids"][0][i] if results["ids"] else "",
                        "distance": results["distances"][0][i] if "distances" in results and results["distances"] else None
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching vector store: {e}")
            return []

# Singleton instance
_vector_store = None

def get_vector_store() -> VectorStore:
    """Get the vector store singleton instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
