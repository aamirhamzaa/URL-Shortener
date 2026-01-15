import re
import requests
import csv
import json
from urllib.parse import urlparse
from datetime import datetime, timedelta
import hashlib
import qrcode
from io import BytesIO
import base64
from user_agents import parse
from logger import logger

def validate_url(url):
    """
    Validate URL format and accessibility
    
    Args:
        url: URL string to validate
        
    Returns:
        dict: Validation result with success flag and message
    """
    try:
        # Basic format validation
        if not url or not isinstance(url, str):
            return {'valid': False, 'error': 'URL cannot be empty'}
        
        # Check if URL starts with http:// or https://
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse URL
        parsed = urlparse(url)
        
        # Validate components
        if not parsed.scheme in ['http', 'https']:
            return {'valid': False, 'error': 'URL must use HTTP or HTTPS protocol'}
        
        if not parsed.netloc:
            return {'valid': False, 'error': 'Invalid domain name'}
        
        # Check for localhost/internal IPs (optional security check)
        if 'localhost' in parsed.netloc or '127.0.0.1' in parsed.netloc:
            return {'valid': False, 'error': 'Local URLs are not allowed'}
        
        # Try to access URL (with timeout)
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                return {'valid': False, 'error': f'URL returned status code {response.status_code}'}
        except requests.RequestException as e:
            return {'valid': False, 'error': f'URL is not accessible: {str(e)}'}
        
        return {'valid': True, 'url': url, 'message': 'URL is valid'}
        
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return {'valid': False, 'error': f'Validation error: {str(e)}'}

def validate_custom_code(code, max_length=30):
    """
    Validate custom short code
    
    Args:
        code: Custom code to validate
        max_length: Maximum allowed length
        
    Returns:
        dict: Validation result
    """
    if not code:
        return {'valid': False, 'error': 'Custom code cannot be empty'}
    
    if len(code) > max_length:
        return {'valid': False, 'error': f'Custom code must be {max_length} characters or less'}
    
    if len(code) < 3:
        return {'valid': False, 'error': 'Custom code must be at least 3 characters'}
    
    # Only alphanumeric and hyphens
    if not re.match(r'^[a-zA-Z0-9-]+$', code):
        return {'valid': False, 'error': 'Custom code can only contain letters, numbers, and hyphens'}
    
    # Cannot start or end with hyphen
    if code.startswith('-') or code.endswith('-'):
        return {'valid': False, 'error': 'Custom code cannot start or end with a hyphen'}
    
    # Reserved words
    reserved = ['api', 'admin', 'stats', 'analytics', 'dashboard', 'login', 'logout', 
                'signup', 'register', 'settings', 'help', 'about', 'contact', 'terms', 
                'privacy', 'delete', 'edit', 'new', 'create']
    
    if code.lower() in reserved:
        return {'valid': False, 'error': 'This code is reserved and cannot be used'}
    
    return {'valid': True, 'message': 'Custom code is valid'}

def sanitize_url(url):
    """
    Sanitize and normalize URL
    
    Args:
        url: URL to sanitize
        
    Returns:
        str: Sanitized URL
    """
    # Remove whitespace
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Remove duplicate slashes (except in protocol)
    url = re.sub(r'([^:])//+', r'\1/', url)
    
    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
    
    return url

