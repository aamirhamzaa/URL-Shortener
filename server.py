import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime
import threading
import time
import config
from logger import logger
from database import Database
from utils import get_ip_info, parse_user_agent

class URLRedirectHandler(http.server.BaseHTTPRequestHandler):
    """Custom HTTP request handler for URL redirection"""
    
    # Class variables
    db = None
    
    def log_message(self, format, *args):
        """Override to use custom logger"""
        logger.debug(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        start_time = time.time()
        
        # Parse URL path
        path = self.path.lstrip('/')
        
        # Remove query parameters
        if '?' in path:
            path = path.split('?')[0]
        
        # Handle root path
        if path == '' or path == 'index.html':
            self.serve_home_page()
            return
        
        # Handle API endpoints
        if path.startswith('api/'):
            self.handle_api(path)
            return
        
        # Handle URL redirection
        self.handle_redirect(path, start_time)
    
    def serve_home_page(self):
        """Serve simple home page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>URL Shortener</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #4CAF50;
                    text-align: center;
                }
                p {
                    text-align: center;
                    color: #666;
                    font-size: 18px;
                }
                .stats {
                    margin-top: 30px;
                    padding: 20px;
                    background: #f9f9f9;
                    border-radius: 5px;
                }
                .stat-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #eee;
                }
                .stat-label {
                    font-weight: bold;
                    color: #333;
                }
                .stat-value {
                    color: #4CAF50;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔗 URL Shortener Pro</h1>
                <p>Server is running successfully!</p>
                <p>Use the desktop application to manage your shortened URLs.</p>
                <div class="stats">
                    <h3>Server Status</h3>
                    <div class="stat-item">
                        <span class="stat-label">Status:</span>
                        <span class="stat-value">Online ✓</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Port:</span>
                        <span class="stat-value">""" + str(config.SERVER_PORT) + """</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Domain:</span>
                        <span class="stat-value">""" + config.CUSTOM_DOMAIN + """</span>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def handle_redirect(self, short_code, start_time):
    
    # Get URL from database
        url_data = self.db.get_url(short_code)
    
        if not url_data:
            self.send_error(404, config.ERROR_MESSAGES['not_found'])
            logger.warning(f"Short code not found: {short_code}")
            return
    
    # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
    
    # Get client info
        ip_address = self.client_address[0]
        user_agent = self.headers.get('User-Agent', '')
    
    # Get geolocation - FIXED!
        country = ""
        city = ""
    
        if config.TRACK_LOCATION:
            geo_info = get_ip_info(ip_address)
            if geo_info:
            # Now these are guaranteed to be strings, not dicts
                country = str(geo_info.get('country', '')).strip()
                city = str(geo_info.get('city', '')).strip()
    
    # Parse user agent
        browser = ""
        device = ""
    
        if config.TRACK_BROWSER:
            ua_info = parse_user_agent(user_agent)
            if ua_info:
                browser = f"{ua_info['browser']['family']} {ua_info['browser']['version']}".strip()
                device = ua_info['device']['family'].strip()
    
    # Log for debugging
        logger.debug(
        f"Recording click | country={country} (type:{type(country).__name__}), "
        f"city={city} (type:{type(city).__name__})"
    )
    
    # Record click
        self.db.record_click(
        short_code=short_code,
        ip_address=ip_address if config.TRACK_IP else '',
        country=country,  # Now guaranteed to be a string
        city=city,        # Now guaranteed to be a string
        browser=browser,
        device=device,
        response_time_ms=response_time_ms
        )
    
    # Redirect to original URL
        self.send_response(301)
        self.send_header('Location', url_data['original_url'])
        self.end_headers()
    
        logger.info(f"Redirected {short_code} -> {url_data['original_url']} ({response_time_ms:.2f}ms)")
    
    def handle_api(self, path):
        """
        Handle API endpoints
        
        Args:
            path: API path
        """
        # Remove 'api/' prefix
        endpoint = path[4:]
        
        if endpoint == 'stats':
            stats = self.db.get_statistics()
            self.send_json_response(stats)
        else:
            self.send_error(404, "API endpoint not found")
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

class URLServer:
    """URL redirect server manager"""
    
    def __init__(self, database: Database, host=config.SERVER_HOST, port=config.SERVER_PORT):
        """
        Initialize server
        
        Args:
            database: Database instance
            host: Server host
            port: Server port
        """
        self.database = database
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
        
        # Set database for handler
        URLRedirectHandler.db = database
        
        logger.info(f"Server initialized on {host}:{port}")
    
    def start(self):
        """Start the server in a separate thread"""
        if self.running:
            logger.warning("Server is already running")
            return False
        
        try:
            # Create server
            self.server = socketserver.TCPServer((self.host, self.port), URLRedirectHandler)
            
            # Start server in thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.running = True
            logger.info(f"Server started at {config.CUSTOM_DOMAIN}")
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the server"""
        if not self.running:
            logger.warning("Server is not running")
            return
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            logger.info("Server stopped")
    
    def is_running(self):
        """Check if server is running"""
        return self.running
    
    def get_url(self):
        """Get server URL"""
        return config.CUSTOM_DOMAIN