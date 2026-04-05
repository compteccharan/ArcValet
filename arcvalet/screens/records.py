"""Records screen for active and completed sessions."""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from arcvalet.database import TIME_FORMAT, get_all_sessions


ACCENT_GREEN = "#1D9E75"


def _format_duration(entry_time_text: str) -> tuple[float, str]:
    entry = datetime.strptime(entry_time_text, TIME_FORMAT)
    seconds = max((datetime.now() - entry).total_seconds(), 0)
    hours_float = seconds / 3600
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return hours_float, f"{hours}h {minutes}m"


class RecordsFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, app: ctk.CTk) -> None:
        super().__init__(master)
        self.app = app
        self.current_status = "active"

        title = ctk.CTkLabel(self, text="Session Records", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(anchor="w", pady=(6, 14))

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 12))

        self.toggle = ctk.CTkSegmentedButton(
            controls,
            values=["Active", "Completed"],
            selected_color=ACCENT_GREEN,
            selected_hover_color="#167C5C",
            command=self._toggle_status,
        )
        self.toggle.set("Active")
        self.toggle.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            controls,
            text="Refresh",
            fg_color=ACCENT_GREEN,
            hover_color="#167C5C",
            command=self.refresh,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            controls,
            text="Back to Dashboard",
            fg_color="#2E3440",
            hover_color="#3B4252",
            command=lambda: self.app.show_screen("dashboard"),
        ).pack(side="left")

        self.table = ctk.CTkScrollableFrame(self, corner_radius=14)
        self.table.pack(fill="both", expand=True)

        self.empty_label = ctk.CTkLabel(self, text="")
        self.empty_label.pack(anchor="w", pady=(8, 0))

    def _toggle_status(self, selected: str) -> None:
        self.current_status = "active" if selected == "Active" else "completed"
        self.refresh()

    def refresh(self) -> None:
        rows = get_all_sessions(self.current_status)

        for widget in self.table.winfo_children():
            widget.destroy()

        if self.current_status == "active":
            headers = ["Plate", "Vehicle", "Spot", "Entry Time", "Duration", "Running Bill"]
        else:
            headers = ["Plate", "Vehicle", "Spot", "Entry Time", "Exit Time", "Total Amount"]

        for col, text in enumerate(headers):
            label = ctk.CTkLabel(self.table, text=text, font=ctk.CTkFont(weight="bold"), anchor="w")
            label.grid(row=0, column=col, sticky="ew", padx=10, pady=(6, 8))
            self.table.grid_columnconfigure(col, weight=1)

        if not rows:
            self.empty_label.configure(text=f"No {self.current_status} sessions found.", text_color="#A8B3BD")
            return

        self.empty_label.configure(text="")

        for row_index, record in enumerate(rows, start=1):
            if self.current_status == "active":
                running_hours, duration_text = _format_duration(record["entry_time"])
                running_bill = round(running_hours * float(record["hourly_rate"]), 2)
                values = [
                    record["plate_number"],
                    record["vehicle_type"],
                    f"#{record['spot_id']}",
                    record["entry_time"],
                    duration_text,
                    f"₹{running_bill:.2f}",
                ]
            else:
                values = [
                    record["plate_number"],
                    record["vehicle_type"],
                    f"#{record['spot_id']}",
                    record["entry_time"],
                    record["exit_time"] or "-",
                    f"₹{float(record['total_amount'] or 0):.2f}",
                ]

            for col, value in enumerate(values):
                ctk.CTkLabel(self.table, text=str(value), anchor="w").grid(
                    row=row_index,
                    column=col,
                    sticky="ew",
                    padx=10,
                    pady=6,
                )
