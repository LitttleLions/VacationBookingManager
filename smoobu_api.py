import requests
from datetime import datetime, timedelta
import json
import time
import logging

logger = logging.getLogger(__name__)

class SmoobuAPI:
    BASE_URL = 'https://login.smoobu.com/api'

    def __init__(self, settings_channel_id, api_key):
        self.settings_channel_id = settings_channel_id
        self.api_key = api_key
        self.headers = {
            'API-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def get_bookings(self, guest_filter='', apartment_filter='', start_date_filter='', end_date_filter='', max_retries=3, initial_delay=1):
        logger.debug("Entering get_bookings method")
        
        # Set date range (current date to 5 years in the future)
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1825)  # 5 years

        # Apply date filters if provided
        if start_date_filter:
            start_date = max(start_date, datetime.strptime(start_date_filter, '%Y-%m-%d').date())
        if end_date_filter:
            end_date = min(end_date, datetime.strptime(end_date_filter, '%Y-%m-%d').date())

        logger.info(f"Requesting bookings from {start_date} to {end_date}")

        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'limit': 500  # Increased limit to 500
        }
        
        all_bookings = []
        page = 1
        total_api_calls = 0

        while True:
            params['page'] = page
            full_url = f"{self.BASE_URL}/reservations"
            logger.info(f"Sending request to {full_url} with params: {params}")
            
            bookings, error = self._fetch_bookings(params, max_retries, initial_delay)
            total_api_calls += 1
            
            if error:
                logger.error(f"Error fetching bookings on page {page}: {error}")
                break

            if not bookings:
                logger.debug(f"No more bookings found after page {page-1}")
                break

            all_bookings.extend(bookings)
            logger.info(f"API returned {len(bookings)} bookings out of {params['limit']} requested")
            logger.info(f"Retrieved {len(bookings)} bookings on page {page}")
            
            if len(bookings) < params['limit']:
                logger.debug(f"Reached last page of results on page {page}")
                break
            
            page += 1

        logger.info(f"Total API calls made: {total_api_calls}")
        logger.info(f"Total bookings fetched: {len(all_bookings)}")

        # Log the date range of all fetched bookings
        if all_bookings:
            earliest_date = min(booking['check_in'] for booking in all_bookings)
            latest_date = max(booking['check_out'] for booking in all_bookings)
            logger.info(f"Date range of all fetched bookings: from {earliest_date} to {latest_date}")

        # Apply filters after fetching all bookings
        filtered_bookings = self._apply_filters(all_bookings, guest_filter, apartment_filter, start_date_filter, end_date_filter)
        logger.info(f"Total bookings after filtering: {len(filtered_bookings)}")

        # Log the date range of filtered bookings
        if filtered_bookings:
            earliest_date = min(booking['check_in'] for booking in filtered_bookings)
            latest_date = max(booking['check_out'] for booking in filtered_bookings)
            logger.info(f"Date range of filtered bookings: from {earliest_date} to {latest_date}")

        return filtered_bookings, None

    def _apply_filters(self, bookings, guest_filter, apartment_filter, start_date_filter, end_date_filter):
        filtered = []
        for booking in bookings:
            if guest_filter and guest_filter.lower() not in booking['guest_name'].lower():
                logger.debug(f"Filtered out booking: {booking['guest_name']} - {booking['check_in']} to {booking['check_out']} - Reason: Guest filter")
                continue
            if apartment_filter and apartment_filter.lower() != booking['apartment_name'].lower():
                logger.debug(f"Filtered out booking: {booking['guest_name']} - {booking['check_in']} to {booking['check_out']} - Reason: Apartment filter")
                continue
            if start_date_filter and booking['check_out'] < start_date_filter:
                logger.debug(f"Filtered out booking: {booking['guest_name']} - {booking['check_in']} to {booking['check_out']} - Reason: Start date filter")
                continue
            if end_date_filter and booking['check_in'] > end_date_filter:
                logger.debug(f"Filtered out booking: {booking['guest_name']} - {booking['check_in']} to {booking['check_out']} - Reason: End date filter")
                continue
            filtered.append(booking)
        return filtered

    def _fetch_bookings(self, params, max_retries, initial_delay):
        for attempt in range(max_retries):
            try:
                url = f"{self.BASE_URL}/reservations"
                logger.info(f"Sending request to {url} with params: {params}")
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"Received response: {json.dumps(data, indent=2)[:5000]}...")  # Truncate if too large
                bookings = []
                for booking in data.get('bookings', []):
                    adults = booking.get('adults', 0) or 0
                    children = booking.get('children', 0) or 0
                    
                    guest_name = (f"{booking.get('firstname', '')} {booking.get('lastname', '')}".strip() or
                                  booking.get('guest-name', '') or
                                  "Unknown Guest")
                    
                    total_price = booking.get('total-amount') or booking.get('price') or 0
                    if isinstance(total_price, str):
                        try:
                            total_price = float(total_price)
                        except ValueError:
                            total_price = 0

                    bookings.append({
                        'guest_name': guest_name,
                        'booking_date': booking.get('created-at', ''),
                        'apartment_name': booking.get('apartment', {}).get('name', ''),
                        'check_in': booking.get('arrival', ''),
                        'check_out': booking.get('departure', ''),
                        'guests': adults + children,
                        'adults': adults,
                        'children': children,
                        'total_price': total_price,
                        'status': booking.get('status', 'Unknown'),
                        'type': booking.get('type', 'Unknown'),
                        'phone_number': booking.get('phone', 'N/A'),
                        'email': booking.get('email', 'N/A'),
                        'notice': booking.get('notice', ''),
                        'assistantNotice': booking.get('assistant-notice', ''),
                        'language': booking.get('language', 'N/A'),
                        'channel_name': booking.get('channel', {}).get('name', 'N/A')
                    })
                logger.info(f"Processed {len(bookings)} bookings")
                return bookings, None
            except requests.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    error_message = f"Error fetching bookings after {max_retries} attempts: {str(e)}"
                    if hasattr(e, 'response'):
                        error_message += f"\nResponse status code: {e.response.status_code if e.response else 'No status code'}"
                        error_message += f"\nResponse content: {e.response.text[:500] if e.response else 'No response content'}..."
                    else:
                        error_message += "\nNo response object available"
                    logger.error(error_message)
                    return [], error_message

    # Add more API methods as needed

# Note: Check API documentation for any constraints on the limit parameter.
# The current implementation uses a limit of 500 bookings per page.
# If the API has a lower limit, adjust the 'limit' parameter in the get_bookings method accordingly.
