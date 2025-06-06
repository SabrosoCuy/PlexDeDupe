PlexDeDupe
A user-friendly GUI tool for managing duplicate media files in Plex Media Server. Automatically identifies movies and TV episodes with multiple versions and helps you reclaim disk space by removing redundant copies.

🗑️ Safety First: Deleted files go to your Recycle Bin/Trash, not permanently deleted!

Show Image
Show Image

🎯 Features
Smart Detection: Automatically finds all movies and TV episodes with multiple versions
Flexible Strategy: Choose to keep either the largest (best quality) or smallest (save space) versions
Visual Interface: Easy-to-use GUI with color-coded actions (green = keep, red = delete)
Safe Operation: Dry-run mode shows what would be deleted without making changes
Space Calculation: Shows exactly how much disk space you'll save
Manual Override: Double-click any item to change its action
Token Security: Password-masked token field with show/hide option
Built-in Help: Detailed instructions for finding your Plex token
⚠️ Important: File Deletion Behavior
Files are moved to the Recycle Bin/Trash, NOT permanently deleted!

File deletion behavior depends on your Plex server settings:

If "Allow media deletion" is ENABLED in Plex (Default):
Removes entry from Plex database
Moves physical files to Recycle Bin (Windows) or Trash (Mac/Linux)
Files can be restored from Recycle Bin if needed
Disk space is freed after emptying Recycle Bin
If "Allow media deletion" is DISABLED in Plex:
Only removes entry from Plex database
Physical files remain untouched on disk
No disk space is freed
To check this setting:

Open Plex Web
Go to Settings → Settings → Library
Click "Show Advanced"
Look for "Allow media deletion"
📋 Requirements
Python 3.6 or higher
Plex Media Server
Plex authentication token
PlexAPI Python library
🚀 Installation
Clone this repository:
bash
git clone https://github.com/yourusername/PlexDeDupe.git
cd PlexDeDupe
Install required dependency:
bash
pip install plexapi
💻 Usage
Run the application:
bash
python plexdedupe.py
Enter your Plex server URL (e.g., http://localhost:32400 or http://192.168.1.100:32400)
Enter your Plex token (click the ? button for detailed instructions)
Click "Connect & Scan" to find duplicates
Review the results:
Items in green will be kept
Items in red will be deleted
Double-click any item to toggle its action
Choose your deletion strategy:
Keep largest (preserve quality)
Keep smallest (maximize space savings)
Enable/disable dry run:
✅ Checked = Preview only (recommended for first use)
❌ Unchecked = Actually perform deletions
Click "Process Selected Deletions" to execute
Files will be moved to Recycle Bin/Trash (not permanently deleted)
You can restore them later if needed
🔑 Finding Your Plex Token
Click the ? button in the app for full instructions, or:

Method 1: Via Plex Web (Easiest)
Sign into Plex Web
Browse to any media item
Click the "..." (three dots) menu
Select "Get Info" → "View XML"
Look for X-Plex-Token= in the URL
Copy everything after the equals sign
Method 2: Via Preferences File
Windows: %LOCALAPPDATA%\Plex Media Server\Preferences.xml
macOS: ~/Library/Application Support/Plex Media Server/Preferences.xml
Linux: $PLEX_HOME/Library/Application Support/Plex Media Server/Preferences.xml
Look for PlexOnlineToken="YOUR_TOKEN_HERE"

🛡️ Safety Features
Recycle Bin Protection: Deleted files go to Recycle Bin/Trash, NOT permanently deleted
Dry Run Mode: Enabled by default - preview what would be deleted without making changes
Visual Confirmation: Color-coded interface clearly shows what will be kept vs deleted
Multiple Confirmations: Must confirm before any deletions occur
Smart Protection: Ensures at least one version is always kept
Manual Override: Double-click to change any automatic selection
Recovery Option: Files can be restored from Recycle Bin if you change your mind
📊 Deletion Strategies
Keep Largest (Default): Preserves the highest quality version
Keep Smallest: Maximizes disk space savings
🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

⚠️ Disclaimer
This tool is not affiliated with Plex Inc. Use at your own risk.

Important: When "Allow media deletion" is enabled in Plex, files are moved to the Recycle Bin/Trash, not permanently deleted. You can recover files from the Recycle Bin if needed. However, always ensure you have backups of important media files before bulk deletion operations.

❓ Frequently Asked Questions
Q: Will this permanently delete my files?
A: No! When Plex's "Allow media deletion" is enabled, files are moved to your system's Recycle Bin (Windows) or Trash (Mac/Linux). You can restore them if needed.

Q: How do I get my files back if I made a mistake?
A: Simply open your Recycle Bin/Trash and restore the files. They'll go back to their original location.

Q: What if I want to free up space immediately?
A: After running PlexDeDupe, you'll need to empty your Recycle Bin/Trash to permanently free up the disk space.

Q: Can I preview what will be deleted?
A: Yes! Dry Run mode is enabled by default. It shows you exactly what would be deleted without actually doing anything.

🐛 Known Issues
Network-mounted drives may have issues with file deletion
Very large libraries may take time to scan
Some NAS devices may not properly support file deletion
📞 Support
If you encounter issues:

Check that your Plex server is running
Verify your token is correct
Ensure you have proper permissions for file deletion
Check the Plex "Allow media deletion" setting
For bugs and feature requests, please open an issue.

🙏 Acknowledgments
Built with python-plexapi
Thanks to the Plex community for inspiration and feedback
✅ Remember: Deleted files go to your Recycle Bin/Trash, not permanently deleted! You can restore them if needed. The Recycle Bin acts as a safety net, giving you a chance to recover files if you change your mind.

