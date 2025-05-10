document.addEventListener('DOMContentLoaded', () => {
    // Initialize API config
    const API_URL = 'http://localhost:8000/api';
    api.init(API_URL);
    
    // Initialize document service
    documentService.init();
    
    // Initialize components
    initializeDropzone();
    initializeDocumentList();
    initializeQuestionTab();
    initializeFlashcardsTab();
    initializeSummaryTab();
    
    // Load initial data
    loadDocuments();
});

// ---------- Initialization functions ----------

function initializeDropzone() {
    const dropzone = document.getElementById('dropzone');
    
    // Prevent default behaviors for drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight dropzone when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.add('drag-over');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.remove('drag-over');
        }, false);
    });
    
    // Handle dropped files
    dropzone.addEventListener('drop', event => {
        const files = event.dataTransfer.files;
        handleFiles(files);
    }, false);
    
    // Handle clicks to open file dialog
    dropzone.addEventListener('click', () => {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.pdf,.png,.jpg,.jpeg';
        fileInput.multiple = false;
        
        fileInput.addEventListener('change', event => {
            const files = event.target.files;
            handleFiles(files);
        });
        
        fileInput.click();
    });
}

function initializeDocumentList() {
    // Handled by document-list.js component
}

function initializeQuestionTab() {
    const askButton = document.getElementById('ask-button');
    const questionInput = document.getElementById('question-input');
    
    askButton.addEventListener('click', () => {
        const question = questionInput.value.trim();
        const documentId = document.getElementById('document-select').value;
        
        if (!question) {
            alert('Please enter a question');
            return;
        }
        
        askQuestion(question, documentId);
    });
    
    // Allow pressing Enter to ask question
    questionInput.addEventListener('keyup', event => {
        if (event.key === 'Enter') {
            askButton.click();
        }
    });
}

function initializeFlashcardsTab() {
    const generateButton = document.getElementById('generate-flashcards-button');
    
    generateButton.addEventListener('click', () => {
        const documentId = document.getElementById('flashcard-document-select').value;
        const count = document.getElementById('flashcard-count').value;
        const topic = document.getElementById('flashcard-topic').value.trim();
        
        if (!documentId) {
            alert('Please select a document');
            return;
        }
        
        generateFlashcards(documentId, count, topic);
    });
}

function initializeSummaryTab() {
    const generateButton = document.getElementById('generate-summary-button');
    
    generateButton.addEventListener('click', () => {
        const documentId = document.getElementById('summary-document-select').value;
        const maxLength = document.getElementById('summary-length').value;
        
        if (!documentId) {
            alert('Please select a document');
            return;
        }
        
        generateSummary(documentId, maxLength);
    });
}

// ---------- Data loading functions ----------

async function loadDocuments() {
    try {
        const documents = await documentService.getDocuments();
        updateDocumentSelects(documents);
    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

function updateDocumentSelects(documents) {
    // Update document selects in all tabs
    const selects = [
        document.getElementById('document-select'),
        document.getElementById('flashcard-document-select'),
        document.getElementById('summary-document-select')
    ];
    
    selects.forEach(select => {
        // Keep the first option (if any)
        const firstOption = select.querySelector('option:first-child');
        select.innerHTML = '';
        if (firstOption) {
            select.appendChild(firstOption);
        }
        
        // Add document options
        documents.forEach(doc => {
            if (doc.status === 'ready') {
                const option = document.createElement('option');
                option.value = doc.id;
                option.textContent = doc.filename;
                select.appendChild(option);
            }
        });
    });
}

// ---------- Action functions ----------

async function handleFiles(files) {
    if (!files.length) return;
    
    const file = files[0]; // Only process the first file
    
    // Validate file type
    const validTypes = ['application/pdf', 'image/png', 'image/jpeg'];
    if (!validTypes.includes(file.type)) {
        alert('Please upload a PDF or image file (PNG, JPG)');
        return;
    }
    
    // Show progress
    const progressContainer = document.getElementById('upload-progress-container');
    const progressBar = document.getElementById('upload-progress');
    progressContainer.classList.remove('d-none');
    progressBar.style.width = '0%';
    
    try {
        // Upload file
        const document = await documentService.uploadDocument(file, (progress) => {
            progressBar.style.width = `${progress}%`;
        });
        
        // Update UI
        setTimeout(() => {
            progressContainer.classList.add('d-none');
            loadDocuments(); // Refresh document list
        }, 500);
        
    } catch (error) {
        console.error('Error uploading file:', error);
        alert('Error uploading file. Please try again.');
        progressContainer.classList.add('d-none');
    }
}

async function askQuestion(question, documentId) {
    showResponseLoader();
    
    try {
        const response = await api.ask(question, documentId);
        
        // Update response container
        const responseContainer = document.getElementById('response-container');
        responseContainer.innerHTML = `
            <h4>Question:</h4>
            <p>${response.question}</p>
            <h4>Answer:</h4>
            <div class="response-content">${response.answer}</div>
        `;
    } catch (error) {
        console.error('Error asking question:', error);
        showErrorResponse('Error asking question. Please try again.');
    } finally {
        hideResponseLoader();
    }
}

async function generateFlashcards(documentId, count, topic) {
    showResponseLoader();
    
    try {
        const response = await api.generateFlashcards(documentId, count, topic);
        
        // Update response container with flashcards
        const responseContainer = document.getElementById('response-container');
        responseContainer.innerHTML = '<h4>Flashcards:</h4><div class="flashcards-container"></div>';
        
        const flashcardsContainer = responseContainer.querySelector('.flashcards-container');
        
        // Use the flashcards component to render the cards
        flashcardsUI.renderFlashcards(response.flashcards, flashcardsContainer);
    } catch (error) {
        console.error('Error generating flashcards:', error);
        showErrorResponse('Error generating flashcards. Please try again.');
    } finally {
        hideResponseLoader();
    }
}

async function generateSummary(documentId, maxLength) {
    showResponseLoader();
    
    try {
        const response = await api.generateSummary(documentId, maxLength);
        
        // Update response container
        const responseContainer = document.getElementById('response-container');
        responseContainer.innerHTML = `
            <h4>Summary:</h4>
            <div class="response-content">${response.summary}</div>
        `;
    } catch (error) {
        console.error('Error generating summary:', error);
        showErrorResponse('Error generating summary. Please try again.');
    } finally {
        hideResponseLoader();
    }
}

// ---------- Helper functions ----------

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function showResponseLoader() {
    const loader = document.getElementById('response-loader');
    loader.classList.remove('d-none');
}

function hideResponseLoader() {
    const loader = document.getElementById('response-loader');
    loader.classList.add('d-none');
}

function showErrorResponse(message) {
    const responseContainer = document.getElementById('response-container');
    responseContainer.innerHTML = `<div class="alert alert-danger">${message}</div>`;
} 