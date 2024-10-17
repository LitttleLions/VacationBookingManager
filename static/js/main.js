document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    if (!container) return;

    container.addEventListener('mouseover', function(e) {
        const item = e.target.closest('.booking-item');
        if (item) {
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
            details.style.backgroundColor = 'white';
            details.style.border = '1px solid #ccc';
            details.style.padding = '5px';
            details.style.zIndex = '1000';
            document.body.appendChild(details);
            
            item.addEventListener('mouseout', function() {
                details.remove();
            });
        }
    });
});
