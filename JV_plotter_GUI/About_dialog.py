import threading
import webbrowser

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from core.version import __version__
from core.updater import check_for_updates, download_and_install_update

GITHUB_URL = "https://github.com/Rusya665/Solar_cells_measurements_plotting"


class AboutDialog(ctk.CTkToplevel):
    """
    Modal 'About' window showing app info, version, and a manual update check button.
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title("About JV Processor")
        self.geometry("460x420")
        self.resizable(False, False)
        self.grab_set()         # Make it modal
        self.focus_force()
        self.lift()

        self._build_ui()

    def _build_ui(self) -> None:
        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="JV Processor",
            font=("Roboto", 22, "bold"),
        ).pack(pady=(22, 2))

        ctk.CTkLabel(
            header,
            text="Solar cell JV curve analysis tool",
            font=("Roboto", 12),
            text_color="#888",
        ).pack(pady=(0, 18))

        # ── Version badge ─────────────────────────────────────────────────
        v_frame = ctk.CTkFrame(self, fg_color="transparent")
        v_frame.pack(pady=(18, 4))

        ctk.CTkLabel(v_frame, text="Version", font=("Roboto", 12), text_color="#888").pack(side="left", padx=6)
        ctk.CTkLabel(
            v_frame,
            text=f"v{__version__}",
            font=("Roboto", 13, "bold"),
            fg_color="#2a5298",
            corner_radius=6,
            padx=10,
            pady=2,
        ).pack(side="left")

        # ── Description ───────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=(
                "Analyses JV curves for photovoltaic applications.\n"
                "Supports Gamry, PalmSens4, SP-150e, SMU, and Keithley 2636.\n"
                "Calculates PCE, Jsc, Voc, FF, Rs, Rsh, and more."
            ),
            font=("Roboto", 12),
            text_color="#aaa",
            justify="center",
            wraplength=400,
        ).pack(pady=(10, 4))

        # ── GitHub link ───────────────────────────────────────────────────
        link = ctk.CTkLabel(
            self,
            text=GITHUB_URL,
            font=("Roboto", 11),
            text_color="#4a9eff",
            cursor="hand2",
        )
        link.pack(pady=(2, 16))
        link.bind("<Button-1>", lambda _: webbrowser.open(GITHUB_URL))

        # ── Separator ─────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color="#333").pack(fill="x", padx=30)

        # ── Credits ───────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=(
                "Release pipeline & icon assisted by AI:\n"
                "Gemini 1.5 Flash via Antigravity IDE  ·  Google Imagen"
            ),
            font=("Roboto", 10),
            text_color="#666",
            justify="center",
            wraplength=400,
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            self,
            text="Author: Rustem Nizamov  ·  MIT License",
            font=("Roboto", 10),
            text_color="#555",
        ).pack(pady=(0, 14))

        # ── Update button ─────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color="#333").pack(fill="x", padx=30)

        self.update_btn = ctk.CTkButton(
            self,
            text="Check for Updates",
            width=200,
            height=36,
            font=("Roboto", 13),
            command=self._check_updates,
        )
        self.update_btn.pack(pady=18)

    def _check_updates(self) -> None:
        """Run the update check in a background thread; show result in a dialog."""
        self.update_btn.configure(state="disabled", text="Checking…")
        threading.Thread(target=self._do_check, daemon=True).start()

    def _do_check(self) -> None:
        available, new_v, url = check_for_updates(__version__)
        self.after(0, lambda: self._show_result(available, new_v, url))

    def _show_result(self, available: bool, new_v, url) -> None:
        self.update_btn.configure(state="normal", text="Check for Updates")
        if available:
            msg = CTkMessagebox(
                title="Update available",
                message=(
                    f"A new version is available!\n\n"
                    f"Current:  v{__version__}\n"
                    f"Latest:    v{new_v}\n\n"
                    f"Download and install now?"
                ),
                icon="info",
                option_1="Install",
                option_2="Later",
            )
            if msg.get() == "Install":
                download_and_install_update(url)
        else:
            CTkMessagebox(
                title="Up to date",
                message=f"You are running the latest version (v{__version__}).",
                icon="check",
                option_1="OK",
            )
