import os
import sys
import threading
from tkinter import messagebox, ttk

import customtkinter as ctk

from JV_plotter_GUI.Main_frame import IVProcessingMainClass
from JV_plotter_GUI.settings import settings
from core.version import __version__
from core.updater import check_for_updates, download_and_install_update


def resource_path(relative: str) -> str:
    """Return the absolute path to a bundled resource.

    Works both when running from source and when frozen by PyInstaller
    (sys._MEIPASS points to the temp extraction directory).
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


class JVProcessorMAIN(ctk.CTk):
    screen_width, screen_height = settings['GUI_main']['screen_width'], settings['GUI_main']['screen_height']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s = ttk.Style()
        self.s.configure('Treeview', rowheight=30)
        self.title("JV processor")
        self.geometry(f"{self.screen_width}x{self.screen_height}")
        self.minsize(700, 600)
        self.resizable(True, True)
        self.main_frame = IVProcessingMainClass(parent=self)

        # Set window icon (title bar + taskbar)
        icon_path = resource_path(os.path.join("Media", "GUI", "icon.ico"))
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # Check for updates 3 seconds after startup (non-blocking)
        self.after(3000, self._schedule_update_check)

    def _schedule_update_check(self) -> None:
        """Launch the update check in a background thread so the UI never blocks."""
        threading.Thread(target=self._do_update_check, daemon=True).start()

    def _do_update_check(self) -> None:
        """
        Query GitHub for a newer release. If one exists, ask the user whether
        to download and install it. Runs on a background thread; all UI calls
        are dispatched back to the main thread via self.after().
        """
        available, new_v, url = check_for_updates(__version__)
        if available:
            self.after(0, lambda: self._prompt_update(new_v, url))

    def _prompt_update(self, new_v: str, url: str) -> None:
        """Show an update dialog and trigger the installer if the user agrees."""
        if messagebox.askyesno(
            "Update available",
            f"A new version of JV Processor is available:\n\n"
            f"  Current:  v{__version__}\n"
            f"  Latest:   v{new_v}\n\n"
            f"Download and install now?",
        ):
            download_and_install_update(url)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    jv_processor_app = JVProcessorMAIN()
    jv_processor_app.mainloop()
