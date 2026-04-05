"""ArcValet application entry point."""

from __future__ import annotations

import customtkinter as ctk

from arcvalet.database import init_db
from arcvalet.screens.dashboard import DashboardFrame
from arcvalet.screens.entry import EntryFrame
from arcvalet.screens.exit import ExitFrame
from arcvalet.screens.records import RecordsFrame


APP_TITLE = "ArcValet"
ACCENT_GREEN = "#1D9E75"


class ArcValetApp(ctk.CTk):
    """Single-window ArcValet app with frame-based navigation."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")

        self.title(APP_TITLE)
        self.geometry("1080x700")
        self.minsize(980, 640)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self.frames: dict[str, ctk.CTkFrame] = {}
        self._create_frames()
        self.show_screen("dashboard")

    def _create_frames(self) -> None:
        self.frames = {
            "dashboard": DashboardFrame(self.container, self),
            "entry": EntryFrame(self.container, self),
            "exit": ExitFrame(self.container, self),
            "records": RecordsFrame(self.container, self),
        }

    def show_screen(self, screen_name: str) -> None:
        for frame in self.frames.values():
            frame.pack_forget()

        selected = self.frames[screen_name]
        selected.pack(fill="both", expand=True)

        refresh_fn = getattr(selected, "refresh", None)
        if callable(refresh_fn):
            refresh_fn()


def run() -> None:
    init_db()
    app = ArcValetApp()
    app.mainloop()


if __name__ == "__main__":
    run()
