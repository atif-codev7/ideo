import customtkinter as ctk
from database.repository import Repository

class HistoryTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Switch History & Audit Log",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left")

        self.clear_btn = ctk.CTkButton(
            self.header_frame,
            text="Clear Logs",
            width=80,
            height=28,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.handle_clear_logs
        )
        self.clear_btn.pack(side="right", padx=(5, 0))

        self.refresh_btn = ctk.CTkButton(
            self.header_frame,
            text="Refresh",
            width=80,
            height=28,
            command=self.refresh
        )
        self.refresh_btn.pack(side="right")

        # Scrollable Logs Area
        self.logs_scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.logs_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.refresh()

    def refresh(self):
        for widget in self.logs_scroll.winfo_children():
            widget.destroy()

        logs = Repository.get_recent_logs(limit=40)
        if not logs:
            empty_lbl = ctk.CTkLabel(
                self.logs_scroll,
                text="No switch events recorded yet.",
                text_color="gray",
                font=ctk.CTkFont(size=13)
            )
            empty_lbl.pack(pady=40)
            return

        for entry in logs:
            row = ctk.CTkFrame(self.logs_scroll, corner_radius=6)
            row.pack(fill="x", pady=3, padx=5)

            theme = entry.get("switched_to", "dark")
            icon = "🌙" if theme == "dark" else "☀️"
            source = entry.get("trigger_source", "manual").replace("_", " ").title()
            duration = entry.get("execution_duration_ms", 0.0)
            ts = entry.get("timestamp", "")
            status = entry.get("status", "SUCCESS")

            status_color = "#10b981" if status == "SUCCESS" else "#ef4444"

            left_text = f"{icon} Switched to {theme.upper()}  •  Source: {source} ({duration}ms)"
            left_lbl = ctk.CTkLabel(row, text=left_text, font=ctk.CTkFont(size=12))
            left_lbl.pack(side="left", padx=10, pady=6)

            right_text = f"{status}  |  {ts}"
            right_lbl = ctk.CTkLabel(row, text=right_text, font=ctk.CTkFont(size=11), text_color=status_color)
            right_lbl.pack(side="right", padx=10, pady=6)

    def handle_clear_logs(self):
        Repository.clear_logs()
        self.refresh()
