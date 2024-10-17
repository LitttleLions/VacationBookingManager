document.addEventListener('DOMContentLoaded', function() {
    const bookingItems = document.querySelectorAll('.booking-item');

    bookingItems.forEach(item => {
        item.addEventListener('mouseover', function(e) {
            const details = this.querySelector('.booking-details');
            details.style.display = 'block';
            details.style.left = e.pageX + 'px';
            details.style.top = e.pageY + 'px';
        });

        item.addEventListener('mouseout', function() {
            this.querySelector('.booking-details').style.display = 'none';
        });
    });
});
