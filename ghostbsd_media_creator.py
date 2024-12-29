import os
import platform
import subprocess
import shutil
import logging
import gi
import threading
import requests

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

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
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.vbox)

        # Add main content box for controls
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.vbox.pack_start(self.content_box, True, True, 0)

        # Label for desktop choice
        self.desktop_label = Gtk.Label(label="Choose GhostBSD Desktop:")
        self.content_box.pack_start(self.desktop_label, False, False, 0)

        # Checkboxes for desktop choice
        self.mate_checkbox = Gtk.CheckButton(label="MATE")
        self.mate_checkbox.connect("toggled", self.on_checkbox_toggled, "MATE")
        self.content_box.pack_start(self.mate_checkbox, False, False, 0)

        self.xfce_checkbox = Gtk.CheckButton(label="XFCE")
        self.xfce_checkbox.connect("toggled", self.on_checkbox_toggled, "XFCE")
        self.content_box.pack_start(self.xfce_checkbox, False, False, 0)

        # Button to proceed
        self.proceed_button = Gtk.Button(label="Next")
        self.proceed_button.connect("clicked", self.on_proceed_clicked)
        self.content_box.pack_start(self.proceed_button, False, False, 0)

        # Media devices
        self.media_label = Gtk.Label(label="")
        self.media_label.hide()  # Initially hidden
        self.content_box.pack_start(self.media_label, False, False, 0)

        self.device_checkboxes = []

        # Add Install button at the bottom
        self.install_button = Gtk.Button(label="Install")
        self.install_button.connect("clicked", self.on_install_clicked)
        self.install_button.set_sensitive(False)
        self.install_button.hide()  # Initially hidden
        self.vbox.pack_start(self.install_button, False, False, 0)

        # Add Status and Progress Bar at the bottom
        self.status_progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.vbox.pack_start(self.status_progress_box, False, False, 0)

        # Status label
        self.status_label = Gtk.Label(label="Status: Waiting for input...")
        self.status_progress_box.pack_start(self.status_label, False, False, 0)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.status_progress_box.pack_start(self.progress_bar, False, False, 0)
        self.progress_bar.hide()

        self.selected_desktop = None
        self.selected_device = None

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
            # Ensure the media label and device checkboxes are shown
            self.media_label.set_text("Choose target media:")
            self.media_label.show()
            for checkbox in self.device_checkboxes:
                checkbox.show()
            self.install_button.show()  # Show the install button only now

            # Hide the "Next" button after it is pressed
            self.proceed_button.hide()
        except Exception as e:
            self.show_error("Failed to list media devices", str(e))
            logging.error(f"Error listing media devices: {e}")

    def list_media_devices(self):
        os_name = platform.system()
        devices = []

        try:
            if os_name == "Linux":
                result = subprocess.run(["lsblk", "-nd", "-o", "NAME,SIZE,TYPE"], stdout=subprocess.PIPE, text=True, check=True)
                devices = [line for line in result.stdout.strip().split("\n") if "disk" in line]
            elif os_name in ["FreeBSD", "GhostBSD"]:
                result = subprocess.run(["geom", "disk", "list"], stdout=subprocess.PIPE, text=True, check=True)
                geom_output = result.stdout.splitlines()
                for i, line in enumerate(geom_output):
                    if line.startswith("Geom name:"):
                        name = line.split(":")[1].strip()
                        size = "Unknown"
                        descr = "Unknown"
                        for j in range(i + 1, len(geom_output)):
                            if geom_output[j].strip().startswith("Mediasize:"):
                                size = geom_output[j].split(":")[1].split("(")[1].split(")")[0]
                            if geom_output[j].strip().startswith("descr:"):
                                descr = geom_output[j].split(":")[1].strip()
                            if geom_output[j].strip() == "":
                                break
                        devices.append(f"{name} ({size}, {descr})")
            elif os_name == "Darwin":
                result = subprocess.run(["diskutil", "list"], stdout=subprocess.PIPE, text=True, check=True)
                devices = [
                    f"{line.split()[0]} ({' '.join(line.split()[1:])})"
                    for line in result.stdout.splitlines()
                    if line.startswith("/dev/disk")
                ]
            else:
                self.show_error("Unsupported OS", f"{os_name} is not supported for this operation.")
                return
        except subprocess.CalledProcessError as e:
            self.show_error("Device Detection Error", f"Error detecting devices: {e}")
            return

        # Clear existing checkboxes
        for checkbox in self.device_checkboxes:
            self.content_box.remove(checkbox)

        # Add new device checkboxes
        self.device_checkboxes = []
        for device in devices:
            checkbox = Gtk.CheckButton(label=device)
            checkbox.connect("toggled", self.on_device_toggled, device.split()[0])
            self.device_checkboxes.append(checkbox)
            self.content_box.pack_start(checkbox, False, False, 0)

    def on_device_toggled(self, checkbox, device):
        if checkbox.get_active():
            self.selected_device = device
            for cb in self.device_checkboxes:
                if cb.get_label().split()[0] != device:
                    cb.set_active(False)
            self.install_button.set_sensitive(True)
        else:
            if self.selected_device == device:
                self.selected_device = None
                self.install_button.set_sensitive(False)

    def on_install_clicked(self, widget):
        if not self.selected_device:
            self.show_error("No Media Selected", "Please select a target media to proceed.")
            return

        # Hide the Install button
        self.install_button.hide()

        # Start installation in a separate thread
        threading.Thread(target=self.perform_installation).start()

    def perform_installation(self):
        if self.selected_desktop == "MATE":
            iso_url = "https://download.ghostbsd.org/releases/amd64/24.10.1/GhostBSD-24.10.1.iso"
        elif self.selected_desktop == "XFCE":
            iso_url = "https://download.ghostbsd.org/releases/amd64/24.10.1/GhostBSD-24.10.1-XFCE.iso"
        iso_file = f"/tmp/ghostbsd-{self.selected_desktop.lower()}.iso"

        try:
            GLib.idle_add(self.progress_bar.show)
            GLib.idle_add(self.progress_bar.set_fraction, 0.0)
            GLib.idle_add(self.update_status, "Downloading GhostBSD ISO...")
            self.download_with_progress(iso_url, iso_file)
            GLib.idle_add(self.update_status, "Installation complete!")
            GLib.idle_add(self.progress_bar.hide)
        except Exception as e:
            GLib.idle_add(self.show_error, "Installation Error", str(e))

    def download_with_progress(self, url, file_path):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1 MB

        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    fraction = downloaded / total_size
                    GLib.idle_add(self.update_progress, fraction)

    def update_progress(self, fraction):
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"{int(fraction * 100)}%")
        self.progress_bar.show()

    def update_status(self, message):
        self.status_label.set_text(f"Status: {message}")

    def show_error(self, title, message):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, title)
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    app = GhostBSDMediaCreator()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

