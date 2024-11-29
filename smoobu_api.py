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
        
        # Set initial date range (current date to 10 years in the future)
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=3650)  # 10 years

        # Apply date filters if provided
        if start_date_filter:
            try:
                filter_start = datetime.strptime(start_date_filter, '%Y-%m-%d').date()
                start_date = filter_start
                logger.info(f"Applied start date filter: {start_date}")
            except ValueError as e:
                logger.error(f"Invalid start date format: {e}")
        if end_date_filter:
            try:
                filter_end = datetime.strptime(end_date_filter, '%Y-%m-%d').date()
                end_date = filter_end
                logger.info(f"Applied end date filter: {end_date}")
            except ValueError as e:
                logger.error(f"Invalid end date format: {e}")

        logger.info(f"Requesting bookings from {start_date} to {end_date}")

        # Initialize parameters with a smaller chunk size to handle API limits
        chunk_size = timedelta(days=90)  # Fetch 90 days at a time
        current_start = start_date
        all_bookings = []
        total_api_calls = 0
        chunk_number = 1

        while current_start < end_date:
            # Calculate end date for current chunk
            chunk_end = min(current_start + chunk_size, end_date)
            logger.info(f"Processing chunk {chunk_number}: {current_start} to {chunk_end}")
            
            params = {
                'from': current_start.strftime('%Y-%m-%d'),
                'to': chunk_end.strftime('%Y-%m-%d'),
                'limit': 25  # Set to match API's actual limit
            }
            
            page = 1
            chunk_bookings = []

            while True:
                params['page'] = page
                logger.debug(f"Fetching page {page} for chunk {chunk_number}")
                
                bookings, error = self._fetch_bookings(params, max_retries, initial_delay)
                total_api_calls += 1
                
                if error:
                    logger.error(f"Error fetching bookings for chunk {chunk_number}, page {page}: {error}")
                    break

                if not bookings:
                    logger.debug(f"No more bookings found in chunk {chunk_number} after page {page-1}")
                    break

                chunk_bookings.extend(bookings)
                logger.debug(f"Retrieved {len(bookings)} bookings on page {page} for chunk {chunk_number}")
                
                # If we received fewer bookings than the limit, we've reached the last page
                if len(bookings) < params['limit']:
                    logger.debug(f"Reached last page of results for chunk {chunk_number} on page {page}")
                    break
                
                page += 1
                time.sleep(1)  # Add a small delay between requests

            # Add chunk bookings to all bookings
            all_bookings.extend(chunk_bookings)
            logger.info(f"Chunk {chunk_number} complete. Retrieved {len(chunk_bookings)} bookings")
            
            # Move to next chunk
            current_start = chunk_end + timedelta(days=1)
            chunk_number += 1

        logger.info(f"Total API calls made: {total_api_calls}")
        logger.info(f"Total bookings fetched before filtering: {len(all_bookings)}")

        # Log the date range of all fetched bookings
        if all_bookings:
            earliest_date = min(booking['arrival'] for booking in all_bookings)
            latest_date = max(booking['departure'] for booking in all_bookings)
            logger.info(f"Date range of all fetched bookings: from {earliest_date} to {latest_date}")

        # Apply filters after fetching all bookings
        filtered_bookings = self._apply_filters(all_bookings, guest_filter, apartment_filter)
        return filtered_bookings, None

    def _apply_filters(self, bookings, guest_filter, apartment_filter):
        filtered = []
        total_bookings = len(bookings)
        logger.debug(f"Starting filtering process on {total_bookings} bookings")

        for booking in bookings:
            # Log the booking being processed
            logger.debug(f"Processing booking: {booking.get('id', 'No ID')} - {booking.get('guest-name', 'Unknown Guest')}")
            
            # Apply guest filter if provided
            if guest_filter:
                guest_name = (
                    booking.get('guest-name') or 
                    f"{booking.get('firstname', '').strip()} {booking.get('lastname', '').strip()}".strip() or 
                    'Unknown Guest'
                ).lower()
                
                if guest_filter.lower() not in guest_name:
                    logger.debug(f"Booking {booking.get('id', 'No ID')} filtered out by guest filter")
                    continue
                logger.debug(f"Booking {booking.get('id', 'No ID')} passed guest filter")

            # Apply apartment filter if provided
            if apartment_filter:
                apartment_name = booking.get('apartment', {}).get('name', '').lower()
                if apartment_filter.lower() != apartment_name:
                    logger.debug(f"Booking {booking.get('id', 'No ID')} filtered out by apartment filter")
                    continue
                logger.debug(f"Booking {booking.get('id', 'No ID')} passed apartment filter")

            filtered.append(booking)

        logger.info(f"Filtering complete: {len(filtered)} bookings remained from {total_bookings}")
        return filtered

    def _fetch_bookings(self, params, max_retries, initial_delay):
        url = f"{self.BASE_URL}/reservations"
        logger.debug(f"Fetching bookings from {url} with params: {params}")

        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, params=params)
                
                # Log the complete request details
                logger.debug(f"Request URL: {response.url}")
                logger.debug(f"Request headers: {self.headers}")
                logger.debug(f"Response status code: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")

                response.raise_for_status()
                
                data = response.json()
                
                # Validate response structure
                if not isinstance(data, dict):
                    error_msg = f"Invalid response format. Expected dict, got {type(data)}"
                    logger.error(error_msg)
                    return [], error_msg

                bookings = data.get('bookings', [])
                if not isinstance(bookings, list):
                    error_msg = f"Invalid bookings format. Expected list, got {type(bookings)}"
                    logger.error(error_msg)
                    return [], error_msg

                # Log response summary
                logger.debug(f"Retrieved {len(bookings)} bookings")
                if bookings:
                    logger.debug(f"First booking sample: {json.dumps(bookings[0], indent=2)}")
                
                return bookings, None

            except requests.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if hasattr(e, 'response'):
                    logger.error(f"Response status code: {e.response.status_code if e.response else 'No status code'}")
                    logger.error(f"Response content: {e.response.text[:1000] if e.response else 'No response content'}...")

                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    error_message = f"Failed to fetch bookings after {max_retries} attempts: {str(e)}"
                    logger.error(error_message)
                    return [], error_message

            except json.JSONDecodeError as e:
                error_message = f"Failed to parse API response: {str(e)}"
                logger.error(error_message)
                if hasattr(e, 'response'):
                    logger.error(f"Raw response content: {e.response.text[:1000]}...")
                return [], error_message

    def get_bookings_for_period(self, start_date, end_date):
        """Helper method to fetch bookings for a specific period"""
        logger.info(f"Fetching bookings for specific period: {start_date} to {end_date}")
        return self.get_bookings(start_date_filter=start_date, end_date_filter=end_date)
