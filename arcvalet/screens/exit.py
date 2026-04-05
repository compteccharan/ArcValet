"""Exit screen for ending parking sessions and billing."""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from arcvalet.database import TIME_FORMAT, complete_session, get_active_session, normalize_plate


ACCENT_GREEN = "#1D9E75"


class ExitFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, app: ctk.CTk) -> None:
        super().__init__(master)
        self.app = app
        self.current_session: dict | None = None
        self.current_amount: float = 0.0

        title = ctk.CTkLabel(self, text="Vehicle Exit", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(anchor="w", pady=(6, 18))

        search_frame = ctk.CTkFrame(self, corner_radius=14)
        search_frame.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(search_frame, text="Plate Number", anchor="w").grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))
        self.plate_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter plate number")
        self.plate_entry.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 14))

        ctk.CTkButton(
            search_frame,
            text="Search Active Session",
            fg_color=ACCENT_GREEN,
            hover_color="#167C5C",
            command=self._search_session,
        ).grid(row=1, column=1, padx=20)

        search_frame.grid_columnconfigure(0, weight=1)

        self.summary_card = ctk.CTkFrame(self, corner_radius=14)
        self.summary_card.pack(fill="x", pady=(0, 16))

        self.summary_label = ctk.CTkLabel(
            self.summary_card,
            text="Search a plate number to see billing summary.",
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=14),
        )
        self.summary_label.pack(fill="x", padx=20, pady=20)

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(fill="x")

        self.confirm_button = ctk.CTkButton(
            action_row,
            text="Confirm Exit",
            fg_color=ACCENT_GREEN,
            hover_color="#167C5C",
            command=self._confirm_exit,
            state="disabled",
        )
        self.confirm_button.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            action_row,
            text="Back to Dashboard",
            fg_color="#2E3440",
            hover_color="#3B4252",
            command=lambda: self.app.show_screen("dashboard"),
        ).pack(side="left")

        self.feedback_label = ctk.CTkLabel(self, text="", justify="left")
        self.feedback_label.pack(anchor="w", pady=(12, 0))

    def refresh(self) -> None:
        self.current_session = None
        self.current_amount = 0.0
        self.confirm_button.configure(state="disabled")
        self.plate_entry.delete(0, "end")
        self.summary_label.configure(text="Search a plate number to see billing summary.")
        self.feedback_label.configure(text="")

    def _search_session(self) -> None:
        plate = normalize_plate(self.plate_entry.get())
        if not plate:
            self.feedback_label.configure(text="Please enter a valid plate number.", text_color="#FF6B6B")
            self.confirm_button.configure(state="disabled")
            return

        session = get_active_session(plate)
        if not session:
            self.current_session = None
            self.current_amount = 0.0
            self.summary_label.configure(text="No active session found for this plate.")
            self.feedback_label.configure(text="", text_color="#A8B3BD")
            self.confirm_button.configure(state="disabled")
            return

        entry_dt = datetime.strptime(session["entry_time"], TIME_FORMAT)
        now_dt = datetime.now()
        duration_seconds = max((now_dt - entry_dt).total_seconds(), 0)
        duration_hours = duration_seconds / 3600
        amount = round(duration_hours * float(session["hourly_rate"]), 2)

        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)

        self.current_session = session
        self.current_amount = amount
        self.confirm_button.configure(state="normal")
        self.feedback_label.configure(text="", text_color="#A8B3BD")

        self.summary_label.configure(
            text=(
                f"Plate: {session['plate_number']}\n"
                f"Spot ID: #{session['spot_id']} ({session['spot_type']})\n"
                f"Entry Time: {session['entry_time']}\n"
                f"Duration: {hours}h {minutes}m\n"
                f"Amount: ₹{amount:.2f}"
            )
        )

    def _confirm_exit(self) -> None:
        if not self.current_session:
            self.feedback_label.configure(text="Search and select an active session first.", text_color="#FF6B6B")
            return

        success = complete_session(
            int(self.current_session["session_id"]),
            int(self.current_session["spot_id"]),
            float(self.current_amount),
        )
        if not success:
            self.feedback_label.configure(text="Unable to complete session. Please refresh and retry.", text_color="#FF6B6B")
            return

        self.feedback_label.configure(text="Session completed successfully. Spot is now available.", text_color="#8CE99A")
        self.confirm_button.configure(state="disabled")
        self.current_session = None
