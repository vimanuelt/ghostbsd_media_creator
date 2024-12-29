# Makefile for GhostBSD Media Creator

APP_NAME = ghostbsd_media_creator
MAIN_SCRIPT = ghostbsd_media_creator.py
LOG_DIR = /var/log
LOG_FILE = $(LOG_DIR)/$(APP_NAME).log

.PHONY: all install uninstall clean run check-deps

all: check-deps
	@echo "Run 'make run' to start the application."

install:
	@echo "Installing $(APP_NAME)..."
	@if [ $$EUID -ne 0 ]; then \
		echo "Please run as root for installation."; \
		exit 1; \
	fi
	@mkdir -p $(LOG_DIR)
	@touch $(LOG_FILE)
	@chmod 600 $(LOG_FILE)
	@echo "Log file created at $(LOG_FILE)."
	@echo "Installation completed."

uninstall:
	@echo "Uninstalling $(APP_NAME)..."
	@if [ $$EUID -ne 0 ]; then \
		echo "Please run as root for uninstallation."; \
		exit 1; \
	fi
	@rm -f $(LOG_FILE)
	@echo "Removed log file $(LOG_FILE)."
	@echo "Uninstallation completed."

clean:
	@echo "Cleaning temporary files..."
	@rm -f *.pyc *.pyo __pycache__/* || true
	@rm -rf __pycache__ || true
	@echo "Temporary files removed."

run:
	@echo "Running $(APP_NAME)..."
	@python3 $(MAIN_SCRIPT)

check-deps:
	@echo "Checking dependencies..."
	@command -v python3 > /dev/null || { echo "Error: python3 is not installed."; exit 1; }
	@command -v wget > /dev/null || { echo "Error: wget is not installed."; exit 1; }
	@command -v dd > /dev/null || { echo "Error: dd is not installed."; exit 1; }
	@command -v umount > /dev/null || { echo "Error: umount is not installed."; exit 1; }
	@os_name=`uname`; \
	if [ "$$os_name" = "Linux" ]; then \
		command -v lsblk > /dev/null || { echo "Error: lsblk is not installed."; exit 1; }; \
	elif [ "$$os_name" = "FreeBSD" ] || [ "$$os_name" = "GhostBSD" ]; then \
		command -v geom > /dev/null || { echo "Error: geom is not installed."; exit 1; }; \
	elif [ "$$os_name" = "Darwin" ]; then \
		command -v diskutil > /dev/null || { echo "Error: diskutil is not installed."; exit 1; }; \
	fi
	@echo "All dependencies are installed."
