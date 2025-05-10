// API service for communicating with the backend
const api = {
    baseUrl: '',
    
    // Initialize API with base URL
    init(baseUrl) {
        this.baseUrl = baseUrl;
    },
    
    // Generic fetch method with error handling
    async fetch(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Request failed with status ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API error for ${endpoint}:`, error);
            throw error;
        }
    },
    
    // Document endpoints
    async getDocuments() {
        return this.fetch('/documents');
    },
    
    async getDocument(documentId) {
        return this.fetch(`/documents/${documentId}`);
    },
    
    async uploadDocument(file, onProgress) {
        const formData = new FormData();
        formData.append('file', file);
        
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Setup progress tracking
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable && onProgress) {
                    const progress = Math.round((event.loaded * 100) / event.total);
                    onProgress(progress);
                }
            });
            
            // Setup completion handler
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        reject(new Error('Invalid response format'));
                    }
                } else {
                    reject(new Error(`Upload failed with status ${xhr.status}`));
                }
            });
            
            // Setup error handler
            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });
            
            // Send the request
            xhr.open('POST', `${this.baseUrl}/documents/upload`);
            xhr.send(formData);
        });
    },
    
    // Question endpoints
    async ask(question, documentId = null) {
        return this.fetch('/questions/ask', {
            method: 'POST',
            body: JSON.stringify({
                question,
                document_id: documentId || null
            })
        });
    },
    
    // Flashcard endpoints
    async generateFlashcards(documentId, count = 5, topic = null) {
        return this.fetch('/questions/flashcards', {
            method: 'POST',
            body: JSON.stringify({
                document_id: documentId,
                count: parseInt(count),
                topic: topic || null
            })
        });
    },
    
    // Summary endpoints
    async generateSummary(documentId, maxLength = 500) {
        return this.fetch('/questions/summary', {
            method: 'POST',
            body: JSON.stringify({
                document_id: documentId,
                max_length: parseInt(maxLength)
            })
        });
    }
}; 