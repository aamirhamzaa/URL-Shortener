import random
import string
from datetime import datetime, timedelta
import config
from logger import logger
from database import Database
from utils import (
    validate_url, check_url_active, is_blacklisted,
    check_dns_resolution
)

class URLShortener:
    """Main URL shortener class"""
    
    def __init__(self, database: Database):
        """
        Initialize URL shortener
        
        Args:
            database: Database instance
        """
        self.db = database
        logger.info("URL Shortener initialized")
    
    def generate_short_code(self):
        """
        Generate random short code
        
        Returns:
            Random short code string
        """
        while True:
            code = ''.join(random.choices(
                config.SHORT_CODE_CHARS,
                k=config.SHORT_CODE_LENGTH
            ))
            
            # Check if code already exists
            if not self.db.get_url(code):
                return code
    
    def shorten_url(self, original_url, custom_code=None, expires_days=None, 
                   notes="", tags="", validate=True):
        """
        Shorten a URL
        
        Args:
            original_url: Original long URL
            custom_code: Custom short code (optional)
            expires_days: Expiration in days (None for no expiration)
            notes: Optional notes
            tags: Optional tags
            validate: Whether to validate URL
        
        Returns:
            Dictionary with result {success, short_code, error}
        """
        result = {
            'success': False,
            'short_code': None,
            'shortened_url': None,
            'error': None
        }
        
        # Validate URL format
        if not validate_url(original_url):
            result['error'] = config.ERROR_MESSAGES['invalid_url']
            logger.warning(f"Invalid URL format: {original_url}")
            return result
        
        # Check blacklist
        if is_blacklisted(original_url):
            result['error'] = config.ERROR_MESSAGES['blacklisted']
            logger.warning(f"Blacklisted URL: {original_url}")
            return result
        
        # Validate URL is active (if enabled)
        if validate and config.CHECK_URL_ACTIVE:
            # Check DNS first
            if not check_dns_resolution(original_url):
                result['error'] = config.ERROR_MESSAGES['dns_error']
                logger.warning(f"DNS resolution failed: {original_url}")
                return result
            
            # Check if URL is accessible
            if not check_url_active(original_url):
                result['error'] = config.ERROR_MESSAGES['url_inactive']
                logger.warning(f"URL inactive: {original_url}")
                return result
        
        # Generate or validate custom code
        if custom_code:
            # Validate custom code
            if len(custom_code) > config.MAX_CUSTOM_LENGTH:
                result['error'] = f"Custom code too long (max {config.MAX_CUSTOM_LENGTH} characters)"
                return result
            
            if not custom_code.isalnum():
                result['error'] = "Custom code must be alphanumeric"
                return result
            
            # Check if custom code is taken
            if self.db.get_url(custom_code):
                result['error'] = config.ERROR_MESSAGES['custom_taken']
                logger.warning(f"Custom code taken: {custom_code}")
                return result
            
            short_code = custom_code
            is_custom = True
        else:
            short_code = self.generate_short_code()
            is_custom = False
        
        # Calculate expiration date
        expires_at = None
        if expires_days:
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        # Insert into database
        if self.db.insert_url(short_code, original_url, is_custom, expires_at, notes, tags):
            result['success'] = True
            result['short_code'] = short_code
            result['shortened_url'] = f"{config.CUSTOM_DOMAIN}/{short_code}"
            logger.info(f"URL shortened: {original_url} -> {short_code}")
        else:
            result['error'] = config.ERROR_MESSAGES['database_error']
            logger.error(f"Database insert failed for: {original_url}")
        
        return result
    
    def get_original_url(self, short_code):
        """
        Get original URL from short code
        
        Args:
            short_code: Shortened code
        
        Returns:
            Original URL or None
        """
        url_data = self.db.get_url(short_code)
        if url_data:
            return url_data['original_url']
        return None
    
    def get_url_details(self, short_code):
        """
        Get complete URL details including analytics
        
        Args:
            short_code: Shortened code
        
        Returns:
            Dictionary with URL details and analytics
        """
        url_data = self.db.get_url(short_code)
        if not url_data:
            return None
        
        # Add click count
        url_data['click_count'] = self.db.get_click_count(short_code)
        
        # Add shortened URL
        url_data['shortened_url'] = f"{config.CUSTOM_DOMAIN}/{short_code}"
        
        return url_data
    
    def update_url(self, short_code, **kwargs):
        """
        Update URL details
        
        Args:
            short_code: Shortened code
            **kwargs: Fields to update
        
        Returns:
            True if successful
        """
        return self.db.update_url(short_code, **kwargs)
    
    def delete_url(self, short_code, permanent=False):
        """
        Delete URL
        
        Args:
            short_code: Shortened code
            permanent: Whether to permanently delete
        
        Returns:
            True if successful
        """
        if permanent:
            return self.db.hard_delete_url(short_code)
        else:
            return self.db.delete_url(short_code)
    
    def search_urls(self, search_term):
        """
        Search URLs
        
        Args:
            search_term: Search string
        
        Returns:
            List of matching URLs
        """
        return self.db.search_urls(search_term)
    
    def get_all_urls(self):
        """
        Get all active URLs
        
        Returns:
            List of all URLs with click counts
        """
        urls = self.db.get_all_urls()
        
        # Add click counts
        for url in urls:
            url['click_count'] = self.db.get_click_count(url['short_code'])
            url['shortened_url'] = f"{config.CUSTOM_DOMAIN}/{url['short_code']}"
        
        return urls
    
    def cleanup_expired_urls(self):
        """
        Mark expired URLs as inactive
        
        Returns:
            Number of URLs cleaned up
        """
        urls = self.db.get_all_urls()
        count = 0
        
        for url in urls:
            if url['expires_at']:
                expires_at = datetime.fromisoformat(url['expires_at'])
                if datetime.now() > expires_at:
                    self.db.delete_url(url['short_code'])
                    count += 1
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired URLs")
        
        return count