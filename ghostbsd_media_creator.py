import os
import platform
import subprocess
import shutil
import logging
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class GhostBSDMediaCreator(Gtk.Window):
    def __init__(self):
        super().__init__(title="GhostBSD Media Creator")
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)

        # Configure logging
        logging.basicConfig(filename='/var/log/ghostbsd_media_creator.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Application started")

        # Ensure the application is run as root
        if os.geteuid() != 0:
            self.show_error("Permission Denied", "This application must be run as root. Please re-run with sudo or as root.")
            logging.error("Application not run as root")
            exit(1)

        # Check dependencies
        missing_tools = self.check_dependencies()
        if missing_tools:
            install_suggestions = "\n".join([self.suggest_dependency_installation(tool) for tool in missing_tools])
            self.show_error("Missing Dependencies", f"The following tools are missing: {', '.join(missing_tools)}.\n{install_suggestions}")
            logging.error(f"Missing dependencies: {', '.join(missing_tools)}")
            exit(1)

        # Create a vertical box layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Label for desktop choice
        self.desktop_label = Gtk.Label(label="Choose GhostBSD Desktop:")
        vbox.pack_start(self.desktop_label, True, True, 0)

        # Checkboxes for desktop choice
        self.mate_checkbox = Gtk.CheckButton(label="MATE")
        self.mate_checkbox.connect("toggled", self.on_checkbox_toggled, "MATE")
        vbox.pack_start(self.mate_checkbox, True, True, 0)

        self.xfce_checkbox = Gtk.CheckButton(label="XFCE")
        self.xfce_checkbox.connect("toggled", self.on_checkbox_toggled, "XFCE")
        vbox.pack_start(self.xfce_checkbox, True, True, 0)

        # Button to proceed
        self.proceed_button = Gtk.Button(label="Next")
        self.proceed_button.connect("clicked", self.on_proceed_clicked)
        vbox.pack_start(self.proceed_button, True, True, 0)

        self.media_label = Gtk.Label(label="")
        self.media_combo = Gtk.ComboBoxText()
        self.install_button = Gtk.Button(label="Install")

        self.selected_desktop = None

    def on_checkbox_toggled(self, checkbox, desktop):
        if checkbox.get_active():
            self.selected_desktop = desktop
            if desktop == "MATE":
                self.xfce_checkbox.set_active(False)
            elif desktop == "XFCE":
                self.mate_checkbox.set_active(False)
        else:
            if self.selected_desktop == desktop:
                self.selected_desktop = None

    def check_dependencies(self):
        required_tools = ["wget", "dd", "umount"]
        os_name = platform.system()
        if os_name == "Linux":
            required_tools.append("lsblk")
        elif os_name in ["FreeBSD", "GhostBSD"]:
            required_tools.append("geom")
        elif os_name == "Darwin":
            required_tools.append("diskutil")

        missing_tools = []
        for tool in required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
        return missing_tools

    def suggest_dependency_installation(self, tool):
        os_name = platform.system()
        if os_name == "Linux":
            return f"Install {tool} using your package manager (e.g., `sudo apt install {tool}` or `sudo yum install {tool}`)."
        elif os_name in ["FreeBSD", "GhostBSD"]:
            return f"Install {tool} using `pkg install {tool}`."
        elif os_name == "Darwin":
            return f"Install {tool} using Homebrew (`brew install {tool}`)."
        return "Unknown platform. Please install the required tool manually."

    def on_proceed_clicked(self, widget):
        if not self.selected_desktop:
            self.show_error("No Desktop Selected", "Please select a desktop environment to proceed.")
            logging.warning("No desktop selected")
            return

        self.desktop_label.set_text(f"You chose {self.selected_desktop} desktop.")
        try:
            self.list_media_devices()
        except Exception as e:
            self.show_error("Failed to list media devices", str(e))
            logging.error(f"Error listing media devices: {e}")

    def list_media_devices(self):
        os_name = platform.system()
        devices = []

        try:
            if os_name == "Linux":
                result = subprocess.run(["lsblk", "-nd", "-o", "NAME"], stdout=subprocess.PIPE, text=True, check=True)
                devices = result.stdout.strip().split("\n")
            elif os_name == "FreeBSD" or os_name == "GhostBSD":
                result = subprocess.run(["geom", "disk", "list"], stdout=subprocess.PIPE, text=True, check=True)
                devices = [line.split()[1] for line in result.stdout.splitlines() if line.startswith("Geom name:")]
            elif os_name == "Darwin":  # macOS
                result = subprocess.run(["diskutil", "list"], stdout=subprocess.PIPE, text=True, check=True)
                devices = [line.split()[0] for line in result.stdout.splitlines() if line.startswith("/dev/disk")]
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error listing media devices: {e}")

        # Update UI
        self.media_label.set_text("Choose target media:")
        for device in devices:
            self.media_combo.append_text(device)
        self.media_combo.set_active(0)

        self.install_button.connect("clicked", self.on_install_clicked)

        # Add new UI elements
        self.add(self.media_label)
        self.add(self.media_combo)
        self.add(self.install_button)
        self.show_all()

    def on_install_clicked(self, widget):
        target_media = self.media_combo.get_active_text()

        if not target_media:
            self.show_error("No Media Selected", "Please select a target media to proceed.")
            logging.warning("No target media selected")
            return

        if self.selected_desktop == "MATE":
            iso_url = "https://download.ghostbsd.org/releases/amd64/24.10.1/GhostBSD-24.10.1.iso"
        elif self.selected_desktop == "XFCE":
            iso_url = "https://download.ghostbsd.org/releases/amd64/24.10.1/GhostBSD-24.10.1-XFCE.iso"
        iso_file = f"/tmp/ghostbsd-{self.selected_desktop.lower()}.iso"

        try:
            # Unmount media
            subprocess.run(["umount", f"/dev/{target_media}"], stderr=subprocess.DEVNULL, check=True)
            logging.info(f"Unmounted {target_media}")

            # Wipe media
            subprocess.run(["dd", "if=/dev/zero", f"of=/dev/{target_media}", "bs=1M", "count=1"], stderr=subprocess.DEVNULL, check=True)
            logging.info(f"Wiped {target_media}")

            # Fetch ISO
            subprocess.run(["wget", "-O", iso_file, iso_url], check=True)
            logging.info(f"Downloaded ISO from {iso_url} to {iso_file}")

            # Burn ISO
            subprocess.run(["dd", f"if={iso_file}", f"of=/dev/{target_media}", "bs=4M", "status=progress"], check=True)
            logging.info(f"Burned ISO to {target_media}")

            # Notify user
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Installation complete!")
            dialog.format_secondary_text(f"GhostBSD {self.selected_desktop} has been installed on {target_media}.")
            dialog.run()
            dialog.destroy()

        except subprocess.CalledProcessError as e:
            self.show_error("Installation Error", f"An error occurred: {e}")
            logging.error(f"Installation error: {e}")
        except Exception as e:
            self.show_error("Unexpected Error", str(e))
            logging.error(f"Unexpected error: {e}")

    def show_error(self, title, message):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, title)
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

# Run the application
if __name__ == "__main__":
    app = GhostBSDMediaCreator()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
