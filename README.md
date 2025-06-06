PlexDeDupe
A user-friendly GUI tool for managing duplicate media files in Plex Media Server. Automatically identifies movies and TV episodes with multiple versions and helps you reclaim disk space by removing redundant copies.
⚠️ WARNING: Files on network drives are PERMANENTLY deleted (no Recycle Bin)!
🗑️ Local drives: Files go to Recycle Bin/Trash
⚠️ Requires: "Allow media deletion" enabled in Plex settings
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

Python 3.6 or higher
Plex Media Server with "Allow media deletion" enabled (required!)
Plex authentication token
PlexAPI Python library

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


Choose your deletion strategy:

Keep largest (preserve quality)
Keep smallest (maximize space savings)


Enable/disable dry run:

✅ Checked = Preview only (recommended for first use)
❌ Unchecked = Actually perform deletions


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
🐛 Known Issues

403 Forbidden Error: Enable "Allow media deletion" in Plex settings
Network drives: No Recycle Bin - files are permanently deleted
NAS/Network shares: Deletions are immediate and permanent
Very large libraries may take time to scan
Some NAS devices may have permission issues with deletion

📞 Support
If you encounter issues:

403 Error? Enable "Allow media deletion" in Plex settings
Check that your Plex server is running
Verify your token is correct
Ensure you have proper permissions for file deletion

For bugs and feature requests, please open an issue.
🙏 Acknowledgments

Built with python-plexapi
Thanks to the Plex community for inspiration and feedback


✅ Key Points:

"Allow media deletion" MUST be enabled in Plex settings or the tool won't work
Local drives: Deleted files go to Recycle Bin/Trash (recoverable)
Network drives: Files are PERMANENTLY deleted (not recoverable)
Always use Dry Run mode first to preview changes