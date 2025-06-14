"""
Experiment Creator UI for Risk Tasks Client
Provides a multi-step wizard interface for creating and configuring experiments.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from typing import Dict, List, Optional, Callable
import json
from datetime import datetime
import copy

from database.db_manager import DatabaseManager
from database.models import TaskType
from utils.experiment_manager import ExperimentManager


class TaskSelectionModal(ctk.CTkToplevel):
    """Modal dialog for selecting tasks."""

    def __init__(self, parent, available_tasks: List[str], selected_callback: Callable):
        super().__init__(parent)
        self.selected_callback = selected_callback
        self.available_tasks = available_tasks
        self.selected_task = None

        # Window setup
        self.title("Select Task")
        self.geometry("500x600")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (250)
        y = (self.winfo_screenheight() // 2) - (300)
        self.geometry(f"500x600+{x}+{y}")

        self.setup_ui()

    def setup_ui(self):
        """Setup the task selection UI."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Select a Task",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)

        # Task list frame
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create task buttons
        task_info = {
            'bart': {
                'name': 'Balloon Task (BART)',
                'icon': '🎈',
                'description': 'Participants inflate a balloon to earn points, but risk losing all if it pops.',
                'color': '#FF6B6B'
            },
            'ice_fishing': {
                'name': 'Ice Fishing',
                'icon': '🐧',
                'description': 'Participants catch fish while risking the ice breaking under the weight.',
                'color': '#4ECDC4'
            },
            'mountain_mining': {
                'name': 'Mountain Mining',
                'icon': '⛏️',
                'description': 'Participants mine ore while risking the rope snapping from too much weight.',
                'color': '#FFE66D'
            },
            'spinning_bottle': {
                'name': 'Spinning Bottle',
                'icon': '🍾',
                'description': 'Participants add segments to increase winnings but risk landing on red.',
                'color': '#95E1D3'
            }
        }

        for task_key in self.available_tasks:
            if task_key in task_info:
                info = task_info[task_key]

                # Task button frame
                task_frame = ctk.CTkFrame(list_frame)
                task_frame.pack(fill="x", padx=10, pady=5)

                # Task button
                task_btn = ctk.CTkButton(
                    task_frame,
                    text=f"{info['icon']} {info['name']}",
                    command=lambda t=task_key: self.select_task(t),
                    height=80,
                    font=ctk.CTkFont(size=16, weight="bold"),
                    fg_color=info['color'],
                    hover_color=self.adjust_color_brightness(info['color'], 0.8)
                )
                task_btn.pack(fill="x", padx=5, pady=5)

                # Description
                desc_label = ctk.CTkLabel(
                    task_frame,
                    text=info['description'],
                    font=ctk.CTkFont(size=12),
                    text_color="gray",
                    wraplength=450
                )
                desc_label.pack(padx=10, pady=(0, 5))

        # Cancel button
        cancel_btn = ctk.CTkButton(
            self,
            text="Cancel",
            command=self.destroy,
            fg_color="gray",
            width=100
        )
        cancel_btn.pack(pady=20)

    def adjust_color_brightness(self, hex_color: str, factor: float) -> str:
        """Adjust color brightness for hover effect."""
        # Remove # if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Adjust brightness
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)

        # Ensure values are within bounds
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def select_task(self, task_key: str):
        """Handle task selection."""
        self.selected_task = task_key
        self.selected_callback(task_key)
        self.destroy()


