document.addEventListener('DOMContentLoaded', function() {
    const bookingItems = document.querySelectorAll('.booking-item');

    bookingItems.forEach(item => {
        item.addEventListener('mouseover', function(e) {
            const details = document.createElement('div');
            details.className = 'booking-details';
            details.innerHTML = `
                <p>Check-in: ${this.dataset.checkIn}</p>
                <p>Check-out: ${this.dataset.checkOut}</p>
                <p>Guests: ${this.dataset.guests}</p>
                <p>Total Price: ${this.dataset.totalPrice}</p>
            `;
            details.style.position = 'absolute';
            details.style.left = e.pageX + 'px';
            details.style.top = e.pageY + 'px';
            document.body.appendChild(details);
        });

        item.addEventListener('mouseout', function() {
            const details = document.querySelector('.booking-details');
            if (details) {
                details.remove();
            }
        });
    });
});
