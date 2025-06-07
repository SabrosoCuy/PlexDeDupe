PlexDeDupe
A user-friendly GUI tool for managing duplicate media files in Plex Media Server. Automatically identifies movies and TV episodes with multiple versions and helps you reclaim disk space by removing redundant copies.
⚠️ WARNING: Files on network drives are PERMANENTLY deleted (no Recycle Bin)!
🗑️ Local drives: Files go to Recycle Bin/Trash
⚠️ Requires: "Allow media deletion" enabled in Plex settings
🎯 Features

Smart Detection: Automatically finds all movies and TV episodes with multiple versions
Flexible Strategy: Choose to keep either the largest (best quality) or smallest (save space) versions
Visual Interface: Easy-to-use GUI with color-coded actions (green = keep, red = delete)
Column Filtering: Filter results by any column (title, type, resolution, etc.) to find specific items
Safe Operation: Dry-run mode shows what would be deleted without making changes
Space Calculation: Shows exactly how much disk space you'll save
Manual Override: Double-click any item to change its action
Token Security: Password-masked token field with show/hide option
Built-in Help: Detailed instructions for finding your Plex token
Debug Console: Optional debug window shows connection details and errors for troubleshooting
Hardlink Mode (Beta): Convert duplicates to hardlinks instead of deleting (saves space without removing files)

Show Image
Main window showing duplicate detection and filtering
Show Image
Optional debug console for troubleshooting
⚠️ Important: File Deletion Behavior
WARNING: Network drives do NOT have a Recycle Bin!
Local Drives (C:, D:, etc.):

Files are moved to Recycle Bin (Windows) or Trash (Mac/Linux)
You can restore files if needed
Space is freed after emptying Recycle Bin

Network Drives (NAS, mapped drives, SMB shares):

Files are PERMANENTLY DELETED
NO Recycle Bin protection
Cannot be recovered
Be EXTRA careful with network storage!

To enable media deletion:

Open Plex Web
Go to Settings → Settings → Library
Click "Show Advanced"
Enable "Allow media deletion"
Save changes

Requirements:

"Allow media deletion" MUST be enabled in Plex settings
Without this setting, PlexDeDupe will fail with a 403 error

To check this setting:

Open Plex Web
Go to Settings → Settings → Library
Click "Show Advanced"
Look for "Allow media deletion"
Make sure it's enabled

📋 Requirements

Python 3.6 or higher (Download Python)
Plex Media Server with "Allow media deletion" enabled (required!)
Plex authentication token
PlexAPI Python library (automatically installed on first run)

🚀 Installation

Clone this repository:
bashgit clone https://github.com/SabrosoCuy/PlexDeDupe.git
cd PlexDeDupe

Install required dependency:
bashpip install plexapi


💻 Usage

Run the application:
bashpython plexdedupe.py