class TaskConfigModal(ctk.CTkToplevel):
    """Modal dialog for configuring task parameters."""

    def __init__(self, parent, task_type: str, current_config: Dict, save_callback: Callable):
        super().__init__(parent)
        self.task_type = task_type
        self.current_config = copy.deepcopy(current_config)
        self.save_callback = save_callback

        # Window setup
        self.title(f"Configure {TaskType.get_display_name(TaskType(task_type))}")
        self.geometry("600x700")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (300)
        y = (self.winfo_screenheight() // 2) - (350)
        self.geometry(f"600x700+{x}+{y}")

        # Configuration variables
        self.config_vars = {}

        self.setup_ui()

    def setup_ui(self):
        """Setup the configuration UI."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text=f"Configure {TaskType.get_display_name(TaskType(self.task_type))}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)

        # Info label
        info_label = ctk.CTkLabel(
            self,
            text="Customize task parameters or use defaults",
            text_color="gray"
        )
        info_label.pack(pady=(0, 10))

        # Scrollable frame for configuration options
        config_frame = ctk.CTkScrollableFrame(self, height=500)
        config_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create configuration UI based on task type
        if self.task_type == 'bart':
            self.create_bart_config(config_frame)
        elif self.task_type == 'ice_fishing':
            self.create_ice_fishing_config(config_frame)
        elif self.task_type == 'mountain_mining':
            self.create_mining_config(config_frame)
        elif self.task_type == 'spinning_bottle':
            self.create_stb_config(config_frame)

        # Button frame
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=20)

        # Reset to defaults button
        reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults,
            fg_color="orange",
            width=150
        )
        reset_btn.pack(side="left", padx=5)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray",
            width=100
        )
        cancel_btn.pack(side="right", padx=5)

        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Configuration",
            command=self.save_config,
            width=150
        )
        save_btn.pack(side="right", padx=5)

    def create_config_row(self, parent, label: str, var_name: str, var_type: str,
                         default_value, options: List = None, info: str = None):
        """Create a configuration row."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=5)

        # Label
        label_widget = ctk.CTkLabel(
            row_frame,
            text=label,
            width=200,
            anchor="w"
        )
        label_widget.pack(side="left", padx=10)

        # Create appropriate input widget
        if var_type == "int":
            var = tk.IntVar(value=default_value)
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=100)
            entry.pack(side="left", padx=10)
        elif var_type == "float":
            var = tk.DoubleVar(value=default_value)
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=100)
            entry.pack(side="left", padx=10)
        elif var_type == "bool":
            var = tk.BooleanVar(value=default_value)
            switch = ctk.CTkSwitch(row_frame, text="", variable=var)
            switch.pack(side="left", padx=10)
        elif var_type == "choice" and options:
            var = tk.StringVar(value=default_value)
            menu = ctk.CTkOptionMenu(row_frame, variable=var, values=options, width=150)
            menu.pack(side="left", padx=10)
        else:
            var = tk.StringVar(value=default_value)
            entry = ctk.CTkEntry(row_frame, textvariable=var, width=200)
            entry.pack(side="left", padx=10)

        # Info label if provided
        if info:
            info_label = ctk.CTkLabel(
                row_frame,
                text=info,
                text_color="gray",
                font=ctk.CTkFont(size=12)
            )
            info_label.pack(side="left", padx=10)

        self.config_vars[var_name] = var

    def create_bart_config(self, parent):
        """Create BART configuration options."""
        self.create_config_row(
            parent, "Maximum Pumps:", "max_pumps", "int",
            self.current_config.get('max_pumps', 48),
            info="(1-128)"
        )

        self.create_config_row(
            parent, "Points per Pump:", "points_per_pump", "int",
            self.current_config.get('points_per_pump', 5)
        )

        # Explosion range
        range_frame = ctk.CTkFrame(parent, fg_color="transparent")
        range_frame.pack(fill="x", pady=5)

        range_label = ctk.CTkLabel(
            range_frame,
            text="Explosion Range:",
            width=200,
            anchor="w"
        )
        range_label.pack(side="left", padx=10)

        explosion_range = self.current_config.get('explosion_range', [8, 48])

        self.config_vars['explosion_min'] = tk.IntVar(value=explosion_range[0])
        min_entry = ctk.CTkEntry(
            range_frame,
            textvariable=self.config_vars['explosion_min'],
            width=60
        )
        min_entry.pack(side="left", padx=5)

        dash_label = ctk.CTkLabel(range_frame, text="-")
        dash_label.pack(side="left")

        self.config_vars['explosion_max'] = tk.IntVar(value=explosion_range[1])
        max_entry = ctk.CTkEntry(
            range_frame,
            textvariable=self.config_vars['explosion_max'],
            width=60
        )
        max_entry.pack(side="left", padx=5)

        self.create_config_row(
            parent, "Keyboard Input Mode:", "keyboard_input_mode", "bool",
            self.current_config.get('keyboard_input_mode', False),
            info="Type number vs. click to pump"
        )

        self.create_config_row(
            parent, "Balloon Color:", "balloon_color", "choice",
            self.current_config.get('balloon_color', 'Red'),
            options=["Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Pink"]
        )

        self.create_config_row(
            parent, "Random Colors:", "random_colors", "bool",
            self.current_config.get('random_colors', False),
            info="Different color each trial"
        )

    def create_ice_fishing_config(self, parent):
        """Create Ice Fishing configuration options."""
        self.create_config_row(
            parent, "Maximum Fish:", "max_fish", "int",
            self.current_config.get('max_fish', 64),
            info="(1-100)"
        )

        self.create_config_row(
            parent, "Points per Fish:", "points_per_fish", "int",
            self.current_config.get('points_per_fish', 5)
        )

    def create_mining_config(self, parent):
        """Create Mountain Mining configuration options."""
        self.create_config_row(
            parent, "Maximum Ore:", "max_ore", "int",
            self.current_config.get('max_ore', 64),
            info="(1-100)"
        )

        self.create_config_row(
            parent, "Points per Ore:", "points_per_ore", "int",
            self.current_config.get('points_per_ore', 5)
        )

    def create_stb_config(self, parent):
        """Create Spinning Bottle configuration options."""
        self.create_config_row(
            parent, "Number of Segments:", "segments", "choice",
            str(self.current_config.get('segments', 16)),
            options=["8", "16", "32"]
        )

        self.create_config_row(
            parent, "Points per Add:", "points_per_add", "int",
            self.current_config.get('points_per_add', 5)
        )

        # Spin speed range
        speed_frame = ctk.CTkFrame(parent, fg_color="transparent")
        speed_frame.pack(fill="x", pady=5)

        speed_label = ctk.CTkLabel(
            speed_frame,
            text="Spin Speed Range:",
            width=200,
            anchor="w"
        )
        speed_label.pack(side="left", padx=10)

        speed_range = self.current_config.get('spin_speed_range', [12.0, 18.0])

        self.config_vars['speed_min'] = tk.DoubleVar(value=speed_range[0])
        min_entry = ctk.CTkEntry(
            speed_frame,
            textvariable=self.config_vars['speed_min'],
            width=60
        )
        min_entry.pack(side="left", padx=5)

        dash_label = ctk.CTkLabel(speed_frame, text="-")
        dash_label.pack(side="left")

        self.config_vars['speed_max'] = tk.DoubleVar(value=speed_range[1])
        max_entry = ctk.CTkEntry(
            speed_frame,
            textvariable=self.config_vars['speed_max'],
            width=60
        )
        max_entry.pack(side="left", padx=5)

        self.create_config_row(
            parent, "Win Color:", "win_color", "choice",
            self.current_config.get('win_color', 'Green'),
            options=["Green", "Blue", "Yellow", "Orange", "Purple"]
        )

        self.create_config_row(
            parent, "Loss Color:", "loss_color", "choice",
            self.current_config.get('loss_color', 'Red'),
            options=["Red", "Blue", "Yellow", "Orange", "Purple"]
        )

    def save_config(self):
        """Save the configuration."""
        new_config = {}

        # Extract values based on task type
        if self.task_type == 'bart':
            new_config['max_pumps'] = self.config_vars['max_pumps'].get()
            new_config['points_per_pump'] = self.config_vars['points_per_pump'].get()
            new_config['explosion_range'] = [
                self.config_vars['explosion_min'].get(),
                self.config_vars['explosion_max'].get()
            ]
            new_config['keyboard_input_mode'] = self.config_vars['keyboard_input_mode'].get()
            new_config['balloon_color'] = self.config_vars['balloon_color'].get()
            new_config['random_colors'] = self.config_vars['random_colors'].get()

        elif self.task_type == 'ice_fishing':
            new_config['max_fish'] = self.config_vars['max_fish'].get()
            new_config['points_per_fish'] = self.config_vars['points_per_fish'].get()

        elif self.task_type == 'mountain_mining':
            new_config['max_ore'] = self.config_vars['max_ore'].get()
            new_config['points_per_ore'] = self.config_vars['points_per_ore'].get()

        elif self.task_type == 'spinning_bottle':
            new_config['segments'] = int(self.config_vars['segments'].get())
            new_config['points_per_add'] = self.config_vars['points_per_add'].get()
            new_config['spin_speed_range'] = [
                self.config_vars['speed_min'].get(),
                self.config_vars['speed_max'].get()
            ]
            new_config['win_color'] = self.config_vars['win_color'].get()
            new_config['loss_color'] = self.config_vars['loss_color'].get()

        self.save_callback(self.task_type, new_config)
        self.destroy()

    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        # Load default configuration
        from pathlib import Path
        config_path = Path("config/settings.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                settings = json.load(f)
                defaults = settings.get('tasks', {}).get(self.task_type, {})
        else:
            defaults = {}

        # Update all variables
        for key, var in self.config_vars.items():
            if key in defaults:
                var.set(defaults[key])
            elif key == 'explosion_min' and 'explosion_range' in defaults:
                var.set(defaults['explosion_range'][0])
            elif key == 'explosion_max' and 'explosion_range' in defaults:
                var.set(defaults['explosion_range'][1])
            elif key == 'speed_min' and 'spin_speed_range' in defaults:
                var.set(defaults['spin_speed_range'][0])
            elif key == 'speed_max' and 'spin_speed_range' in defaults:
                var.set(defaults['spin_speed_range'][1])


class SessionTaskItem(ctk.CTkFrame):
    """A single task item in the session configuration."""

    def __init__(self, parent, task_type: str, task_config: Dict,
                 on_configure: Callable, on_remove: Callable, can_reorder: bool = True):
        super().__init__(parent)
        self.task_type = task_type
        self.task_config = task_config
        self.on_configure = on_configure
        self.on_remove = on_remove
        self.can_reorder = can_reorder

        self.setup_ui()

    def setup_ui(self):
        """Setup the task item UI."""
        # Main container
        self.configure(height=80)

        # Drag handle (if reordering allowed)
        if self.can_reorder:
            handle_label = ctk.CTkLabel(
                self,
                text="☰",
                font=ctk.CTkFont(size=20),
                width=30
            )
            handle_label.pack(side="left", padx=10)

        # Task icon and name
        task_icons = {
            'bart': '🎈',
            'ice_fishing': '🐧',
            'mountain_mining': '⛏️',
            'spinning_bottle': '🍾'
        }

        icon = task_icons.get(self.task_type, '📋')
        display_name = TaskType.get_display_name(TaskType(self.task_type))

        task_label = ctk.CTkLabel(
            self,
            text=f"{icon} {display_name}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        task_label.pack(side="left", padx=10, expand=True, fill="x")

        # Configuration status
        config_status = "Customized" if self.task_config else "Default settings"
        status_label = ctk.CTkLabel(
            self,
            text=config_status,
            text_color="green" if self.task_config else "gray",
            font=ctk.CTkFont(size=12)
        )
        status_label.pack(side="left", padx=10)

        # Configure button
        config_btn = ctk.CTkButton(
            self,
            text="Configure",
            command=lambda: self.on_configure(self.task_type),
            width=100,
            height=35
        )
        config_btn.pack(side="left", padx=5)

        # Remove button
        remove_btn = ctk.CTkButton(
            self,
            text="×",
            command=lambda: self.on_remove(self.task_type),
            width=35,
            height=35,
            fg_color="red",
            hover_color="darkred"
        )
        remove_btn.pack(side="left", padx=5)


class ExperimentCreator(ctk.CTkFrame):
    """Multi-step wizard for creating experiments."""

    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.experiment_manager = ExperimentManager(db_manager)

        # Wizard state
        self.current_step = 1
        self.total_steps = 3
        self.experiment_config = {
            'name': '',
            'code': '',
            'description': '',
            'num_sessions': 1,
            'randomize_order': False,
            'sessions': {}
        }

        # UI components storage
        self.step_frames = {}
        self.navigation_buttons = {}

        # Task configuration storage
        self.task_configs = {}
        self.session_task_lists = {}
        self.session_task_items = {}

        # Setup UI
        self.setup_ui()

        # Show first step
        self.show_step(1)

    def setup_ui(self):
        """Setup the main wizard interface."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Create New Experiment",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Progress indicator
        self.create_progress_indicator()

        # Main content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create all step frames
        self.create_step_frames()

        # Navigation buttons
        self.create_navigation_buttons()

    def create_progress_indicator(self):
        """Create the step progress indicator."""
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=20, pady=10)

        # Create step indicators
        self.step_indicators = []
        step_labels = ["Template Settings", "Session Configuration", "Review & Create"]

        for i in range(self.total_steps):
            step_container = ctk.CTkFrame(progress_frame, fg_color="transparent")
            step_container.pack(side="left", expand=True, fill="x")

            # Step number circle
            circle_frame = ctk.CTkFrame(
                step_container,
                width=40,
                height=40,
                corner_radius=20
            )
            circle_frame.pack()
            circle_frame.pack_propagate(False)

            number_label = ctk.CTkLabel(
                circle_frame,
                text=str(i + 1),
                font=ctk.CTkFont(size=16, weight="bold")
            )
            number_label.pack(expand=True)

            # Step label
            label = ctk.CTkLabel(
                step_container,
                text=step_labels[i],
                font=ctk.CTkFont(size=12)
            )
            label.pack(pady=(5, 0))

            self.step_indicators.append({
                'container': step_container,
                'circle': circle_frame,
                'number': number_label,
                'label': label
            })

            # Add connector line (except after last step)
            if i < self.total_steps - 1:
                line_frame = ctk.CTkFrame(
                    progress_frame,
                    height=2,
                    fg_color="gray50"
                )
                line_frame.pack(side="left", fill="x", expand=True, pady=(0, 35))

    def update_progress_indicator(self):
        """Update the visual progress indicator."""
        for i, indicator in enumerate(self.step_indicators):
            if i < self.current_step - 1:
                # Completed step
                indicator['circle'].configure(fg_color="green")
                indicator['number'].configure(text="✓")
            elif i == self.current_step - 1:
                # Current step
                indicator['circle'].configure(fg_color="#1f6aa5")
                indicator['number'].configure(text=str(i + 1))
            else:
                # Future step
                indicator['circle'].configure(fg_color="gray70")
                indicator['number'].configure(text=str(i + 1))

    def create_step_frames(self):
        """Create frames for each wizard step."""
        # Step 1: Template Settings
        self.step_frames[1] = self.create_step1_frame()

        # Step 2: Session Configuration
        self.step_frames[2] = self.create_step2_frame()

        # Step 3: Review & Create
        self.step_frames[3] = self.create_step3_frame()

    def create_navigation_buttons(self):
        """Create navigation buttons for the wizard."""
        nav_frame = ctk.CTkFrame(self)
        nav_frame.pack(fill="x", padx=20, pady=20)

        # Cancel button
        self.cancel_button = ctk.CTkButton(
            nav_frame,
            text="Cancel",
            command=self.on_cancel,
            fg_color="gray",
            width=100
        )
        self.cancel_button.pack(side="left", padx=5)

        # Previous button
        self.prev_button = ctk.CTkButton(
            nav_frame,
            text="← Previous",
            command=self.previous_step,
            width=100
        )
        self.prev_button.pack(side="left", padx=5)

        # Save draft button
        self.save_draft_button = ctk.CTkButton(
            nav_frame,
            text="Save Draft",
            command=self.save_draft,
            fg_color="orange",
            width=100
        )
        self.save_draft_button.pack(side="left", padx=20)

        # Next button
        self.next_button = ctk.CTkButton(
            nav_frame,
            text="Next →",
            command=self.next_step,
            width=100
        )
        self.next_button.pack(side="right", padx=5)

        # Create button (hidden initially)
        self.create_button = ctk.CTkButton(
            nav_frame,
            text="Create Experiment",
            command=self.create_experiment,
            fg_color="green",
            width=150
        )
        self.create_button.pack(side="right", padx=5)
        self.create_button.pack_forget()

    def create_step1_frame(self) -> ctk.CTkFrame:
        """Create Step 1: Experiment Template Settings."""
        frame = ctk.CTkFrame(self.content_frame)

        # Step title
        title = ctk.CTkLabel(
            frame,
            text="Step 1: Experiment Template Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Form container
        form_frame = ctk.CTkFrame(frame)
        form_frame.pack(fill="both", expand=True, padx=40, pady=20)

        # Experiment name
        name_label = ctk.CTkLabel(
            form_frame,
            text="Experiment Name:",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.name_var = tk.StringVar()
        self.name_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.name_var,
            placeholder_text="Enter a descriptive name",
            width=400
        )
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        # Experiment code
        code_label = ctk.CTkLabel(
            form_frame,
            text="Experiment Code:",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        code_label.grid(row=1, column=0, sticky="w", padx=10, pady=10)

        code_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        code_frame.grid(row=1, column=1, sticky="w", padx=10, pady=10)

        self.code_var = tk.StringVar()
        self.code_entry = ctk.CTkEntry(
            code_frame,
            textvariable=self.code_var,
            placeholder_text="Leave blank for auto-generation",
            width=250
        )
        self.code_entry.pack(side="left")

        self.generate_code_button = ctk.CTkButton(
            code_frame,
            text="Generate",
            command=self.generate_code,
            width=80
        )
        self.generate_code_button.pack(side="left", padx=(10, 0))

        # Description
        desc_label = ctk.CTkLabel(
            form_frame,
            text="Description:",
            font=ctk.CTkFont(size=14),
            anchor="nw"
        )
        desc_label.grid(row=2, column=0, sticky="nw", padx=10, pady=10)

        self.desc_text = ctk.CTkTextbox(
            form_frame,
            width=400,
            height=100
        )
        self.desc_text.grid(row=2, column=1, padx=10, pady=10)

        # Number of sessions
        sessions_label = ctk.CTkLabel(
            form_frame,
            text="Number of Sessions:",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        sessions_label.grid(row=3, column=0, sticky="w", padx=10, pady=10)

        sessions_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        sessions_frame.grid(row=3, column=1, sticky="w", padx=10, pady=10)

        self.sessions_var = tk.IntVar(value=1)
        session1_radio = ctk.CTkRadioButton(
            sessions_frame,
            text="1 Session",
            variable=self.sessions_var,
            value=1,
            command=self.on_session_count_changed
        )
        session1_radio.pack(side="left", padx=(0, 20))

        session2_radio = ctk.CTkRadioButton(
            sessions_frame,
            text="2 Sessions",
            variable=self.sessions_var,
            value=2,
            command=self.on_session_count_changed
        )
        session2_radio.pack(side="left")

        # Tasks per session
        tasks_label = ctk.CTkLabel(
            form_frame,
            text="Tasks per Session:",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        tasks_label.grid(row=4, column=0, sticky="w", padx=10, pady=10)

        self.tasks_var = tk.IntVar(value=2)
        self.tasks_menu = ctk.CTkOptionMenu(
            form_frame,
            variable=self.tasks_var,
            values=["1", "2", "3", "4"],
            width=150
        )
        self.tasks_menu.grid(row=4, column=1, sticky="w", padx=10, pady=10)

        # Randomize order
        random_label = ctk.CTkLabel(
            form_frame,
            text="Task Order:",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        random_label.grid(row=5, column=0, sticky="w", padx=10, pady=10)

        self.randomize_var = tk.BooleanVar(value=False)
        self.randomize_switch = ctk.CTkSwitch(
            form_frame,
            text="Randomize task order for each participant",
            variable=self.randomize_var,
            onvalue=True,
            offvalue=False
        )
        self.randomize_switch.grid(row=5, column=1, sticky="w", padx=10, pady=10)

        # Validation indicators
        self.validation_frame = ctk.CTkFrame(frame)
        self.validation_frame.pack(fill="x", padx=40, pady=10)

        self.validation_label = ctk.CTkLabel(
            self.validation_frame,
            text="",
            text_color="red"
        )
        self.validation_label.pack()

        return frame

    def create_step2_frame(self) -> ctk.CTkFrame:
        """Create Step 2: Session Configuration."""
        frame = ctk.CTkFrame(self.content_frame)

        # Step title
        title = ctk.CTkLabel(
            frame,
            text="Step 2: Session Configuration",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # This will be dynamically populated based on Step 1 selections
        self.session_config_container = ctk.CTkFrame(frame)
        self.session_config_container.pack(fill="both", expand=True, padx=20, pady=10)

        return frame

    def create_step3_frame(self) -> ctk.CTkFrame:
        """Create Step 3: Review & Create."""
        frame = ctk.CTkFrame(self.content_frame)

        # Step title
        title = ctk.CTkLabel(
            frame,
            text="Step 3: Review & Create",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Review container
        self.review_container = ctk.CTkScrollableFrame(frame, height=400)
        self.review_container.pack(fill="both", expand=True, padx=40, pady=20)

        return frame

    def generate_code(self):
        """Generate a random experiment code."""
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.code_var.set(code)

    def on_session_count_changed(self):
        """Handle session count change."""
        # This will affect Step 2 layout
        pass

    def validate_step1(self) -> tuple[bool, str]:
        """Validate Step 1 inputs."""
        errors = []

        # Check name
        name = self.name_var.get().strip()
        if not name:
            errors.append("Experiment name is required")

        # Check code uniqueness if provided
        code = self.code_var.get().strip()
        if code:
            existing = self.db_manager.get_experiment_by_code(code)
            if existing:
                errors.append("Experiment code already exists")

        if errors:
            return False, "\n".join(errors)

        return True, ""

    def validate_step2(self) -> tuple[bool, str]:
        """Validate Step 2 session configuration."""
        errors = []

        # Check that all sessions have tasks
        for session_num in range(1, self.sessions_var.get() + 1):
            session_key = str(session_num)
            if session_key not in self.experiment_config['sessions']:
                errors.append(f"Session {session_num} has no configuration")
                continue

            session_tasks = self.experiment_config['sessions'][session_key].get('tasks', [])
            if not session_tasks:
                errors.append(f"Session {session_num} must have at least one task")
            elif len(session_tasks) != self.tasks_var.get():
                errors.append(f"Session {session_num} must have exactly {self.tasks_var.get()} tasks")

        # Check for duplicate tasks across sessions
        all_tasks = []
        for session_config in self.experiment_config['sessions'].values():
            for task in session_config.get('tasks', []):
                if task['type'] in all_tasks:
                    errors.append(f"Task {TaskType.get_display_name(TaskType(task['type']))} appears in multiple sessions")
                all_tasks.append(task['type'])

        if errors:
            return False, "\n".join(errors)

        return True, ""

    def show_step(self, step: int):
        """Show the specified step."""
        # Hide all steps
        for frame in self.step_frames.values():
            frame.pack_forget()

        # Show current step
        if step in self.step_frames:
            self.step_frames[step].pack(fill="both", expand=True)

        # Update navigation buttons
        self.prev_button.configure(state="normal" if step > 1 else "disabled")

        if step == self.total_steps:
            self.next_button.pack_forget()
            self.create_button.pack(side="right", padx=5)
        else:
            self.create_button.pack_forget()
            self.next_button.pack(side="right", padx=5)

        # Update progress
        self.current_step = step
        self.update_progress_indicator()

        # Special handling for Step 2
        if step == 2:
            self.populate_session_configuration()
        elif step == 3:
            self.populate_review()

    def next_step(self):
        """Move to the next step."""
        # Validate current step
        if self.current_step == 1:
            is_valid, error_msg = self.validate_step1()
            if not is_valid:
                self.validation_label.configure(text=error_msg)
                return

            # Save Step 1 data
            self.experiment_config['name'] = self.name_var.get().strip()
            self.experiment_config['code'] = self.code_var.get().strip()
            self.experiment_config['description'] = self.desc_text.get("1.0", "end-1c").strip()
            self.experiment_config['num_sessions'] = self.sessions_var.get()
            self.experiment_config['randomize_order'] = self.randomize_var.get()

        elif self.current_step == 2:
            # Validate Step 2
            is_valid, error_msg = self.validate_step2()
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return

        # Clear validation message
        if hasattr(self, 'validation_label'):
            self.validation_label.configure(text="")

        # Move to next step
        if self.current_step < self.total_steps:
            self.show_step(self.current_step + 1)

    def previous_step(self):
        """Move to the previous step."""
        if self.current_step > 1:
            self.show_step(self.current_step - 1)

    def populate_session_configuration(self):
        """Populate Step 2 based on Step 1 selections."""
        # Clear existing content
        for widget in self.session_config_container.winfo_children():
            widget.destroy()

        # Reset task storage
        self.session_task_lists = {}
        self.session_task_items = {}

        # Create layout based on number of sessions
        num_sessions = self.sessions_var.get()
        tasks_per_session = self.tasks_var.get()
        is_random = self.randomize_var.get()

        if num_sessions == 1:
            # Single column layout
            self.create_session_config(self.session_config_container, 1, tasks_per_session, is_random)
        else:
            # Split-screen layout with tabs
            tab_view = ctk.CTkTabview(self.session_config_container)
            tab_view.pack(fill="both", expand=True)

            for i in range(1, num_sessions + 1):
                tab = tab_view.add(f"Session {i}")
                self.create_session_config(tab, i, tasks_per_session, is_random)

    def create_session_config(self, parent, session_num: int, max_tasks: int, is_random: bool):
        """Create configuration UI for a single session."""
        # Session header
        header_frame = ctk.CTkFrame(parent)
        header_frame.pack(fill="x", padx=20, pady=10)

        session_label = ctk.CTkLabel(
            header_frame,
            text=f"Session {session_num} Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        session_label.pack(side="left")

        # Instructions
        if is_random:
            instruction_text = "Tasks will be randomized for each participant. Click + to add tasks."
        else:
            instruction_text = "Tasks will appear in the order shown. Drag to reorder. Click + to add tasks."

        instruction_label = ctk.CTkLabel(
            parent,
            text=instruction_text,
            text_color="gray"
        )
        instruction_label.pack(pady=5)

        # Task list container
        task_container = ctk.CTkScrollableFrame(parent, height=300)
        task_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Store reference to container
        self.session_task_lists[session_num] = task_container

        # Initialize session in config
        session_key = str(session_num)
        if session_key not in self.experiment_config['sessions']:
            self.experiment_config['sessions'][session_key] = {
                'tasks': []
            }

        # Initialize task items storage for this session
        self.session_task_items[session_num] = []

        # Load existing tasks if any
        existing_tasks = self.experiment_config['sessions'][session_key].get('tasks', [])
        for task in existing_tasks:
            self.add_task_to_session(session_num, task['type'], task.get('config', {}))

        # Add task button
        add_frame = ctk.CTkFrame(parent)
        add_frame.pack(fill="x", padx=20, pady=10)

        # Show task count
        task_count_label = ctk.CTkLabel(
            add_frame,
            text=f"Tasks: {len(self.session_task_items.get(session_num, []))}/{max_tasks}"
        )
        task_count_label.pack(side="left", padx=10)

        # Store reference to update later
        if not hasattr(self, 'task_count_labels'):
            self.task_count_labels = {}
        self.task_count_labels[session_num] = task_count_label

        add_button = ctk.CTkButton(
            add_frame,
            text="+ Add Task",
            command=lambda: self.show_task_selection(session_num),
            width=200,
            height=50,
            state="normal" if len(self.session_task_items.get(session_num, [])) < max_tasks else "disabled"
        )
        add_button.pack(side="right", padx=10)

        # Store reference to button
        if not hasattr(self, 'add_buttons'):
            self.add_buttons = {}
        self.add_buttons[session_num] = add_button

    def show_task_selection(self, session_num: int):
        """Show task selection modal."""
        # Get already used tasks across all sessions
        used_tasks = set()
        for session_config in self.experiment_config['sessions'].values():
            for task in session_config.get('tasks', []):
                used_tasks.add(task['type'])

        # Get available tasks
        all_tasks = [task.value for task in TaskType]
        available_tasks = [task for task in all_tasks if task not in used_tasks]

        if not available_tasks:
            messagebox.showinfo("No Tasks Available", "All tasks have been assigned to sessions.")
            return

        # Create and show modal
        modal = TaskSelectionModal(
            self,
            available_tasks,
            lambda task: self.add_task_to_session(session_num, task)
        )

    def add_task_to_session(self, session_num: int, task_type: str, config: Dict = None):
        """Add a task to a session."""
        # Get container
        container = self.session_task_lists.get(session_num)
        if not container:
            return

        # Create task item
        task_item = SessionTaskItem(
            container,
            task_type,
            config or {},
            lambda t: self.configure_task(session_num, t),
            lambda t: self.remove_task_from_session(session_num, t),
            can_reorder=not self.randomize_var.get()
        )
        task_item.pack(fill="x", padx=10, pady=5)

        # Store reference
        self.session_task_items[session_num].append({
            'type': task_type,
            'widget': task_item,
            'config': config or {}
        })

        # Update experiment config
        session_key = str(session_num)
        self.experiment_config['sessions'][session_key]['tasks'].append({
            'type': task_type,
            'order': len(self.session_task_items[session_num]),
            'config': config or {}
        })

        # Update UI
        self.update_session_ui(session_num)

    def remove_task_from_session(self, session_num: int, task_type: str):
        """Remove a task from a session."""
        # Find and remove task item
        items = self.session_task_items.get(session_num, [])
        for i, item in enumerate(items):
            if item['type'] == task_type:
                # Destroy widget
                item['widget'].destroy()

                # Remove from list
                items.pop(i)

                # Update config
                session_key = str(session_num)
                tasks = self.experiment_config['sessions'][session_key]['tasks']
                self.experiment_config['sessions'][session_key]['tasks'] = [
                    t for t in tasks if t['type'] != task_type
                ]

                break

        # Update UI
        self.update_session_ui(session_num)

    def configure_task(self, session_num: int, task_type: str):
        """Open task configuration modal."""
        # Find current config
        current_config = {}
        items = self.session_task_items.get(session_num, [])
        for item in items:
            if item['type'] == task_type:
                current_config = item['config']
                break

        # Open modal
        modal = TaskConfigModal(
            self,
            task_type,
            current_config,
            lambda t, c: self.save_task_config(session_num, t, c)
        )

    def save_task_config(self, session_num: int, task_type: str, config: Dict):
        """Save task configuration."""
        # Update in storage
        items = self.session_task_items.get(session_num, [])
        for item in items:
            if item['type'] == task_type:
                item['config'] = config

                # Update widget to show customized status
                item['widget'].task_config = config
                item['widget'].destroy()

                # Recreate widget with updated config
                container = self.session_task_lists.get(session_num)
                new_item = SessionTaskItem(
                    container,
                    task_type,
                    config,
                    lambda t: self.configure_task(session_num, t),
                    lambda t: self.remove_task_from_session(session_num, t),
                    can_reorder=not self.randomize_var.get()
                )

                # Find position and insert
                for i, it in enumerate(items):
                    if it['type'] == task_type:
                        new_item.pack(fill="x", padx=10, pady=5)
                        item['widget'] = new_item
                        break

                break

        # Update config
        session_key = str(session_num)
        tasks = self.experiment_config['sessions'][session_key]['tasks']
        for task in tasks:
            if task['type'] == task_type:
                task['config'] = config
                break

    def update_session_ui(self, session_num: int):
        """Update UI elements for a session."""
        # Update task count
        current_count = len(self.session_task_items.get(session_num, []))
        max_count = self.tasks_var.get()

        if session_num in self.task_count_labels:
            self.task_count_labels[session_num].configure(
                text=f"Tasks: {current_count}/{max_count}"
            )

        # Update add button state
        if session_num in self.add_buttons:
            self.add_buttons[session_num].configure(
                state="normal" if current_count < max_count else "disabled"
            )

    def populate_review(self):
        """Populate the review step with experiment summary."""
        # Clear existing content
        for widget in self.review_container.winfo_children():
            widget.destroy()

        # Experiment details
        details_frame = ctk.CTkFrame(self.review_container)
        details_frame.pack(fill="x", padx=20, pady=10)

        details_title = ctk.CTkLabel(
            details_frame,
            text="Experiment Details",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        details_title.pack(anchor="w", pady=(10, 5))

        # Show configuration summary
        details = [
            ("Name:", self.experiment_config.get('name', 'Not set')),
            ("Code:", self.experiment_config.get('code', 'Auto-generate') or 'Auto-generate'),
            ("Description:", self.experiment_config.get('description', 'None') or 'None'),
            ("Sessions:", str(self.experiment_config.get('num_sessions', 1))),
            ("Randomize Order:", "Yes" if self.experiment_config.get('randomize_order', False) else "No")
        ]

        for label, value in details:
            row_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            label_widget = ctk.CTkLabel(
                row_frame,
                text=label,
                font=ctk.CTkFont(weight="bold"),
                width=120,
                anchor="w"
            )
            label_widget.pack(side="left")

            value_widget = ctk.CTkLabel(
                row_frame,
                text=value,
                anchor="w"
            )
            value_widget.pack(side="left", padx=10)

        # Session details
        sessions_frame = ctk.CTkFrame(self.review_container)
        sessions_frame.pack(fill="x", padx=20, pady=10)

        sessions_title = ctk.CTkLabel(
            sessions_frame,
            text="Session Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        sessions_title.pack(anchor="w", pady=(10, 5))

        # Show each session
        for session_num in range(1, self.experiment_config['num_sessions'] + 1):
            session_key = str(session_num)
            session_config = self.experiment_config['sessions'].get(session_key, {})

            # Session header
            session_header = ctk.CTkLabel(
                sessions_frame,
                text=f"Session {session_num}:",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            session_header.pack(anchor="w", pady=(10, 5))

            # Tasks in session
            tasks = session_config.get('tasks', [])
            if tasks:
                for i, task in enumerate(tasks):
                    task_name = TaskType.get_display_name(TaskType(task['type']))
                    config_status = "Customized" if task.get('config') else "Default settings"

                    task_label = ctk.CTkLabel(
                        sessions_frame,
                        text=f"  • {task_name} ({config_status})",
                        anchor="w"
                    )
                    task_label.pack(anchor="w", padx=20)
            else:
                no_tasks_label = ctk.CTkLabel(
                    sessions_frame,
                    text="  No tasks configured",
                    anchor="w",
                    text_color="red"
                )
                no_tasks_label.pack(anchor="w", padx=20)

    def save_draft(self):
        """Save current configuration as draft."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Experiment Draft"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.experiment_config, f, indent=2)
                messagebox.showinfo("Success", f"Draft saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save draft: {e}")

    def create_experiment(self):
        """Create the experiment with current configuration."""
        # Final validation
        is_valid, errors = self.experiment_manager.validate_experiment_config(self.experiment_config)

        if not is_valid:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        # Create experiment
        success, experiment_id, message = self.experiment_manager.create_experiment(
            self.experiment_config['name'],
            self.experiment_config['code'] if self.experiment_config['code'] else None,
            self.experiment_config
        )

        if success:
            messagebox.showinfo("Success", message)
            self.reset_wizard()
        else:
            messagebox.showerror("Error", message)

    def reset_wizard(self):
        """Reset the wizard to initial state."""
        self.current_step = 1
        self.experiment_config = {
            'name': '',
            'code': '',
            'description': '',
            'num_sessions': 1,
            'randomize_order': False,
            'sessions': {}
        }

        # Clear form fields
        self.name_var.set("")
        self.code_var.set("")
        self.desc_text.delete("1.0", "end")
        self.sessions_var.set(1)
        self.tasks_var.set(2)
        self.randomize_var.set(False)

        # Clear task storage
        self.task_configs = {}
        self.session_task_lists = {}
        self.session_task_items = {}

        # Show first step
        self.show_step(1)

    def on_cancel(self):
        """Handle cancel button click."""
        if messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel? All progress will be lost."):
            self.reset_wizard()