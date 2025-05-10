# Multimodal Study Assistant

A full-stack application to help students study by understanding lecture slides, handwritten notes, and textbook pages.

## Features

- Upload and process PDF documents and images (JPG, PNG)
- Extract text using OCR for images and PDF text extraction
- Use RAG (Retrieval-Augmented Generation) to answer study questions
- Generate flashcards based on document content
- Create summaries of study materials
- Simple, clean user interface

## Technologies Used

### Backend
- FastAPI (Python)
- Gemini API (Google Generative AI) for LLM generation
- Tesseract OCR for image text extraction
- PyMuPDF for PDF text extraction
- ChromaDB for vector storage
- SentenceTransformers for embeddings

### Frontend
- HTML/CSS/JavaScript
- Bootstrap for UI components

## Installation

### Prerequisites
- Python 3.9+
- Tesseract OCR installed on your system
- Gemini API key (Google Generative AI)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd multimodal-study-assistant
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your configuration:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Quick Start

1. Start the backend server:
```bash
python run.py
```

2. Start the frontend server:
```bash
cd frontend
python serve.py
```

The frontend will be available at http://localhost:8080

## Usage

- Upload PDFs or images using the web interface
- Ask questions, generate flashcards, or create summaries from your documents

## Cleaning Up the Project

- **Remove all files in `uploads/`** for a fresh start (except for an empty `.gitkeep` if you want to keep the folder structure)
- **Remove `chroma_db/chroma.sqlite3`** to reset the vector database
- **Do not commit `venv/`** to version control; add it to your `.gitignore`

## Project Structure

```
multimodal-study-assistant/
├── app/                   # Backend application
│   ├── api/               # API endpoints
│   ├── core/              # Core processing logic
│   ├── db/                # Database and storage interfaces
│   ├── models/            # Data models
│   ├── utils/             # Utility functions
│   └── main.py            # FastAPI application
├── frontend/              # Frontend application
│   ├── src/               # Source JS/CSS
│   └── index.html         # Main HTML page
├── uploads/               # Uploaded documents (clean regularly)
├── chroma_db/             # Vector DB (clean regularly)
├── requirements.txt       # Python dependencies
├── run.py                 # Application runner
├── .env                   # Environment variables (not committed)
└── README.md              # This file
```

## Notes

- Make sure Tesseract OCR is installed and available in your PATH.
- If you do not provide a Gemini API key, LLM-based features (flashcards, summaries, advanced Q&A) will not work.
- For a clean repo, do not commit user uploads, database files, or your virtual environment.

## License

[MIT License](LICENSE)

## Academic Project Context

This project is designed for a Master's-level software engineering class to demonstrate:

1. RAG (Retrieval-Augmented Generation) architecture
2. Autonomous agent behavior (flashcard generation, summarization)
3. Multimodal input handling (text, images, PDFs)
4. Clean, modular code structure

## Gemini API Integration

To enhance the quality of flashcards and summaries generated from your PDFs, you must configure the application to use Gemini (Google Generative AI):

1. Create a `.env` file in the root directory if it doesn't exist
2. Add your Gemini API key to the file:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
3. Restart the application

The application will automatically detect the API key and use Gemini for generating accurate and useful flashcards and summaries from your documents.

> **Note:** If you don't provide an API key, the application will not be able to use LLM-based features (flashcards, summaries, advanced Q&A).

## Troubleshooting

- If you encounter errors related to PDF processing, ensure you have the required system dependencies for PyMuPDF and pdf2image.
- For OCR functionality, make sure Tesseract OCR is installed on your system.
- When running without a Gemini API key, the application will not be able to use LLM-based features.
