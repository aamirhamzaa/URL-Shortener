import sys
import os
import tkinter as tk
from tkinter import messagebox
import config
from logger import logger,setup_logging
from database import Database
from gui import URLShortenerGUI

def check_dependencies():
    """
    Check if all required dependencies are installed
    
    Returns:
        bool: True if all dependencies are available
    """
    required_packages = [
        'flask', 'requests', 'qrcode', 'matplotlib', 
        'PIL', 'pyperclip', 'user_agents'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"Missing required packages: {', '.join(missing)}")
        messagebox.showerror(
            "Missing Dependencies",
            f"The following packages are required but not installed:\n\n"
            f"{', '.join(missing)}\n\n"
            f"Please install them using:\n"
            f"pip install {' '.join(missing)}"
        )
        return False
    
    return True

def initialize_application():
    """
    Initialize application components
    
    Returns:
        bool: True if initialization successful
    """
    try:
        # Setup logging
        setup_logging()
        logger.info("="*60)
        logger.info("URL Shortener Application Starting")
        logger.info("="*60)
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("Python 3.8 or higher is required")
            messagebox.showerror(
                "Python Version Error",
                "Python 3.8 or higher is required to run this application."
            )
            return False
        
        logger.info(f"Python version: {sys.version}")
        
        # Check dependencies
        if not check_dependencies():
            return False
        
        # Create data directory if it doesn't exist
        os.makedirs(config.DATA_DIR, exist_ok=True)
        logger.info(f"Data directory: {config.DATA_DIR}")
        
        # Initialize database
        db = Database()
        logger.info("Database initialized successfully")
        db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        messagebox.showerror(
            "Initialization Error",
            f"Failed to initialize application:\n\n{str(e)}"
        )
        return False

def main():
    """
    Main application entry point
    """
    try:
        # Initialize application
        if not initialize_application():
            logger.error("Application initialization failed")
            sys.exit(1)
        
        # Create root window
        root = tk.Tk()
        
        # Set window properties
        root.withdraw()  # Hide window during initialization
        
        # Center window on screen
        window_width = 1400
        window_height = 900
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create and run GUI
        logger.info("Creating GUI...")
        app = URLShortenerGUI(root)
        
        # Show window
        root.deiconify()
        
        logger.info("Application started successfully")
        logger.info(f"Server URL: {config.CUSTOM_DOMAIN}")
        
        # Run application
        app.run()
        
        # Cleanup
        logger.info("Application shutting down...")
        logger.info("="*60)
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        messagebox.showerror(
            "Fatal Error",
            f"A fatal error occurred:\n\n{str(e)}\n\n"
            f"Please check the log file for details."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()