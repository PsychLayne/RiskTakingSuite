#!/usr/bin/env python3
"""
Risk Tasks Client - Main Application
A unified client for managing 4 risk-taking tasks to study correlations
between different risk assessment paradigms.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Import core modules
from database.db_manager import DatabaseManager
from database.models import Participant, Session, TrialData
from ui.participant_manager import ParticipantManager
from ui.session_manager import SessionManager
from ui.settings_panel import SettingsPanel
from ui.data_viewer import DataViewer
from ui.experiment_builder import ExperimentBuilder
from utils.task_scheduler import TaskScheduler
from utils.backup_manager import BackupManager


class RiskTasksClient(ctk.CTk):
    """Main application window for the Risk Tasks Client."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Risk Tasks Client")
        self.geometry("1600x1000")
        self.minsize(1000, 700)

        # Initialize database
        self.db_manager = DatabaseManager()
        self.db_manager.initialize()

        # Initialize utilities
        self.task_scheduler = TaskScheduler()
        self.backup_manager = BackupManager(self.db_manager)

        # Load configuration
        self.load_config()

        # Setup UI
        self.setup_ui()

        # Schedule automatic backups
        self.schedule_backup()

    def load_config(self):
        """Load application configuration from JSON file."""
        config_path = Path("config/settings.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Create default configuration
            self.config = {
                "experiment": {
                    "total_trials_per_task": 30,
                    "session_gap_days": 14,
                    "max_session_duration": 60
                },
                "display": {
                    "fullscreen": True,
                    "resolution": "1920x1080"
                },
                "data": {
                    "auto_backup": True,
                    "backup_interval_hours": 24
                },
                "tasks": {
                    "bart": {
                        "max_pumps": 48,
                        "points_per_pump": 5,
                        "explosion_range": [8, 48],
                        "keyboard_input_mode": False,
                        "balloon_color": "Red",
                        "random_colors": False
                    },
                    "ice_fishing": {
                        "max_fish": 64,
                        "points_per_fish": 5,
                        "break_probability_function": "linear"
                    },
                    "mountain_mining": {
                        "max_ore": 64,
                        "points_per_ore": 5,
                        "snap_probability_function": "linear"
                    },
                    "spinning_bottle": {
                        "segments": 16,
                        "points_per_add": 5,
                        "spin_speed_range": [12.0, 18.0],
                        "win_color": "Green",
                        "loss_color": "Red"
                    }
                }
            }
            # Save default config
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)

    def setup_ui(self):
        """Setup the main user interface."""
        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Create sidebar
        self.create_sidebar()

        # Create main content area
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Create pages
        self.pages = {}
        self.create_pages()

        # Show dashboard by default
        self.show_page("dashboard")

    def create_sidebar(self):
        """Create the navigation sidebar."""
        self.sidebar = ctk.CTkFrame(self.main_container, width=200)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)

        # App title
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="Risk Tasks\nClient",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Navigation buttons
        nav_buttons = [
            ("Dashboard", "dashboard", "📊"),
            ("Experiments", "experiments", "🧪"),
            ("Participants", "participants", "👥"),
            ("Sessions", "sessions", "🎮"),
            ("Data Analysis", "data", "📈"),
            ("Settings", "settings", "⚙️")
        ]

        for text, page_name, icon in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon} {text}",
                command=lambda p=page_name: self.show_page(p),
                width=180,
                height=40
            )
            btn.pack(pady=5)

        # Exit button at bottom
        exit_btn = ctk.CTkButton(
            self.sidebar,
            text="🚪 Exit",
            command=self.on_closing,
            width=180,
            height=40,
            fg_color="darkred",
            hover_color="red"
        )
        exit_btn.pack(side="bottom", pady=20)

    def create_pages(self):
        """Create all application pages."""
        # Dashboard page
        self.pages["dashboard"] = self.create_dashboard_page()

        # Experiments page
        self.pages["experiments"] = ExperimentBuilder(
            self.content_frame,
            self.db_manager
        )

        # Participants page
        self.pages["participants"] = ParticipantManager(
            self.content_frame,
            self.db_manager
        )

        # Sessions page
        self.pages["sessions"] = SessionManager(
            self.content_frame,
            self.db_manager,
            self.task_scheduler
        )

        # Data analysis page
        self.pages["data"] = DataViewer(
            self.content_frame,
            self.db_manager
        )

        # Settings page
        self.pages["settings"] = SettingsPanel(
            self.content_frame,
            self.config,
            self.save_config
        )

    def create_dashboard_page(self):
        """Create the dashboard page."""
        dashboard = ctk.CTkFrame(self.content_frame)

        # Title
        title = ctk.CTkLabel(
            dashboard,
            text="Dashboard",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=20)

        # Statistics frame
        stats_frame = ctk.CTkFrame(dashboard)
        stats_frame.pack(fill="x", padx=20, pady=10)

        # Get statistics from database
        stats = self.db_manager.get_statistics()

        # Create stat cards
        stat_cards = [
            ("Total Participants", stats.get("total_participants", 0), "👥"),
            ("Active Sessions", stats.get("active_sessions", 0), "🎮"),
            ("Completed Sessions", stats.get("completed_sessions", 0), "✅"),
            ("Total Trials", stats.get("total_trials", 0), "📊")
        ]

        for i, (label, value, icon) in enumerate(stat_cards):
            card = ctk.CTkFrame(stats_frame)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)

            icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=40))
            icon_label.pack(pady=10)

            value_label = ctk.CTkLabel(
                card,
                text=str(value),
                font=ctk.CTkFont(size=36, weight="bold")
            )
            value_label.pack()

            text_label = ctk.CTkLabel(card, text=label)
            text_label.pack(pady=5)

        # Active experiments section
        exp_frame = ctk.CTkFrame(dashboard)
        exp_frame.pack(fill="x", padx=20, pady=20)

        exp_title = ctk.CTkLabel(
            exp_frame,
            text="Active Experiments",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        exp_title.pack(pady=10)

        # Get active experiments
        experiments = self.db_manager.get_active_experiments()

        if experiments:
            exp_list_frame = ctk.CTkFrame(exp_frame)
            exp_list_frame.pack(fill="x", padx=20, pady=10)

            for exp in experiments[:5]:  # Show up to 5 experiments
                exp_item = ctk.CTkFrame(exp_list_frame)
                exp_item.pack(fill="x", pady=5)

                exp_label = ctk.CTkLabel(
                    exp_item,
                    text=f"{exp['experiment_code']}: {exp['name']}",
                    anchor="w"
                )
                exp_label.pack(side="left", padx=10)

                enrolled_label = ctk.CTkLabel(
                    exp_item,
                    text=f"{exp['enrolled_count']} enrolled",
                    text_color="gray"
                )
                enrolled_label.pack(side="right", padx=10)
        else:
            no_exp_label = ctk.CTkLabel(
                exp_frame,
                text="No active experiments",
                text_color="gray"
            )
            no_exp_label.pack(pady=10)

        # Quick actions frame
        actions_frame = ctk.CTkFrame(dashboard)
        actions_frame.pack(fill="x", padx=20, pady=20)

        actions_title = ctk.CTkLabel(
            actions_frame,
            text="Quick Actions",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        actions_title.pack(pady=10)

        # Action buttons
        actions_row = ctk.CTkFrame(actions_frame)
        actions_row.pack()

        new_exp_btn = ctk.CTkButton(
            actions_row,
            text="🧪 New Experiment",
            command=lambda: self.show_page("experiments"),
            width=200,
            height=50
        )
        new_exp_btn.pack(side="left", padx=10)

        new_participant_btn = ctk.CTkButton(
            actions_row,
            text="➕ New Participant",
            command=lambda: self.show_page("participants"),
            width=200,
            height=50
        )
        new_participant_btn.pack(side="left", padx=10)

        view_data_btn = ctk.CTkButton(
            actions_row,
            text="📈 View Data",
            command=lambda: self.show_page("data"),
            width=200,
            height=50
        )
        view_data_btn.pack(side="left", padx=10)

        # Recent activity
        activity_frame = ctk.CTkFrame(dashboard)
        activity_frame.pack(fill="both", expand=True, padx=20, pady=10)

        activity_title = ctk.CTkLabel(
            activity_frame,
            text="Recent Activity",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        activity_title.pack(pady=10)

        # Activity list
        activity_list = ctk.CTkTextbox(activity_frame, height=200)
        activity_list.pack(fill="both", expand=True, padx=10, pady=10)

        # Get recent activities
        recent_activities = self.db_manager.get_recent_activities(limit=10)
        for activity in recent_activities:
            activity_list.insert("end", f"{activity}\n")

        activity_list.configure(state="disabled")

        return dashboard

    def show_page(self, page_name):
        """Show the specified page."""
        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()

        # Show selected page
        if page_name in self.pages:
            self.pages[page_name].pack(fill="both", expand=True)

            # Refresh page if it has a refresh method
            if hasattr(self.pages[page_name], 'refresh'):
                self.pages[page_name].refresh()

    def save_config(self):
        """Save configuration to file."""
        config_path = Path("config/settings.json")
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def schedule_backup(self):
        """Schedule automatic database backup."""
        if self.config["data"]["auto_backup"]:
            self.backup_manager.start_auto_backup(
                interval_hours=self.config["data"]["backup_interval_hours"]
            )

    def on_closing(self):
        """Handle application closing."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Perform cleanup
            self.backup_manager.stop_auto_backup()
            self.db_manager.close()
            self.destroy()
            sys.exit()


def main():
    """Main entry point for the application."""
    # Create necessary directories
    directories = ["config", "data", "logs", "tasks", "data/backups"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True, parents=True)

    # Create and run the application
    app = RiskTasksClient()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()