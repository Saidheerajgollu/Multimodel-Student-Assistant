import os
from typing import List, Dict, Any, Optional
import json
import random
from dotenv import load_dotenv

from app.db.document_store import DocumentStore
from app.db.vector_store import get_vector_store
from app.models.question import Flashcard

# Import the correct Gemini client
import google.generativeai as genai

# Load environment variables
load_dotenv()

gemini_api_key = os.environ.get("GEMINI_API_KEY")
if not gemini_api_key:
    raise RuntimeError("GEMINI_API_KEY not configured. Please set the GEMINI_API_KEY environment variable.")

# Configure the Gemini client with the API key
genai.configure(api_key=gemini_api_key)

# Debug function
def log_debug(message):
    with open("debug.txt", "a") as f:
        f.write(f"{message}\n")

# Set the model to the latest version
DEFAULT_MODEL = "gemini-1.5-flash"
log_debug(f"Using model: {DEFAULT_MODEL}")

async def answer_question(
    question: str, 
    document_id: Optional[str] = None,
    document_store: DocumentStore = None
) -> str:
    """
    Answer a question using RAG and Gemini.
    """
    try:
        log_debug(f"answer_question called with question: {question}")
        # Get relevant context
        context = await retrieve_context(question, document_id)
        if not context:
            log_debug("No context found for question")
            return "I couldn't find any relevant information to answer your question."
        log_debug(f"Retrieved {len(context)} context chunks")
        # Format context for the prompt
        formatted_context = "\n\n".join([f"[{i+1}] {chunk['content']}" for i, chunk in enumerate(context)])
        prompt = f"""
Answer the question using only the information in the context below. If the context doesn't contain the answer, acknowledge that you don't have enough information.

CONTEXT:
{formatted_context}

QUESTION: {question}
"""
        # Use the correct API format
        model = genai.GenerativeModel(DEFAULT_MODEL)
        response = model.generate_content(prompt)
        answer = response.text.strip()
        log_debug(f"Got Gemini response, length: {len(answer)}")
        return answer
    except Exception as e:
        log_debug(f"Error using Gemini for answer: {e}")
        print(f"Error using Gemini for answer: {e}")
        return "I encountered an error while trying to answer your question. Please try again."

def simple_answering(question: str, context: List[Dict[str, Any]]) -> str:
    """
    Simple text-based answering without using an LLM.
    
    Args:
        question: The question to answer
        context: List of relevant document chunks
        
    Returns:
        str: The answer to the question
    """
    try:
        # Extract the most relevant chunk
        most_relevant = context[0]['content'] if context else ""
        
        # For questions asking what something is about
        if "what is" in question.lower() and "about" in question.lower():
            # Look for sentences containing keywords from the question
            question_words = set(question.lower().split())
            important_words = [word for word in question_words if len(word) > 3 and word not in 
                               {'what', 'is', 'are', 'the', 'about', 'for', 'this', 'that', 'these', 'those'}]
            
            # Join all contexts
            full_text = "\n".join([chunk['content'] for chunk in context])
            
            # Split into sentences
            sentences = [s.strip() for s in full_text.replace('\n', ' ').split('.') if s.strip()]
            
            # Find sentences with the most question keywords
            relevant_sentences = []
            for sentence in sentences:
                sentence_lower = sentence.lower()
                keyword_count = sum(1 for word in important_words if word in sentence_lower)
                if keyword_count > 0:
                    relevant_sentences.append((sentence, keyword_count))
            
            # Sort by relevance
            relevant_sentences.sort(key=lambda x: x[1], reverse=True)
            
            # Take the top 3 most relevant sentences
            answer_sentences = [s[0] for s in relevant_sentences[:3]]
            
            if answer_sentences:
                return " ".join(answer_sentences) + "."
        
        # If we couldn't construct a good answer, return the most relevant chunk
        return f"Based on the document, here's what I found:\n\n{most_relevant}"
    
    except Exception as e:
        log_debug(f"Error in simple answering: {e}")
        print(f"Error in simple answering: {e}")
        return "I found relevant information but couldn't formulate a concise answer. Here's the most relevant text from your document:\n\n" + context[0]['content'] if context else "No relevant information found."

async def generate_flashcards(
    document_id: str,
    count: int = 5,
    topic: Optional[str] = None,
    document_store: DocumentStore = None
) -> List[Flashcard]:
    """
    Generate flashcards for a document using Gemini.
    """
    # Get document chunks
    chunks = []
    if document_store:
        doc_chunks = document_store.get_chunks(document_id)
        chunks = [chunk.content for chunk in doc_chunks]
    if not chunks:
        return []
    try:
        content = "\n\n".join(chunks[:10])  # Limit to first 10 chunks to avoid token limits
        topic_str = f" about {topic}" if topic else ""
        prompt = f"""
Generate {count} study flashcards{topic_str} based on the following content.
Each flashcard should be in the format: Q: ... A: ...
Focus on key concepts, definitions, and important facts.
Return only the flashcards, no explanations or extra text.
CONTENT:\n{content}
"""
        # Use the correct API format
        model = genai.GenerativeModel(DEFAULT_MODEL)
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        # Parse flashcards from the response (expecting Q: ... A: ... format)
        flashcards = []
        for block in response_text.split("Q:"):
            block = block.strip()
            if not block:
                continue
            if "A:" in block:
                q, a = block.split("A:", 1)
                flashcards.append(Flashcard(front="Q: " + q.strip(), back="A: " + a.strip()))
        if not flashcards:
            raise ValueError("No flashcards parsed from Gemini response.")
        return flashcards[:count]
    except Exception as e:
        log_debug(f"Error generating flashcards with Gemini: {e}")
        raise RuntimeError(f"Failed to generate flashcards with Gemini: {e}")

