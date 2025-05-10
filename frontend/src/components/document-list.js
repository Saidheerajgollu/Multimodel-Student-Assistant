// Document list component
const documentList = {
    // Update the document list UI
    updateDocumentList(documents) {
        const listElement = document.getElementById('document-list');
        
        if (!listElement) return;
        
        // Clear the list
        listElement.innerHTML = '';
        
        // If no documents, show message
        if (!documents || documents.length === 0) {
            const noDocsItem = document.createElement('li');
            noDocsItem.className = 'list-group-item text-muted';
            noDocsItem.textContent = 'No documents uploaded yet';
            listElement.appendChild(noDocsItem);
            return;
        }
        
        // Add each document to the list
        documents.forEach(doc => {
            const item = document.createElement('li');
            item.className = 'list-group-item document-item';
            
            // Create document info
            const documentInfo = document.createElement('div');
            documentInfo.className = 'document-info';
            documentInfo.innerHTML = `
                <div>${this.getStatusIcon(doc.status)} ${doc.filename}</div>
                <small class="text-muted">${this.formatDate(doc.created_at)}</small>
            `;
            
            // Create status badge
            const statusBadge = document.createElement('span');
            statusBadge.className = `document-status status-${doc.status}`;
            statusBadge.textContent = this.formatStatus(doc.status);
            
            // Add elements to item
            item.appendChild(documentInfo);
            item.appendChild(statusBadge);
            
            // Add item to list
            listElement.appendChild(item);
        });
        
        // Update document selects
        this.updateDocumentSelects(documents);
    },
    
    // Update document selects in all tabs
    updateDocumentSelects(documents) {
        const selects = [
            document.getElementById('document-select'),
            document.getElementById('flashcard-document-select'),
            document.getElementById('summary-document-select')
        ];
        
        selects.forEach(select => {
            if (!select) return;
            
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
    },
    
    // Get an icon for the document status
    getStatusIcon(status) {
        switch (status) {
            case 'pending':
                return '<i class="bi bi-hourglass"></i>';
            case 'processing':
                return '<i class="bi bi-arrow-repeat"></i>';
            case 'ready':
                return '<i class="bi bi-check-circle"></i>';
            case 'error':
                return '<i class="bi bi-exclamation-circle"></i>';
            default:
                return '';
        }
    },
    
    // Format the status for display
    formatStatus(status) {
        switch (status) {
            case 'pending':
                return 'Pending';
            case 'processing':
                return 'Processing';
            case 'ready':
                return 'Ready';
            case 'error':
                return 'Error';
            default:
                return status;
        }
    },
    
    // Format a date string
    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        return date.toLocaleString();
    }
}; 