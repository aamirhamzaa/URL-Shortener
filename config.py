import os
from pathlib import Path

# ============================================================================
# PROJECT PATHS
# ============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
BACKUPS_DIR = DATA_DIR / "backups"
QRCODES_DIR = DATA_DIR / "qrcodes"
ASSETS_DIR = BASE_DIR / "assets"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, BACKUPS_DIR, QRCODES_DIR, ASSETS_DIR]:
    directory.mkdir(exist_ok=True)

# ============================================================================
# DATABASE SETTINGS
# ============================================================================
DATABASE_PATH = DATA_DIR / "urls.db"
BACKUP_INTERVAL_HOURS = 24  # Auto-backup every 24 hours

# ============================================================================
# SERVER SETTINGS
# ============================================================================
SERVER_HOST = "localhost"
SERVER_PORT = 8080
CUSTOM_DOMAIN = f"http://{SERVER_HOST}:{SERVER_PORT}"

# ============================================================================
# URL SHORTENING SETTINGS
# ============================================================================
SHORT_CODE_LENGTH = 6  # Length of generated short codes (e.g., "abc123")
SHORT_CODE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
MAX_CUSTOM_LENGTH = 50  # Maximum length for custom short codes

# ============================================================================
# VALIDATION SETTINGS
# ============================================================================
CHECK_URL_ACTIVE = True  # Validate if URLs are accessible
DNS_TIMEOUT = 5  # Seconds to wait for DNS resolution
REQUEST_TIMEOUT = 10  # Seconds to wait for URL validation

# Malicious URL blacklist (domains to block)
BLACKLISTED_DOMAINS = [
    "malware.com",
    "phishing.com",
    "scam.com",
    # Add more as needed
]

# ============================================================================
# ANALYTICS SETTINGS
# ============================================================================
TRACK_IP = True
TRACK_GEOLOCATION = True
TRACK_BROWSER = True
TRACK_DEVICE = True
TRACK_RESPONSE_TIME = True

# IP Geolocation API (free tier)
GEOLOCATION_API = "http://ip-api.com/json/"  # Free, no API key needed

# ============================================================================
# GUI SETTINGS
# ============================================================================
WINDOW_TITLE = "URL Shortener Pro"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700

# Theme settings
THEMES = {
    "light": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "accent": "#4CAF50",
        "secondary": "#2196F3",
        "error": "#f44336",
        "warning": "#ff9800",
        "success": "#4CAF50",
        "card_bg": "#ffffff",
        "border": "#cccccc"
    },
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#ffffff",
        "accent": "#4CAF50",
        "secondary": "#2196F3",
        "error": "#f44336",
        "warning": "#ff9800",
        "success": "#4CAF50",
        "card_bg": "#2d2d2d",
        "border": "#3d3d3d"
    }
}

# Default theme
DEFAULT_THEME = "dark"

# Font settings
FONT_FAMILY = "Segoe UI"
FONT_SIZE_SMALL = 9
FONT_SIZE_NORMAL = 10
FONT_SIZE_LARGE = 12
FONT_SIZE_TITLE = 16

# ============================================================================
# LOGGING SETTINGS
# ============================================================================
LOG_TO_CONSOLE = True
LOG_TO_FILE = True
LOG_FILE_PATH = LOGS_DIR / "url_shortener.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
MAX_LOG_SIZE_MB = 10  # Max size before log rotation
LOG_BACKUP_COUNT = 5  # Number of backup logs to keep

# ============================================================================
# QR CODE SETTINGS
# ============================================================================
QR_VERSION = 1  # QR code version (1-40)
QR_BOX_SIZE = 10  # Size of each QR code box
QR_BORDER = 4  # Border size
QR_FILL_COLOR = "black"
QR_BACK_COLOR = "white"

# ============================================================================
# KEYBOARD SHORTCUTS
# ============================================================================
SHORTCUTS = {
    "new_url": "<Control-n>",
    "search": "<Control-f>",
    "refresh": "<F5>",
    "delete": "<Delete>",
    "copy": "<Control-c>",
    "save": "<Control-s>",
    "quit": "<Control-q>",
    "toggle_theme": "<Control-t>"
}

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================
ANALYTICS_REFRESH_INTERVAL = 5000  # Milliseconds (5 seconds)
AUTO_BACKUP_ENABLED = True

# ============================================================================
# EXPORT SETTINGS
# ============================================================================
EXPORT_FORMATS = ["CSV", "JSON", "TXT"]
DEFAULT_EXPORT_FORMAT = "CSV"

# ============================================================================
# SOCIAL MEDIA SETTINGS
# ============================================================================
SOCIAL_MEDIA = {
    "twitter": "https://twitter.com/intent/tweet?url=",
    "facebook": "https://www.facebook.com/sharer/sharer.php?u=",
    "linkedin": "https://www.linkedin.com/sharing/share-offsite/?url="
}

# ============================================================================
# EMAIL TEMPLATE
# ============================================================================
EMAIL_SUBJECT = "Check out this link!"
EMAIL_BODY_TEMPLATE = """
Hello!

I wanted to share this link with you:
{shortened_url}

Original URL: {original_url}

Created on: {created_date}

Best regards
"""

# ============================================================================
# ERROR MESSAGES
# ============================================================================
ERROR_MESSAGES = {
    "invalid_url": "Invalid URL format. Please enter a valid URL starting with http:// or https://",
    "url_inactive": "URL appears to be inactive or unreachable",
    "blacklisted": "This URL is blacklisted and cannot be shortened",
    "custom_taken": "This custom short code is already taken",
    "database_error": "Database error occurred. Please try again",
    "server_error": "Server error occurred. Please restart the server",
    "not_found": "Shortened URL not found",
    "expired": "This URL has expired",
    "dns_error": "DNS resolution failed for this URL"
}

# ============================================================================
# SUCCESS MESSAGES
# ============================================================================
SUCCESS_MESSAGES = {
    "url_created": "URL shortened successfully!",
    "url_updated": "URL updated successfully!",
    "url_deleted": "URL deleted successfully!",
    "copied": "Copied to clipboard!",
    "exported": "Data exported successfully!",
    "backup_created": "Backup created successfully!",
    "theme_saved": "Theme preferences saved!"
}

# Tracking settings
TRACK_IP = True
TRACK_LOCATION = True  # Add this line
TRACK_BROWSER = True