def generate_simple_flashcards(chunks: List[str], count: int = 5, topic: Optional[str] = None) -> List[Flashcard]:
    """
    Generate simple flashcards without using an LLM.
    
    Args:
        chunks: Document chunks
        count: Number of flashcards to generate
        topic: Optional topic to focus on
        
    Returns:
        List[Flashcard]: Generated flashcards
    """
    flashcards = []
    
    # Join all text
    full_text = " ".join(chunks)
    
    # Split into sentences
    sentences = [s.strip() for s in full_text.replace('\n', ' ').split('.') if s.strip() and len(s.split()) > 5]
    
    # Filter for topic if provided
    if topic:
        topic_lower = topic.lower()
        topic_sentences = [s for s in sentences if topic_lower in s.lower()]
        if topic_sentences:
            sentences = topic_sentences
    
    # Take up to 'count' random sentences
    if sentences:
        selected = random.sample(sentences, min(count * 2, len(sentences)))
        
        for i in range(min(count, len(selected) // 2)):
            # Create a simple "complete the sentence" flashcard
            sentence = selected[i]
            # Find a significant word to remove
            words = sentence.split()
            if len(words) > 4:
                # Choose a word from the middle of the sentence
                idx = len(words) // 2
                target_word = words[idx]
                if len(target_word) > 3:  # Only choose significant words
                    question = " ".join(words[:idx] + ["_____"] + words[idx+1:])
                    flashcards.append(Flashcard(
                        front=f"Complete the sentence: {question}",
                        back=f"Answer: {target_word}"
                    ))
                    continue
            
            # Fallback - create a "what is described here" flashcard
            flashcards.append(Flashcard(
                front=f"What concept is being described here: '{sentence}'",
                back=f"This describes a key concept from your document."
            ))
    
    # If we couldn't generate enough, add some generic ones
    while len(flashcards) < count:
        flashcards.append(Flashcard(
            front=f"Important concept #{len(flashcards) + 1} from your document",
            back="Review your document to fully understand this concept."
        ))
    
    return flashcards

async def generate_summary(
    document_id: str,
    max_length: int = 500,
    document_store: DocumentStore = None
) -> str:
    """
    Generate a summary of a document using Gemini.
    """
    # Get document chunks
    chunks = []
    if document_store:
        doc_chunks = document_store.get_chunks(document_id)
        chunks = [chunk.content for chunk in doc_chunks]
    if not chunks:
        return "No content available to summarize."
    try:
        content = "\n\n".join(chunks[:15])  # Limit to avoid token limits
        prompt = f"""
Summarize the following content in about {max_length} words.
Focus on the main points, key concepts, and important details.
The summary should be concise, coherent, and well-structured.
CONTENT:\n{content}
"""
        # Use the correct API format
        model = genai.GenerativeModel(DEFAULT_MODEL)
        response = model.generate_content(prompt)
        summary = response.text.strip()
        if not summary:
            raise ValueError("No summary returned from Gemini.")
        return summary
    except Exception as e:
        log_debug(f"Error generating summary with Gemini: {e}")
        raise RuntimeError(f"Failed to generate summary with Gemini: {e}")

def generate_simple_summary(chunks: List[str], max_length: int = 500) -> str:
    """
    Generate a simple summary without using an LLM.
    
    Args:
        chunks: Document chunks
        max_length: Maximum length of summary in words
        
    Returns:
        str: Generated summary
    """
    try:
        # Join all text
        full_text = " ".join(chunks)
        
        # Split into sentences
        sentences = [s.strip() for s in full_text.replace('\n', ' ').split('.') if s.strip()]
        
        # Calculate how many sentences we need for the target length
        avg_words_per_sentence = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        target_sentences = int(max_length / avg_words_per_sentence)
        
        # Select sentences: first few, some from middle, and last few
        summary_sentences = []
        
        # Always include the first 1-2 sentences
        start_count = min(2, len(sentences))
        summary_sentences.extend(sentences[:start_count])
        
        # Add some from the middle if there are enough sentences
        if len(sentences) > 5:
            middle_start = len(sentences) // 3
            middle_end = 2 * len(sentences) // 3
            middle_count = min(target_sentences - 4, middle_end - middle_start)
            if middle_count > 0:
                step = (middle_end - middle_start) // middle_count
                for i in range(middle_start, middle_end, max(1, step)):
                    if len(summary_sentences) < target_sentences - 2:
                        summary_sentences.append(sentences[i])
        
        # Always include the last 1-2 sentences
        end_count = min(2, len(sentences))
        if end_count > 0 and len(sentences) > 3:
            summary_sentences.extend(sentences[-end_count:])
        
        # Join summary sentences
        summary = '. '.join(summary_sentences)
        
        # Ensure the summary ends with a period
        if summary and not summary.endswith('.'):
            summary += '.'
            
        return summary
    
    except Exception as e:
        print(f"Error generating simple summary: {e}")
        
        # Fallback - return the first chunk
        if chunks:
            words = chunks[0].split()
            if len(words) > max_length:
                return ' '.join(words[:max_length]) + '...'
            return chunks[0]
        
        return "Could not generate summary."

async def retrieve_context(
    query: str, 
    document_id: Optional[str] = None,
    max_chunks: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant context for a query.
    
    Args:
        query: The search query
        document_id: Optional document ID to restrict search
        max_chunks: Maximum number of chunks to retrieve
        
    Returns:
        List of relevant document chunks
    """
    vector_store = get_vector_store()
    
    # Create filter if document_id is provided
    filter_dict = {"document_id": document_id} if document_id else None
    
    # Search for relevant chunks
    results = vector_store.search(
        query=query,
        filter_dict=filter_dict,
        limit=max_chunks
    )
    
    return results
