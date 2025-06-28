// Document service for managing documents
const documentService = {
    documents: [],
    refreshInterval: null,
    
    // Initialize document service
    init() {
        // Start periodic refresh of document status
        this.startRefreshInterval();
    },
    
    // Start refreshing document statuses periodically
    startRefreshInterval() {
        // Clear any existing interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Check for documents with processing status every 5 seconds
        this.refreshInterval = setInterval(async () => {
            const hasProcessingDocuments = this.documents.some(doc => doc.status === 'processing');
            
            if (hasProcessingDocuments) {
                await this.refreshDocuments();
                documentList.updateDocumentList(this.documents);
            }
        }, 5000);
    },
    
    // Stop refreshing document statuses
    stopRefreshInterval() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    },
    
    // Upload a document
    async uploadDocument(file, onProgress) {
        const document = await api.uploadDocument(file, onProgress);
        
        // Add to local documents and refresh UI
        this.documents.push(document);
        documentList.updateDocumentList(this.documents);
        
        return document;
    },
    
    // Get all documents
    async getDocuments() {
        await this.refreshDocuments();
        return this.documents;
    },
    
    // Get a single document by ID
    getDocument(documentId) {
        return this.documents.find(doc => doc.id === documentId);
    },
    
    // Refresh documents from API
    async refreshDocuments() {
        try {
            const response = await api.getDocuments();
            this.documents = response.documents || [];
            return this.documents;
        } catch (error) {
            console.error('Error refreshing documents:', error);
            return this.documents;
        }
    }
}; 