Enter your Plex server URL (e.g., http://localhost:32400 or http://192.168.1.100:32400)
Enter your Plex token (click the ? button for detailed instructions)
Click "Connect & Scan" to find duplicates

If you get a 403 error later, you need to enable "Allow media deletion" in Plex


Review the results:

Items in green will be kept
Items in red will be deleted
Double-click any item to toggle its action
Use filters: Type in the filter boxes above results to search for specific items
Click "Clear Filters" to remove all filters


Choose your deletion strategy:

Keep largest (preserve quality)
Keep smallest (maximize space savings)


Optional: Enable debug console:

Check "Show debug console" to see detailed connection and processing information
Helpful for troubleshooting connection issues


Enable/disable dry run:

✅ Checked = Preview only (recommended for first use)
❌ Unchecked = Actually perform deletions


Advanced Options (Beta):

Hardlink Mode: Convert duplicates to hardlinks instead of deleting
Only works on same drive - files on different drives will be skipped
See Hardlink Mode section below for details


Click "Process Selected Deletions" to execute


⚠️ CHECK FIRST: Are your files on a network drive? They'll be permanently deleted!
Local drives: Files go to Recycle Bin/Trash (recoverable)
Network drives: Files are permanently deleted (NOT recoverable)

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

Recycle Bin Protection (local drives only): Files go to Recycle Bin/Trash on local drives
⚠️ Network Drive Warning: Files on network drives are PERMANENTLY deleted
Dry Run Mode: Enabled by default - preview what would be deleted without making changes
Visual Confirmation: Color-coded interface clearly shows what will be kept vs deleted
Multiple Confirmations: Must confirm before any deletions occur
Smart Protection: Ensures at least one version is always kept
Manual Override: Double-click to change any automatic selection

📊 Deletion Strategies

Keep Largest (Default): Preserves the highest quality version
Keep Smallest: Maximizes disk space savings

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.
📝 License
This project is licensed under the MIT License - see the LICENSE file for details.
⚠️ Disclaimer
This tool is not affiliated with Plex Inc. Use at your own risk.
Critical Warnings:

Network drives: Files are PERMANENTLY deleted (no Recycle Bin)
Local drives: Files go to Recycle Bin/Trash (can be recovered)
"Allow media deletion" MUST be enabled in Plex settings
Without this setting, the tool will fail with a 403 error

Always ensure you have backups of important media files before bulk deletion operations, especially on network drives.
❓ Frequently Asked Questions
Q: I'm getting a 403 error when trying to delete files
A: You need to enable "Allow media deletion" in Plex settings. Without this, PlexDeDupe cannot function.
Q: Will this permanently delete my files?
A:

Local drives: No! Files go to Recycle Bin/Trash
Network drives: YES! Files are permanently deleted immediately

Q: My media is on a NAS/network drive. Is it safe to use?
A: Be VERY careful! Network drives don't have a Recycle Bin. Files will be permanently deleted. Always use Dry Run first and have backups.
Q: How do I get my files back if I made a mistake?
A:

Local drives: Restore from Recycle Bin/Trash
Network drives: You can't - files are gone permanently (this is why backups are important)

Q: What if I want to free up space immediately?
A: After running PlexDeDupe on local drives, empty your Recycle Bin/Trash. For network drives, space is freed immediately.
Q: Can I preview what will be deleted?
A: Yes! Dry Run mode is enabled by default. It shows you exactly what would be deleted without actually doing anything.
Q: What is Hardlink Mode?
A: Instead of deleting duplicates, it converts them to hardlinks - multiple file paths pointing to the same data. This saves space without removing files. Only works on the same drive.
Q: Why are some files skipped in Hardlink Mode?
A: Hardlinks only work on the same drive. Files on different drives (like C: and D:) or network drives cannot be hardlinked and will be skipped.
Q: How do I find specific items in my results?
A: Use the filter boxes above the results table. Type any text to search - for example, type "4K" in Resolution to see only 4K files, or "movie" in Type to see only movies. Click "Clear Filters" to reset.
🐛 Known Issues

403 Forbidden Error: Enable "Allow media deletion" in Plex settings
Network drives: No Recycle Bin - files are permanently deleted
NAS/Network shares: Deletions are immediate and permanent
Very large libraries may take time to scan
Some NAS devices may have permission issues with deletion
Filtering: Parent items are shown if any child matches the filter

🔗 Hardlink Mode (Beta Feature)
Convert duplicates to hardlinks instead of deleting them!
What are hardlinks?
Hardlinks allow the same file to appear in multiple locations without using extra disk space. Instead of having two copies of a 50GB movie, you have one file that appears in both places.
Benefits:

Save disk space without losing files
Keep your folder organization intact
Both "copies" stay in sync (they're the same file)
Plex still sees both locations

Limitations:
⚠️ Important: Hardlinks have strict requirements:

Same Drive Only: Both files MUST be on the same drive/volume
No Network Drives: Does NOT work on network shares, NAS, or mapped drives
No Cross-Drive: Cannot hardlink between C: and D: drives
Identical Files: Files must have exactly the same content

How to use:

Enable "Convert to hardlinks instead of deleting" in Advanced Options
Select which version to keep (others will become hardlinks to it)
Files on different drives will be automatically skipped
Check the debug console to see which files were skipped and why

Example:
Before (using 100GB):
C:\Movies\Avatar.mkv (50GB)
C:\4K-Movies\Avatar.mkv (50GB)

After hardlinking (using 50GB):
C:\Movies\Avatar.mkv → (points to same file)
C:\4K-Movies\Avatar.mkv → (points to same file)
Both paths still exist and work, but they share the same disk space!
📞 Support
If you encounter issues:

403 Error? Enable "Allow media deletion" in Plex settings
Check that your Plex server is running
Verify your token is correct
Ensure you have proper permissions for file deletion
Enable Debug Console: Check "Show debug console" to see detailed connection info and errors

The debug console shows:

Connection attempts and errors
Detailed scan progress
File deletion details
Helpful error messages for troubleshooting

For bugs and feature requests, please open an issue.
🙏 Acknowledgments

Built with python-plexapi
Thanks to the Plex community for inspiration and feedback


✅ Key Points:

"Allow media deletion" MUST be enabled in Plex settings or the tool won't work
Local drives: Deleted files go to Recycle Bin/Trash (recoverable)
Network drives: Files are PERMANENTLY deleted (not recoverable)
Always use Dry Run mode first to preview changes