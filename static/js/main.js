document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    if (!container) {
        console.error('Container element not found');
        return;
    }

    let currentTooltip = null;

    function createTooltip(bookingData) {
        const tooltip = document.createElement('div');
        tooltip.className = 'booking-tooltip';
        tooltip.innerHTML = `
            <h3>${bookingData.guest_name || 'N/A'}</h3>
            <p><strong>Apartment:</strong> ${bookingData.apartment_name || 'N/A'}</p>
            <p><strong>Check-in:</strong> ${bookingData.check_in || 'N/A'}</p>
            <p><strong>Check-out:</strong> ${bookingData.check_out || 'N/A'}</p>
            <p><strong>Guests:</strong> ${bookingData.guests || 'N/A'}</p>
            <p><strong>Total Price:</strong> ${bookingData.total_price || 'N/A'}</p>
            <p><strong>Phone:</strong> ${bookingData.phone_number || 'N/A'}</p>
            <p><strong>Language:</strong> ${bookingData.language || 'N/A'}</p>
            <p><strong>Channel:</strong> ${bookingData.channel_name || 'N/A'}</p>
            <p><strong>Notice:</strong> ${bookingData.notice || 'N/A'}</p>
            <p><strong>Assistance Notes:</strong> ${bookingData.assistantNotice || 'N/A'}</p>
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
            left = x - rect.width - 10;
        }

        if (top + rect.height > viewportHeight) {
            top = y - rect.height - 10;
        }

        tooltip.style.position = 'fixed';
        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
    }

    function showTooltip(e) {
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
    }

    function hideTooltip(e) {
        if (!e.target.closest('.booking-item') && currentTooltip) {
            currentTooltip.remove();
            currentTooltip = null;
        }
    }

    container.addEventListener('mouseover', showTooltip);
    container.addEventListener('mouseout', hideTooltip);

    document.addEventListener('mousemove', function(e) {
        if (currentTooltip) {
            positionTooltip(currentTooltip, e.clientX, e.clientY);
        }
    });

    console.log('JavaScript initialization completed');
});