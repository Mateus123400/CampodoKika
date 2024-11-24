// Socket.io initialization
const socket = io();

// Global event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize date picker with current date
    const datePicker = document.getElementById('date-picker');
    if (datePicker) {
        const today = new Date().toISOString().split('T')[0];
        datePicker.value = today;
        datePicker.min = today;
    }

    // Handle booking form submission
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleBookingSubmit);
    }

    // Handle time slot management
    const timeSlotForm = document.getElementById('time-slot-form');
    if (timeSlotForm) {
        timeSlotForm.addEventListener('submit', handleTimeSlotSubmit);
    }

    // Handle payment confirmation
    const confirmPaymentButtons = document.querySelectorAll('.confirm-payment');
    confirmPaymentButtons.forEach(button => {
        button.addEventListener('click', handlePaymentConfirmation);
    });

    // Handle message sending
    const messageForm = document.getElementById('message-form');
    if (messageForm) {
        messageForm.addEventListener('submit', handleMessageSubmit);
    }
});

// Booking form handler
function handleBookingSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    fetch('/book', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert(data.message || 'Erro ao fazer reserva');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Erro ao fazer reserva');
    });
}

// Time slot management handler
function handleTimeSlotSubmit(e) {
    e.preventDefault();
    const time = document.getElementById('new-time-slot').value;
    
    fetch('/admin/time-slots', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ time: time })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert(data.message || 'Erro ao adicionar horário');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Erro ao adicionar horário');
    });
}

// Payment confirmation handler
function handlePaymentConfirmation(e) {
    const bookingId = e.target.dataset.bookingId;
    
    fetch(`/admin/confirm-payment/${bookingId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert(data.message || 'Erro ao confirmar pagamento');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Erro ao confirmar pagamento');
    });
}

// Message handling
function handleMessageSubmit(e) {
    e.preventDefault();
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (message) {
        socket.emit('send_message', { message: message });
        messageInput.value = '';
    }
}

// Socket.io event listeners
socket.on('new_message', function(data) {
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${data.is_admin ? 'admin-message' : 'user-message'} mb-3 fade-in`;
        
        messageDiv.innerHTML = `
            <div class="message-header d-flex justify-content-between">
                <strong>${data.user}</strong>
                <small>${data.timestamp}</small>
            </div>
            <div class="message-content">
                ${data.message}
            </div>
        `;
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
