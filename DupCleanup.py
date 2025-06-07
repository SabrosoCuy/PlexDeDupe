#!/usr/bin/env python3
"""
PlexDeDupe - Duplicate Media Manager for Plex
A GUI tool to find and remove duplicate movies and TV episodes in Plex Media Server.
https://github.com/SabrosoCuy/PlexDeDupe

Features:
- Scans Plex library for duplicate media files
- Choose to keep largest (quality) or smallest (space) versions
- Color-coded interface with manual override options
- Column filtering to search and find specific items
- Dry-run mode for safe preview
- Debug console for troubleshooting
- Hardlink mode (Beta) - convert duplicates to hardlinks instead of deleting
- Files go to Recycle Bin on local drives (permanent deletion on network drives)

Requires: 
- Plex Media Server with "Allow media deletion" enabled
- Python 3.6+
- plexapi package (auto-installed on first run)

No additional dependencies needed for filtering or hardlink features.

Version: 1.2.1 (Bug fixes for episode metadata handling)
"""

import sys
import subprocess
import importlib.util
import tkinter as tk
from tkinter import messagebox, ttk

# Check and install dependencies
def check_and_install_dependencies():
    """Check if required packages are installed and install them if needed."""
    required_packages = {
        'plexapi': 'plexapi',
        # Add any future dependencies here:
        # 'package_name': 'pip_install_name',
    }
    
    missing_packages = []
    for package, pip_name in required_packages.items():
        if importlib.util.find_spec(package) is None:
            missing_packages.append((package, pip_name))
    
    if not missing_packages:
        print("[PlexDeDupe] All dependencies are already installed")
        return
    
    # Create a simple GUI prompt
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    packages_list = ", ".join([pkg[1] for pkg in missing_packages])
    result = messagebox.askyesno(
        "Missing Dependencies",
        f"PlexDeDupe requires the following package(s) which are not installed:\n{packages_list}\n\n"
        "Would you like to install them automatically?\n\n"
        f"This will run: pip install {' '.join([pkg[1] for pkg in missing_packages])}",
        icon='question'
    )
    
    if result:
        # Show installation window
        install_window = tk.Toplevel()
        install_window.title("Installing Dependencies")
        install_window.geometry("400x150")
        
        # Center the window
        install_window.update_idletasks()
        x = (install_window.winfo_screenwidth() // 2) - (install_window.winfo_width() // 2)
        y = (install_window.winfo_screenheight() // 2) - (install_window.winfo_height() // 2)
        install_window.geometry(f"+{x}+{y}")
        
        label = tk.Label(install_window, text=f"Installing {packages_list}...\nThis may take a moment.", pady=20)
        label.pack()
        
        progress = ttk.Progressbar(install_window, mode='indeterminate')
        progress.pack(pady=10, padx=20, fill=tk.X)
        progress.start(10)
        
        install_window.update()
        
        try:
            # Install all missing packages
            for package, pip_name in missing_packages:
                print(f"[PlexDeDupe] Installing {pip_name}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
            
            install_window.destroy()
            print("[PlexDeDupe] All packages installed successfully!")
            messagebox.showinfo("Success", f"{packages_list} installed successfully!\n\nPlexDeDupe will now start.")
        except subprocess.CalledProcessError as e:
            install_window.destroy()
            print(f"[PlexDeDupe] Failed to install packages: {str(e)}")
            messagebox.showerror(
                "Installation Failed",
                f"Failed to install {packages_list} automatically.\n\n"
                "Please install manually by running:\n"
                f"pip install {' '.join([pkg[1] for pkg in missing_packages])}\n\n"
                "in your command prompt or terminal."
            )
            sys.exit(1)
    else:
        messagebox.showinfo(
            "Installation Required",
            "PlexDeDupe requires these packages to function.\n\n"
            "Please install manually by running:\n"
            f"pip install {' '.join([pkg[1] for pkg in missing_packages])}\n\n"
            "in your command prompt or terminal."
        )
        sys.exit(1)
    
    root.destroy()

# Check dependencies before importing
check_and_install_dependencies()

# Now import the rest
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from plexapi.server import PlexServer
from collections import defaultdict
import os
import webbrowser
import datetime
import hashlib
import shutil

class PlexDuplicateManager:
    def __init__(self, root):
        self.root = root
        self.root.title("PlexDeDupe - Plex Duplicate Media Manager")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)  # Set minimum window size
        
        self.plex = None
        self.current_duplicates = {'movies': {}, 'shows': {}}
        self.console_window = None
        self.filter_vars = {}
        self.filter_entries = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Connection Frame
        conn_frame = ttk.LabelFrame(main_frame, text="Plex Server Connection", padding="10")
        conn_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # URL Input
        ttk.Label(conn_frame, text="Plex Server URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.url_var = tk.StringVar(value="http://localhost:32400")
        self.url_entry = ttk.Entry(conn_frame, textvariable=self.url_var, width=40)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Token Input with help button
        token_label_frame = ttk.Frame(conn_frame)
        token_label_frame.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(token_label_frame, text="Plex Token:").pack(side=tk.LEFT)
        help_btn = ttk.Button(token_label_frame, text="?", width=3, command=self.show_token_help)
        help_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(conn_frame, textvariable=self.token_var, width=40, show="*")
        self.token_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        
        # Show/Hide token button
        self.show_token_var = tk.BooleanVar(value=False)
        self.show_token_btn = ttk.Checkbutton(conn_frame, text="Show Token", 
                                               variable=self.show_token_var,
                                               command=self.toggle_token_visibility)
        self.show_token_btn.grid(row=1, column=2, pady=(5, 0))
        
        # Connect Button
        self.connect_btn = ttk.Button(conn_frame, text="Connect & Scan", command=self.connect_and_scan)
        self.connect_btn.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Auto-select checkbox
        self.auto_select_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto-select versions for deletion based on strategy below", 
                        variable=self.auto_select_var,
                        command=self.on_auto_select_changed).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Deletion strategy radio buttons
        strategy_frame = ttk.Frame(options_frame)
        strategy_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=(20, 0), pady=(5, 0))
        
        self.deletion_strategy_var = tk.StringVar(value="keep_largest")
        
        ttk.Radiobutton(strategy_frame, text="Keep largest (delete smaller versions)", 
                        variable=self.deletion_strategy_var, 
                        value="keep_largest",
                        command=self.on_strategy_changed).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Radiobutton(strategy_frame, text="Keep smallest (delete larger versions)", 
                        variable=self.deletion_strategy_var, 
                        value="keep_smallest",
                        command=self.on_strategy_changed).pack(side=tk.LEFT)
        
        # Dry run checkbox
        self.dry_run_var = tk.BooleanVar(value=True)
        self.dry_run_checkbox = ttk.Checkbutton(options_frame, text="Dry run (preview what would be deleted without making any changes)", 
                        variable=self.dry_run_var)
        self.dry_run_checkbox.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
        # Debug console checkbox
        self.show_console_var = tk.BooleanVar(value=False)
        console_checkbox = ttk.Checkbutton(options_frame, text="Show debug console (displays connection info and errors)", 
                        variable=self.show_console_var,
                        command=self.toggle_console)
        console_checkbox.grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        
        # Console help text
        console_help = ttk.Label(options_frame, text="    Useful for troubleshooting connection issues", 
                                font=('TkDefaultFont', 8), foreground='gray')
        console_help.grid(row=4, column=0, sticky=tk.W, padx=(20, 0))
        
        # Advanced Options Frame
        advanced_frame = ttk.LabelFrame(main_frame, text="Advanced Options (Beta)", padding="10")
        advanced_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Hardlink mode
        self.hardlink_mode_var = tk.BooleanVar(value=False)
        hardlink_checkbox = ttk.Checkbutton(advanced_frame, 
                                          text="Convert to hardlinks instead of deleting (saves space without removing files)", 
                                          variable=self.hardlink_mode_var,
                                          command=self.on_hardlink_mode_changed)
        hardlink_checkbox.grid(row=0, column=0, sticky=tk.W)
        
        # Hardlink warning text
        warning_text = ("⚠️ Hardlink Limitations:\n"
                       "• Only works on the same drive/volume (not across drives)\n"
                       "• Does NOT work on network drives, NAS, or mapped drives\n"
                       "• Some backup software may not handle hardlinks properly\n"
                       "• Requires files to be identical (same content)")
        warning_label = ttk.Label(advanced_frame, text=warning_text, 
                                 font=('TkDefaultFont', 8), foreground='#CC6600')
        warning_label.grid(row=1, column=0, sticky=tk.W, padx=(20, 0), pady=(5, 0))
        
        # Results Frame
        results_frame = ttk.LabelFrame(main_frame, text="Duplicate Media", padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)
        
        # Filter Frame
        filter_frame = ttk.Frame(results_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Filter help text
        filter_help = ttk.Label(filter_frame, text="Filters (case-insensitive):", font=('TkDefaultFont', 9, 'bold'))
        filter_help.grid(row=0, column=0, sticky=tk.W, padx=(5, 10))
        
        # Create filter entries for each column
        columns = ['Title', 'Type', 'Resolution', 'Codec', 'Size', 'Path', 'Action']
        column_widths = [20, 10, 10, 8, 8, 20, 8]  # Adjusted widths for each column
        
        for i, (col, width) in enumerate(zip(columns, column_widths)):
            # Create StringVar for each filter
            self.filter_vars[col] = tk.StringVar()
            self.filter_vars[col].trace('w', self.apply_filters)
            
            # Create label
            label = ttk.Label(filter_frame, text=f"{col}:", font=('TkDefaultFont', 8))
            label.grid(row=0, column=i*2+1, sticky=tk.W, padx=(5, 2))
            
            # Create entry
            entry = ttk.Entry(filter_frame, textvariable=self.filter_vars[col], width=width, font=('TkDefaultFont', 9))
            entry.grid(row=0, column=i*2+2, sticky=tk.W, padx=(0, 10))
            self.filter_entries[col] = entry
            
            # Bind Enter key to apply filter
            entry.bind('<Return>', lambda e: self.apply_filters())
        
        # Clear filters button (initially hidden)
        self.clear_filters_btn = ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters)
        self.clear_filters_btn.grid(row=0, column=len(columns)*2+2, padx=(10, 0))
        self.clear_filters_btn.grid_remove()  # Initially hidden
        
        # Configure column weights for filter frame
        for i in range(len(columns)*2):
            filter_frame.columnconfigure(i, weight=1)
        
        # Create Treeview for results
        self.tree = ttk.Treeview(results_frame, columns=('Type', 'Resolution', 'Codec', 'Size', 'Path', 'Action'), 
                                 show='tree headings', height=15)
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure columns
        self.tree.heading('#0', text='Media Title')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Resolution', text='Resolution')
        self.tree.heading('Codec', text='Codec')
        self.tree.heading('Size', text='Size')
        self.tree.heading('Path', text='File Path')
        self.tree.heading('Action', text='Action')
        
        # Column widths
        self.tree.column('#0', width=250)
        self.tree.column('Type', width=80)
        self.tree.column('Resolution', width=80)
        self.tree.column('Codec', width=60)
        self.tree.column('Size', width=80)
        self.tree.column('Path', width=200)
        self.tree.column('Action', width=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=vsb.set)
        
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=2, column=0, sticky=(tk.E, tk.W))
        self.tree.configure(xscrollcommand=hsb.set)
        
        # Bind double-click to toggle action
        self.tree.bind('<Double-1>', self.on_item_double_click)
        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)
        
        # Action Buttons Frame
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.process_btn = ttk.Button(action_frame, text="Process Selected Deletions", 
                                      command=self.process_deletions, state='disabled')
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_btn = ttk.Button(action_frame, text="Refresh", 
                                      command=self.connect_and_scan, state='disabled')
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status bar
        self.status_var = tk.StringVar(value="Not connected")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure grid weights for main_frame
        main_frame.rowconfigure(3, weight=1)
        
        # Log successful startup
        print("[PlexDeDupe] GUI initialized successfully")
    
    def show_token_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("How to Find Your Plex Token")
        help_window.geometry("600x400")
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Create scrolled text widget
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        help_text = """HOW TO FIND YOUR PLEX TOKEN

There are several ways to find your Plex token:

METHOD 1: Using Plex Web App (Easiest)
1. Sign into Plex Web (app.plex.tv)
2. Navigate to any item in your library (movie, show, etc.)
3. Click the "..." (three dots) button
4. Select "Get Info"
5. Click "View XML" at the bottom of the info window
6. Look at the URL in your browser - you'll see:
   X-Plex-Token=YOUR_TOKEN_HERE
7. Copy everything after "X-Plex-Token="

METHOD 2: Using Browser Developer Tools
1. Sign into Plex Web
2. Open Developer Tools (F12 in most browsers)
3. Go to the Network tab
4. Navigate around Plex
5. Look for any request and check the headers
6. Find "X-Plex-Token" in the request headers

METHOD 3: From Plex Media Server Settings
1. On the computer running Plex Media Server
2. Find the Preferences.xml file:
   - Windows: %LOCALAPPDATA%\\Plex Media Server\\
   - macOS: ~/Library/Application Support/Plex Media Server/
   - Linux: $PLEX_HOME/Library/Application Support/Plex Media Server/
3. Open Preferences.xml in a text editor
4. Look for PlexOnlineToken="YOUR_TOKEN_HERE"

IMPORTANT NOTES:
- Keep your token private - it provides full access to your server
- The token is tied to your account
- If you suspect your token was compromised, sign out of all devices

FILE DELETION WARNING:
- "Allow media deletion" MUST be enabled in Plex settings
- Without this setting, PlexDeDupe will fail with a 403 error
- Local drives: Files go to Recycle Bin/Trash (recoverable)
- Network drives: Files are PERMANENTLY deleted (NOT recoverable!)"""
        
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')
        
        # Close button
        close_btn = ttk.Button(help_window, text="Close", command=help_window.destroy)
        close_btn.pack(pady=10)
        
        # Center the window
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (help_window.winfo_width() // 2)
        y = (help_window.winfo_screenheight() // 2) - (help_window.winfo_height() // 2)
        help_window.geometry(f"+{x}+{y}")
    
    def toggle_console(self):
        """Show or hide the debug console window"""
        if self.show_console_var.get():
            self.create_console_window()
        else:
            if self.console_window and self.console_window.winfo_exists():
                self.console_window.destroy()
                self.console_window = None
    
    def create_console_window(self):
        """Create the debug console window"""
        if self.console_window and self.console_window.winfo_exists():
            self.console_window.lift()
            return
            
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("PlexDeDupe - Debug Console")
        self.console_window.geometry("800x400")
        
        # Position to the right of main window
        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() + 10
        y = self.root.winfo_y()
        self.console_window.geometry(f"+{x}+{y}")
        
        # Create console text area
        console_frame = ttk.Frame(self.console_window, padding="5")
        console_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.console_text = scrolledtext.ScrolledText(
            console_frame, 
            wrap=tk.WORD, 
            width=100, 
            height=24,
            bg='black',
            fg='lime',
            font=('Consolas', 9)
        )
        self.console_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear button
        clear_btn = ttk.Button(console_frame, text="Clear Console", command=self.clear_console)
        clear_btn.grid(row=1, column=0, pady=(5, 0))
        
        # Configure grid weights
        self.console_window.columnconfigure(0, weight=1)
        self.console_window.rowconfigure(0, weight=1)
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        
        # Handle window close
        self.console_window.protocol("WM_DELETE_WINDOW", self.on_console_close)
        
        self.log_message("Debug console opened", "INFO")
        self.log_message(f"PlexDeDupe version started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log_message(f"Python version: {sys.version}", "INFO")
        self.log_message(f"Operating System: {os.name} - {sys.platform}", "INFO")
        try:
            import plexapi
            self.log_message(f"PlexAPI version: {plexapi.__version__ if hasattr(plexapi, '__version__') else 'Unknown'}", "INFO")
        except:
            self.log_message("PlexAPI version: Unable to determine", "WARNING")
    
    def on_console_close(self):
        """Handle console window close"""
        self.show_console_var.set(False)
        if self.console_window:
            self.console_window.destroy()
            self.console_window = None
    
    def clear_console(self):
        """Clear the console text"""
        if self.console_text:
            self.console_text.delete(1.0, tk.END)
    
    def log_message(self, message, level="INFO"):
        """Log a message to the console if it's open"""
        if self.console_window and self.console_window.winfo_exists() and self.console_text:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Color based on level
            if level == "ERROR":
                self.console_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
                self.console_text.insert(tk.END, f"[{level}] ", 'error')
                self.console_text.insert(tk.END, f"{message}\n", 'error_msg')
            elif level == "WARNING":
                self.console_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
                self.console_text.insert(tk.END, f"[{level}] ", 'warning')
                self.console_text.insert(tk.END, f"{message}\n", 'warning_msg')
            elif level == "SUCCESS":
                self.console_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
                self.console_text.insert(tk.END, f"[{level}] ", 'success')
                self.console_text.insert(tk.END, f"{message}\n", 'success_msg')
            else:
                self.console_text.insert(tk.END, f"[{timestamp}] [{level}] {message}\n")
            
            # Configure tags for colors
            self.console_text.tag_config('timestamp', foreground='gray')
            self.console_text.tag_config('error', foreground='red', font=('Consolas', 9, 'bold'))
            self.console_text.tag_config('error_msg', foreground='pink')
            self.console_text.tag_config('warning', foreground='orange', font=('Consolas', 9, 'bold'))
            self.console_text.tag_config('warning_msg', foreground='yellow')
            self.console_text.tag_config('success', foreground='green', font=('Consolas', 9, 'bold'))
            self.console_text.tag_config('success_msg', foreground='lightgreen')
            
            # Auto-scroll to bottom
            self.console_text.see(tk.END)
            self.console_text.update_idletasks()
    
    def apply_filters(self, *args):
        """Apply filters to the tree view"""
        # Check if any filters are active
        has_filters = any(var.get().strip() for var in self.filter_vars.values())
        
        # Show/hide clear button based on filter status
        if has_filters:
            self.clear_filters_btn.grid()
            # Log which filters are active
            active_filters = [f"{col}: '{var.get()}'" for col, var in self.filter_vars.items() if var.get().strip()]
            self.log_message(f"Filters applied: {', '.join(active_filters)}", "INFO")
        else:
            self.clear_filters_btn.grid_remove()
        
        # Get all items
        all_items = []
        
        def get_all_items(parent=''):
            for child in self.tree.get_children(parent):
                item_data = {
                    'id': child,
                    'parent': parent,
                    'text': self.tree.item(child)['text'],
                    'values': self.tree.item(child)['values'],
                    'tags': self.tree.item(child)['tags']
                }
                all_items.append(item_data)
                # Recursively get children
                get_all_items(child)
        
        # Store current state before filtering
        if not hasattr(self, '_unfiltered_items'):
            self._unfiltered_items = []
            get_all_items()
            self._unfiltered_items = all_items.copy()
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Re-add items that match filters
        parent_ids = {}  # Map old parent IDs to new ones
        
        for item in self._unfiltered_items:
            # Check if item matches all filters
            matches = True
            
            # Title filter (from item text)
            title_filter = self.filter_vars['Title'].get().strip().lower()
            if title_filter and title_filter not in item['text'].lower():
                matches = False
            
            # Other column filters
            if matches and item['values']:
                for i, col in enumerate(['Type', 'Resolution', 'Codec', 'Size', 'Path', 'Action']):
                    filter_val = self.filter_vars[col].get().strip().lower()
                    if filter_val and i < len(item['values']):
                        item_val = str(item['values'][i]).lower()
                        if filter_val not in item_val:
                            matches = False
                            break
            
            # Add item if it matches or if it's a parent of a matching item
            if matches or self._has_matching_children(item['id'], title_filter):
                # Determine parent
                parent = ''
                if item['parent'] and item['parent'] in parent_ids:
                    parent = parent_ids[item['parent']]
                
                # Insert item
                new_id = self.tree.insert(parent, 'end', text=item['text'], 
                                         values=item['values'], tags=item['tags'])
                parent_ids[item['id']] = new_id
                
                # Expand parent if it has filtered children
                if parent:
                    self.tree.item(parent, open=True)
    
    def _has_matching_children(self, parent_id, title_filter):
        """Check if any children match the filter"""
        if not hasattr(self, '_unfiltered_items'):
            return False
            
        for item in self._unfiltered_items:
            if item['parent'] == parent_id:
                # Check title match
                if not title_filter or title_filter in item['text'].lower():
                    return True
                    
                # Check other filters
                all_match = True
                for i, col in enumerate(['Type', 'Resolution', 'Codec', 'Size', 'Path', 'Action']):
                    filter_val = self.filter_vars[col].get().strip().lower()
                    if filter_val and i < len(item['values']):
                        item_val = str(item['values'][i]).lower()
                        if filter_val not in item_val:
                            all_match = False
                            break
                
                if all_match:
                    return True
                    
                # Recursively check children
                if self._has_matching_children(item['id'], title_filter):
                    return True
        
        return False
    
    def clear_filters(self):
        """Clear all filters"""
        self.log_message("Clearing all filters", "INFO")
        
        # Clear all filter variables
        for var in self.filter_vars.values():
            var.set('')
        
        # This will trigger apply_filters through the trace
    
    def on_hardlink_mode_changed(self):
        """Handle hardlink mode toggle"""
        if self.hardlink_mode_var.get():
            self.log_message("Hardlink mode ENABLED - duplicates will be converted to hardlinks", "WARNING")
            self.process_btn.config(text="Convert Selected to Hardlinks")
            self.root.title("PlexDeDupe - Plex Duplicate Media Manager (Hardlink Mode)")
            # Update dry run text
            if hasattr(self, 'dry_run_checkbox'):
                self.dry_run_checkbox.config(text="Dry run (preview what would be converted without making changes)")
            # Warn about limitations
            response = messagebox.askyesno(
                "Hardlink Mode - Important Limitations",
                "Hardlink mode will convert duplicates to hardlinks instead of deleting.\n\n"
                "⚠️ LIMITATIONS:\n"
                "• Only works on the SAME drive/volume\n"
                "• Will NOT work across different drives\n"
                "• Will NOT work on network drives or NAS\n"
                "• Files must be IDENTICAL (same content)\n\n"
                "Files on different drives will be skipped.\n\n"
                "Do you want to enable hardlink mode?",
                icon='warning'
            )
            if not response:
                self.hardlink_mode_var.set(False)
                self.process_btn.config(text="Process Selected Deletions")
                self.root.title("PlexDeDupe - Plex Duplicate Media Manager")
        else:
            self.log_message("Hardlink mode DISABLED - duplicates will be deleted normally", "INFO")
            self.process_btn.config(text="Process Selected Deletions")
            self.root.title("PlexDeDupe - Plex Duplicate Media Manager")
            if hasattr(self, 'dry_run_checkbox'):
                self.dry_run_checkbox.config(text="Dry run (preview what would be deleted without making any changes)")
    
    def on_auto_select_changed(self):
        """Handle auto-select checkbox change"""
        if self.auto_select_var.get() and hasattr(self, 'current_duplicates'):
            # Re-populate results with new auto-selection
            self._populate_results()
    
    def on_strategy_changed(self):
        """Handle deletion strategy change"""
        if self.auto_select_var.get() and hasattr(self, 'current_duplicates'):
            # Re-populate results with new strategy
            self._populate_results()
    
    def get_file_hash(self, filepath, chunk_size=8192):
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            file_size = os.path.getsize(filepath)
            size_gb = file_size / (1024**3)
            
            if size_gb > 1:  # Log for files larger than 1GB
                self.log_message(f"    Calculating hash for {size_gb:.1f} GB file...", "INFO")
            
            with open(filepath, "rb") as f:
                while chunk := f.read(chunk_size):
                    sha256_hash.update(chunk)
            
            hash_result = sha256_hash.hexdigest()
            if size_gb > 1:
                self.log_message(f"    Hash calculation complete", "INFO")
            
            return hash_result
        except Exception as e:
            self.log_message(f"Error calculating hash for {filepath}: {str(e)}", "ERROR")
            return None
    
    def can_hardlink(self, file1, file2):
        """Check if two files can be hardlinked"""
        try:
            # Check if both files exist
            if not os.path.exists(file1) or not os.path.exists(file2):
                return False, "One or both files don't exist"
            
            # Check if on same device (required for hardlinks)
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)
            if stat1.st_dev != stat2.st_dev:
                return False, "Files are on different drives/volumes"
            
            # Check if files are already hardlinked
            if stat1.st_ino == stat2.st_ino:
                return False, "Files are already hardlinked"
            
            # Check if files have same size
            if stat1.st_size != stat2.st_size:
                return False, "Files have different sizes"
            
            # For large files, skip hash check if user confirms they're identical
            size_gb = stat1.st_size / (1024**3)
            if size_gb > 10:  # Files larger than 10GB
                self.log_message(f"  Large file ({size_gb:.1f} GB) - hash calculation may take time", "INFO")
            
            # Check if content is identical (hash comparison)
            hash1 = self.get_file_hash(file1)
            hash2 = self.get_file_hash(file2)
            if hash1 != hash2 or hash1 is None:
                return False, "Files have different content"
            
            return True, "Files can be hardlinked"
            
        except Exception as e:
            return False, f"Error checking hardlink compatibility: {str(e)}"
    
    def create_hardlink(self, source_file, target_file):
        """Create a hardlink from source to target"""
        try:
            # Backup the target file path
            target_backup = target_file + ".plexdedupe_backup"
            
            # Move target to backup
            shutil.move(target_file, target_backup)
            
            try:
                # Create hardlink
                os.link(source_file, target_file)
                # Remove backup
                os.remove(target_backup)
                return True, "Hardlink created successfully"
            except Exception as link_error:
                # Restore from backup if hardlink fails
                shutil.move(target_backup, target_file)
                return False, f"Failed to create hardlink: {str(link_error)}"
                
        except Exception as e:
            return False, f"Error during hardlink creation: {str(e)}"
    
    def toggle_token_visibility(self):
        if self.show_token_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")
    
    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()
        # Also log status updates to console
        self.log_message(f"Status: {message}", "INFO")
    
    def connect_and_scan(self):
        # Log the scan initiation
        self.log_message("=" * 60, "INFO")
        self.log_message("User initiated connection and scan", "INFO")
        
        # Disable buttons during scan
        self.connect_btn.config(state='disabled')
        self.process_btn.config(state='disabled')
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Run in separate thread to prevent UI freeze
        thread = threading.Thread(target=self._scan_duplicates)
        thread.daemon = True
        thread.start()
    
    def _scan_duplicates(self):
        try:
            # Connect to Plex
            self.update_status("Connecting to Plex server...")
            url = self.url_var.get()
            token = self.token_var.get()
            
            # Log connection details (safely)
            self.log_message(f"Attempting to connect to Plex server at: {url}", "INFO")
            if not url:
                self.log_message("ERROR: No URL provided!", "ERROR")
                raise Exception("Please enter a Plex server URL")
            if not token:
                self.log_message("ERROR: No token provided!", "ERROR") 
                raise Exception("Please enter a Plex token")
            
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                self.log_message("WARNING: URL should start with http:// or https://", "WARNING")
            
            # Check for common Plex port
            if ':32400' not in url and 'plex.tv' not in url:
                self.log_message("INFO: URL doesn't include :32400 - make sure this is correct for your setup", "INFO")
            
            self.log_message(f"Token length: {len(token)} characters", "INFO")
            self.log_message("Using provided authentication token", "INFO")
            
            try:
                self.plex = PlexServer(url, token)
                self.log_message(f"Successfully connected to: {self.plex.friendlyName}", "SUCCESS")
                self.log_message(f"Plex version: {self.plex.version}", "INFO")
                self.log_message(f"Platform: {self.plex.platform} {self.plex.platformVersion}", "INFO")
            except Exception as conn_error:
                self.log_message(f"Connection failed: {str(conn_error)}", "ERROR")
                if "401" in str(conn_error):
                    self.log_message("401 Unauthorized - Check your Plex token", "ERROR")
                elif "404" in str(conn_error):
                    self.log_message("404 Not Found - Check your Plex server URL", "ERROR")
                elif "connection" in str(conn_error).lower() or "timed out" in str(conn_error).lower():
                    self.log_message("Connection error - Is Plex server running and accessible?", "ERROR")
                    self.log_message("Check that:", "ERROR")
                    self.log_message("  1. Plex Media Server is running", "ERROR")
                    self.log_message("  2. The URL is correct (including port)", "ERROR")
                    self.log_message("  3. No firewall is blocking the connection", "ERROR")
                raise conn_error
            
            self.update_status(f"Connected to: {self.plex.friendlyName}")
            
            # Find duplicates
            self.update_status("Scanning for duplicate media...")
            self.log_message("Starting duplicate media scan...", "INFO")
            self.log_message("Note: If scan fails on a specific show/movie, check debug console for details", "INFO")
            
            # List libraries
            libraries = list(self.plex.library.sections())
            self.log_message(f"Found {len(libraries)} libraries to scan", "INFO")
            for lib in libraries:
                self.log_message(f"  - {lib.title} ({lib.type})", "INFO")
            
            self.current_duplicates = self.find_duplicate_media()
            
            # Log summary
            total_movie_dupes = len(self.current_duplicates['movies'])
            total_show_dupes = len(self.current_duplicates['shows'])
            self.log_message(f"Scan complete! Found {total_movie_dupes} movies and {total_show_dupes} TV episodes with duplicates", "SUCCESS")
            
            # Update UI in main thread
            self.root.after(0, self._populate_results)
            
        except Exception as e:
            self.log_message(f"Fatal error during scan: {str(e)}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror("Connection Error", str(e)))
            self.root.after(0, lambda: self.update_status("Connection failed"))
            self.root.after(0, lambda: self.connect_btn.config(state='normal'))
    
    def get_media_size(self, media):
        """Safely get media size, handling missing attributes"""
        try:
            if hasattr(media, 'size') and media.size is not None:
                return media.size
            # Try to get size from parts if media.size is not available
            if hasattr(media, 'parts') and media.parts:
                total_size = 0
                for part in media.parts:
                    if hasattr(part, 'size') and part.size is not None:
                        total_size += part.size
                return total_size if total_size > 0 else 0
        except:
            pass
        return 0
    
    def find_duplicate_media(self):
        duplicates = {
            'movies': {},
            'shows': {}
        }
        
        # Check movies
        movie_count = 0
        movie_dupe_count = 0
        for library in self.plex.library.sections():
            if library.type == 'movie':
                self.log_message(f"Scanning movie library: {library.title}", "INFO")
                all_movies = library.all()
                self.log_message(f"  Total movies in library: {len(all_movies)}", "INFO")
                
                for movie in all_movies:
                    movie_count += 1
                    if len(movie.media) > 1:
                        movie_dupe_count += 1
                        media_list = []
                        self.log_message(f"  Found duplicate: {movie.title} ({len(movie.media)} versions)", "WARNING")
                        
                        for media in movie.media:
                            try:
                                size = self.get_media_size(media)
                                media_info = {
                                    'media_obj': media,
                                    'resolution': str(media.videoResolution) if hasattr(media, 'videoResolution') and media.videoResolution else 'Unknown',
                                    'codec': str(media.videoCodec) if hasattr(media, 'videoCodec') and media.videoCodec else 'Unknown',
                                    'bitrate': media.bitrate if hasattr(media, 'bitrate') else 0,
                                    'size': size,
                                    'file': media.parts[0].file if hasattr(media, 'parts') and media.parts and hasattr(media.parts[0], 'file') else 'Unknown',
                                    'movie_obj': movie
                                }
                                media_list.append(media_info)
                            except Exception as e:
                                self.log_message(f"    Error processing media for {movie.title}: {str(e)}", "ERROR")
                                
                        if media_list:
                            duplicates['movies'][movie.title] = sorted(media_list, key=lambda x: x['size'], reverse=True)
        
        self.log_message(f"Movie scan complete: {movie_count} total movies, {movie_dupe_count} with duplicates", "INFO")
        
        # Check TV shows
        show_count = 0
        episode_count = 0
        episode_dupe_count = 0
        for library in self.plex.library.sections():
            if library.type == 'show':
                self.log_message(f"Scanning TV library: {library.title}", "INFO")
                try:
                    all_shows = library.all()
                    self.log_message(f"  Total shows in library: {len(all_shows)}", "INFO")
                    
                    for show in all_shows:
                        show_count += 1
                        show_title = show.title if show.title else f"Unknown Show (ID: {show.ratingKey})"
                        
                        try:
                            episodes = show.episodes()
                            
                            for episode in episodes:
                                episode_count += 1
                                try:
                                    if len(episode.media) > 1:
                                        episode_dupe_count += 1
                                        media_list = []
                                        
                                        # Handle missing season/episode numbers
                                        try:
                                            season_num = episode.seasonNumber if episode.seasonNumber is not None else 0
                                            episode_num = episode.episodeNumber if episode.episodeNumber is not None else 0
                                            episode_title = episode.title if episode.title else "Unknown Episode"
                                            
                                            episode_display = f"{show_title} - S{season_num:02d}E{episode_num:02d}"
                                            if episode_title != "Unknown Episode":
                                                episode_display += f" - {episode_title}"
                                            
                                            self.log_message(f"  Found duplicate: {episode_display} ({len(episode.media)} versions)", "WARNING")
                                        except Exception as format_error:
                                            # Fallback display if formatting fails
                                            episode_display = f"{show_title} - Episode (formatting error)"
                                            self.log_message(f"  Error formatting episode info for {show_title}: {str(format_error)}", "ERROR")
                                            self.log_message(f"    Raw data - Season: {getattr(episode, 'seasonNumber', 'None')}, Episode: {getattr(episode, 'episodeNumber', 'None')}, Title: {getattr(episode, 'title', 'None')}", "ERROR")
                                        
                                        for media in episode.media:
                                            try:
                                                size = self.get_media_size(media)
                                                media_info = {
                                                    'media_obj': media,
                                                    'resolution': str(media.videoResolution) if hasattr(media, 'videoResolution') and media.videoResolution else 'Unknown',
                                                    'codec': str(media.videoCodec) if hasattr(media, 'videoCodec') and media.videoCodec else 'Unknown',
                                                    'bitrate': media.bitrate if hasattr(media, 'bitrate') else 0,
                                                    'size': size,
                                                    'file': media.parts[0].file if hasattr(media, 'parts') and media.parts and hasattr(media.parts[0], 'file') else 'Unknown',
                                                    'episode_obj': episode
                                                }
                                                media_list.append(media_info)
                                            except Exception as e:
                                                error_msg = f"Error processing media for {episode_display}: {str(e)}"
                                                self.log_message(f"    {error_msg}", "ERROR")
                                                print(f"[PlexDeDupe] {error_msg}")
                                                
                                        if media_list:
                                            duplicates['shows'][episode_display] = sorted(media_list, key=lambda x: x['size'], reverse=True)
                                except Exception as episode_error:
                                    self.log_message(f"  Error processing episode in '{show_title}': {str(episode_error)}", "ERROR")
                                    self.log_message(f"    Episode details - Season: {getattr(episode, 'seasonNumber', 'None')}, Episode: {getattr(episode, 'episodeNumber', 'None')}", "ERROR")
                                    continue
                                    
                        except Exception as show_error:
                            self.log_message(f"  Error processing show '{show_title}': {str(show_error)}", "ERROR")
                            self.log_message(f"  Skipping this show and continuing...", "WARNING")
                            continue
                except Exception as lib_error:
                    self.log_message(f"  Error accessing TV library '{library.title}': {str(lib_error)}", "ERROR")
                    continue
        
        self.log_message(f"TV scan complete: {show_count} shows, {episode_count} total episodes, {episode_dupe_count} with duplicates", "INFO")
        
        return duplicates
    
    def _populate_results(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clear filters and stored items when populating new results
        if hasattr(self, '_unfiltered_items'):
            delattr(self, '_unfiltered_items')
        
        # Clear any active filters
        for var in self.filter_vars.values():
            var.set('')
        
        total_items = 0
        total_space_saveable = 0
        
        # Add movies
        for title, versions in self.current_duplicates['movies'].items():
            parent = self.tree.insert('', 'end', text=title, values=('Movie', '', '', '', '', ''))
            
            for i, version in enumerate(versions):
                size_gb = version['size'] / (1024**3) if version['size'] > 0 else 0
                
                # Determine action based on strategy
                if self.auto_select_var.get():
                    if self.deletion_strategy_var.get() == "keep_largest":
                        # Keep the largest (first in sorted list), delete others
                        action = 'KEEP' if i == 0 else 'DELETE'
                    else:  # keep_smallest
                        # Keep the smallest (last in sorted list), delete others
                        action = 'KEEP' if i == len(versions) - 1 else 'DELETE'
                    
                    if action == 'DELETE':
                        total_space_saveable += version['size']
                else:
                    action = 'KEEP'
                
                # Format file path for display
                file_path = version['file']
                display_path = file_path[-50:] if len(file_path) > 50 else file_path
                
                values = (
                    'Movie',
                    version['resolution'],
                    version['codec'],
                    f"{size_gb:.2f} GB" if size_gb > 0 else "Unknown",
                    display_path,
                    action
                )
                
                item_id = self.tree.insert(parent, 'end', text=f"Version {i+1}", values=values)
                # Store the full media info in the tree item
                self.tree.set(item_id, 'Action', action)
                
                # Tag items for easy identification
                if action == 'DELETE':
                    self.tree.item(item_id, tags=('delete',))
                else:
                    self.tree.item(item_id, tags=('keep',))
                
            total_items += 1
        
        # Add TV episodes
        for episode_title, versions in self.current_duplicates['shows'].items():
            parent = self.tree.insert('', 'end', text=episode_title, values=('TV Episode', '', '', '', '', ''))
            
            for i, version in enumerate(versions):
                size_gb = version['size'] / (1024**3) if version['size'] > 0 else 0
                
                # Determine action based on strategy
                if self.auto_select_var.get():
                    if self.deletion_strategy_var.get() == "keep_largest":
                        # Keep the largest (first in sorted list), delete others
                        action = 'KEEP' if i == 0 else 'DELETE'
                    else:  # keep_smallest
                        # Keep the smallest (last in sorted list), delete others
                        action = 'KEEP' if i == len(versions) - 1 else 'DELETE'
                    
                    if action == 'DELETE':
                        total_space_saveable += version['size']
                else:
                    action = 'KEEP'
                
                # Format file path for display
                file_path = version['file']
                display_path = file_path[-50:] if len(file_path) > 50 else file_path
                
                values = (
                    'TV Episode',
                    version['resolution'],
                    version['codec'],
                    f"{size_gb:.2f} GB" if size_gb > 0 else "Unknown",
                    display_path,
                    action
                )
                
                item_id = self.tree.insert(parent, 'end', text=f"Version {i+1}", values=values)
                self.tree.set(item_id, 'Action', action)
                
                # Tag items
                if action == 'DELETE':
                    self.tree.item(item_id, tags=('delete',))
                else:
                    self.tree.item(item_id, tags=('keep',))
                
            total_items += 1
        
        # Configure tag colors
        self.tree.tag_configure('delete', background='#ffcccc')
        self.tree.tag_configure('keep', background='#ccffcc')
        
        # Update status
        space_gb = total_space_saveable / (1024**3) if total_space_saveable > 0 else 0
        status_msg = f"Found {total_items} items with duplicates. Potential space savings: {space_gb:.2f} GB"
        if total_items > 0:
            status_msg += " | Type in filter boxes to search"
        self.update_status(status_msg)
        
        # Enable buttons
        self.connect_btn.config(state='normal')
        self.refresh_btn.config(state='normal')
        if total_items > 0:
            self.process_btn.config(state='normal')
    
    def on_item_select(self, event):
        """Handle item selection in the tree"""
        selection = self.tree.selection()
        if selection and self.console_window and self.console_window.winfo_exists():
            item = selection[0]
            item_text = self.tree.item(item)['text']
            values = self.tree.item(item)['values']
            if values:  # Only log for actual media items, not parent folders
                media_type = values[0]
                if media_type in ['Movie', 'TV Episode']:
                    path = values[4]
                    action = values[5]
                    self.log_message(f"Selected: {item_text} - Action: {action}", "INFO")
                    if path and path != '':
                        self.log_message(f"  Full path: {path}", "INFO")
    
    def on_item_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        parent = self.tree.parent(item)
        
        # Only allow action changes on version items, not parent items
        if parent:
            current_action = self.tree.set(item, 'Action')
            new_action = 'KEEP' if current_action == 'DELETE' else 'DELETE'
            self.tree.set(item, 'Action', new_action)
            
            # Log the change
            item_text = self.tree.item(item)['text']
            parent_text = self.tree.item(parent)['text']
            self.log_message(f"Action changed: {parent_text} - {item_text} -> {new_action}", "INFO")
            
            # Update tags
            if new_action == 'DELETE':
                self.tree.item(item, tags=('delete',))
            else:
                self.tree.item(item, tags=('keep',))
            
            # Ensure at least one version is kept
            self._validate_selections(parent)
    
    def _validate_selections(self, parent):
        # Ensure at least one child is marked as KEEP
        children = self.tree.get_children(parent)
        keep_count = sum(1 for child in children if self.tree.set(child, 'Action') == 'KEEP')
        
        if keep_count == 0 and children:
            # Force the first child to KEEP
            first_child = children[0]
            self.tree.set(first_child, 'Action', 'KEEP')
            self.tree.item(first_child, tags=('keep',))
    
    def process_deletions(self):
        # Log deletion request
        self.log_message("=" * 60, "INFO")
        self.log_message("User clicked 'Process Selected Deletions'", "INFO")
        
        # Collect all items marked for deletion
        items_to_delete = []
        
        for parent in self.tree.get_children():
            parent_text = self.tree.item(parent)['text']
            media_type = self.tree.set(parent, 'Type')
            
            for child in self.tree.get_children(parent):
                if self.tree.set(child, 'Action') == 'DELETE':
                    child_text = self.tree.item(child)['text']
                    size = self.tree.set(child, 'Size')
                    
                    # Get the actual media object
                    version_index = int(child_text.split()[-1]) - 1
                    
                    if media_type == 'Movie':
                        media_info = self.current_duplicates['movies'][parent_text][version_index]
                    else:
                        media_info = self.current_duplicates['shows'][parent_text][version_index]
                    
                    items_to_delete.append({
                        'title': parent_text,
                        'version': child_text,
                        'file_path': media_info['file'],
                        'size': size,
                        'media_obj': media_info['media_obj'],
                        'plex_item': media_info.get('movie_obj') or media_info.get('episode_obj')
                    })
        
        if not items_to_delete:
            messagebox.showinfo("No Items Selected", "No items are marked for deletion.")
            self.log_message("No items marked for deletion", "INFO")
            return
        
        # Calculate total size
        total_size = 0
        for item in items_to_delete:
            try:
                size_str = item['size'].replace(' GB', '')
                if size_str != 'Unknown':
                    total_size += float(size_str)
            except:
                pass
        
        self.log_message(f"Items marked for deletion: {len(items_to_delete)}", "INFO")
        self.log_message(f"Total space to be freed: {total_size:.2f} GB", "INFO")
        self.log_message(f"Dry run mode: {'ENABLED' if self.dry_run_var.get() else 'DISABLED'}", 
                        "INFO" if self.dry_run_var.get() else "WARNING")
        
        if self.dry_run_var.get():
            message = f"DRY RUN MODE\n\nWould delete {len(items_to_delete)} file(s)\nTotal space that would be freed: {total_size:.2f} GB\n\nNo files will actually be deleted."
            messagebox.showinfo("Dry Run Results", message)
            self.log_message("Dry run completed - no files were deleted", "INFO")
            return
        
        message = f"Are you sure you want to delete {len(items_to_delete)} duplicate(s)?\n\n"
        message += f"Total space to be freed: {total_size:.2f} GB\n\n"
        message += "⚠️ WARNING: Check your file locations!\n"
        message += "• Local drives: Files go to Recycle Bin\n"
        message += "• Network drives: Files are PERMANENTLY deleted!\n\n"
        message += "This action cannot be undone through PlexDeDupe!"
        
        if messagebox.askyesno("Confirm Deletion", message, icon='warning'):
            self.log_message("User confirmed deletion - proceeding", "WARNING")
            self._perform_deletions(items_to_delete)
        else:
            self.log_message("User cancelled deletion", "INFO")
    
    def _perform_hardlinks(self, items_to_convert):
        """Convert duplicates to hardlinks instead of deleting"""
        success_count = 0
        skip_count = 0
        error_count = 0
        errors = []
        
        self.log_message(f"Starting hardlink conversion for {len(items_to_convert)} items", "INFO")
        
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Converting to Hardlinks")
        progress_window.geometry("600x300")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        progress_label = ttk.Label(progress_window, text="Converting duplicates to hardlinks...")
        progress_label.pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=len(items_to_convert))
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_text = scrolledtext.ScrolledText(progress_window, height=10, width=70)
        status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for i, item in enumerate(items_to_convert):
            try:
                # Update progress
                progress_var.set(i)
                status_text.insert(tk.END, f"Processing: {item['title']} - {item['version']}\n")
                status_text.see(tk.END)
                progress_window.update()
                
                self.log_message(f"Processing hardlink: {item['title']} - {item['version']}", "INFO")
                
                source_file = item['keep_file']
                target_file = item['file_path']
                
                if not source_file or source_file == 'Unknown' or target_file == 'Unknown':
                    status_text.insert(tk.END, f"  ✗ Skipped: Unknown file path\n")
                    self.log_message(f"  Skipped: Unknown file path", "WARNING")
                    skip_count += 1
                    continue
                
                self.log_message(f"  Source: {source_file}", "INFO")
                self.log_message(f"  Target: {target_file}", "INFO")
                
                # Check if files can be hardlinked
                can_link, reason = self.can_hardlink(source_file, target_file)
                
                if not can_link:
                    status_text.insert(tk.END, f"  ✗ Skipped: {reason}\n")
                    self.log_message(f"  Skipped: {reason}", "WARNING")
                    skip_count += 1
                    
                    # If on different drives, note it prominently
                    if "different drives" in reason:
                        status_text.insert(tk.END, f"    ⚠️ Files are on different drives - cannot hardlink\n")
                    continue
                
                # Delete from Plex first
                media_to_delete = item['media_obj']
                try:
                    media_to_delete.delete()
                    status_text.insert(tk.END, f"  ✓ Removed duplicate from Plex\n")
                    self.log_message(f"  Removed duplicate from Plex", "SUCCESS")
                except Exception as delete_error:
                    if "403" in str(delete_error):
                        raise Exception("'Allow media deletion' is not enabled in Plex settings.")
                    else:
                        raise delete_error
                
                # Create hardlink
                success, message = self.create_hardlink(source_file, target_file)
                
                if success:
                    success_count += 1
                    status_text.insert(tk.END, f"  ✓ Created hardlink successfully\n")
                    self.log_message(f"  Hardlink created successfully", "SUCCESS")
                    
                    # Verify space saved
                    try:
                        file_size = os.path.getsize(source_file)
                        size_gb = file_size / (1024**3)
                        status_text.insert(tk.END, f"    → Saved {size_gb:.2f} GB\n")
                    except:
                        pass
                else:
                    error_count += 1
                    status_text.insert(tk.END, f"  ✗ Failed: {message}\n")
                    self.log_message(f"  Failed: {message}", "ERROR")
                    errors.append(f"{item['title']}: {message}")
                
            except Exception as e:
                error_count += 1
                error_msg = f"Failed to process {item['title']}: {str(e)}"
                errors.append(error_msg)
                status_text.insert(tk.END, f"  ✗ Error: {str(e)}\n")
                self.log_message(f"  Error: {str(e)}", "ERROR")
            
            status_text.see(tk.END)
            progress_window.update()
        
        progress_var.set(len(items_to_convert))
        progress_window.destroy()
        
        # Log completion
        self.log_message(f"Hardlink conversion complete: {success_count} successful, {skip_count} skipped, {error_count} errors", 
                        "SUCCESS" if error_count == 0 else "WARNING")
        
        # Show results
        if error_count > 0 or skip_count > 0:
            result_msg = f"Hardlink conversion completed:\n\n"
            result_msg += f"Successfully converted: {success_count}\n"
            result_msg += f"Skipped (different drives, etc): {skip_count}\n"
            result_msg += f"Errors: {error_count}\n\n"
            
            if skip_count > 0:
                result_msg += "Note: Files on different drives cannot be hardlinked.\n\n"
            
            if errors:
                result_msg += "Errors:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    result_msg += f"\n... and {len(errors) - 5} more errors"
            
            messagebox.showwarning("Hardlink Conversion Completed", result_msg)
        else:
            result_msg = f"Successfully converted {success_count} duplicate(s) to hardlinks!\n\n"
            result_msg += "The same file now appears in multiple locations without using extra space."
            messagebox.showinfo("Success", result_msg)
        
        # Refresh the display
        self.connect_and_scan()
    
    def _perform_deletions(self, items_to_delete):
        success_count = 0
        error_count = 0
        errors = []
        files_deleted = 0
        
        # Ask user if they want to delete physical files too
        delete_files = messagebox.askyesno(
            "Delete Physical Files?",
            "Do you also want to delete the physical video files from disk?\n\n"
            "YES = Delete files from disk (permanent!)\n"
            "NO = Only remove from Plex (files remain on disk)",
            icon='warning'
        )
        
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Deleting Files")
        progress_window.geometry("500x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        progress_label = ttk.Label(progress_window, text="Processing deletions...")
        progress_label.pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=len(items_to_delete))
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_text = scrolledtext.ScrolledText(progress_window, height=6, width=60)
        status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for i, item in enumerate(items_to_delete):
            try:
                # Update progress
                progress_var.set(i)
                status_text.insert(tk.END, f"Processing: {item['title']} - {item['version']}\n")
                status_text.see(tk.END)
                progress_window.update()
                
                # Get file path before deleting from Plex
                file_path = item['file_path']
                
                # Delete from Plex
                media_to_delete = item['media_obj']
                try:
                    media_to_delete.delete()
                    success_count += 1
                    status_text.insert(tk.END, f"  ✓ Removed from Plex\n")
                    # Check if file path looks like a network path
                    if file_path.startswith('\\\\') or file_path.startswith('//') or ':' not in file_path[:2]:
                        status_text.insert(tk.END, f"    ⚠️ Network path - file permanently deleted\n")
                    else:
                        status_text.insert(tk.END, f"    ↻ Local file - moved to Recycle Bin\n")
                except Exception as delete_error:
                    if "403" in str(delete_error) or "Forbidden" in str(delete_error):
                        raise Exception("'Allow media deletion' is not enabled in Plex settings. Please enable it to use this tool.")
                    else:
                        raise delete_error
                
                # Delete physical file if requested
                if delete_files and file_path != 'Unknown':
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            files_deleted += 1
                            status_text.insert(tk.END, f"  ✓ Deleted file from disk\n")
                        else:
                            status_text.insert(tk.END, f"  ⚠ File not found on disk\n")
                    except Exception as e:
                        status_text.insert(tk.END, f"  ✗ Failed to delete file: {str(e)}\n")
                
            except Exception as e:
                error_count += 1
                error_msg = f"Failed to process {item['title']}: {str(e)}"
                errors.append(error_msg)
                status_text.insert(tk.END, f"  ✗ Error: {str(e)}\n")
            
            status_text.see(tk.END)
            progress_window.update()
        
        progress_var.set(len(items_to_delete))
        progress_window.destroy()
        
        # Log completion
        self.log_message(f"Deletion process complete: {success_count} successful, {error_count} errors", 
                        "SUCCESS" if error_count == 0 else "WARNING")
        
        # Show results
        if error_count > 0:
            result_msg = f"Deletion completed with errors:\n\n"
            result_msg += f"Plex entries removed: {success_count}\n"
            if delete_files:
                result_msg += f"Files deleted from disk: {files_deleted}\n"
            result_msg += f"Errors: {error_count}\n\n"
            result_msg += "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                result_msg += f"\n... and {len(errors) - 5} more errors"
            messagebox.showwarning("Deletion Completed", result_msg)
        else:
            result_msg = f"Successfully removed {success_count} entries from Plex!"
            if delete_files:
                result_msg += f"\nDeleted {files_deleted} files from disk."
            messagebox.showinfo("Success", result_msg)
        
        # Refresh the display
        self.connect_and_scan()

def main():
    print("[PlexDeDupe] Starting PlexDeDupe...")
    print(f"[PlexDeDupe] Python version: {sys.version}")
    print(f"[PlexDeDupe] Current time: {datetime.datetime.now()}")
    
    root = tk.Tk()
    app = PlexDuplicateManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()