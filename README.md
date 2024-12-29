# GhostBSD Media Creator

**GhostBSD Media Creator** is a GTK3-based Python application for creating bootable USB drives with GhostBSD MATE or XFCE editions. This application automates the process of downloading the appropriate ISO, wiping the target media, and burning the ISO image using `dd`.

## Features
- Supports Linux, FreeBSD, GhostBSD, and macOS.
- Automatically detects available media devices.
- Downloads and burns the selected GhostBSD ISO.
- Detailed error handling and logging for easy troubleshooting.

## Prerequisites
This application requires the following tools to be installed on your system:
- `wget` (for downloading the ISO)
- `dd` (for burning the ISO)
- `umount` (for unmounting the target media)
- Platform-specific tools:
  - **Linux**: `lsblk`
  - **FreeBSD/GhostBSD**: `geom`
  - **macOS**: `diskutil`

### Installing Dependencies
- **Linux**: Use your package manager (e.g., `sudo apt install wget dd lsblk`).
- **FreeBSD/GhostBSD**: Use `pkg install wget dd geom`.
- **macOS**: Use Homebrew (`brew install wget` and ensure `dd` and `diskutil` are available).

## How to Use
1. **Run as Root**:
   Ensure the application is run with root privileges.
   ```bash
   sudo python3 ghostbsd_media_creator.py

2. **Select Desktop:**
        Choose between MATE and XFCE editions of GhostBSD.

3. **Select Target Media:**
        The application lists available media devices.
        Select the appropriate target device (e.g., /dev/sdb for Linux or /dev/da0 for FreeBSD).

4. **Burn ISO:**
        The application downloads the selected ISO and burns it to the target device.

## Logging

Logs are saved in /var/log/ghostbsd_media_creator.log. Use this file to troubleshoot any issues.
Error Handling

### The application detects and handles common issues such as:

    Missing dependencies: Provides platform-specific installation instructions.
    Incorrect permissions: Prompts the user to run the application as root.
    Target media errors: Ensures the media is unmounted and not in use before proceeding.

## Supported Platforms

    Linux
    FreeBSD
    GhostBSD
    macOS

## Development
### Requirements

    Python 3.x
    gi module for GTK3 (install via pip install PyGObject on Linux).

## Running the Application
```sh 
python3 ghostbsd_media_creator.py
```

## Future Improvements

    Add a graphical progress bar for operations.
    Support for resuming interrupted downloads.
    Allow specifying custom ISO URLs.

## License

This project is licensed under the BSD 3-Clause License.
