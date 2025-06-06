import sys
import subprocess
import importlib.util
import tkinter as tk
from tkinter import messagebox, ttk

# Check and install dependencies
def check_and_install_dependencies():
    """Check if required packages are installed and install them if needed."""
    # First check if plexapi is installed
    if importlib.util.find_spec('plexapi') is None:
        # Create a simple GUI prompt
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        result = messagebox.askyesno(
            "Missing Dependency",
            "PlexDeDupe requires the 'plexapi' package which is not installed.\n\n"
            "Would you like to install it automatically?\n\n"
            "This will run: pip install plexapi",
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
            
            label = tk.Label(install_window, text="Installing plexapi...\nThis may take a moment.", pady=20)
            label.pack()
            
            progress = ttk.Progressbar(install_window, mode='indeterminate')
            progress.pack(pady=10, padx=20, fill=tk.X)
            progress.start(10)
            
            install_window.update()
            
            try:
                # Install the package
                subprocess.check_call([sys.executable, "-m", "pip", "install", "plexapi"], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
                install_window.destroy()
                messagebox.showinfo("Success", "plexapi has been installed successfully!\n\nPlexDeDupe will now start.")
            except subprocess.CalledProcessError:
                install_window.destroy()
                messagebox.showerror(
                    "Installation Failed",
                    "Failed to install plexapi automatically.\n\n"
                    "Please install it manually by running:\n"
                    "pip install plexapi\n\n"
                    "in your command prompt or terminal."
                )
                sys.exit(1)
        else:
            messagebox.showinfo(
                "Installation Required",
                "PlexDeDupe requires plexapi to function.\n\n"
                "Please install it manually by running:\n"
                "pip install plexapi\n\n"
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

class PlexDuplicateManager:
    def __init__(self, root):
        self.root = root
        self.root.title("PlexDeDupe - Plex Duplicate Media Manager")
        self.root.geometry("900x700")
        
        self.plex = None
        self.current_duplicates = {'movies': {}, 'shows': {}}
        
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
        ttk.Checkbutton(options_frame, text="Dry run (preview what would be deleted without making any changes)", 
                        variable=self.dry_run_var).grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
        # Results Frame
        results_frame = ttk.LabelFrame(main_frame, text="Duplicate Media", padding="10")
        results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Create Treeview for results
        self.tree = ttk.Treeview(results_frame, columns=('Type', 'Resolution', 'Codec', 'Size', 'Path', 'Action'), 
                                 show='tree headings', height=15)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
        self.tree.column('Type', width=60)
        self.tree.column('Resolution', width=80)
        self.tree.column('Codec', width=60)
        self.tree.column('Size', width=80)
        self.tree.column('Path', width=200)
        self.tree.column('Action', width=100)
        
        # Scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=vsb.set)
        
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        self.tree.configure(xscrollcommand=hsb.set)
        
        # Bind double-click to toggle action
        self.tree.bind('<Double-1>', self.on_item_double_click)
        
        # Action Buttons Frame
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.process_btn = ttk.Button(action_frame, text="Process Selected Deletions", 
                                      command=self.process_deletions, state='disabled')
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_btn = ttk.Button(action_frame, text="Refresh", 
                                      command=self.connect_and_scan, state='disabled')
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status bar
        self.status_var = tk.StringVar(value="Not connected")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure grid weights for main_frame
        main_frame.rowconfigure(2, weight=1)
    
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
    
    def toggle_token_visibility(self):
        if self.show_token_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")
    
    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def connect_and_scan(self):
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
            self.plex = PlexServer(self.url_var.get(), self.token_var.get())
            self.update_status(f"Connected to: {self.plex.friendlyName}")
            
            # Find duplicates
            self.update_status("Scanning for duplicate media...")
            self.current_duplicates = self.find_duplicate_media()
            
            # Update UI in main thread
            self.root.after(0, self._populate_results)
            
        except Exception as e:
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
        for library in self.plex.library.sections():
            if library.type == 'movie':
                for movie in library.all():
                    if len(movie.media) > 1:
                        media_list = []
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
                                print(f"Error processing media for {movie.title}: {str(e)}")
                                
                        if media_list:
                            duplicates['movies'][movie.title] = sorted(media_list, key=lambda x: x['size'], reverse=True)
        
        # Check TV shows
        for library in self.plex.library.sections():
            if library.type == 'show':
                for show in library.all():
                    for episode in show.episodes():
                        if len(episode.media) > 1:
                            media_list = []
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
                                    print(f"Error processing media for {show.title} - {episode.title}: {str(e)}")
                                    
                            if media_list:
                                episode_key = f"{show.title} - S{episode.seasonNumber:02d}E{episode.episodeNumber:02d} - {episode.title}"
                                duplicates['shows'][episode_key] = sorted(media_list, key=lambda x: x['size'], reverse=True)
        
        return duplicates
    
    def _populate_results(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
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
        self.update_status(f"Found {total_items} items with duplicates. Potential space savings: {space_gb:.2f} GB")
        
        # Enable buttons
        self.connect_btn.config(state='normal')
        self.refresh_btn.config(state='normal')
        if total_items > 0:
            self.process_btn.config(state='normal')
    
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
        
        if self.dry_run_var.get():
            message = f"DRY RUN MODE\n\nWould delete {len(items_to_delete)} file(s)\nTotal space that would be freed: {total_size:.2f} GB\n\nNo files will actually be deleted."
            messagebox.showinfo("Dry Run Results", message)
            return
        
        message = f"Are you sure you want to delete {len(items_to_delete)} duplicate(s)?\n\n"
        message += f"Total space to be freed: {total_size:.2f} GB\n\n"
        message += "⚠️ WARNING: Check your file locations!\n"
        message += "• Local drives: Files go to Recycle Bin\n"
        message += "• Network drives: Files are PERMANENTLY deleted!\n\n"
        message += "This action cannot be undone through PlexDeDupe!"
        
        if messagebox.askyesno("Confirm Deletion", message, icon='warning'):
            self._perform_deletions(items_to_delete)
    
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
    root = tk.Tk()
    app = PlexDuplicateManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()