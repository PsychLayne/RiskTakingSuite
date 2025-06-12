"""
Settings Panel for Risk Tasks Client
Provides interface for configuring experiment and task parameters.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import json
from pathlib import Path
from typing import Dict, Callable

from database.models import TaskType


class SettingsPanel(ctk.CTkFrame):
    """UI component for application settings and configuration."""

    def __init__(self, parent, config: Dict, save_callback: Callable):
        super().__init__(parent)
        self.config = config
        self.save_callback = save_callback
        self.task_config_frames = {}

        # Create a copy of config for editing
        self.working_config = json.loads(json.dumps(config))

        # Initialize all variables with defaults
        self.initialize_variables()

        # Setup UI
        self.setup_ui()

        # Load current values
        self.load_config_values()

    def initialize_variables(self):
        """Initialize all configuration variables with default values."""
        # Experiment variables
        self.trials_var = tk.IntVar(value=30)
        self.gap_var = tk.IntVar(value=14)
        self.duration_var = tk.IntVar(value=60)

        # Display variables
        self.fullscreen_var = tk.BooleanVar(value=True)
        self.resolution_var = tk.StringVar(value="1920x1080")

        # Data variables
        self.backup_var = tk.BooleanVar(value=True)
        self.interval_var = tk.IntVar(value=24)

        # BART variables
        self.bart_max_pumps_var = tk.IntVar(value=48)
        self.bart_points_var = tk.IntVar(value=5)
        self.bart_min_var = tk.IntVar(value=8)
        self.bart_max_var = tk.IntVar(value=48)

        # Ice Fishing variables
        self.ice_max_fish_var = tk.IntVar(value=64)
        self.ice_points_var = tk.IntVar(value=5)
        self.ice_prob_var = tk.StringVar(value="linear")

        # Mountain Mining variables
        self.mining_max_ore_var = tk.IntVar(value=64)
        self.mining_points_var = tk.IntVar(value=5)
        self.mining_prob_var = tk.StringVar(value="linear")

        # Spinning Bottle variables
        self.stb_segments_var = tk.IntVar(value=16)
        self.stb_points_var = tk.IntVar(value=5)
        self.stb_min_speed_var = tk.DoubleVar(value=12.0)
        self.stb_max_speed_var = tk.DoubleVar(value=18.0)

    def setup_ui(self):
        """Setup the settings interface."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Create scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=900, height=600)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Experiment Settings Section
        self.create_experiment_settings()

        # Display Settings Section
        self.create_display_settings()

        # Data Settings Section
        self.create_data_settings()

        # Task-Specific Settings Sections
        self.create_task_settings()

        # Button frame
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=20)

        save_button = ctk.CTkButton(
            button_frame,
            text="Save Settings",
            command=self.save_settings,
            width=150
        )
        save_button.pack(side="left", padx=10)

        reset_button = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults,
            width=150,
            fg_color="orange"
        )
        reset_button.pack(side="left", padx=10)

        export_button = ctk.CTkButton(
            button_frame,
            text="Export Config",
            command=self.export_config,
            width=150,
            fg_color="gray"
        )
        export_button.pack(side="left", padx=10)

    def create_section_header(self, parent, text: str):
        """Create a section header with separator."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10))

        label = ctk.CTkLabel(
            header_frame,
            text=text,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        label.pack(side="left", padx=10)

        # Separator line
        separator = ttk.Separator(header_frame, orient="horizontal")
        separator.pack(side="left", fill="x", expand=True, padx=20)

    def create_experiment_settings(self):
        """Create experiment configuration section."""
        self.create_section_header(self.scroll_frame, "Experiment Settings")

        exp_frame = ctk.CTkFrame(self.scroll_frame)
        exp_frame.pack(fill="x", padx=20, pady=10)

        # Trials per task
        trials_frame = ctk.CTkFrame(exp_frame, fg_color="transparent")
        trials_frame.pack(fill="x", pady=5)

        trials_label = ctk.CTkLabel(
            trials_frame,
            text="Trials per task:",
            width=200,
            anchor="w"
        )
        trials_label.pack(side="left", padx=10)

        trials_spinbox = ctk.CTkEntry(
            trials_frame,
            textvariable=self.trials_var,
            width=100
        )
        trials_spinbox.pack(side="left", padx=10)

        trials_info = ctk.CTkLabel(
            trials_frame,
            text="(Number of trials for each task)",
            text_color="gray"
        )
        trials_info.pack(side="left", padx=10)

        # Session gap
        gap_frame = ctk.CTkFrame(exp_frame, fg_color="transparent")
        gap_frame.pack(fill="x", pady=5)

        gap_label = ctk.CTkLabel(
            gap_frame,
            text="Session gap (days):",
            width=200,
            anchor="w"
        )
        gap_label.pack(side="left", padx=10)

        gap_spinbox = ctk.CTkEntry(
            gap_frame,
            textvariable=self.gap_var,
            width=100
        )
        gap_spinbox.pack(side="left", padx=10)

        gap_info = ctk.CTkLabel(
            gap_frame,
            text="(Days between sessions)",
            text_color="gray"
        )
        gap_info.pack(side="left", padx=10)

        # Max session duration
        duration_frame = ctk.CTkFrame(exp_frame, fg_color="transparent")
        duration_frame.pack(fill="x", pady=5)

        duration_label = ctk.CTkLabel(
            duration_frame,
            text="Max session duration (min):",
            width=200,
            anchor="w"
        )
        duration_label.pack(side="left", padx=10)

        duration_spinbox = ctk.CTkEntry(
            duration_frame,
            textvariable=self.duration_var,
            width=100
        )
        duration_spinbox.pack(side="left", padx=10)

        duration_info = ctk.CTkLabel(
            duration_frame,
            text="(Maximum time per session)",
            text_color="gray"
        )
        duration_info.pack(side="left", padx=10)

    def create_display_settings(self):
        """Create display configuration section."""
        self.create_section_header(self.scroll_frame, "Display Settings")

        display_frame = ctk.CTkFrame(self.scroll_frame)
        display_frame.pack(fill="x", padx=20, pady=10)

        # Fullscreen toggle
        fullscreen_frame = ctk.CTkFrame(display_frame, fg_color="transparent")
        fullscreen_frame.pack(fill="x", pady=5)

        fullscreen_label = ctk.CTkLabel(
            fullscreen_frame,
            text="Fullscreen mode:",
            width=200,
            anchor="w"
        )
        fullscreen_label.pack(side="left", padx=10)

        fullscreen_switch = ctk.CTkSwitch(
            fullscreen_frame,
            text="Enable fullscreen for tasks",
            variable=self.fullscreen_var
        )
        fullscreen_switch.pack(side="left", padx=10)

        # Resolution
        resolution_frame = ctk.CTkFrame(display_frame, fg_color="transparent")
        resolution_frame.pack(fill="x", pady=5)

        resolution_label = ctk.CTkLabel(
            resolution_frame,
            text="Resolution:",
            width=200,
            anchor="w"
        )
        resolution_label.pack(side="left", padx=10)

        resolution_menu = ctk.CTkOptionMenu(
            resolution_frame,
            variable=self.resolution_var,
            values=["1920x1080", "1600x900", "1366x768", "1280x720"],
            width=150
        )
        resolution_menu.pack(side="left", padx=10)

    def create_data_settings(self):
        """Create data management settings section."""
        self.create_section_header(self.scroll_frame, "Data Management")

        data_frame = ctk.CTkFrame(self.scroll_frame)
        data_frame.pack(fill="x", padx=20, pady=10)

        # Auto backup
        backup_frame = ctk.CTkFrame(data_frame, fg_color="transparent")
        backup_frame.pack(fill="x", pady=5)

        backup_label = ctk.CTkLabel(
            backup_frame,
            text="Automatic backup:",
            width=200,
            anchor="w"
        )
        backup_label.pack(side="left", padx=10)

        backup_switch = ctk.CTkSwitch(
            backup_frame,
            text="Enable automatic backups",
            variable=self.backup_var,
            command=self.on_backup_toggle
        )
        backup_switch.pack(side="left", padx=10)

        # Backup interval
        self.interval_frame = ctk.CTkFrame(data_frame, fg_color="transparent")
        self.interval_frame.pack(fill="x", pady=5)

        interval_label = ctk.CTkLabel(
            self.interval_frame,
            text="Backup interval (hours):",
            width=200,
            anchor="w"
        )
        interval_label.pack(side="left", padx=10)

        interval_spinbox = ctk.CTkEntry(
            self.interval_frame,
            textvariable=self.interval_var,
            width=100
        )
        interval_spinbox.pack(side="left", padx=10)

    def create_task_settings(self):
        """Create task-specific settings sections."""
        tasks = [
            ("BART", "bart", self.create_bart_settings),
            ("Ice Fishing", "ice_fishing", self.create_ice_fishing_settings),
            ("Mountain Mining", "mountain_mining", self.create_mining_settings),
            ("Spinning Bottle", "spinning_bottle", self.create_stb_settings)
        ]

        for display_name, task_key, create_func in tasks:
            self.create_section_header(self.scroll_frame, f"{display_name} Settings")

            task_frame = ctk.CTkFrame(self.scroll_frame)
            task_frame.pack(fill="x", padx=20, pady=10)

            self.task_config_frames[task_key] = task_frame
            create_func(task_frame, task_key)

    def create_bart_settings(self, parent, task_key):
        """Create BART-specific settings."""
        # Max pumps
        max_pumps_frame = ctk.CTkFrame(parent, fg_color="transparent")
        max_pumps_frame.pack(fill="x", pady=5)

        max_pumps_label = ctk.CTkLabel(
            max_pumps_frame,
            text="Maximum pumps:",
            width=200,
            anchor="w"
        )
        max_pumps_label.pack(side="left", padx=10)

        max_pumps_entry = ctk.CTkEntry(
            max_pumps_frame,
            textvariable=self.bart_max_pumps_var,
            width=100
        )
        max_pumps_entry.pack(side="left", padx=10)

        # Points per pump
        points_frame = ctk.CTkFrame(parent, fg_color="transparent")
        points_frame.pack(fill="x", pady=5)

        points_label = ctk.CTkLabel(
            points_frame,
            text="Points per pump:",
            width=200,
            anchor="w"
        )
        points_label.pack(side="left", padx=10)

        points_entry = ctk.CTkEntry(
            points_frame,
            textvariable=self.bart_points_var,
            width=100
        )
        points_entry.pack(side="left", padx=10)

        # Explosion range
        range_frame = ctk.CTkFrame(parent, fg_color="transparent")
        range_frame.pack(fill="x", pady=5)

        range_label = ctk.CTkLabel(
            range_frame,
            text="Explosion range (min-max):",
            width=200,
            anchor="w"
        )
        range_label.pack(side="left", padx=10)

        min_entry = ctk.CTkEntry(
            range_frame,
            textvariable=self.bart_min_var,
            width=60
        )
        min_entry.pack(side="left", padx=5)

        dash_label = ctk.CTkLabel(range_frame, text="-")
        dash_label.pack(side="left")

        max_entry = ctk.CTkEntry(
            range_frame,
            textvariable=self.bart_max_var,
            width=60
        )
        max_entry.pack(side="left", padx=5)

    def create_ice_fishing_settings(self, parent, task_key):
        """Create Ice Fishing settings."""
        # Max fish
        max_fish_frame = ctk.CTkFrame(parent, fg_color="transparent")
        max_fish_frame.pack(fill="x", pady=5)

        max_fish_label = ctk.CTkLabel(
            max_fish_frame,
            text="Maximum fish:",
            width=200,
            anchor="w"
        )
        max_fish_label.pack(side="left", padx=10)

        max_fish_entry = ctk.CTkEntry(
            max_fish_frame,
            textvariable=self.ice_max_fish_var,
            width=100
        )
        max_fish_entry.pack(side="left", padx=10)

        # Points per fish
        points_frame = ctk.CTkFrame(parent, fg_color="transparent")
        points_frame.pack(fill="x", pady=5)

        points_label = ctk.CTkLabel(
            points_frame,
            text="Points per fish:",
            width=200,
            anchor="w"
        )
        points_label.pack(side="left", padx=10)

        points_entry = ctk.CTkEntry(
            points_frame,
            textvariable=self.ice_points_var,
            width=100
        )
        points_entry.pack(side="left", padx=10)

        # Break probability function
        prob_frame = ctk.CTkFrame(parent, fg_color="transparent")
        prob_frame.pack(fill="x", pady=5)

        prob_label = ctk.CTkLabel(
            prob_frame,
            text="Break probability:",
            width=200,
            anchor="w"
        )
        prob_label.pack(side="left", padx=10)

        prob_menu = ctk.CTkOptionMenu(
            prob_frame,
            variable=self.ice_prob_var,
            values=["linear", "exponential", "logarithmic"],
            width=150
        )
        prob_menu.pack(side="left", padx=10)

    def create_mining_settings(self, parent, task_key):
        """Create Mountain Mining settings."""
        # Max ore
        max_ore_frame = ctk.CTkFrame(parent, fg_color="transparent")
        max_ore_frame.pack(fill="x", pady=5)

        max_ore_label = ctk.CTkLabel(
            max_ore_frame,
            text="Maximum ore:",
            width=200,
            anchor="w"
        )
        max_ore_label.pack(side="left", padx=10)

        max_ore_entry = ctk.CTkEntry(
            max_ore_frame,
            textvariable=self.mining_max_ore_var,
            width=100
        )
        max_ore_entry.pack(side="left", padx=10)

        # Points per ore
        points_frame = ctk.CTkFrame(parent, fg_color="transparent")
        points_frame.pack(fill="x", pady=5)

        points_label = ctk.CTkLabel(
            points_frame,
            text="Points per ore:",
            width=200,
            anchor="w"
        )
        points_label.pack(side="left", padx=10)

        points_entry = ctk.CTkEntry(
            points_frame,
            textvariable=self.mining_points_var,
            width=100
        )
        points_entry.pack(side="left", padx=10)

        # Snap probability function
        prob_frame = ctk.CTkFrame(parent, fg_color="transparent")
        prob_frame.pack(fill="x", pady=5)

        prob_label = ctk.CTkLabel(
            prob_frame,
            text="Snap probability:",
            width=200,
            anchor="w"
        )
        prob_label.pack(side="left", padx=10)

        prob_menu = ctk.CTkOptionMenu(
            prob_frame,
            variable=self.mining_prob_var,
            values=["linear", "exponential", "logarithmic"],
            width=150
        )
        prob_menu.pack(side="left", padx=10)

    def create_stb_settings(self, parent, task_key):
        """Create Spinning Bottle settings."""
        # Segments
        segments_frame = ctk.CTkFrame(parent, fg_color="transparent")
        segments_frame.pack(fill="x", pady=5)

        segments_label = ctk.CTkLabel(
            segments_frame,
            text="Number of segments:",
            width=200,
            anchor="w"
        )
        segments_label.pack(side="left", padx=10)

        segments_entry = ctk.CTkEntry(
            segments_frame,
            textvariable=self.stb_segments_var,
            width=100
        )
        segments_entry.pack(side="left", padx=10)

        # Points per add
        points_frame = ctk.CTkFrame(parent, fg_color="transparent")
        points_frame.pack(fill="x", pady=5)

        points_label = ctk.CTkLabel(
            points_frame,
            text="Points per add:",
            width=200,
            anchor="w"
        )
        points_label.pack(side="left", padx=10)

        points_entry = ctk.CTkEntry(
            points_frame,
            textvariable=self.stb_points_var,
            width=100
        )
        points_entry.pack(side="left", padx=10)

        # Spin speed range
        speed_frame = ctk.CTkFrame(parent, fg_color="transparent")
        speed_frame.pack(fill="x", pady=5)

        speed_label = ctk.CTkLabel(
            speed_frame,
            text="Spin speed range:",
            width=200,
            anchor="w"
        )
        speed_label.pack(side="left", padx=10)

        min_speed_entry = ctk.CTkEntry(
            speed_frame,
            textvariable=self.stb_min_speed_var,
            width=60
        )
        min_speed_entry.pack(side="left", padx=5)

        dash_label = ctk.CTkLabel(speed_frame, text="-")
        dash_label.pack(side="left")

        max_speed_entry = ctk.CTkEntry(
            speed_frame,
            textvariable=self.stb_max_speed_var,
            width=60
        )
        max_speed_entry.pack(side="left", padx=5)

    def on_backup_toggle(self):
        """Handle backup toggle switch."""
        if self.backup_var.get():
            self.interval_frame.pack(fill="x", pady=5)
        else:
            self.interval_frame.pack_forget()

    def load_config_values(self):
        """Load current configuration values into UI."""
        # Experiment settings
        self.trials_var.set(self.config.get("experiment", {}).get("total_trials_per_task", 30))
        self.gap_var.set(self.config.get("experiment", {}).get("session_gap_days", 14))
        self.duration_var.set(self.config.get("experiment", {}).get("max_session_duration", 60))

        # Display settings
        self.fullscreen_var.set(self.config.get("display", {}).get("fullscreen", True))
        self.resolution_var.set(self.config.get("display", {}).get("resolution", "1920x1080"))

        # Data settings
        self.backup_var.set(self.config.get("data", {}).get("auto_backup", True))
        self.interval_var.set(self.config.get("data", {}).get("backup_interval_hours", 24))
        self.on_backup_toggle()

        # Task-specific settings
        tasks_config = self.config.get("tasks", {})

        # BART
        bart_config = tasks_config.get("bart", {})
        self.bart_max_pumps_var.set(bart_config.get("max_pumps", 48))
        self.bart_points_var.set(bart_config.get("points_per_pump", 5))
        explosion_range = bart_config.get("explosion_range", [8, 48])
        self.bart_min_var.set(explosion_range[0])
        self.bart_max_var.set(explosion_range[1])

        # Ice Fishing
        ice_config = tasks_config.get("ice_fishing", {})
        self.ice_max_fish_var.set(ice_config.get("max_fish", 64))
        self.ice_points_var.set(ice_config.get("points_per_fish", 5))
        self.ice_prob_var.set(ice_config.get("break_probability_function", "linear"))

        # Mountain Mining
        mining_config = tasks_config.get("mountain_mining", {})
        self.mining_max_ore_var.set(mining_config.get("max_ore", 64))
        self.mining_points_var.set(mining_config.get("points_per_ore", 5))
        self.mining_prob_var.set(mining_config.get("snap_probability_function", "linear"))

        # Spinning Bottle
        stb_config = tasks_config.get("spinning_bottle", {})
        self.stb_segments_var.set(stb_config.get("segments", 16))
        self.stb_points_var.set(stb_config.get("points_per_add", 5))
        speed_range = stb_config.get("spin_speed_range", [12.0, 18.0])
        self.stb_min_speed_var.set(speed_range[0])
        self.stb_max_speed_var.set(speed_range[1])

    def validate_settings(self):
        """Validate all settings before saving."""
        errors = []

        # Experiment validation
        if self.trials_var.get() < 1:
            errors.append("Trials per task must be at least 1")

        if self.gap_var.get() < 1:
            errors.append("Session gap must be at least 1 day")

        if self.duration_var.get() < 10:
            errors.append("Session duration must be at least 10 minutes")

        # Backup validation
        if self.backup_var.get() and self.interval_var.get() < 1:
            errors.append("Backup interval must be at least 1 hour")

        # BART validation
        if self.bart_min_var.get() >= self.bart_max_var.get():
            errors.append("BART: Minimum explosion must be less than maximum")

        # STB validation
        if self.stb_min_speed_var.get() >= self.stb_max_speed_var.get():
            errors.append("STB: Minimum speed must be less than maximum")

        return errors

    def save_settings(self):
        """Save current settings."""
        # Validate first
        errors = self.validate_settings()
        if errors:
            messagebox.showerror(
                "Validation Error",
                "Please fix the following errors:\n\n" + "\n".join(errors)
            )
            return

        # Update working config
        self.working_config["experiment"]["total_trials_per_task"] = self.trials_var.get()
        self.working_config["experiment"]["session_gap_days"] = self.gap_var.get()
        self.working_config["experiment"]["max_session_duration"] = self.duration_var.get()

        self.working_config["display"]["fullscreen"] = self.fullscreen_var.get()
        self.working_config["display"]["resolution"] = self.resolution_var.get()

        self.working_config["data"]["auto_backup"] = self.backup_var.get()
        self.working_config["data"]["backup_interval_hours"] = self.interval_var.get()

        # Ensure tasks section exists
        if "tasks" not in self.working_config:
            self.working_config["tasks"] = {}

        # Task configs
        self.working_config["tasks"]["bart"] = {
            "max_pumps": self.bart_max_pumps_var.get(),
            "points_per_pump": self.bart_points_var.get(),
            "explosion_range": [self.bart_min_var.get(), self.bart_max_var.get()]
        }

        self.working_config["tasks"]["ice_fishing"] = {
            "max_fish": self.ice_max_fish_var.get(),
            "points_per_fish": self.ice_points_var.get(),
            "break_probability_function": self.ice_prob_var.get()
        }

        self.working_config["tasks"]["mountain_mining"] = {
            "max_ore": self.mining_max_ore_var.get(),
            "points_per_ore": self.mining_points_var.get(),
            "snap_probability_function": self.mining_prob_var.get()
        }

        self.working_config["tasks"]["spinning_bottle"] = {
            "segments": self.stb_segments_var.get(),
            "points_per_add": self.stb_points_var.get(),
            "spin_speed_range": [self.stb_min_speed_var.get(), self.stb_max_speed_var.get()]
        }

        # Update main config
        self.config.update(self.working_config)

        # Call save callback
        self.save_callback()

        messagebox.showinfo("Success", "Settings saved successfully!")

    def reset_to_defaults(self):
        """Reset all settings to default values."""
        result = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?"
        )

        if result:
            # Create default config
            default_config = {
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
                        "explosion_range": [8, 48]
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
                        "spin_speed_range": [12.0, 18.0]
                    }
                }
            }

            self.config.update(default_config)
            self.working_config = json.loads(json.dumps(default_config))
            self.load_config_values()

            messagebox.showinfo("Success", "Settings reset to defaults!")

    def export_config(self):
        """Export configuration to file."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.working_config, f, indent=4)
                messagebox.showinfo("Success", f"Configuration exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export configuration: {e}")