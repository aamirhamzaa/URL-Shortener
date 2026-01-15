import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from datetime import datetime
import webbrowser
import pyperclip
from PIL import Image, ImageTk
import io
import base64
import threading
import config
from logger import logger
from database import Database
from url_shortener import URLShortener
from server import URLServer
from analytics import Analytics
from utils import export_to_csv, export_to_json, validate_url

class ModernButton(tk.Button):
    """Modern styled button"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            relief=tk.FLAT,
            borderwidth=0,
            cursor='hand2',
            **kwargs
        )
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.default_bg = kwargs.get('bg', '#4CAF50')
        self.hover_bg = kwargs.get('activebackground', '#45a049')
    
    def on_enter(self, e):
        self['background'] = self.hover_bg
    
    def on_leave(self, e):
        self['background'] = self.default_bg

class URLShortenerGUI:
    """Main GUI application"""
    
    def __init__(self, root):
        """
        Initialize GUI
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("🔗 URL Shortener Pro")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Set icon (if available)
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # Initialize components
        self.db = Database()
        self.shortener = URLShortener(self.db)
        self.server = URLServer(self.db)
        self.analytics = Analytics(self.db)
        
        # GUI variables
        self.url_var = tk.StringVar()
        self.custom_code_var = tk.StringVar()
        self.expires_var = tk.StringVar(value="Never")
        self.notes_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.validate_url_var = tk.BooleanVar(value=True)
        self.auto_copy_var = tk.BooleanVar(value=True)
        self.server_status_var = tk.StringVar(value="Stopped")
        
        # Create GUI
        self.create_styles()
        self.create_menu()
        self.create_layout()
        
        # Start server automatically
        self.start_server()
        
        # Load initial data
        self.refresh_urls()
        self.update_statistics()
        
        # Set up auto-refresh
        self.auto_refresh()
        
        logger.info("GUI initialized successfully")
    
    def create_styles(self):
        """Create custom styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors
        self.colors = {
            'primary': '#4CAF50',
            'secondary': '#2196F3',
            'danger': '#f44336',
            'warning': '#FF9800',
            'success': '#8BC34A',
            'bg': '#f5f5f5',
            'card': '#ffffff',
            'text': '#333333',
            'text_light': '#666666'
        }
        
        # Configure styles
        self.style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'), foreground=self.colors['primary'])
        self.style.configure('Subtitle.TLabel', font=('Segoe UI', 12), foreground=self.colors['text_light'])
        self.style.configure('Card.TFrame', background=self.colors['card'], relief=tk.RAISED, borderwidth=1)
        self.style.configure('Stat.TLabel', font=('Segoe UI', 18, 'bold'), foreground=self.colors['primary'])
        self.style.configure('StatLabel.TLabel', font=('Segoe UI', 10), foreground=self.colors['text_light'])
        
        # Treeview style
        self.style.configure('Treeview', rowheight=30, font=('Segoe UI', 10))
        self.style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background=self.colors['primary'], foreground='white')
        self.style.map('Treeview', background=[('selected', self.colors['secondary'])])
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import URLs...", command=self.import_urls)
        file_menu.add_command(label="Export URLs...", command=self.export_urls)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Database", command=self.backup_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Server menu
        server_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Server", menu=server_menu)
        server_menu.add_command(label="Start Server", command=self.start_server)
        server_menu.add_command(label="Stop Server", command=self.stop_server)
        server_menu.add_command(label="Restart Server", command=self.restart_server)
        server_menu.add_separator()
        server_menu.add_command(label="Server Settings", command=self.show_server_settings)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Bulk Shortener", command=self.show_bulk_shortener)
        tools_menu.add_command(label="QR Code Generator", command=self.show_qr_generator)
        tools_menu.add_command(label="URL Validator", command=self.show_url_validator)
        tools_menu.add_separator()
        tools_menu.add_command(label="Cleanup Expired URLs", command=self.cleanup_expired)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_layout(self):
        """Create main layout"""
        # Main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_shorten_tab()
        self.create_manage_tab()
        self.create_analytics_tab()
        self.create_settings_tab()
        
        # Status bar
        self.create_status_bar(main_container)
    
    def create_shorten_tab(self):
        """Create URL shortening tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="  🔗 Shorten URL  ")
        
        # Title section
        title_frame = ttk.Frame(tab)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Shorten Your URL", style='Title.TLabel').pack(anchor=tk.W)
        ttk.Label(title_frame, text="Enter a long URL below to create a shortened link", 
                 style='Subtitle.TLabel').pack(anchor=tk.W)
        
        # Main card
        card = ttk.Frame(tab, style='Card.TFrame', padding="30")
        card.pack(fill=tk.BOTH, expand=True)
        
        # URL input section
        input_frame = ttk.LabelFrame(card, text="URL Information", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Original URL
        ttk.Label(input_frame, text="Original URL *", font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(input_frame, textvariable=self.url_var, font=('Segoe UI', 11), width=60)
        url_entry.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 15))
        url_entry.focus()
        
        # Custom code
        ttk.Label(input_frame, text="Custom Short Code (optional)", font=('Segoe UI', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        custom_entry = ttk.Entry(input_frame, textvariable=self.custom_code_var, font=('Segoe UI', 11), width=30)
        custom_entry.grid(row=3, column=0, sticky=tk.W, pady=(0, 15))
        
        ttk.Label(input_frame, text=f"Max {config.MAX_CUSTOM_LENGTH} characters, alphanumeric only", 
                 font=('Segoe UI', 9), foreground=self.colors['text_light']).grid(
            row=4, column=0, sticky=tk.W)
        
        # Expiration
        ttk.Label(input_frame, text="Expiration", font=('Segoe UI', 10, 'bold')).grid(
            row=2, column=1, sticky=tk.W, padx=(30, 0), pady=5)
        expires_combo = ttk.Combobox(input_frame, textvariable=self.expires_var, 
                                     values=["Never", "1 day", "7 days", "30 days", "90 days", "1 year"],
                                     state='readonly', width=15)
        expires_combo.grid(row=3, column=1, sticky=tk.W, padx=(30, 0), pady=(0, 15))
        
        input_frame.columnconfigure(0, weight=1)
        
        # Additional options
        options_frame = ttk.LabelFrame(card, text="Additional Options", padding="15")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Notes
        ttk.Label(options_frame, text="Notes", font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        notes_entry = ttk.Entry(options_frame, textvariable=self.notes_var, font=('Segoe UI', 10), width=60)
        notes_entry.grid(row=1, column=0, sticky=tk.EW, pady=(0, 15))
        
        # Tags
        ttk.Label(options_frame, text="Tags (comma-separated)", font=('Segoe UI', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        tags_entry = ttk.Entry(options_frame, textvariable=self.tags_var, font=('Segoe UI', 10), width=60)
        tags_entry.grid(row=3, column=0, sticky=tk.EW, pady=(0, 15))
        
        # Checkboxes
        check_frame = ttk.Frame(options_frame)
        check_frame.grid(row=4, column=0, sticky=tk.W)
        
        ttk.Checkbutton(check_frame, text="Validate URL before shortening", 
                       variable=self.validate_url_var).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Checkbutton(check_frame, text="Auto-copy shortened URL", 
                       variable=self.auto_copy_var).pack(side=tk.LEFT)
        
        options_frame.columnconfigure(0, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(card)
        button_frame.pack(fill=tk.X)
        
        ModernButton(
            button_frame,
            text="✨ Shorten URL",
            command=self.shorten_url,
            bg=self.colors['primary'],
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ModernButton(
            button_frame,
            text="🔄 Clear",
            command=self.clear_shorten_form,
            bg=self.colors['warning'],
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            padx=30,
            pady=10
        ).pack(side=tk.LEFT)
        
        # Result section
        self.result_frame = ttk.LabelFrame(card, text="Result", padding="15")
        self.result_frame.pack(fill=tk.X, pady=(20, 0))
        self.result_frame.pack_forget()  # Hide initially
        
        # Bind Enter key
        url_entry.bind('<Return>', lambda e: self.shorten_url())
    
    def create_manage_tab(self):
        """Create URL management tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="  📊 Manage URLs  ")
        
        # Title and controls
        header_frame = ttk.Frame(tab)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Manage URLs", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Search bar
        search_frame = ttk.Frame(header_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Entry(search_frame, textvariable=self.search_var, font=('Segoe UI', 10), 
                 width=30).pack(side=tk.LEFT, padx=(0, 5))
        ModernButton(
            search_frame,
            text="🔍 Search",
            command=self.search_urls,
            bg=self.colors['secondary'],
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=(0, 5))
        ModernButton(
            search_frame,
            text="🔄 Refresh",
            command=self.refresh_urls,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=5
        ).pack(side=tk.LEFT)
        
        # URLs table
        table_frame = ttk.Frame(tab)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        columns = ('Short Code', 'Original URL', 'Clicks', 'Created', 'Expires', 'Tags')
        self.urls_tree = ttk.Treeview(table_frame, columns=columns, show='tree headings',
                                      yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.urls_tree.yview)
        hsb.config(command=self.urls_tree.xview)
        
        # Configure columns
        self.urls_tree.column('#0', width=0, stretch=tk.NO)
        self.urls_tree.column('Short Code', width=120, anchor=tk.W)
        self.urls_tree.column('Original URL', width=400, anchor=tk.W)
        self.urls_tree.column('Clicks', width=80, anchor=tk.CENTER)
        self.urls_tree.column('Created', width=150, anchor=tk.CENTER)
        self.urls_tree.column('Expires', width=150, anchor=tk.CENTER)
        self.urls_tree.column('Tags', width=200, anchor=tk.W)
        
        # Configure headings
        for col in columns:
            self.urls_tree.heading(col, text=col, command=lambda c=col: self.sort_urls(c))
        
        self.urls_tree.pack(fill=tk.BOTH, expand=True)
        
        # Context menu
        self.create_context_menu()
        
        # Bind events
        self.urls_tree.bind('<Button-3>', self.show_context_menu)
        self.urls_tree.bind('<Double-1>', self.view_url_details)
        
        # Action buttons
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        ModernButton(
            action_frame,
            text="👁️ View Details",
            command=self.view_url_details,
            bg=self.colors['secondary'],
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ModernButton(
            action_frame,
            text="📋 Copy URL",
            command=self.copy_selected_url,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ModernButton(
            action_frame,
            text="✏️ Edit",
            command=self.edit_url,
            bg=self.colors['warning'],
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ModernButton(
            action_frame,
            text="🗑️ Delete",
            command=self.delete_url,
            bg=self.colors['danger'],
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=8
        ).pack(side=tk.LEFT)
    
    def create_analytics_tab(self):
        """Create analytics tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="  📈 Analytics  ")
        
        # Title
        ttk.Label(tab, text="Analytics Dashboard", style='Title.TLabel').pack(anchor=tk.W, pady=(0, 20))
        
        # Statistics cards
        stats_frame = ttk.Frame(tab)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Create stat cards
        self.stat_cards = {}
        stat_names = ['Total URLs', 'Total Clicks', 'Avg Clicks/URL', 'Avg Response Time']
        
        for i, name in enumerate(stat_names):
            card = self.create_stat_card(stats_frame, name, "0")
            card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
            self.stat_cards[name] = card
        
        # Charts section
        charts_notebook = ttk.Notebook(tab)
        charts_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Clicks over time
        clicks_frame = ttk.Frame(charts_notebook, padding="20")
        charts_notebook.add(clicks_frame, text="Clicks Over Time")
        
        self.clicks_chart_label = ttk.Label(clicks_frame)
        self.clicks_chart_label.pack(fill=tk.BOTH, expand=True)
        
        # Geographic distribution
        geo_frame = ttk.Frame(charts_notebook, padding="20")
        charts_notebook.add(geo_frame, text="Geographic Distribution")
        
        self.geo_chart_label = ttk.Label(geo_frame)
        self.geo_chart_label.pack(fill=tk.BOTH, expand=True)
        
        # Browser/Device stats
        browser_frame = ttk.Frame(charts_notebook, padding="20")
        charts_notebook.add(browser_frame, text="Browser & Device Stats")
        
        browser_container = ttk.Frame(browser_frame)
        browser_container.pack(fill=tk.BOTH, expand=True)
        
        browser_left = ttk.Frame(browser_container)
        browser_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        browser_right = ttk.Frame(browser_container)
        browser_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.browser_chart_label = ttk.Label(browser_left)
        self.browser_chart_label.pack(fill=tk.BOTH, expand=True)
        
        self.device_chart_label = ttk.Label(browser_right)
        self.device_chart_label.pack(fill=tk.BOTH, expand=True)
        
        # Export button
        export_frame = ttk.Frame(tab)
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        ModernButton(
            export_frame,
            text="📊 Export Report",
            command=self.export_analytics_report,
            bg=self.colors['primary'],
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT)
        
        # Load analytics
        self.update_analytics()
    
    def create_settings_tab(self):
        """Create settings tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="  ⚙️ Settings  ")
        
        # Title
        ttk.Label(tab, text="Application Settings", style='Title.TLabel').pack(anchor=tk.W, pady=(0, 20))
        
        # Settings sections
        settings_notebook = ttk.Notebook(tab)
        settings_notebook.pack(fill=tk.BOTH, expand=True)
        
        # General settings
        general_frame = ttk.Frame(settings_notebook, padding="20")
        settings_notebook.add(general_frame, text="General")
        
        self.create_general_settings(general_frame)
        
        # Server settings
        server_frame = ttk.Frame(settings_notebook, padding="20")
        settings_notebook.add(server_frame, text="Server")
        
        self.create_server_settings(server_frame)
        
        # Advanced settings
        advanced_frame = ttk.Frame(settings_notebook, padding="20")
        settings_notebook.add(advanced_frame, text="Advanced")
        
        self.create_advanced_settings(advanced_frame)
    
    def create_stat_card(self, parent, title, value):
        """Create a statistics card"""
        card = ttk.Frame(parent, style='Card.TFrame', padding="15")
        
        ttk.Label(card, text=title, style='StatLabel.TLabel').pack()
        value_label = ttk.Label(card, text=value, style='Stat.TLabel')
        value_label.pack()
        
        return value_label
    
    def create_context_menu(self):
        """Create context menu for URLs table"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="View Details", command=self.view_url_details)
        self.context_menu.add_command(label="Copy Short URL", command=self.copy_selected_url)
        self.context_menu.add_command(label="Open in Browser", command=self.open_url_in_browser)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit", command=self.edit_url)
        self.context_menu.add_command(label="Delete", command=self.delete_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="View Analytics", command=self.view_url_analytics)
    
    def create_status_bar(self, parent):
        """Create status bar"""
        status_bar = ttk.Frame(parent, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Server status
        self.server_status_label = ttk.Label(
            status_bar,
            text="Server: Stopped",
            font=('Segoe UI', 9),
            foreground=self.colors['danger']
        )
        self.server_status_label.pack(side=tk.LEFT, padx=10)
        
        # URL count
        self.url_count_label = ttk.Label(
            status_bar,
            text="URLs: 0",
            font=('Segoe UI', 9)
        )
        self.url_count_label.pack(side=tk.LEFT, padx=10)
        
        # Last update
        self.last_update_label = ttk.Label(
            status_bar,
            text="Last update: Never",
            font=('Segoe UI', 9)
        )
        self.last_update_label.pack(side=tk.RIGHT, padx=10)
    
    def create_general_settings(self, parent):
        """Create general settings section"""
        # Domain settings
        domain_frame = ttk.LabelFrame(parent, text="Domain Settings", padding="15")
        domain_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(domain_frame, text="Custom Domain:", font=('Segoe UI', 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        domain_entry = ttk.Entry(domain_frame, font=('Segoe UI', 10), width=40)
        domain_entry.insert(0, config.CUSTOM_DOMAIN)
        domain_entry.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        
        domain_frame.columnconfigure(1, weight=1)
        
        # URL settings
        url_frame = ttk.LabelFrame(parent, text="URL Settings", padding="15")
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(url_frame, text="Short Code Length:", font=('Segoe UI', 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        length_spin = ttk.Spinbox(url_frame, from_=4, to=10, width=10)
        length_spin.set(config.SHORT_CODE_LENGTH)
        length_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(url_frame, text="Max Custom Length:", font=('Segoe UI', 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        max_spin = ttk.Spinbox(url_frame, from_=10, to=50, width=10)
        max_spin.set(config.MAX_CUSTOM_LENGTH)
        max_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
    
    def create_server_settings(self, parent):
        """Create server settings section"""
        # Server info
        info_frame = ttk.LabelFrame(parent, text="Server Information", padding="15")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(info_frame, text=f"Host: {config.SERVER_HOST}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Port: {config.SERVER_PORT}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"URL: {config.CUSTOM_DOMAIN}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        # Server controls
        controls_frame = ttk.LabelFrame(parent, text="Server Controls", padding="15")
        controls_frame.pack(fill=tk.X)
        
        ModernButton(
            controls_frame,
            text="▶️ Start Server",
            command=self.start_server,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ModernButton(
            controls_frame,
            text="⏸️ Stop Server",
            command=self.stop_server,
            bg=self.colors['danger'],
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ModernButton(
            controls_frame,
            text="🔄 Restart Server",
            command=self.restart_server,
            bg=self.colors['warning'],
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT)
    
    def create_advanced_settings(self, parent):
        """Create advanced settings section"""
        # Tracking settings
        tracking_frame = ttk.LabelFrame(parent, text="Tracking Settings", padding="15")
        tracking_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Checkbutton(tracking_frame, text="Track IP addresses").pack(anchor=tk.W)
        ttk.Checkbutton(tracking_frame, text="Track geolocation").pack(anchor=tk.W)
        ttk.Checkbutton(tracking_frame, text="Track browser/device").pack(anchor=tk.W)
        
        # Database settings
        db_frame = ttk.LabelFrame(parent, text="Database", padding="15")
        db_frame.pack(fill=tk.X)
        
        ttk.Label(db_frame, text=f"Database: {config.DATABASE_PATH}", font=('Segoe UI', 10)).pack(anchor=tk.W)
        
        ModernButton(
            db_frame,
            text="🗄️ Backup Database",
            command=self.backup_database,
            bg=self.colors['secondary'],
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8
        ).pack(anchor=tk.W, pady=(10, 0))
    
    # URL Management Methods
    def shorten_url(self):
        """Shorten URL"""
        original_url = self.url_var.get().strip()
        
        if not original_url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
        
        custom_code = self.custom_code_var.get().strip() or None
        notes = self.notes_var.get().strip()
        tags = self.tags_var.get().strip()
        validate = self.validate_url_var.get()
        
        # Parse expiration
        expires_days = None
        expires_text = self.expires_var.get()
        if expires_text != "Never":
            if "day" in expires_text:
                expires_days = int(expires_text.split()[0])
            elif "year" in expires_text:
                expires_days = 365
        
        # Shorten URL
        result = self.shortener.shorten_url(
            original_url,
            custom_code=custom_code,
            expires_days=expires_days,
            notes=notes,
            tags=tags,
            validate=validate
        )
        
        if result['success']:
            # Show result
            self.show_result(result)
            
            # Auto-copy if enabled
            if self.auto_copy_var.get():
                pyperclip.copy(result['shortened_url'])
            
            # Clear form
            self.clear_shorten_form()
            
            # Refresh
            self.refresh_urls()
            self.update_statistics()
            
            logger.info(f"URL shortened successfully: {result['short_code']}")
        else:
            messagebox.showerror("Error", result['error'])
    
    def show_result(self, result):
        """Show shortening result"""
        # Clear previous result
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # Show result frame
        self.result_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Success message
        ttk.Label(
            self.result_frame,
            text="✅ URL Shortened Successfully!",
            font=('Segoe UI', 12, 'bold'),
            foreground=self.colors['success']
        ).pack(pady=(0, 10))
        
        # Shortened URL
        url_frame = ttk.Frame(self.result_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        url_entry = ttk.Entry(url_frame, font=('Segoe UI', 11), width=50)
        url_entry.insert(0, result['shortened_url'])
        url_entry.config(state='readonly')
        url_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ModernButton(
            url_frame,
            text="📋 Copy",
            command=lambda: self.copy_to_clipboard(result['shortened_url']),
            bg=self.colors['secondary'],
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ModernButton(
            url_frame,
            text="🌐 Open",
            command=lambda: webbrowser.open(result['shortened_url']),
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=5
        ).pack(side=tk.LEFT)
    
    def clear_shorten_form(self):
        """Clear shortening form"""
        self.url_var.set("")
        self.custom_code_var.set("")
        self.expires_var.set("Never")
        self.notes_var.set("")
        self.tags_var.set("")
        self.result_frame.pack_forget()
    
    def refresh_urls(self):
        """Refresh URLs table"""
        # Clear table
        for item in self.urls_tree.get_children():
            self.urls_tree.delete(item)
        
        # Get URLs
        urls = self.shortener.get_all_urls()
        
        # Populate table
        for url in urls:
            created = datetime.fromisoformat(url['created_at']).strftime('%Y-%m-%d %H:%M')
            expires = url['expires_at']
            if expires:
                expires = datetime.fromisoformat(expires).strftime('%Y-%m-%d')
            else:
                expires = "Never"
            
            self.urls_tree.insert('', tk.END, values=(
                url['short_code'],
                url['original_url'][:60] + '...' if len(url['original_url']) > 60 else url['original_url'],
                url['click_count'],
                created,
                expires,
                url['tags'] or ""
            ))
        
        # Update status
        self.url_count_label.config(text=f"URLs: {len(urls)}")
        self.last_update_label.config(text=f"Last update: {datetime.now().strftime('%H:%M:%S')}")
    
    def search_urls(self):
        """Search URLs"""
        search_term = self.search_var.get().strip()
        
        if not search_term:
            self.refresh_urls()
            return
        
        # Clear table
        for item in self.urls_tree.get_children():
            self.urls_tree.delete(item)
        
        # Search
        urls = self.shortener.search_urls(search_term)
        
        # Populate table
        for url in urls:
            click_count = self.shortener.db.get_click_count(url['short_code'])
            created = datetime.fromisoformat(url['created_at']).strftime('%Y-%m-%d %H:%M')
            expires = url['expires_at']
            if expires:
                expires = datetime.fromisoformat(expires).strftime('%Y-%m-%d')
            else:
                expires = "Never"
            
            self.urls_tree.insert('', tk.END, values=(
                url['short_code'],
                url['original_url'][:60] + '...' if len(url['original_url']) > 60 else url['original_url'],
                click_count,
                created,
                expires,
                url['tags'] or ""
            ))
    
    def sort_urls(self, column):
        """Sort URLs by column"""
        # Implementation for sorting
        pass
    
    def view_url_details(self, event=None):
        """View detailed information about selected URL"""
        selection = self.urls_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a URL")
            return
        
        item = self.urls_tree.item(selection[0])
        short_code = item['values'][0]
        
        # Get full details
        details = self.shortener.get_url_details(short_code)
        
        if not details:
            messagebox.showerror("Error", "URL not found")
            return
        
        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"URL Details - {short_code}")
        details_window.geometry("700x600")
        details_window.transient(self.root)
        
        # Content
        content = scrolledtext.ScrolledText(details_window, font=('Consolas', 10), wrap=tk.WORD)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Format details
        text = f"""
╔══════════════════════════════════════════════════════════════╗
║                      URL DETAILS                              ║
╚══════════════════════════════════════════════════════════════╝

Short Code:      {details['short_code']}
Shortened URL:   {details['shortened_url']}
Original URL:    {details['original_url']}

Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Clicks:    {details['click_count']}
Created:         {datetime.fromisoformat(details['created_at']).strftime('%Y-%m-%d %H:%M:%S')}
Expires:         {details['expires_at'] or 'Never'}
Custom:          {'Yes' if details.get('is_custom', False) else 'No'}

Additional Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Notes:           {details['notes'] or 'None'}
Tags:            {details['tags'] or 'None'}
        """
        
        content.insert('1.0', text.strip())
        content.config(state='disabled')
        
        # Close button
        ModernButton(
            details_window,
            text="Close",
            command=details_window.destroy,
            bg=self.colors['secondary'],
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8
        ).pack(pady=(0, 20))
    
    def copy_selected_url(self):
        """Copy selected short URL"""
        selection = self.urls_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a URL")
            return
        
        item = self.urls_tree.item(selection[0])
        short_code = item['values'][0]
        short_url = f"{config.CUSTOM_DOMAIN}/{short_code}"
        
        self.copy_to_clipboard(short_url)
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        pyperclip.copy(text)
        messagebox.showinfo("Success", "Copied to clipboard!")
    
    def open_url_in_browser(self):
        """Open selected URL in browser"""
        selection = self.urls_tree.selection()
        if not selection:
            return
        
        item = self.urls_tree.item(selection[0])
        short_code = item['values'][0]
        short_url = f"{config.CUSTOM_DOMAIN}/{short_code}"
        
        webbrowser.open(short_url)
    
    def edit_url(self):
        """Edit selected URL"""
        selection = self.urls_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a URL")
            return
        
        item = self.urls_tree.item(selection[0])
        short_code = item['values'][0]
        
        # Get current details
        details = self.shortener.get_url_details(short_code)
        
        # Create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit URL - {short_code}")
        edit_window.geometry("500x400")
        edit_window.transient(self.root)
        
        # Form
        form_frame = ttk.Frame(edit_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Original URL (read-only)
        ttk.Label(form_frame, text="Original URL:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        url_entry = ttk.Entry(form_frame, font=('Segoe UI', 10))
        url_entry.insert(0, details['original_url'])
        url_entry.config(state='readonly')
        url_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Notes
        ttk.Label(form_frame, text="Notes:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        notes_var = tk.StringVar(value=details['notes'] or "")
        notes_entry = ttk.Entry(form_frame, textvariable=notes_var, font=('Segoe UI', 10))
        notes_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Tags
        ttk.Label(form_frame, text="Tags:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        tags_var = tk.StringVar(value=details['tags'] or "")
        tags_entry = ttk.Entry(form_frame, textvariable=tags_var, font=('Segoe UI', 10))
        tags_entry.pack(fill=tk.X, pady=(0, 15))
        
        def save_changes():
            if self.shortener.update_url(short_code, notes=notes_var.get(), tags=tags_var.get()):
                messagebox.showinfo("Success", "URL updated successfully!")
                edit_window.destroy()
                self.refresh_urls()
            else:
                messagebox.showerror("Error", "Failed to update URL")
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ModernButton(
            button_frame,
            text="💾 Save",
            command=save_changes,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ModernButton(
            button_frame,
            text="❌ Cancel",
            command=edit_window.destroy,
            bg=self.colors['danger'],
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT)
    
    def delete_url(self):
        """Delete selected URL"""
        selection = self.urls_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a URL")
            return
        
        item = self.urls_tree.item(selection[0])
        short_code = item['values'][0]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm", f"Delete URL '{short_code}'?\n\nThis action cannot be undone."):
            if self.shortener.delete_url(short_code, permanent=True):
                messagebox.showinfo("Success", "URL deleted successfully!")
                self.refresh_urls()
                self.update_statistics()
            else:
                messagebox.showerror("Error", "Failed to delete URL")
    
    def show_context_menu(self, event):
        """Show context menu"""
        # Select item under cursor
        item = self.urls_tree.identify_row(event.y)
        if item:
            self.urls_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def view_url_analytics(self):
        """View analytics for selected URL"""
        selection = self.urls_tree.selection()
        if not selection:
            return
        
        item = self.urls_tree.item(selection[0])
        short_code = item['values'][0]
        
        # Switch to analytics tab and filter by short_code
        self.notebook.select(2)  # Analytics tab
        # Update charts for specific URL
        self.update_analytics(short_code)
    
    # Analytics Methods
    def update_statistics(self):
        """Update statistics cards"""
        stats = self.db.get_statistics()
        
        self.stat_cards['Total URLs'].config(text=str(stats.get('total_urls', 0)))
        self.stat_cards['Total Clicks'].config(text=str(stats.get('total_clicks', 0)))
        self.stat_cards['Avg Clicks/URL'].config(text=f"{stats.get('avg_clicks_per_url', 0):.1f}")
        self.stat_cards['Avg Response Time'].config(text=f"{stats.get('avg_response_time_ms', 0):.1f}ms")
    
    def update_analytics(self, short_code=None):
        """Update all analytics charts"""
        def update_thread():
            try:
                logger.debug("Starting analytics update...")
                
                # Clicks over time
                try:
                    clicks_img = self.analytics.generate_clicks_chart(short_code)
                    if clicks_img:
                        self.display_chart(self.clicks_chart_label, clicks_img)
                    else:
                        self.clicks_chart_label.config(text="No click data available")
                except Exception as e:
                    logger.error(f"Error generating clicks chart: {e}")
                    self.clicks_chart_label.config(text=f"Error: {str(e)}")
                
                # Geographic distribution
                try:
                    geo_img = self.analytics.generate_geographic_chart(short_code)
                    if geo_img:
                        self.display_chart(self.geo_chart_label, geo_img)
                    else:
                        self.geo_chart_label.config(text="No geographic data available")
                except Exception as e:
                    logger.error(f"Error generating geographic chart: {e}")
                    self.geo_chart_label.config(text=f"Error: {str(e)}")
                
                # Browser distribution
                try:
                    browser_data = self.analytics.get_browser_distribution(short_code)
                    if browser_data:
                        browser_img = self.analytics.generate_pie_chart(browser_data, "Browser Distribution")
                        if browser_img:
                            self.display_chart(self.browser_chart_label, browser_img)
                    else:
                        self.browser_chart_label.config(text="No browser data available")
                except Exception as e:
                    logger.error(f"Error generating browser chart: {e}")
                    self.browser_chart_label.config(text=f"Error: {str(e)}")
                
                # Device distribution
                try:
                    device_data = self.analytics.get_device_distribution(short_code)
                    if device_data:
                        device_img = self.analytics.generate_pie_chart(device_data, "Device Distribution")
                        if device_img:
                            self.display_chart(self.device_chart_label, device_img)
                    else:
                        self.device_chart_label.config(text="No device data available")
                except Exception as e:
                    logger.error(f"Error generating device chart: {e}")
                    self.device_chart_label.config(text=f"Error: {str(e)}")
                
                logger.debug("Analytics update completed successfully")
            
            except Exception as e:
                logger.error(f"Fatal error in analytics update: {e}")
        
        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()
    
    def display_chart(self, label, image_base64):
        """Display chart image"""
        try:
            if not image_base64:
                label.config(text="No chart data available")
                return
            
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Resize image to fit label
            max_width = 800
            max_height = 500
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            label.config(image=photo, text="")
            label.image = photo  # Keep reference
        except Exception as e:
            logger.error(f"Error displaying chart: {e}")
            label.config(text=f"Error displaying chart: {str(e)}")
    
    def export_analytics_report(self):
        """Export analytics report"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            report = self.analytics.export_analytics_report()
            with open(filename, 'w') as f:
                f.write(report)
            messagebox.showinfo("Success", f"Report exported to {filename}")
    
    # Server Methods
    def start_server(self):
        """Start URL redirect server"""
        if self.server.is_running():
            messagebox.showinfo("Info", "Server is already running")
            return
        
        if self.server.start():
            self.server_status_var.set("Running")
            self.server_status_label.config(
                text=f"Server: Running on {config.CUSTOM_DOMAIN}",
                foreground=self.colors['success']
            )
            messagebox.showinfo("Success", f"Server started successfully!\n\nURL: {config.CUSTOM_DOMAIN}")
        else:
            messagebox.showerror("Error", "Failed to start server")
    
    def stop_server(self):
        """Stop URL redirect server"""
        if not self.server.is_running():
            messagebox.showinfo("Info", "Server is not running")
            return
        
        self.server.stop()
        self.server_status_var.set("Stopped")
        self.server_status_label.config(
            text="Server: Stopped",
            foreground=self.colors['danger']
        )
        messagebox.showinfo("Success", "Server stopped")
    
    def restart_server(self):
        """Restart server"""
        self.stop_server()
        self.root.after(1000, self.start_server)
    
    def show_server_settings(self):
        """Show server settings dialog"""
        messagebox.showinfo("Server Settings", 
                           f"Host: {config.SERVER_HOST}\nPort: {config.SERVER_PORT}\nDomain: {config.CUSTOM_DOMAIN}")
    
    # Utility Methods
    def auto_refresh(self):
        """Auto-refresh data"""
        self.refresh_urls()
        self.update_statistics()
        self.root.after(30000, self.auto_refresh)  # Every 30 seconds
    
    def backup_database(self):
        """Backup database"""
        from shutil import copy2
        filename = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            initialfile=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        
        if filename:
            try:
                copy2(config.DATABASE_PATH, filename)
                messagebox.showinfo("Success", f"Database backed up to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Backup failed: {e}")
    
    def import_urls(self):
        """Import URLs from file"""
        messagebox.showinfo("Import", "Import feature coming soon!")
    
    def export_urls(self):
        """Export URLs to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            urls = self.shortener.get_all_urls()
            
            if filename.endswith('.csv'):
                success = export_to_csv(urls, filename)
            elif filename.endswith('.json'):
                success = export_to_json(urls, filename)
            else:
                success = False
            
            if success:
                messagebox.showinfo("Success", f"URLs exported to {filename}")
            else:
                messagebox.showerror("Error", "Export failed")
    
    def cleanup_expired(self):
        """Cleanup expired URLs"""
        count = self.shortener.cleanup_expired_urls()
        messagebox.showinfo("Cleanup", f"Cleaned up {count} expired URLs")
        self.refresh_urls()
        self.update_statistics()
    
    def show_bulk_shortener(self):
        """Show bulk URL shortener"""
        messagebox.showinfo("Bulk Shortener", "Bulk shortening feature coming soon!")
    
    def show_qr_generator(self):
        """Show QR code generator"""
        messagebox.showinfo("QR Generator", "QR code generator coming soon!")
    
    def show_url_validator(self):
        """Show URL validator"""
        messagebox.showinfo("URL Validator", "URL validator coming soon!")
    
    def show_documentation(self):
        """Show documentation"""
        webbrowser.open("https://github.com/yourusername/url-shortener")
    
    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = """
        Keyboard Shortcuts:
        
        Ctrl+N - New URL
        Ctrl+R - Refresh
        Ctrl+F - Search
        Ctrl+Q - Quit
        Delete - Delete selected URL
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        URL Shortener Pro
        Version 1.0.0
        
        A professional URL shortening service with
        analytics, custom domains, and more.
        
        Created with Python & Tkinter
        © 2024 All Rights Reserved
        """
        messagebox.showinfo("About", about_text)
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Stop server
            if self.server.is_running():
                self.server.stop()
            
            # Close database
            self.db.close()
            
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()