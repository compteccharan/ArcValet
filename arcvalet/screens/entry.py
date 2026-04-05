"""Entry screen for registering incoming vehicles."""

from __future__ import annotations

import re

import customtkinter as ctk

from arcvalet.database import create_session, get_active_session, get_available_spot, normalize_plate


ACCENT_GREEN = "#1D9E75"
PLATE_RE = re.compile(r"^[A-Z0-9-]{1,15}$")

PREFERENCE_MAP = {
    "Standard": "standard",
    "Quick Exit": "quick_exit",
    "Luxury": "luxury",
    "Bike Zone": "bike",
    "EV Charger": "ev",
}


class EntryFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, app: ctk.CTk) -> None:
        super().__init__(master)
        self.app = app

        title = ctk.CTkLabel(self, text="Vehicle Entry", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(anchor="w", pady=(6, 18))

        form = ctk.CTkFrame(self, corner_radius=14)
        form.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(form, text="Plate Number", anchor="w").grid(row=0, column=0, sticky="w", padx=20, pady=(18, 6))
        self.plate_entry = ctk.CTkEntry(form, placeholder_text="e.g. KA01AB1234")
        self.plate_entry.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))

        ctk.CTkLabel(form, text="Vehicle Type", anchor="w").grid(row=2, column=0, sticky="w", padx=20, pady=(4, 6))
        self.vehicle_combo = ctk.CTkComboBox(form, values=["Bike", "Car", "SUV", "EV", "Luxury"])
        self.vehicle_combo.set("Car")
        self.vehicle_combo.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 12))

        ctk.CTkLabel(form, text="Spot Preference", anchor="w").grid(row=4, column=0, sticky="w", padx=20, pady=(4, 6))
        self.preference_combo = ctk.CTkComboBox(
            form,
            values=["Standard", "Quick Exit", "Luxury", "Bike Zone", "EV Charger"],
        )
        self.preference_combo.set("Standard")
        self.preference_combo.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 16))

        form.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            self,
            text="Assign Spot",
            fg_color=ACCENT_GREEN,
            hover_color="#167C5C",
            height=42,
            command=self._handle_submit,
        ).pack(anchor="w", pady=(0, 12))

        self.message_label = ctk.CTkLabel(self, text="", justify="left")
        self.message_label.pack(anchor="w", pady=(0, 12))

        ctk.CTkButton(
            self,
            text="Back to Dashboard",
            fg_color="#2E3440",
            hover_color="#3B4252",
            height=38,
            command=lambda: self.app.show_screen("dashboard"),
        ).pack(anchor="w")

    def refresh(self) -> None:
        self.message_label.configure(text="")
        self.plate_entry.delete(0, "end")
        self.vehicle_combo.set("Car")
        self.preference_combo.set("Standard")

    def _handle_submit(self) -> None:
        raw_plate = self.plate_entry.get()
        plate = normalize_plate(raw_plate)
        vehicle_type = self.vehicle_combo.get()
        preference_label = self.preference_combo.get()
        spot_type = PREFERENCE_MAP.get(preference_label)

        if not plate or not PLATE_RE.match(plate):
            self.message_label.configure(text="Please enter a valid plate (letters, numbers, dash only).", text_color="#FF6B6B")
            return

        existing = get_active_session(plate)
        if existing:
            self.message_label.configure(
                text=f"Vehicle {plate} already has an active session at Spot #{existing['spot_id']}.",
                text_color="#FFB347",
            )
            return

        if not spot_type:
            self.message_label.configure(text="Please select a valid parking preference.", text_color="#FF6B6B")
            return

        spot = get_available_spot(spot_type)
        if not spot:
            self.message_label.configure(
                text=f"No available spots in {preference_label}. Try another preference.",
                text_color="#FFB347",
            )
            return

        try:
            session_id = create_session(plate, vehicle_type, int(spot["spot_id"]))
        except ValueError as exc:
            self.message_label.configure(text=str(exc), text_color="#FF6B6B")
            return

        self.message_label.configure(
            text=(
                f"Session #{session_id} created successfully.\n"
                f"Assigned Spot: #{spot['spot_id']} ({preference_label})\n"
                f"Rate: ₹{float(spot['hourly_rate']):.2f}/hr"
            ),
            text_color="#8CE99A",
        )