def generate_qr_code(url, size=300):
    """
    Generate QR code for URL
    
    Args:
        url: URL to encode
        size: QR code size in pixels
        
    Returns:
        str: Base64 encoded QR code image
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize
        img = img.resize((size, size))
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64
        
    except Exception as e:
        logger.error(f"QR code generation error: {e}")
        return None

def export_to_csv(data, filename):
    """
    Export data to CSV file
    
    Args:
        data: List of dictionaries to export
        filename: Output filename
        
    Returns:
        bool: Success status
    """
    try:
        if not data:
            return False
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Data exported to CSV: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return False

def export_to_json(data, filename, pretty=True):
    """
    Export data to JSON file
    
    Args:
        data: Data to export
        filename: Output filename
        pretty: Pretty print JSON
        
    Returns:
        bool: Success status
    """
    try:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            if pretty:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            else:
                json.dump(data, jsonfile, ensure_ascii=False)
        
        logger.info(f"Data exported to JSON: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"JSON export error: {e}")
        return False

def import_from_csv(filename):
    """
    Import data from CSV file
    
    Args:
        filename: Input filename
        
    Returns:
        list: Imported data or None
    """
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)
        
        logger.info(f"Data imported from CSV: {filename}")
        return data
        
    except Exception as e:
        logger.error(f"CSV import error: {e}")
        return None

def import_from_json(filename):
    """
    Import data from JSON file
    
    Args:
        filename: Input filename
        
    Returns:
        Data or None
    """
    try:
        with open(filename, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        
        logger.info(f"Data imported from JSON: {filename}")
        return data
        
    except Exception as e:
        logger.error(f"JSON import error: {e}")
        return None

def calculate_expiration_date(days=None):
    """
    Calculate expiration date
    
    Args:
        days: Number of days until expiration (None for no expiration)
        
    Returns:
        str: ISO format expiration date or None
    """
    if days is None:
        return None
    
    expiration = datetime.now() + timedelta(days=days)
    return expiration.isoformat()

def is_expired(expiration_date):
    """
    Check if date has expired
    
    Args:
        expiration_date: ISO format date string
        
    Returns:
        bool: True if expired
    """
    if not expiration_date:
        return False
    
    try:
        exp_date = datetime.fromisoformat(expiration_date)
        return datetime.now() > exp_date
    except:
        return False

def hash_string(text, algorithm='sha256'):
    """
    Hash a string
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        str: Hashed string
    """
    if algorithm == 'md5':
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(text.encode()).hexdigest()
    else:
        return hashlib.sha256(text.encode()).hexdigest()

def format_number(number):
    """
    Format number with commas
    
    Args:
        number: Number to format
        
    Returns:
        str: Formatted number
    """
    return f"{number:,}"

def format_size(size_bytes):
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def format_duration(seconds):
    """
    Format duration in human-readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}h"
    else:
        return f"{seconds/86400:.1f}d"

def parse_tags(tags_string):
    """
    Parse comma-separated tags
    
    Args:
        tags_string: Comma-separated tags
        
    Returns:
        str: Cleaned tags string
    """
    if not tags_string:
        return ""
    
    # Split by comma, strip whitespace, remove empty
    tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag)
    
    return ', '.join(unique_tags)

def get_domain_from_url(url):
    """
    Extract domain from URL
    
    Args:
        url: Full URL
        
    Returns:
        str: Domain name
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ""

def truncate_text(text, max_length=100, suffix='...'):
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def validate_email(email):
    """
    Validate email address
    
    Args:
        email: Email to validate
        
    Returns:
        bool: True if valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_user_agent_info(user_agent):
    """
    Parse user agent string to extract browser and OS info
    
    Args:
        user_agent: User agent string
        
    Returns:
        dict: Browser and OS information
    """
    info = {
        'browser': 'Unknown',
        'os': 'Unknown',
        'device': 'Desktop'
    }
    
    if not user_agent:
        return info
    
    ua_lower = user_agent.lower()
    
    # Browser detection
    if 'chrome' in ua_lower and 'edg' not in ua_lower:
        info['browser'] = 'Chrome'
    elif 'firefox' in ua_lower:
        info['browser'] = 'Firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        info['browser'] = 'Safari'
    elif 'edg' in ua_lower:
        info['browser'] = 'Edge'
    elif 'opera' in ua_lower or 'opr' in ua_lower:
        info['browser'] = 'Opera'
    elif 'msie' in ua_lower or 'trident' in ua_lower:
        info['browser'] = 'Internet Explorer'
    
    # OS detection
    if 'windows' in ua_lower:
        info['os'] = 'Windows'
    elif 'mac' in ua_lower:
        info['os'] = 'macOS'
    elif 'linux' in ua_lower:
        info['os'] = 'Linux'
    elif 'android' in ua_lower:
        info['os'] = 'Android'
    elif 'ios' in ua_lower or 'iphone' in ua_lower or 'ipad' in ua_lower:
        info['os'] = 'iOS'
    
    # Device detection
    if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
        info['device'] = 'Mobile'
    elif 'tablet' in ua_lower or 'ipad' in ua_lower:
        info['device'] = 'Tablet'
    
    return info

def generate_random_string(length=10, charset='alphanumeric'):
    """
    Generate random string
    
    Args:
        length: String length
        charset: Character set (alphanumeric, alpha, numeric, hex)
        
    Returns:
        str: Random string
    """
    import random
    import string
    
    if charset == 'alphanumeric':
        chars = string.ascii_letters + string.digits
    elif charset == 'alpha':
        chars = string.ascii_letters
    elif charset == 'numeric':
        chars = string.digits
    elif charset == 'hex':
        chars = string.hexdigits.lower()
    else:
        chars = string.ascii_letters + string.digits
    
    return ''.join(random.choice(chars) for _ in range(length))

