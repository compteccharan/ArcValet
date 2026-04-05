"""Dashboard screen for ArcValet."""

from __future__ import annotations

import customtkinter as ctk

from arcvalet.database import get_spot_overview, get_today_revenue


ACCENT_GREEN = "#1D9E75"


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, app: ctk.CTk) -> None:
        super().__init__(master)
        self.app = app

        title = ctk.CTkLabel(self, text="ArcValet", font=ctk.CTkFont(size=30, weight="bold"))
        title.pack(anchor="w", pady=(6, 14))

        subtitle = ctk.CTkLabel(
            self,
            text="Smart parking operations for premium public spaces",
            font=ctk.CTkFont(size=14),
            text_color="#A8B3BD",
        )
        subtitle.pack(anchor="w", pady=(0, 20))

        self.metrics_card = ctk.CTkFrame(self, corner_radius=14)
        self.metrics_card.pack(fill="x", pady=(0, 20))

        self.total_label = ctk.CTkLabel(self.metrics_card, text="Total Spots: 0", font=ctk.CTkFont(size=18, weight="bold"))
        self.total_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        self.occupied_label = ctk.CTkLabel(self.metrics_card, text="Occupied: 0", font=ctk.CTkFont(size=18, weight="bold"))
        self.occupied_label.grid(row=0, column=1, padx=20, pady=20, sticky="w")

        self.available_label = ctk.CTkLabel(self.metrics_card, text="Available: 0", font=ctk.CTkFont(size=18, weight="bold"))
        self.available_label.grid(row=0, column=2, padx=20, pady=20, sticky="w")

        self.revenue_label = ctk.CTkLabel(self.metrics_card, text="Today's Revenue: ₹0.00", font=ctk.CTkFont(size=18, weight="bold"))
        self.revenue_label.grid(row=0, column=3, padx=20, pady=20, sticky="w")

        for i in range(4):
            self.metrics_card.grid_columnconfigure(i, weight=1)

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x")

        ctk.CTkButton(
            button_row,
            text="Entry",
            fg_color=ACCENT_GREEN,
            hover_color="#167C5C",
            height=42,
            command=lambda: self.app.show_screen("entry"),
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            button_row,
            text="Exit",
            fg_color=ACCENT_GREEN,
            hover_color="#167C5C",
            height=42,
            command=lambda: self.app.show_screen("exit"),
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            button_row,
            text="Records",
            fg_color=ACCENT_GREEN,
            hover_color="#167C5C",
            height=42,
            command=lambda: self.app.show_screen("records"),
        ).pack(side="left", padx=(0, 12))

    def refresh(self) -> None:
        overview = get_spot_overview()
        revenue = get_today_revenue()

        self.total_label.configure(text=f"Total Spots: {overview['total']}")
        self.occupied_label.configure(text=f"Occupied: {overview['occupied']}")
        self.available_label.configure(text=f"Available: {overview['available']}")
        self.revenue_label.configure(text=f"Today's Revenue: ₹{revenue:.2f}")
