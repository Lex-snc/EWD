// Function to save and send SMS message
function saveMessage() {
    const messageText = document.getElementById('editable-message').value.trim();
    
    if (!messageText) {
        Swal.fire({
            icon: 'warning',
            title: 'Empty Message',
            text: 'Please enter a message before sending.'
        });
        return;
    }

    // Show loading state
    Swal.fire({
        title: 'Sending message...',
        didOpen: () => {
            Swal.showLoading();
        }
    });

    // Send message to backend
    fetch('/send_sms', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: messageText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Success!',
                text: 'Message sent successfully'
            });
            // Clear the message box after successful send
            document.getElementById('editable-message').value = '';
        } else {
            throw new Error(data.message || 'Failed to send message');
        }
    })
    .catch(error => {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Failed to send message. Please try again.'
        });
    });
}

// Character count functionality
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('editable-message');
    const charCount = document.getElementById('char-count');

    messageInput.addEventListener('input', function() {
        const count = this.value.length;
        charCount.textContent = count;
        
        // Visual feedback when approaching limit
        if (count > 140) {
            charCount.style.color = '#e74c3c';
        } else if (count > 120) {
            charCount.style.color = '#f39c12';
        } else {
            charCount.style.color = '#666';
        }
    });
});

// Function to update monitoring data
function updateMonitoringData() {
    fetch('/monitor')
        .then(response => response.json())
        .then(data => {
            document.getElementById('monitor-terminal').innerHTML = `
                <p>Water Level: ${data.water_level} cm</p>
                <p>Current: ${data.current} A</p>
                <p>Timestamp: ${data.timestamp}</p>
            `;
        })
        .catch(error => console.error('Error updating monitoring data:', error));
}

// Update monitoring data every 5 seconds
setInterval(updateMonitoringData, 5000);
