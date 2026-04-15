# PyCNCSync

A cross-platform application for syncing CNC files between a local folder and Google Drive. Supports both client and server modes with automatic file synchronization.

## Features

- **Dual Mode Operation**
  - **Client Mode**: Push local files to Google Drive, sync on changes
  - **Server Mode**: Pull entire CNC folder from Google Drive every 15 seconds
  
- **Cross-Platform**: Runs on Windows and macOS
- **System Tray Integration**: Minimalist UI with tray icon
- **Google Drive Integration**: OAuth authentication, secure credential handling
- **Auto-Updates**: Downloads latest rclone binary automatically
- **Professional Installers**: Native installers for both platforms

## Downloads

### Latest Release (Auto-Built)

**Get the latest stable build from GitHub Actions:**

í´— **[View Latest Builds](https://github.com/YOUR-USERNAME/PyCNCSync/actions)**

Or download directly:

#### Windows
- **Installer**: [PyCNCSync-Installer.exe](https://github.com/YOUR-USERNAME/PyCNCSync/actions)
  - Standard Windows installer with uninstall support
  - Installs to Program Files with Start Menu shortcuts

#### macOS
- **DMG Installer**: [PyCNCSync.dmg](https://github.com/YOUR-USERNAME/PyCNCSync/actions)
  - Disk image installer
  - Drag app to Applications folder to install

**To download:**
1. Go to [GitHub Actions](https://github.com/YOUR-USERNAME/PyCNCSync/actions)
2. Click the latest workflow run (green checkmark)
3. Scroll to **Artifacts** section
4. Download `PyCNCSync-windows-installer` or `PyCNCSync-macos-installer`

## Installation

### Windows
1. Download `PyCNCSync-Installer.exe`
2. Run the installer
3. Follow the setup wizard
4. Find PyCNCSync in Start Menu or Program Files

### macOS
1. Download `PyCNCSync.dmg`
2. Double-click to mount the disk image
3. Drag `PyCNCSync.app` to Applications folder
4. Launch from Applications

## Setup

1. **First Launch**
   - Red circle icon = Starting up
   - App will open Settings window
   - Select "Client" or "Server" mode
   - Choose local folder to sync

2. **Google Drive Authentication**
   - Click "Google Login" in tray menu
   - Browser opens for OAuth login
   - App stores secure token (no password saved)

3. **Start Syncing**
   - **Client**: Local changes push to Drive automatically
   - **Server**: Pull from Drive every 15 seconds

## Modes Explained

### Client Mode
- **Use when**: You own the CNC files locally
- **Behavior**: Local folder â†’ Google Drive (one-way push)
- **Sync**: Automatic on file changes + force push on startup
- **Idle battery**: Minimal (event-driven, no polling)

### Server Mode
- **Use when**: Files are managed on Google Drive
- **Behavior**: Google Drive â†’ Local folder (one-way pull)
- **Sync**: Every 15 seconds (polling)
- **No file watcher**: Reduces overhead on server machines

## Configuration

Settings are stored in `config.json`:
```json
{
  "username": "YourGoogleFirstName",
  "local_folder": "/path/to/sync",
  "mode": "client"
}
```

Edit anytime by clicking **Settings** in tray menu.

## Troubleshooting

**"rclone not found"**
- App auto-downloads rclone on first launch
- Check file permissions in the app directory

**"Google login failed"**
- Try clicking "Google Login" again
- Check internet connection
- Clear rclone config: Delete `rclone.conf`

**Files not syncing**
- Client mode: Watch local folder, ensure it has permissions
- Server mode: Check polling every 15 seconds in logs

## Requirements

- Python 3.11+ (if building from source)
- Internet connection for Google Drive
- ~50MB disk space

## Building from Source

```bash
# Clone the repo
git clone https://github.com/YOUR-USERNAME/PyCNCSync.git
cd PyCNCSync

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Build installer
pyinstaller app.spec
```

## Technical Details

- **Framework**: Python 3.11, Tkinter, Watchdog
- **Sync Backend**: rclone (auto-downloaded)
- **Authentication**: Google OAuth via rclone
- **UI**: System tray with native menus
- **Icons**: Custom startup/idle/uploading/error states

## License

MIT

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check existing issues for solutions

---

**Auto-built from GitHub Actions on every push to `main` branch**
