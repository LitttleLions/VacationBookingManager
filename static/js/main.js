document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    if (!container) {
        console.error('Container element not found');
        return;
    }

    let currentTooltip = null;

    function createTooltip(bookingData) {
        const tooltip = document.createElement('div');
        tooltip.className = 'booking-details';
        tooltip.innerHTML = `
            <p><strong>Guest:</strong> ${bookingData.guest_name}</p>
            <p><strong>Apartment:</strong> ${bookingData.apartment_name}</p>
            <p><strong>Check-in:</strong> ${bookingData.check_in}</p>
            <p><strong>Check-out:</strong> ${bookingData.check_out}</p>
            <p><strong>Guests:</strong> ${bookingData.guests}</p>
            <p><strong>Total Price:</strong> ${bookingData.total_price}</p>
            <p><strong>Phone:</strong> ${bookingData.phone_number}</p>
            <p><strong>Language:</strong> ${bookingData.language}</p>
            <p><strong>Notes:</strong> ${bookingData.assistance_notes}</p>
        `;
        return tooltip;
    }

    function positionTooltip(tooltip, x, y) {
        const rect = tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let left = x + 10;
        let top = y + 10;

        if (left + rect.width > viewportWidth) {
            left = viewportWidth - rect.width - 10;
        }

        if (top + rect.height > viewportHeight) {
            top = viewportHeight - rect.height - 10;
        }

        tooltip.style.position = 'fixed';
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }

    container.addEventListener('mouseover', function(e) {
        const bookingItem = e.target.closest('.booking-item');
        if (bookingItem) {
            if (currentTooltip) {
                currentTooltip.remove();
            }
            try {
                const bookingData = JSON.parse(bookingItem.dataset.booking);
                const tooltip = createTooltip(bookingData);
                positionTooltip(tooltip, e.clientX, e.clientY);
                document.body.appendChild(tooltip);
                currentTooltip = tooltip;
            } catch (error) {
                console.error('Error creating tooltip:', error);
            }
        }
    });

    document.addEventListener('mousemove', function(e) {
        if (currentTooltip) {
            positionTooltip(currentTooltip, e.clientX, e.clientY);
        }
    });

    container.addEventListener('mouseout', function(e) {
        if (!e.target.closest('.booking-item') && currentTooltip) {
            currentTooltip.remove();
            currentTooltip = null;
        }
    });

    console.log('JavaScript initialization completed');
});
