document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    if (!container) return;

    let currentDetails = null;

    container.addEventListener('mouseover', function(e) {
        const item = e.target.closest('.booking-item');
        if (item) {
            if (currentDetails) {
                currentDetails.remove();
            }
            const details = document.createElement('div');
            details.className = 'booking-details';
            details.innerHTML = `
                <p>Check-in: ${item.dataset.checkIn || 'N/A'}</p>
                <p>Check-out: ${item.dataset.checkOut || 'N/A'}</p>
                <p>Guests: ${item.dataset.guests || 'N/A'}</p>
                <p>Total Price: ${item.dataset.totalPrice || 'N/A'}</p>
                <p>Status: ${item.dataset.status || 'N/A'}</p>
                <p>Type: ${item.dataset.type || 'N/A'}</p>
            `;
            details.style.position = 'absolute';
            details.style.left = (e.pageX + 10) + 'px';
            details.style.top = (e.pageY + 10) + 'px';
            document.body.appendChild(details);
            currentDetails = details;
        }
    });

    document.body.addEventListener('mouseout', function(e) {
        if (!e.target.closest('.booking-item') && currentDetails) {
            currentDetails.remove();
            currentDetails = null;
        }
    });
});
