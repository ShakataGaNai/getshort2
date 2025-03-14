// Main JavaScript file for GetShort URL Shortener

// Helper function to format date objects
function formatDate(date) {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Add current year to footer
document.addEventListener('DOMContentLoaded', function() {
    // Get all time elements that need to be formatted
    const timeElements = document.querySelectorAll('time.timeago');
    timeElements.forEach(element => {
        const timestamp = element.getAttribute('datetime');
        element.textContent = formatDate(timestamp);
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
});