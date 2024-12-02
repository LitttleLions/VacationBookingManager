import requests
from datetime import datetime, timedelta
import json
import time
import logging
from functools import lru_cache
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class SmoobuAPI:
    BASE_URL = 'https://login.smoobu.com/api'
    CACHE_DURATION = 300  # 5 minutes in seconds

    def __init__(self, settings_channel_id, api_key):
        self.settings_channel_id = settings_channel_id
        self.api_key = api_key
        self.headers = {
            'API-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self._cache: Dict[str, Tuple[List, float]] = {}
        self._rate_limit_remaining = 1000
        self._rate_limit_reset = 0

    def _get_cache_key(self, params: dict) -> str:
        """Generate a cache key from the request parameters"""
        return json.dumps(params, sort_keys=True)

    def _is_cache_valid(self, cache_time: float) -> bool:
        """Check if the cached data is still valid"""
        return time.time() - cache_time < self.CACHE_DURATION

    def _update_rate_limits(self, headers: dict):
        """Update rate limiting information from response headers"""
        self._rate_limit_remaining = int(headers.get('x-ratelimit-remaining', 1000))
        self._rate_limit_reset = int(headers.get('x-ratelimit-retry-after', 0))
        logger.debug(f"Rate limit remaining: {self._rate_limit_remaining}")

    def _should_use_cache(self, cache_key: str) -> bool:
        """Determine if cached data should be used"""
        if cache_key in self._cache:
            data, cache_time = self._cache[cache_key]
            if self._is_cache_valid(cache_time):
                logger.debug("Using cached data")
                return True
        return False

    def get_bookings(self, guest_filter='', apartment_filter='', start_date_filter='', end_date_filter='', max_retries=3, initial_delay=1):
        logger.debug("Entering get_bookings method")
        
        # Set initial date range (current date to future)
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

        # Initialize parameters with increased chunk size (365 days)
        chunk_size = timedelta(days=365)  # Increased from 90 to 365 days
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

            # Check cache before making API call
            cache_key = self._get_cache_key(params)
            if self._should_use_cache(cache_key):
                chunk_bookings = self._cache[cache_key][0]
                logger.debug(f"Using cached data for chunk {chunk_number}")
            else:
                page = 1
                chunk_bookings = []

                while True:
                    params['page'] = page
                    logger.debug(f"Fetching page {page} for chunk {chunk_number}")
                    
                    # Check rate limits before making request
                    if self._rate_limit_remaining < 10:
                        wait_time = max(0, self._rate_limit_reset - time.time())
                        logger.warning(f"Rate limit nearly exceeded. Waiting {wait_time} seconds")
                        time.sleep(wait_time)
                    
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
                    
                    if len(bookings) < params['limit']:
                        logger.debug(f"Reached last page of results for chunk {chunk_number} on page {page}")
                        break
                    
                    page += 1
                    time.sleep(1)  # Add a small delay between requests

                # Cache the chunk results
                self._cache[cache_key] = (chunk_bookings, time.time())

            # Add chunk bookings to all bookings
            all_bookings.extend(chunk_bookings)
            logger.info(f"Chunk {chunk_number} complete. Retrieved {len(chunk_bookings)} bookings")
            
            # Move to next chunk
            current_start = chunk_end + timedelta(days=1)
            chunk_number += 1

        logger.info(f"Total API calls made: {total_api_calls}")
        logger.info(f"Total bookings fetched before filtering: {len(all_bookings)}")

        # Normalize field names in all bookings
        normalized_bookings = self._normalize_booking_fields(all_bookings)

        # Apply filters after fetching all bookings
        try:
            filtered_bookings = self._apply_filters(normalized_bookings, guest_filter, apartment_filter)
            return filtered_bookings, None
        except Exception as e:
            error_msg = f"Error applying filters: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

    def _normalize_booking_fields(self, bookings: List[dict]) -> List[dict]:
        """Normalize field names to ensure consistency"""
        normalized = []
        for booking in bookings:
            adults = int(booking.get('adults', 0) or 0)
            children = int(booking.get('children', 0) or 0)
            normalized_booking = {
                'check_in': booking.get('arrival'),
                'check_out': booking.get('departure'),
                'guest_name': (
                    booking.get('guest-name') or 
                    f"{booking.get('firstname', '').strip()} {booking.get('lastname', '').strip()}".strip() or 
                    'Unknown Guest'
                ),
                'apartment_name': booking.get('apartment', {}).get('name'),
                'channel_name': booking.get('channel', {}).get('name', 'Direct'),
                'phone_number': booking.get('phone', ''),
                'email': booking.get('email', ''),
                'adults': adults,
                'children': children,
                'guests': adults + children,
                'assistant_notice': booking.get('assistant-notice', ''),
                'language': booking.get('language', 'en'),
                'total_price': booking.get('price', ''),
            }
            normalized.append(normalized_booking)
        return normalized

    def _apply_filters(self, bookings, guest_filter, apartment_filter):
        """Apply filters with improved error handling and logging"""
        filtered = []
        total_bookings = len(bookings)
        logger.debug(f"Starting filtering process on {total_bookings} bookings")

        try:
            for booking in bookings:
                # Log the booking being processed
                guest_name = booking.get('guest_name', 'Unknown Guest')
                channel_name = booking.get('channel_name', '')
                logger.debug(f"Processing booking: {guest_name} (Channel: {channel_name})")
                
                # Filter out Unknown Guest and Blocked channel bookings
                if guest_name == 'Unknown Guest' or channel_name == 'Blocked channel':
                    logger.debug(f"Filtering out booking - Guest: {guest_name}, Channel: {channel_name}")
                    continue

                # Apply guest filter if provided
                if guest_filter:
                    if guest_filter.lower() not in guest_name.lower():
                        logger.debug(f"Booking filtered out by guest filter: {guest_name}")
                        continue
                    logger.debug(f"Booking passed guest filter: {guest_name}")

                # Apply apartment filter if provided
                if apartment_filter:
                    apartment_name = booking.get('apartment_name', '').lower()
                    if apartment_filter.lower() != apartment_name:
                        logger.debug(f"Booking filtered out by apartment filter: {apartment_name}")
                        continue
                    logger.debug(f"Booking passed apartment filter: {apartment_name}")

                filtered.append(booking)
                logger.debug(f"Added booking to filtered list: {guest_name} in {booking.get('apartment_name')}")

            logger.info(f"Filtering complete: {len(filtered)} bookings remained from {total_bookings}")
            logger.debug("Filtered bookings by apartment:")
            apartment_counts = {}
            for booking in filtered:
                apt = booking.get('apartment_name')
                apartment_counts[apt] = apartment_counts.get(apt, 0) + 1
            for apt, count in apartment_counts.items():
                logger.debug(f"  {apt}: {count} bookings")
            return filtered

        except Exception as e:
            logger.error(f"Error during filtering: {str(e)}")
            raise

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

                # Update rate limit information
                self._update_rate_limits(response.headers)

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