def create_backup_filename(prefix='backup', extension='db'):
    """
    Create backup filename with timestamp
    
    Args:
        prefix: Filename prefix
        extension: File extension
        
    Returns:
        str: Backup filename
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}.{extension}"

def clean_string(text):
    """
    Clean string by removing special characters
    
    Args:
        text: Text to clean
        
    Returns:
        str: Cleaned text
    """
    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable())
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def safe_divide(numerator, denominator, default=0):
    """
    Safely divide numbers
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division fails
        
    Returns:
        float: Result or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default

def percentage(part, whole, decimals=1):
    """
    Calculate percentage
    
    Args:
        part: Part value
        whole: Whole value
        decimals: Decimal places
        
    Returns:
        float: Percentage
    """
    if whole == 0:
        return 0
    return round((part / whole) * 100, decimals)

def check_url_active(url):
    """Check if a URL is reachable"""
    import requests
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400
    except:
        return False
    
def is_blacklisted(url, blacklist=None):
    """
    Check if a URL is blacklisted.
    
    Args:
        url (str): The URL to check
        blacklist (list, optional): List of blacklisted domains/patterns
        
    Returns:
        bool: True if URL is blacklisted, False otherwise
    """
    if blacklist is None:
        # Default blacklist of common malicious/spam domains
        blacklist = [
            'bit.ly',  # Often used for spam (you might want to allow this)
            'malware.com',
            'phishing.com',
            'spam.com',
            # Add more domains as needed
        ]
    
    # Get domain from URL
    domain = get_domain_from_url(url)
    
    # Check against blacklist
    for blocked in blacklist:
        if blocked.lower() in domain.lower():
            return True
    
    return False   

def check_dns_resolution(url):
    """
    Check if a domain/URL can be resolved via DNS.
    
    Args:
        url (str): The URL or domain to check
        
    Returns:
        bool: True if DNS resolution succeeds, False otherwise
    """
    import socket
    from urllib.parse import urlparse
    
    try:
        # Extract domain from URL if full URL is provided
        if url.startswith(('http://', 'https://')):
            domain = urlparse(url).netloc
        else:
            domain = url
        
        # Remove port if present
        domain = domain.split(':')[0]
        
        # Attempt DNS resolution
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        # DNS resolution failed
        return False
    except Exception:
        return False 
    
def get_ip_info(ip_address):
    """
    Get information about an IP address using ipapi.co service.
    
    Args:
        ip_address (str): The IP address to look up
        
    Returns:
        dict: IP information including location, ISP, etc., or None if failed
    """
    import requests
    
    try:
        # Using ipapi.co free API (no key required)
        response = requests.get(
            f"https://ipapi.co/{ip_address}/json/",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            # Map API response to standardized format
            return {
                'country': data.get('country_name', ''),  # Changed from 'country'
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'postal': data.get('postal', ''),
                'latitude': data.get('latitude', ''),
                'longitude': data.get('longitude', ''),
                'isp': data.get('org', ''),
                'timezone': data.get('timezone', '')
            }
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting IP info: {e}")
        return None
    
def parse_user_agent(user_agent_string):
    """
    Parse a user agent string to extract browser, OS, and device information.
    
    Args:
        user_agent_string (str): The user agent string to parse
        
    Returns:
        dict: Parsed information about browser, OS, and device
    """
    try:
        from user_agents import parse
        
        ua = parse(user_agent_string)
        
        return {
            'browser': {
                'family': ua.browser.family,
                'version': ua.browser.version_string
            },
            'os': {
                'family': ua.os.family,
                'version': ua.os.version_string
            },
            'device': {
                'family': ua.device.family,
                'brand': ua.device.brand,
                'model': ua.device.model
            },
            'is_mobile': ua.is_mobile,
            'is_tablet': ua.is_tablet,
            'is_pc': ua.is_pc,
            'is_bot': ua.is_bot,
            'raw_string': user_agent_string
        }
    except ImportError:
        print("user-agents library not installed. Install with: pip install user-agents")
        return None
    except Exception as e:
        print(f"Error parsing user agent: {e}")
        return None    