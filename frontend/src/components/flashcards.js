// Flashcards UI component
const flashcardsUI = {
    // Render flashcards in a container
    renderFlashcards(flashcards, container) {
        if (!container) return;
        
        // Clear the container
        container.innerHTML = '';
        
        // If no flashcards, show message
        if (!flashcards || flashcards.length === 0) {
            const message = document.createElement('p');
            message.className = 'text-muted';
            message.textContent = 'No flashcards generated';
            container.appendChild(message);
            return;
        }
        
        // Get the flashcard template
        const template = document.getElementById('flashcard-template');
        
        // Create each flashcard
        flashcards.forEach(flashcard => {
            // Clone the template
            const flashcardElement = template.content.cloneNode(true);
            
            // Set the content
            flashcardElement.querySelector('.flashcard-front-text').textContent = flashcard.front;
            flashcardElement.querySelector('.flashcard-back-text').textContent = flashcard.back;
            
            // Add to container
            container.appendChild(flashcardElement);
        });
        
        // Initialize click handlers
        this.initializeFlashcardInteractions(container);
    },
    
    // Initialize flashcard interactions
    initializeFlashcardInteractions(container) {
        // For this simple implementation, we'll rely on CSS hover effect
        // But you could add click handlers here to flip cards on click
        const flashcards = container.querySelectorAll('.flashcard');
        
        flashcards.forEach(card => {
            card.addEventListener('click', () => {
                card.querySelector('.flashcard-inner').classList.toggle('flipped');
            });
        });
    }
}; 