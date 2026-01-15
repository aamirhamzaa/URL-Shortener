import sqlite3
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import config
from logger import logger



class Database:
    """Database manager for URL shortener"""
    
    def __init__(self, db_path=config.DATABASE_PATH):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        logger.info(f"Database initialized at {db_path}")
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            self.cursor = self.conn.cursor()
            logger.debug("Database connection established")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def create_tables(self):
        """Create all required tables"""
        try:
            # URLs table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    short_code TEXT UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    custom BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT 1,
                    notes TEXT,
                    tags TEXT,
                    password TEXT NULL
                )
            ''')
            
            # Clicks table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS clicks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    short_code TEXT NOT NULL,
                    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    country TEXT,
                    city TEXT,
                    browser TEXT,
                    device TEXT,
                    response_time_ms REAL,
                    FOREIGN KEY (short_code) REFERENCES urls(short_code) ON DELETE CASCADE
                )
            ''')
            
            # Settings table (for user preferences)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_clicks_short_code ON clicks(short_code)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON urls(created_at)')
            
            self.conn.commit()
            logger.info("Database tables created/verified")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def insert_url(self, short_code, original_url, custom=False, expires_at=None, notes="", tags=""):
        """
        Insert new URL into database
        
        Args:
            short_code: Shortened code
            original_url: Original URL
            custom: Whether it's a custom short code
            expires_at: Expiration datetime (None for no expiration)
            notes: Optional notes
            tags: Optional tags (comma-separated)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute('''
                INSERT INTO urls (short_code, original_url, custom, expires_at, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (short_code, original_url, custom, expires_at, notes, tags))
            self.conn.commit()
            logger.log_url_created(short_code, original_url, custom)
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Short code '{short_code}' already exists")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error inserting URL: {e}")
            return False
    
    def get_url(self, short_code):
        """
        Get URL by short code
        
        Args:
            short_code: Shortened code
        
        Returns:
            Dictionary with URL data or None
        """
        try:
            self.cursor.execute('''
                SELECT * FROM urls WHERE short_code = ? AND is_active = 1
            ''', (short_code,))
            row = self.cursor.fetchone()
            
            if row:
                # Check if expired
                if row['expires_at']:
                    expires_at = datetime.fromisoformat(row['expires_at'])
                    if datetime.now() > expires_at:
                        logger.warning(f"URL {short_code} has expired")
                        return None
                
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving URL: {e}")
            return None
    
    def get_all_urls(self, include_inactive=False):
        """
        Get all URLs from database
        
        Args:
            include_inactive: Include inactive URLs
        
        Returns:
            List of URL dictionaries
        """
        try:
            if include_inactive:
                self.cursor.execute('SELECT * FROM urls ORDER BY created_at DESC')
            else:
                self.cursor.execute('SELECT * FROM urls WHERE is_active = 1 ORDER BY created_at DESC')
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all URLs: {e}")
            return []
    
    def update_url(self, short_code, original_url=None, notes=None, tags=None, expires_at=None):
        """
        Update existing URL
        
        Args:
            short_code: Shortened code
            original_url: New original URL (optional)
            notes: New notes (optional)
            tags: New tags (optional)
            expires_at: New expiration (optional)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            updates = []
            params = []
            
            if original_url is not None:
                updates.append("original_url = ?")
                params.append(original_url)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            if tags is not None:
                updates.append("tags = ?")
                params.append(tags)
            if expires_at is not None:
                updates.append("expires_at = ?")
                params.append(expires_at)
            
            if not updates:
                return False
            
            params.append(short_code)
            query = f"UPDATE urls SET {', '.join(updates)} WHERE short_code = ?"
            
            self.cursor.execute(query, params)
            self.conn.commit()
            logger.log_url_updated(short_code, original_url or "metadata")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating URL: {e}")
            return False
    
    def delete_url(self, short_code):
        """
        Delete URL (soft delete - marks as inactive)
        
        Args:
            short_code: Shortened code
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute('''
                UPDATE urls SET is_active = 0 WHERE short_code = ?
            ''', (short_code,))
            self.conn.commit()
            logger.log_url_deleted(short_code)
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting URL: {e}")
            return False
    
    def hard_delete_url(self, short_code):
        """
        Permanently delete URL and associated clicks
        
        Args:
            short_code: Shortened code
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute('DELETE FROM clicks WHERE short_code = ?', (short_code,))
            self.cursor.execute('DELETE FROM urls WHERE short_code = ?', (short_code,))
            self.conn.commit()
            logger.log_url_deleted(f"{short_code} (permanent)")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error hard deleting URL: {e}")
            return False
    
    def record_click(self, short_code, ip_address="", country="", city="", 
                    browser="", device="", response_time_ms=0):
        """
        Record a click/visit to a shortened URL
        
        Args:
            short_code: Shortened code
            ip_address: Visitor's IP address
            country: Visitor's country
            city: Visitor's city
            browser: Browser name
            device: Device type
            response_time_ms: Response time in milliseconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute('''
                INSERT INTO clicks (short_code, ip_address, country, city, 
                                   browser, device, response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (short_code, ip_address, country, city, browser, device, response_time_ms))
            self.conn.commit()
            logger.log_url_accessed(short_code, ip_address)
            return True
        except sqlite3.Error as e:
            logger.error(f"Error recording click: {e}")
            return False
    
    def get_click_count(self, short_code):
        """
        Get total click count for a URL
        
        Args:
            short_code: Shortened code
        
        Returns:
            Click count
        """
        try:
            self.cursor.execute('''
                SELECT COUNT(*) as count FROM clicks WHERE short_code = ?
            ''', (short_code,))
            result = self.cursor.fetchone()
            return result['count'] if result else 0
        except sqlite3.Error as e:
            logger.error(f"Error getting click count: {e}")
            return 0
    
    def get_clicks(self, short_code=None, limit=None, start_date=None, end_date=None):
        """
        Get click records with optional filters
        
        Args:
            short_code: Filter by specific short code (optional)
            limit: Limit number of results (optional)
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
        
        Returns:
            List of click records
        """
        try:
            query = 'SELECT * FROM clicks WHERE 1=1'
            params = []
            
            if short_code:
                query += ' AND short_code = ?'
                params.append(short_code)
            
            if start_date:
                query += ' AND clicked_at >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND clicked_at <= ?'
                params.append(end_date)
            
            query += ' ORDER BY clicked_at DESC'
            
            if limit:
                query += f' LIMIT {limit}'
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting clicks: {e}")
            return []
    
    def search_urls(self, search_term):
        """
        Search URLs by short code, original URL, or notes
        
        Args:
            search_term: Search string
        
        Returns:
            List of matching URLs
        """
        try:
            search_pattern = f'%{search_term}%'
            self.cursor.execute('''
                SELECT * FROM urls 
                WHERE (short_code LIKE ? OR original_url LIKE ? OR notes LIKE ? OR tags LIKE ?)
                AND is_active = 1
                ORDER BY created_at DESC
            ''', (search_pattern, search_pattern, search_pattern, search_pattern))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error searching URLs: {e}")
            return []
    
    def get_statistics(self):
        """
        Get overall statistics
        
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {}
            
            # Total URLs
            self.cursor.execute('SELECT COUNT(*) as count FROM urls WHERE is_active = 1')
            stats['total_urls'] = self.cursor.fetchone()['count']
            
            # Total clicks
            self.cursor.execute('SELECT COUNT(*) as count FROM clicks')
            stats['total_clicks'] = self.cursor.fetchone()['count']
            
            # Average clicks per URL
            stats['avg_clicks_per_url'] = stats['total_clicks'] / stats['total_urls'] if stats['total_urls'] > 0 else 0
            
            # Most clicked URL
            self.cursor.execute('''
                SELECT short_code, COUNT(*) as clicks 
                FROM clicks 
                GROUP BY short_code 
                ORDER BY clicks DESC 
                LIMIT 1
            ''')
            result = self.cursor.fetchone()
            stats['most_clicked'] = {'short_code': result['short_code'], 'clicks': result['clicks']} if result else None
            
            # Average response time
            self.cursor.execute('SELECT AVG(response_time_ms) as avg_time FROM clicks')
            result = self.cursor.fetchone()
            stats['avg_response_time_ms'] = result['avg_time'] if result['avg_time'] else 0
            
            # Top countries
            self.cursor.execute('''
                SELECT country, COUNT(*) as count 
                FROM clicks 
                WHERE country != "" 
                GROUP BY country 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            stats['top_countries'] = [dict(row) for row in self.cursor.fetchall()]
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def create_backup(self):
        """
        Create database backup
        
        Returns:
            Backup file path or None
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = config.BACKUPS_DIR / f"backup_{timestamp}.db"
            
            # Close connection temporarily for backup
            self.conn.close()
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Reconnect
            self.connect()
            
            logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            self.connect()  # Ensure reconnection
            return None
    
    def save_setting(self, key, value):
        """
        Save user setting
        
        Args:
            key: Setting key
            value: Setting value
        
        Returns:
            True if successful
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, json.dumps(value)))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving setting: {e}")
            return False
    
    def get_setting(self, key, default=None):
        """
        Get user setting
        
        Args:
            key: Setting key
            default: Default value if not found
        
        Returns:
            Setting value or default
        """
        try:
            self.cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = self.cursor.fetchone()
            if result:
                return json.loads(result['value'])
            return default
        except sqlite3.Error as e:
            logger.error(f"Error getting setting: {e}")
            return default
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")