document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
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
                <p>Check-in: ${item.dataset.checkIn}</p>
                <p>Check-out: ${item.dataset.checkOut}</p>
                <p>Guests: ${item.dataset.guests}</p>
                <p>Total Price: ${item.dataset.totalPrice}</p>
                <p>Status: ${item.dataset.status}</p>
                <p>Type: ${item.dataset.type}</p>
            `;
            details.style.position = 'absolute';
            details.style.left = (e.pageX + 10) + 'px';
            details.style.top = (e.pageY + 10) + 'px';
            container.appendChild(details);
            currentDetails = details;
        }
    });

    container.addEventListener('mouseout', function(e) {
        if (!e.target.closest('.booking-item') && currentDetails) {
            currentDetails.remove();
            currentDetails = null;
        }
    });
});
