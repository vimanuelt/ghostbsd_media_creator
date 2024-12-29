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
