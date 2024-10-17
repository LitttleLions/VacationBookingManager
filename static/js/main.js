document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    if (!container) {
        console.error('Container element not found');
        return;
    }

    let currentDetails = null;

    function createDetailsElement(item) {
        const details = document.createElement('div');
        details.className = 'booking-details';
        details.innerHTML = `
            <p>Apartment: ${item.dataset.apartmentName || 'N/A'}</p>
            <p>Guest: ${item.dataset.guestName || 'N/A'}</p>
            <p>Phone: ${item.dataset.phoneNumber || 'N/A'}</p>
            <p>Check-in: ${item.dataset.checkIn || 'N/A'}</p>
            <p>Check-out: ${item.dataset.checkOut || 'N/A'}</p>
            <p>Guests: ${item.dataset.guests || 'N/A'}</p>
            <p>Assistance Notes: ${item.dataset.assistanceNotes || 'N/A'}</p>
            <p>Language: ${item.dataset.language || 'N/A'}</p>
            <p>Booking Date: ${item.dataset.bookingDate || 'N/A'}</p>
            <p>Total Price: ${item.dataset.totalPrice || 'N/A'}</p>
            <p>Status: ${item.dataset.status || 'N/A'}</p>
            <p>Type: ${item.dataset.type || 'N/A'}</p>
        `;
        return details;
    }

    function positionDetails(details, x, y) {
        if (details) {
            details.style.position = 'absolute';
            details.style.left = (x + 10) + 'px';
            details.style.top = (y + 10) + 'px';
        }
    }

    container.addEventListener('mouseover', function(e) {
        const item = e.target.closest('.booking-item');
        if (item) {
            if (currentDetails) {
                currentDetails.remove();
            }
            try {
                const details = createDetailsElement(item);
                positionDetails(details, e.pageX, e.pageY);
                container.appendChild(details);
                currentDetails = details;
            } catch (error) {
                console.error('Error creating details element:', error);
            }
        }
    });

    document.addEventListener('mousemove', function(e) {
        if (currentDetails) {
            positionDetails(currentDetails, e.pageX, e.pageY);
        }
    });

    container.addEventListener('mouseout', function(e) {
        if (!e.target.closest('.booking-item') && currentDetails) {
            currentDetails.remove();
            currentDetails = null;
        }
    });

    console.log('JavaScript initialization completed');
});
