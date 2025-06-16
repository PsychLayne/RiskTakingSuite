"""
Experiment Builder UI for Risk Tasks Client - FIXED VERSION
Handles empty inputs and allows 0 session gap for immediate sessions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime, timedelta
import json
import random
import string
from typing import Dict, List, Optional, Tuple
import copy

from database.db_manager import DatabaseManager
from database.models import TaskType, Experiment, ExperimentConfig


class ExperimentBuilder(ctk.CTkFrame):
    """UI component for building and managing experiments."""

    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_experiment_id = None
        self.temp_config = {}

        # Store task instances (allows same task with different configs)
        self.task_instances = {}  # {instance_id: {task_type, display_name, config}}
        self.next_instance_id = 1

        # Setup UI
        self.setup_ui()

        # Load experiments
        self.refresh()

    def safe_get_int(self, var: tk.IntVar, default: int) -> int:
        """Safely get integer value from IntVar, returning default if empty or invalid."""
        try:
            value = var.get()
            return value if value else default
        except (tk.TclError, ValueError):
            return default

    def safe_get_string(self, var: tk.StringVar, default: str = "") -> str:
        """Safely get string value from StringVar."""
        try:
            return var.get() or default
        except tk.TclError:
            return default

    def setup_ui(self):
        """Setup the experiment builder interface."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Experiment Builder",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        # Tab 1: Experiment List
        self.list_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.list_frame, text="Experiments")
        self.create_experiment_list_tab()

        # Tab 2: Create/Edit Experiment - REDESIGNED
        self.builder_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.builder_frame, text="Builder")
        self.create_redesigned_builder_tab()

        # Tab 3: Experiment Analytics
        self.analytics_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.analytics_frame, text="Analytics")
        self.create_analytics_tab()

    def create_experiment_list_tab(self):
        """Create the experiment list tab."""
        # Controls
        controls_frame = ctk.CTkFrame(self.list_frame)
        controls_frame.pack(fill="x", padx=20, pady=10)

        new_btn = ctk.CTkButton(
            controls_frame,
            text="+ New Experiment",
            command=self.new_experiment,
            width=150
        )
        new_btn.pack(side="left", padx=5)

        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh",
            command=self.refresh_experiments,
            width=100
        )
        refresh_btn.pack(side="right", padx=5)

        # Experiment list
        list_container = ctk.CTkFrame(self.list_frame)
        list_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Create treeview
        columns = ("Code", "Name", "Participants", "Status", "Created")
        self.exp_tree = ttk.Treeview(
            list_container,
            columns=columns,
            show="headings",
            height=15
        )

        # Configure columns
        self.exp_tree.heading("Code", text="Code")
        self.exp_tree.heading("Name", text="Name")
        self.exp_tree.heading("Participants", text="Participants")
        self.exp_tree.heading("Status", text="Status")
        self.exp_tree.heading("Created", text="Created")

        self.exp_tree.column("Code", width=100)
        self.exp_tree.column("Name", width=250)
        self.exp_tree.column("Participants", width=100)
        self.exp_tree.column("Status", width=100)
        self.exp_tree.column("Created", width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=self.exp_tree.yview
        )
        self.exp_tree.configure(yscrollcommand=scrollbar.set)

        self.exp_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind selection
        self.exp_tree.bind("<<TreeviewSelect>>", self.on_experiment_select)

        # Action buttons
        action_frame = ctk.CTkFrame(self.list_frame)
        action_frame.pack(fill="x", padx=20, pady=10)

        self.edit_btn = ctk.CTkButton(
            action_frame,
            text="Edit",
            command=self.edit_experiment,
            state="disabled",
            width=100
        )
        self.edit_btn.pack(side="left", padx=5)

        self.duplicate_btn = ctk.CTkButton(
            action_frame,
            text="Duplicate",
            command=self.duplicate_experiment,
            state="disabled",
            width=100
        )
        self.duplicate_btn.pack(side="left", padx=5)

        self.toggle_btn = ctk.CTkButton(
            action_frame,
            text="Toggle Active",
            command=self.toggle_active,
            state="disabled",
            width=120
        )
        self.toggle_btn.pack(side="left", padx=5)

        self.view_stats_btn = ctk.CTkButton(
            action_frame,
            text="View Stats",
            command=self.view_statistics,
            state="disabled",
            width=100
        )
        self.view_stats_btn.pack(side="left", padx=5)

    def create_redesigned_builder_tab(self):
        """Create the redesigned experiment builder tab with improved layout."""
        # Create main container with two columns
        main_container = ctk.CTkFrame(self.builder_frame)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Left column - Basic info and settings
        left_frame = ctk.CTkFrame(main_container, width=400)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Create scrollable frame for left column
        left_scroll = ctk.CTkScrollableFrame(left_frame)
        left_scroll.pack(fill="both", expand=True)

        # Right column - Task configuration
        right_frame = ctk.CTkFrame(main_container, width=500)
        right_frame.pack(side="right", fill="both", expand=True)

        # Basic Information Section
        self.create_basic_info_section_redesigned(left_scroll)

        # Experiment Parameters Section
        self.create_parameters_section_redesigned(left_scroll)

        # Task Configuration Section - REDESIGNED
        self.create_task_config_section_redesigned(right_frame)

        # Save/Cancel buttons at bottom
        button_frame = ctk.CTkFrame(self.builder_frame)
        button_frame.pack(fill="x", padx=20, pady=20)

        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save Experiment",
            command=self.save_experiment,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel_edit,
            width=150,
            height=40,
            fg_color="gray"
        )
        cancel_btn.pack(side="left", padx=10)

        preview_btn = ctk.CTkButton(
            button_frame,
            text="👁️ Preview Config",
            command=self.preview_config,
            width=150,
            height=40,
            fg_color="blue"
        )
        preview_btn.pack(side="right", padx=10)

    def create_basic_info_section_redesigned(self, parent):
        """Create basic information section with cleaner layout."""
        # Section header with icon
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        section_label = ctk.CTkLabel(
            header_frame,
            text="📋 Basic Information",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_label.pack(side="left")

        info_frame = ctk.CTkFrame(parent)
        info_frame.pack(fill="x", pady=10)

        # Two-column layout for basic fields
        left_col = ctk.CTkFrame(info_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=10)

        right_col = ctk.CTkFrame(info_frame, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=10)

        # Experiment code (left column)
        code_label = ctk.CTkLabel(left_col, text="Experiment Code", anchor="w")
        code_label.pack(fill="x", pady=(5, 2))

        code_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        code_frame.pack(fill="x")

        self.code_var = tk.StringVar()
        self.code_entry = ctk.CTkEntry(
            code_frame,
            textvariable=self.code_var,
            placeholder_text="e.g., EXP001"
        )
        self.code_entry.pack(side="left", fill="x", expand=True)

        generate_btn = ctk.CTkButton(
            code_frame,
            text="🎲",
            command=self.generate_experiment_code,
            width=30,
            height=28
        )
        generate_btn.pack(side="right", padx=(5, 0))

        # Max participants (right column)
        max_label = ctk.CTkLabel(right_col, text="Max Participants", anchor="w")
        max_label.pack(fill="x", pady=(5, 2))

        self.max_participants_var = tk.StringVar()
        self.max_participants_entry = ctk.CTkEntry(
            right_col,
            textvariable=self.max_participants_var,
            placeholder_text="Leave empty for unlimited"
        )
        self.max_participants_entry.pack(fill="x")

        # Name (full width)
        name_label = ctk.CTkLabel(info_frame, text="Experiment Name", anchor="w")
        name_label.pack(fill="x", padx=10, pady=(15, 2))

        self.name_var = tk.StringVar()
        name_entry = ctk.CTkEntry(
            info_frame,
            textvariable=self.name_var,
            placeholder_text="Give your experiment a descriptive name"
        )
        name_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Description
        desc_label = ctk.CTkLabel(info_frame, text="Description", anchor="w")
        desc_label.pack(fill="x", padx=10, pady=(5, 2))

        self.desc_text = ctk.CTkTextbox(info_frame, height=80)
        self.desc_text.pack(fill="x", padx=10, pady=(0, 10))

        # Date settings in a collapsible frame
        date_toggle = ctk.CTkButton(
            parent,
            text="📅 Date Settings (Optional) ▼",
            command=lambda: self.toggle_frame(date_frame),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover=False,
            anchor="w"
        )
        date_toggle.pack(fill="x", pady=5)

        self.date_frame = date_frame = ctk.CTkFrame(parent)
        date_frame.pack(fill="x", pady=5)
        date_frame.pack_forget()  # Initially hidden

        # Date fields
        dates_container = ctk.CTkFrame(date_frame, fg_color="transparent")
        dates_container.pack(fill="x", padx=20, pady=10)

        start_label = ctk.CTkLabel(dates_container, text="Start Date:", width=100, anchor="w")
        start_label.grid(row=0, column=0, sticky="w", pady=5)

        self.start_date_var = tk.StringVar()
        start_entry = ctk.CTkEntry(
            dates_container,
            textvariable=self.start_date_var,
            placeholder_text="YYYY-MM-DD"
        )
        start_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        end_label = ctk.CTkLabel(dates_container, text="End Date:", width=100, anchor="w")
        end_label.grid(row=1, column=0, sticky="w", pady=5)

        self.end_date_var = tk.StringVar()
        end_entry = ctk.CTkEntry(
            dates_container,
            textvariable=self.end_date_var,
            placeholder_text="YYYY-MM-DD"
        )
        end_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        dates_container.columnconfigure(1, weight=1)

    def create_parameters_section_redesigned(self, parent):
        """Create experiment parameters section with cleaner layout and validation."""
        # Section header
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10))

        section_label = ctk.CTkLabel(
            header_frame,
            text="⚙️ Experiment Parameters",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_label.pack(side="left")

        params_frame = ctk.CTkFrame(parent)
        params_frame.pack(fill="x", pady=10)

        # Create parameter cards
        params_grid = ctk.CTkFrame(params_frame, fg_color="transparent")
        params_grid.pack(fill="x", padx=20, pady=10)

        # Trials per task card
        trials_card = ctk.CTkFrame(params_grid)
        trials_card.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(trials_card, text="Trials per Task", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        # Use StringVar instead of IntVar for better empty handling
        self.trials_var = tk.StringVar(value="30")
        trials_entry = ctk.CTkEntry(trials_card, textvariable=self.trials_var, width=100)
        trials_entry.pack(pady=(0, 5))

        # Add validation
        trials_entry.bind('<FocusOut>', lambda e: self.validate_int_entry_string(self.trials_var, "30", 1, 100, "Trials per task"))

        ctk.CTkLabel(trials_card, text="(1-100)", font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(0, 10))

        # Session gap card
        gap_card = ctk.CTkFrame(params_grid)
        gap_card.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(gap_card, text="Session Gap (days)", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        self.gap_var = tk.StringVar(value="14")
        gap_entry = ctk.CTkEntry(gap_card, textvariable=self.gap_var, width=100)
        gap_entry.pack(pady=(0, 5))

        # Add validation - now allows 0 for immediate sessions
        gap_entry.bind('<FocusOut>', lambda e: self.validate_int_entry_string(self.gap_var, "14", 0, 365, "Session gap"))

        ctk.CTkLabel(gap_card, text="(0 = immediate)", font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(0, 10))

        # Tasks per session card
        tasks_card = ctk.CTkFrame(params_grid)
        tasks_card.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(tasks_card, text="Tasks per Session", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        tasks_frame = ctk.CTkFrame(tasks_card, fg_color="transparent")
        tasks_frame.pack(pady=(0, 10))

        self.tasks_per_session_var = tk.IntVar(value=2)

        # Radio buttons for common choices
        ctk.CTkRadioButton(
            tasks_frame,
            text="1 task",
            variable=self.tasks_per_session_var,
            value=1,
            command=self.on_tasks_per_session_change
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            tasks_frame,
            text="2 tasks",
            variable=self.tasks_per_session_var,
            value=2,
            command=self.on_tasks_per_session_change
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            tasks_frame,
            text="3 tasks",
            variable=self.tasks_per_session_var,
            value=3,
            command=self.on_tasks_per_session_change
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            tasks_frame,
            text="4 tasks",
            variable=self.tasks_per_session_var,
            value=4,
            command=self.on_tasks_per_session_change
        ).pack(side="left", padx=10)

        params_grid.columnconfigure(0, weight=1)
        params_grid.columnconfigure(1, weight=1)

    def validate_int_entry_string(self, var: tk.StringVar, default: str, min_val: int, max_val: int, field_name: str):
        """Validate and fix integer entry fields using StringVar."""
        try:
            value_str = var.get().strip()
            if not value_str:  # Empty string
                var.set(default)
                return

            value = int(value_str)
            if value < min_val:
                var.set(str(min_val))
                raise ValueError(f"Value too low")
            elif value > max_val:
                var.set(str(max_val))
                raise ValueError(f"Value too high")

        except ValueError as e:
            # If not a valid integer or out of range
            if "invalid literal" in str(e):
                var.set(default)

            # Show friendly message
            if field_name == "Session gap" and min_val == 0:
                messagebox.showinfo(
                    "Input Corrected",
                    f"{field_name} must be between {min_val} and {max_val} days.\n"
                    f"Use 0 to allow immediate sessions.\n"
                    f"Value has been set to {var.get()}."
                )
            else:
                messagebox.showinfo(
                    "Input Corrected",
                    f"{field_name} must be between {min_val} and {max_val}.\n"
                    f"Value has been set to {var.get()}."
                )

    def validate_int_entry(self, var: tk.IntVar, default: int, min_val: int, max_val: int, field_name: str):
        """Validate and fix integer entry fields."""
        try:
            value = var.get()
            if value < min_val or value > max_val:
                raise ValueError()
        except (tk.TclError, ValueError):
            # If empty or invalid, set to default
            try:
                current = var.get()
                if current < min_val:
                    var.set(min_val)
                elif current > max_val:
                    var.set(max_val)
            except:
                var.set(default)

            # Show friendly message
            if field_name == "Session gap" and min_val == 0:
                messagebox.showinfo(
                    "Input Corrected",
                    f"{field_name} must be between {min_val} and {max_val} days.\n"
                    f"Use 0 to allow immediate sessions.\n"
                    f"Value has been set to {var.get()}."
                )
            else:
                messagebox.showinfo(
                    "Input Corrected",
                    f"{field_name} must be between {min_val} and {max_val}.\n"
                    f"Value has been set to {var.get()}."
                )

    def create_task_config_section_redesigned(self, parent):
        """Create redesigned task configuration section that supports task instances."""
        # Section header
        header_frame = ctk.CTkFrame(parent)
        header_frame.pack(fill="x", padx=20, pady=(10, 20))

        section_label = ctk.CTkLabel(
            header_frame,
            text="🎮 Task Configuration",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        section_label.pack(side="left")

        # Add help text
        help_label = ctk.CTkLabel(
            header_frame,
            text="Add tasks and configure their parameters",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        help_label.pack(side="left", padx=(20, 0))

        # Task selection frame
        selection_frame = ctk.CTkFrame(parent)
        selection_frame.pack(fill="x", padx=20, pady=10)

        selection_label = ctk.CTkLabel(
            selection_frame,
            text="Add a task to your experiment:",
            font=ctk.CTkFont(size=14)
        )
        selection_label.pack(pady=(10, 5))

        # Task type dropdown
        task_options_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        task_options_frame.pack(fill="x", pady=10)

        self.task_type_var = tk.StringVar(value="Select a task...")
        task_menu = ctk.CTkOptionMenu(
            task_options_frame,
            variable=self.task_type_var,
            values=[TaskType.get_display_name(t) for t in TaskType],
            width=200
        )
        task_menu.pack(side="left", padx=10)

        add_task_btn = ctk.CTkButton(
            task_options_frame,
            text="➕ Add Task",
            command=self.add_task_instance,
            width=120,
            height=35,
            fg_color="green"
        )
        add_task_btn.pack(side="left", padx=10)

        # Task instances list
        list_label = ctk.CTkLabel(
            parent,
            text="Tasks in this experiment:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        list_label.pack(fill="x", padx=20, pady=(20, 5))

        # Scrollable frame for task instances
        self.task_list_frame = ctk.CTkScrollableFrame(parent, height=300)
        self.task_list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Session assignment section
        self.create_session_assignment_section(parent)

    def create_session_assignment_section(self, parent):
        """Create section for assigning tasks to sessions."""
        # Section header
        assign_frame = ctk.CTkFrame(parent)
        assign_frame.pack(fill="x", padx=20, pady=(20, 10))

        assign_label = ctk.CTkLabel(
            assign_frame,
            text="📅 Session Assignment",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        assign_label.pack(side="left")

        # Assignment type selection
        self.sequence_type_var = tk.StringVar(value="random")

        type_frame = ctk.CTkFrame(parent)
        type_frame.pack(fill="x", padx=20, pady=10)

        random_radio = ctk.CTkRadioButton(
            type_frame,
            text="Random assignment (balanced)",
            variable=self.sequence_type_var,
            value="random",
            command=self.on_sequence_type_change
        )
        random_radio.pack(side="left", padx=20)

        fixed_radio = ctk.CTkRadioButton(
            type_frame,
            text="Fixed sequence",
            variable=self.sequence_type_var,
            value="fixed",
            command=self.on_sequence_type_change
        )
        fixed_radio.pack(side="left", padx=20)

        # Fixed sequence configuration
        self.fixed_sequence_frame = ctk.CTkFrame(parent)
        self.sequence_dropdowns_frame = ctk.CTkFrame(self.fixed_sequence_frame)
        self.sequence_dropdowns_frame.pack(fill="x", padx=20, pady=10)

    def add_task_instance(self):
        """Add a new task instance to the experiment."""
        task_display = self.task_type_var.get()
        if task_display == "Select a task...":
            messagebox.showwarning("No Selection", "Please select a task type first")
            return

        # Find the task type
        task_type = None
        for t in TaskType:
            if TaskType.get_display_name(t) == task_display:
                task_type = t.value
                break

        if not task_type:
            return

        # Create unique instance ID
        instance_id = f"task_{self.next_instance_id}"
        self.next_instance_id += 1

        # Check if this is a duplicate task type
        existing_count = sum(1 for inst in self.task_instances.values()
                             if inst['task_type'] == task_type)

        if existing_count > 0:
            # Create a unique display name for the duplicate
            display_name = f"{task_display} (Version {existing_count + 1})"
        else:
            display_name = task_display

        # Create task instance
        self.task_instances[instance_id] = {
            'task_type': task_type,
            'display_name': display_name,
            'config': {}  # Will be populated when user configures
        }

        # Create UI for this instance
        self.create_task_instance_ui(instance_id)

        # Update sequence dropdowns if in fixed mode
        if self.sequence_type_var.get() == "fixed":
            self.update_sequence_inputs()

    def create_task_instance_ui(self, instance_id):
        """Create UI for a task instance in the list."""
        instance = self.task_instances[instance_id]

        # Create card for this task instance
        card = ctk.CTkFrame(self.task_list_frame)
        card.pack(fill="x", pady=5)

        # Header with task name and actions
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)

        # Task icon and name
        task_label = ctk.CTkLabel(
            header_frame,
            text=f"🎯 {instance['display_name']}",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        task_label.pack(side="left", fill="x", expand=True)

        # Configure button
        config_btn = ctk.CTkButton(
            header_frame,
            text="⚙️ Configure",
            command=lambda: self.configure_task_instance(instance_id),
            width=100,
            height=30,
            fg_color="blue"
        )
        config_btn.pack(side="left", padx=5)

        # Remove button
        remove_btn = ctk.CTkButton(
            header_frame,
            text="❌ Remove",
            command=lambda: self.remove_task_instance(instance_id),
            width=80,
            height=30,
            fg_color="red"
        )
        remove_btn.pack(side="left", padx=5)

        # Status indicator
        if instance['config']:
            status_text = "✅ Configured"
            status_color = "green"
        else:
            status_text = "⚠️ Not configured (using defaults)"
            status_color = "orange"

        status_label = ctk.CTkLabel(
            card,
            text=status_text,
            font=ctk.CTkFont(size=12),
            text_color=status_color
        )
        status_label.pack(fill="x", padx=10, pady=(0, 10))

        # Store the card reference
        instance['ui_card'] = card

    def configure_task_instance(self, instance_id):
        """Show configuration dialog for a specific task instance."""
        instance = self.task_instances[instance_id]
        task_type = instance['task_type']

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Configure {instance['display_name']}")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()

        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text=f"Configure {instance['display_name']}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)

        info_label = ctk.CTkLabel(
            dialog,
            text="Leave fields empty to use default values",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_label.pack()

        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(dialog, width=450, height=400)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Store override widgets
        override_widgets = {}

        # Task-specific configurations
        if task_type == 'bart':
            self._create_bart_overrides(scroll_frame, override_widgets)
        elif task_type == 'ice_fishing':
            self._create_ice_fishing_overrides(scroll_frame, override_widgets)
        elif task_type == 'mountain_mining':
            self._create_mining_overrides(scroll_frame, override_widgets)
        elif task_type == 'spinning_bottle':
            self._create_stb_overrides(scroll_frame, override_widgets)

        # Load existing config if any
        if instance['config']:
            self._load_instance_config(instance['config'], override_widgets, task_type)

        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", pady=20)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=lambda: self.save_instance_config(dialog, instance_id, override_widgets),
            width=100
        )
        save_btn.pack(side="left", padx=20)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            fg_color="gray"
        )
        cancel_btn.pack(side="left")

    def _load_instance_config(self, config, widgets, task_type):
        """Load existing configuration into widgets."""
        if task_type == 'bart':
            if 'max_pumps' in config:
                widgets['max_pumps'].set(str(config['max_pumps']))
            if 'points_per_pump' in config:
                widgets['points_per_pump'].set(str(config['points_per_pump']))
            if 'explosion_range' in config:
                widgets['explosion_min'].set(str(config['explosion_range'][0]))
                widgets['explosion_max'].set(str(config['explosion_range'][1]))
            if 'keyboard_input_mode' in config:
                widgets['keyboard_input_mode'].set(config['keyboard_input_mode'])
            if 'balloon_color' in config:
                widgets['balloon_color'].set(config['balloon_color'])
            if 'random_colors' in config:
                widgets['random_colors'].set(config['random_colors'])
        # Similar for other task types...

    def save_instance_config(self, dialog, instance_id, widgets):
        """Save configuration for a task instance."""
        instance = self.task_instances[instance_id]
        task_type = instance['task_type']

        # Build config based on task type
        config = {}

        if task_type == 'bart':
            # Process BART-specific config
            if widgets['max_pumps'].get().strip():
                try:
                    config['max_pumps'] = int(widgets['max_pumps'].get())
                except ValueError:
                    messagebox.showerror("Invalid Value", "Max pumps must be a number")
                    return

            if widgets['points_per_pump'].get().strip():
                try:
                    config['points_per_pump'] = int(widgets['points_per_pump'].get())
                except ValueError:
                    messagebox.showerror("Invalid Value", "Points per pump must be a number")
                    return

            if widgets['explosion_min'].get().strip() and widgets['explosion_max'].get().strip():
                try:
                    min_val = int(widgets['explosion_min'].get())
                    max_val = int(widgets['explosion_max'].get())
                    if min_val >= max_val:
                        messagebox.showerror("Invalid Value", "Min explosion must be less than max")
                        return
                    config['explosion_range'] = [min_val, max_val]
                except ValueError:
                    messagebox.showerror("Invalid Value", "Explosion range must be numbers")
                    return

            config['keyboard_input_mode'] = widgets['keyboard_input_mode'].get()
            if widgets['balloon_color'].get():
                config['balloon_color'] = widgets['balloon_color'].get()
            config['random_colors'] = widgets['random_colors'].get()

        elif task_type == 'ice_fishing':
            if widgets['max_fish'].get().strip():
                try:
                    config['max_fish'] = int(widgets['max_fish'].get())
                except ValueError:
                    messagebox.showerror("Invalid Value", "Max fish must be a number")
                    return

            if widgets['points_per_fish'].get().strip():
                try:
                    config['points_per_fish'] = int(widgets['points_per_fish'].get())
                except ValueError:
                    messagebox.showerror("Invalid Value", "Points per fish must be a number")
                    return

        # Similar for other task types...

        # Save config to instance
        instance['config'] = config

        # Update UI to show configured status
        if instance.get('ui_card'):
            # Find and update status label
            for widget in instance['ui_card'].winfo_children():
                if isinstance(widget, ctk.CTkLabel) and ("✅" in widget.cget("text") or "⚠️" in widget.cget("text")):
                    widget.configure(text="✅ Configured", text_color="green")
                    break

        dialog.destroy()
        messagebox.showinfo("Success", f"{instance['display_name']} configuration saved!")

    def remove_task_instance(self, instance_id):
        """Remove a task instance from the experiment."""
        if instance_id in self.task_instances:
            # Confirm removal
            instance = self.task_instances[instance_id]
            result = messagebox.askyesno(
                "Confirm Removal",
                f"Remove {instance['display_name']} from the experiment?"
            )

            if result:
                # Remove UI
                if 'ui_card' in instance and instance['ui_card']:
                    instance['ui_card'].destroy()

                # Remove from dict
                del self.task_instances[instance_id]

                # Update sequence dropdowns if needed
                if self.sequence_type_var.get() == "fixed":
                    self.update_sequence_inputs()

    def on_tasks_per_session_change(self):
        """Handle change in tasks per session."""
        # Update sequence inputs if in fixed mode
        if self.sequence_type_var.get() == "fixed":
            self.update_sequence_inputs()

    def on_sequence_type_change(self):
        """Handle sequence type change."""
        if self.sequence_type_var.get() == "fixed":
            self.fixed_sequence_frame.pack(fill="x", padx=20, pady=10)
            self.update_sequence_inputs()
        else:
            self.fixed_sequence_frame.pack_forget()

    def update_sequence_inputs(self):
        """Update fixed sequence input fields based on task instances and tasks per session."""
        # Clear existing inputs
        for widget in self.sequence_dropdowns_frame.winfo_children():
            widget.destroy()

        if not self.task_instances:
            info_label = ctk.CTkLabel(
                self.sequence_dropdowns_frame,
                text="Add tasks first to configure sequences",
                text_color="gray"
            )
            info_label.pack(pady=20)
            return

        # Get task instance names
        task_options = [inst['display_name'] for inst in self.task_instances.values()]
        tasks_per_session = self.safe_get_int(self.tasks_per_session_var, 2)

        # Create dropdowns for 2 sessions
        self.sequence_vars = {}

        for session in range(1, 3):  # Assuming 2 sessions
            session_label = ctk.CTkLabel(
                self.sequence_dropdowns_frame,
                text=f"Session {session}:",
                font=ctk.CTkFont(weight="bold")
            )
            session_label.grid(row=session - 1, column=0, sticky="w", pady=10)

            self.sequence_vars[session] = []

            for task_num in range(tasks_per_session):
                task_var = tk.StringVar()
                self.sequence_vars[session].append(task_var)

                task_menu = ctk.CTkOptionMenu(
                    self.sequence_dropdowns_frame,
                    variable=task_var,
                    values=task_options,
                    width=200
                )
                task_menu.grid(row=session - 1, column=task_num + 1, padx=5, pady=5)

                # If only one task per session, pre-select if only one task available
                if tasks_per_session == 1 and len(task_options) == 1:
                    task_var.set(task_options[0])

    def toggle_frame(self, frame):
        """Toggle visibility of a frame."""
        if frame.winfo_viewable():
            frame.pack_forget()
        else:
            frame.pack(fill="x", pady=5)

    def preview_config(self):
        """Preview the experiment configuration."""
        try:
            config = self.build_experiment_config()

            # Create preview window
            preview_window = ctk.CTkToplevel(self)
            preview_window.title("Configuration Preview")
            preview_window.geometry("600x500")

            # Title
            title_label = ctk.CTkLabel(
                preview_window,
                text="Experiment Configuration Preview",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=20)

            # Config display
            text_widget = ctk.CTkTextbox(preview_window, height=400)
            text_widget.pack(fill="both", expand=True, padx=20, pady=10)

            # Format config as JSON
            config_text = json.dumps(config, indent=2)
            text_widget.insert("1.0", config_text)
            text_widget.configure(state="disabled")

            # Close button
            close_btn = ctk.CTkButton(
                preview_window,
                text="Close",
                command=preview_window.destroy
            )
            close_btn.pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate preview: {e}")

    def build_experiment_config(self) -> Dict:
        """Build the experiment configuration with task instances."""
        # Validate and get values with defaults - using safe methods
        try:
            trials_str = self.trials_var.get().strip()
            trials_per_task = int(trials_str) if trials_str else 30
            if trials_per_task < 1:
                trials_per_task = 30
        except (ValueError, tk.TclError):
            trials_per_task = 30

        try:
            gap_str = self.gap_var.get().strip()
            session_gap_days = int(gap_str) if gap_str else 14
            if session_gap_days < 0:
                session_gap_days = 14
        except (ValueError, tk.TclError):
            session_gap_days = 14

        tasks_per_session = self.safe_get_int(self.tasks_per_session_var, 2)

        # Get task instances and their configs
        task_configs = {}
        enabled_tasks = []
        unique_task_types = set()

        for instance_id, instance in self.task_instances.items():
            task_type = instance['task_type']
            unique_task_types.add(task_type)

            # Add to task configs with instance ID as key
            task_configs[instance_id] = {
                'task_type': task_type,
                'display_name': instance['display_name'],
                **instance['config']  # Merge with custom config
            }
            enabled_tasks.append(instance_id)

        # Also create a standard tasks section for compatibility
        tasks_section = {}
        for task_type in unique_task_types:
            # Find the first instance of this task type and use its config
            for instance_id, instance in self.task_instances.items():
                if instance['task_type'] == task_type:
                    tasks_section[task_type] = instance['config']
                    break

        config = {
            "experiment": {
                "total_trials_per_task": trials_per_task,
                "session_gap_days": session_gap_days,
                "tasks_per_session": tasks_per_session,
                "enabled_task_instances": enabled_tasks,
                "enabled_tasks": list(unique_task_types),  # Add this for compatibility
                "task_sequence": {
                    "type": self.sequence_type_var.get()
                }
            },
            "display": {
                "fullscreen": True,
                "resolution": "1920x1080"
            },
            "data": {
                "auto_backup": True,
                "backup_interval_hours": 24
            },
            "task_instances": task_configs,
            "tasks": tasks_section  # Add standard tasks section
        }

        # Add fixed sequences if applicable
        if self.sequence_type_var.get() == "fixed" and hasattr(self, 'sequence_vars'):
            sequences = {}
            for session, vars in self.sequence_vars.items():
                # Map display names back to instance IDs
                task_sequence = []
                for var in vars:
                    display_name = var.get()
                    # Find instance ID by display name
                    for inst_id, inst in self.task_instances.items():
                        if inst['display_name'] == display_name:
                            task_sequence.append(inst_id)
                            break
                sequences[str(session)] = task_sequence

            config["experiment"]["task_sequence"]["sequences"] = sequences

        return config

    def save_experiment(self):
        """Save the current experiment with validation."""
        # Validate form
        if not self.code_var.get().strip():
            messagebox.showerror("Error", "Experiment code is required")
            return

        if not self.name_var.get().strip():
            messagebox.showerror("Error", "Experiment name is required")
            return

        if not self.task_instances:
            messagebox.showerror("Error", "At least one task must be added to the experiment")
            return

        # Check if we have enough tasks for the sessions
        tasks_per_session = self.safe_get_int(self.tasks_per_session_var, 2)
        if len(self.task_instances) < tasks_per_session:
            messagebox.showerror(
                "Error",
                f"You need at least {tasks_per_session} task(s) for your session configuration"
            )
            return

        # Validate numeric fields using safe methods
        try:
            # Force validation
            self.validate_int_entry_string(self.trials_var, "30", 1, 100, "Trials per task")
            self.validate_int_entry_string(self.gap_var, "14", 0, 365, "Session gap")
        except:
            return

        # Build configuration
        config = self.build_experiment_config()

        # Parse dates
        start_date = None
        end_date = None

        if self.start_date_var.get():
            try:
                start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid start date format. Use YYYY-MM-DD")
                return

        if self.end_date_var.get():
            try:
                end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid end date format. Use YYYY-MM-DD")
                return

        # Parse max participants
        max_participants = None
        max_part_str = self.max_participants_var.get().strip()
        if max_part_str:
            try:
                max_participants = int(max_part_str)
                if max_participants < 1:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error", "Max participants must be a positive number")
                return

        try:
            if self.current_experiment_id:
                # Update existing
                self.db_manager.update_experiment(
                    self.current_experiment_id,
                    name=self.name_var.get().strip(),
                    description=self.desc_text.get("1.0", "end-1c").strip(),
                    config=config,
                    start_date=start_date,
                    end_date=end_date,
                    max_participants=max_participants
                )
                messagebox.showinfo("Success", "Experiment updated successfully!")
            else:
                # Create new
                self.db_manager.create_experiment(
                    experiment_code=self.code_var.get().strip(),
                    name=self.name_var.get().strip(),
                    config=config,
                    description=self.desc_text.get("1.0", "end-1c").strip(),
                    start_date=start_date,
                    end_date=end_date,
                    max_participants=max_participants,
                    created_by="Admin"
                )
                messagebox.showinfo("Success", "Experiment created successfully!")

            # Refresh and go back to list
            self.refresh()
            self.notebook.select(0)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save experiment: {e}")

    def load_experiment_to_form(self, experiment: Dict):
        """Load experiment data into the form."""
        # Basic info
        self.code_var.set(experiment['experiment_code'])
        self.code_entry.configure(state="disabled")  # Can't change code after creation
        self.name_var.set(experiment['name'])
        self.desc_text.delete("1.0", "end")
        if experiment['description']:
            self.desc_text.insert("1.0", experiment['description'])

        # Dates
        if experiment['start_date']:
            start_date = datetime.fromisoformat(experiment['start_date'])
            self.start_date_var.set(start_date.strftime("%Y-%m-%d"))
        if experiment['end_date']:
            end_date = datetime.fromisoformat(experiment['end_date'])
            self.end_date_var.set(end_date.strftime("%Y-%m-%d"))

        # Max participants
        if experiment['max_participants']:
            self.max_participants_var.set(str(experiment['max_participants']))

        # Load config
        config = experiment['config']
        exp_config = config.get('experiment', {})

        # Parameters - convert to strings for StringVar
        self.trials_var.set(str(exp_config.get('total_trials_per_task', 30)))
        self.gap_var.set(str(exp_config.get('session_gap_days', 14)))
        self.tasks_per_session_var.set(exp_config.get('tasks_per_session', 2))

        # Clear existing task instances
        self.task_instances = {}
        self.next_instance_id = 1
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()

        # Load task instances if new format
        if 'task_instances' in config:
            # New format with instances
            for instance_id, instance_config in config['task_instances'].items():
                self.task_instances[instance_id] = {
                    'task_type': instance_config['task_type'],
                    'display_name': instance_config.get('display_name',
                                                        TaskType.get_display_name(
                                                            TaskType(instance_config['task_type']))),
                    'config': {k: v for k, v in instance_config.items()
                               if k not in ['task_type', 'display_name']}
                }
                self.create_task_instance_ui(instance_id)
        else:
            # Legacy format - convert to instances
            # This maintains backward compatibility
            enabled_tasks = exp_config.get('enabled_tasks', [])
            task_configs = config.get('tasks', {})

            for task_type in enabled_tasks:
                instance_id = f"task_{self.next_instance_id}"
                self.next_instance_id += 1

                self.task_instances[instance_id] = {
                    'task_type': task_type,
                    'display_name': TaskType.get_display_name(TaskType(task_type)),
                    'config': task_configs.get(task_type, {})
                }
                self.create_task_instance_ui(instance_id)

        # Sequence type
        sequence_config = exp_config.get('task_sequence', {})
        self.sequence_type_var.set(sequence_config.get('type', 'random'))
        self.on_sequence_type_change()

        # Load fixed sequences if applicable
        if sequence_config.get('type') == 'fixed' and 'sequences' in sequence_config:
            # Update the dropdowns with saved sequences
            self.update_sequence_inputs()
            # TODO: Populate the sequence dropdowns with saved values

    def clear_builder_form(self):
        """Clear the builder form."""
        self.code_var.set("")
        self.code_entry.configure(state="normal")
        self.name_var.set("")
        self.desc_text.delete("1.0", "end")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.max_participants_var.set("")

        # Reset to defaults as strings
        self.trials_var.set("30")
        self.gap_var.set("14")
        self.tasks_per_session_var.set(2)

        # Clear task instances
        self.task_instances = {}
        self.next_instance_id = 1
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()

        self.sequence_type_var.set("random")
        self.on_sequence_type_change()

    # ... (rest of the methods remain the same) ...

    def _create_bart_overrides(self, parent, widgets):
        """Create BART-specific override controls."""
        # Max pumps
        max_pumps_frame = ctk.CTkFrame(parent)
        max_pumps_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(max_pumps_frame, text="Max pumps:", width=150, anchor="w").pack(side="left")
        max_pumps_var = tk.StringVar()
        widgets['max_pumps'] = max_pumps_var
        ctk.CTkEntry(max_pumps_frame, textvariable=max_pumps_var, width=100,
                     placeholder_text="e.g., 48").pack(side="left")

        # Points per pump
        points_frame = ctk.CTkFrame(parent)
        points_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(points_frame, text="Points per pump:", width=150, anchor="w").pack(side="left")
        points_var = tk.StringVar()
        widgets['points_per_pump'] = points_var
        ctk.CTkEntry(points_frame, textvariable=points_var, width=100,
                     placeholder_text="e.g., 5").pack(side="left")

        # Explosion range
        range_frame = ctk.CTkFrame(parent)
        range_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(range_frame, text="Explosion range:", width=150, anchor="w").pack(side="left")
        min_var = tk.StringVar()
        max_var = tk.StringVar()
        widgets['explosion_min'] = min_var
        widgets['explosion_max'] = max_var

        ctk.CTkEntry(range_frame, textvariable=min_var, width=45,
                     placeholder_text="Min").pack(side="left", padx=2)
        ctk.CTkLabel(range_frame, text="-").pack(side="left")
        ctk.CTkEntry(range_frame, textvariable=max_var, width=45,
                     placeholder_text="Max").pack(side="left", padx=2)

        # Keyboard mode
        keyboard_frame = ctk.CTkFrame(parent)
        keyboard_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(keyboard_frame, text="Keyboard mode:", width=150, anchor="w").pack(side="left")
        keyboard_var = tk.BooleanVar()
        widgets['keyboard_input_mode'] = keyboard_var
        ctk.CTkCheckBox(keyboard_frame, text="Enable", variable=keyboard_var).pack(side="left")

        # Balloon color
        color_frame = ctk.CTkFrame(parent)
        color_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(color_frame, text="Balloon color:", width=150, anchor="w").pack(side="left")
        color_var = tk.StringVar()
        widgets['balloon_color'] = color_var
        ctk.CTkOptionMenu(color_frame, variable=color_var,
                          values=["Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Pink"],
                          width=100).pack(side="left")

        # Random colors
        random_frame = ctk.CTkFrame(parent)
        random_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(random_frame, text="Random colors:", width=150, anchor="w").pack(side="left")
        random_var = tk.BooleanVar()
        widgets['random_colors'] = random_var
        ctk.CTkCheckBox(random_frame, text="Enable", variable=random_var).pack(side="left")

    def _create_ice_fishing_overrides(self, parent, widgets):
        """Create Ice Fishing-specific override controls."""
        # Max fish
        max_fish_frame = ctk.CTkFrame(parent)
        max_fish_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(max_fish_frame, text="Max fish:", width=150, anchor="w").pack(side="left")
        max_fish_var = tk.StringVar()
        widgets['max_fish'] = max_fish_var
        ctk.CTkEntry(max_fish_frame, textvariable=max_fish_var, width=100,
                     placeholder_text="e.g., 64").pack(side="left")

        # Points per fish
        points_frame = ctk.CTkFrame(parent)
        points_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(points_frame, text="Points per fish:", width=150, anchor="w").pack(side="left")
        points_var = tk.StringVar()
        widgets['points_per_fish'] = points_var
        ctk.CTkEntry(points_frame, textvariable=points_var, width=100,
                     placeholder_text="e.g., 5").pack(side="left")

    def _create_mining_overrides(self, parent, widgets):
        """Create Mountain Mining-specific override controls."""
        # Max ore
        max_ore_frame = ctk.CTkFrame(parent)
        max_ore_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(max_ore_frame, text="Max ore:", width=150, anchor="w").pack(side="left")
        max_ore_var = tk.StringVar()
        widgets['max_ore'] = max_ore_var
        ctk.CTkEntry(max_ore_frame, textvariable=max_ore_var, width=100,
                     placeholder_text="e.g., 64").pack(side="left")

        # Points per ore
        points_frame = ctk.CTkFrame(parent)
        points_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(points_frame, text="Points per ore:", width=150, anchor="w").pack(side="left")
        points_var = tk.StringVar()
        widgets['points_per_ore'] = points_var
        ctk.CTkEntry(points_frame, textvariable=points_var, width=100,
                     placeholder_text="e.g., 5").pack(side="left")

    def _create_stb_overrides(self, parent, widgets):
        """Create Spinning Bottle-specific override controls."""
        # Segments
        segments_frame = ctk.CTkFrame(parent)
        segments_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(segments_frame, text="Segments:", width=150, anchor="w").pack(side="left")
        segments_var = tk.StringVar()
        widgets['segments'] = segments_var
        ctk.CTkOptionMenu(segments_frame, variable=segments_var,
                          values=["8", "16", "32"],
                          width=100).pack(side="left")

        # Points per add
        points_frame = ctk.CTkFrame(parent)
        points_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(points_frame, text="Points per add:", width=150, anchor="w").pack(side="left")
        points_var = tk.StringVar()
        widgets['points_per_add'] = points_var
        ctk.CTkEntry(points_frame, textvariable=points_var, width=100,
                     placeholder_text="e.g., 5").pack(side="left")

        # Spin speed range
        speed_frame = ctk.CTkFrame(parent)
        speed_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(speed_frame, text="Speed range:", width=150, anchor="w").pack(side="left")
        min_speed_var = tk.StringVar()
        max_speed_var = tk.StringVar()
        widgets['speed_min'] = min_speed_var
        widgets['speed_max'] = max_speed_var

        ctk.CTkEntry(speed_frame, textvariable=min_speed_var, width=45,
                     placeholder_text="Min").pack(side="left", padx=2)
        ctk.CTkLabel(speed_frame, text="-").pack(side="left")
        ctk.CTkEntry(speed_frame, textvariable=max_speed_var, width=45,
                     placeholder_text="Max").pack(side="left", padx=2)

        # Win color
        win_color_frame = ctk.CTkFrame(parent)
        win_color_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(win_color_frame, text="Win color:", width=150, anchor="w").pack(side="left")
        win_color_var = tk.StringVar()
        widgets['win_color'] = win_color_var
        ctk.CTkOptionMenu(win_color_frame, variable=win_color_var,
                          values=["Green", "Blue", "Yellow", "Orange", "Purple"],
                          width=100).pack(side="left")

        # Loss color
        loss_color_frame = ctk.CTkFrame(parent)
        loss_color_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(loss_color_frame, text="Loss color:", width=150, anchor="w").pack(side="left")
        loss_color_var = tk.StringVar()
        widgets['loss_color'] = loss_color_var
        ctk.CTkOptionMenu(loss_color_frame, variable=loss_color_var,
                          values=["Red", "Blue", "Yellow", "Orange", "Purple"],
                          width=100).pack(side="left")

    # Keep all the existing methods from the original class...
    def refresh(self):
        """Refresh all data."""
        self.refresh_experiments()

    def refresh_experiments(self):
        """Refresh the experiment list."""
        # Clear tree
        for item in self.exp_tree.get_children():
            self.exp_tree.delete(item)

        # Get experiments
        experiments = self.db_manager.get_active_experiments()

        for exp in experiments:
            created_date = datetime.fromisoformat(exp['created_date'])
            status = "Active" if exp['is_active'] else "Inactive"

            self.exp_tree.insert(
                "",
                "end",
                values=(
                    exp['experiment_code'],
                    exp['name'],
                    f"{exp['enrolled_count']}/{exp['max_participants'] or '∞'}",
                    status,
                    created_date.strftime("%Y-%m-%d")
                ),
                tags=(exp['id'],)
            )

    def on_experiment_select(self, event):
        """Handle experiment selection."""
        selection = self.exp_tree.selection()
        if selection:
            # Enable action buttons
            self.edit_btn.configure(state="normal")
            self.duplicate_btn.configure(state="normal")
            self.toggle_btn.configure(state="normal")
            self.view_stats_btn.configure(state="normal")
        else:
            # Disable action buttons
            self.edit_btn.configure(state="disabled")
            self.duplicate_btn.configure(state="disabled")
            self.toggle_btn.configure(state="disabled")
            self.view_stats_btn.configure(state="disabled")

    def new_experiment(self):
        """Create a new experiment."""
        self.current_experiment_id = None
        self.clear_builder_form()
        self.notebook.select(1)  # Switch to builder tab

    def edit_experiment(self):
        """Edit selected experiment."""
        selection = self.exp_tree.selection()
        if not selection:
            return

        item = self.exp_tree.item(selection[0])
        experiment_id = item['tags'][0]

        # Load experiment data
        experiment = self.db_manager.get_experiment(experiment_id=experiment_id)
        if experiment:
            self.current_experiment_id = experiment_id
            self.load_experiment_to_form(experiment)
            self.notebook.select(1)  # Switch to builder tab

    def cancel_edit(self):
        """Cancel editing and return to list."""
        self.clear_builder_form()
        self.notebook.select(0)

    def duplicate_experiment(self):
        """Duplicate the selected experiment."""
        selection = self.exp_tree.selection()
        if not selection:
            return

        item = self.exp_tree.item(selection[0])
        experiment_id = item['tags'][0]

        # Load experiment
        experiment = self.db_manager.get_experiment(experiment_id=experiment_id)
        if experiment:
            # Generate new code
            self.generate_experiment_code()
            new_code = self.code_var.get()

            # Create duplicate
            try:
                self.db_manager.create_experiment(
                    experiment_code=new_code,
                    name=f"{experiment['name']} (Copy)",
                    config=experiment['config'],
                    description=experiment['description'],
                    max_participants=experiment['max_participants'],
                    created_by="Admin"
                )

                messagebox.showinfo("Success", f"Experiment duplicated with code: {new_code}")
                self.refresh()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to duplicate experiment: {e}")

    def toggle_active(self):
        """Toggle active status of selected experiment."""
        selection = self.exp_tree.selection()
        if not selection:
            return

        item = self.exp_tree.item(selection[0])
        experiment_id = item['tags'][0]

        # Get current status
        experiment = self.db_manager.get_experiment(experiment_id=experiment_id)
        if experiment:
            new_status = not experiment['is_active']

            try:
                self.db_manager.update_experiment(
                    experiment_id,
                    is_active=new_status
                )

                status_text = "activated" if new_status else "deactivated"
                messagebox.showinfo("Success", f"Experiment {status_text}")
                self.refresh()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to update experiment: {e}")

    def view_statistics(self):
        """View statistics for selected experiment."""
        selection = self.exp_tree.selection()
        if not selection:
            return

        item = self.exp_tree.item(selection[0])
        experiment_id = item['tags'][0]

        # Switch to analytics tab and load stats
        self.load_experiment_analytics(experiment_id)
        self.notebook.select(2)

    def create_analytics_tab(self):
        """Create the analytics tab."""
        # Title
        title_label = ctk.CTkLabel(
            self.analytics_frame,
            text="Experiment Analytics",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)

        # Stats display
        self.stats_text = ctk.CTkTextbox(self.analytics_frame, height=500)
        self.stats_text.pack(fill="both", expand=True, padx=20, pady=10)

    def load_experiment_analytics(self, experiment_id: int):
        """Load analytics for an experiment."""
        experiment = self.db_manager.get_experiment(experiment_id=experiment_id)
        stats = self.db_manager.get_experiment_statistics(experiment_id)

        # Clear text
        self.stats_text.delete("1.0", "end")

        # Build analytics report
        report = []
        report.append(f"Experiment: {experiment['name']}")
        report.append(f"Code: {experiment['experiment_code']}")
        report.append(f"Status: {'Active' if experiment['is_active'] else 'Inactive'}")
        report.append("")

        report.append("=== Enrollment Statistics ===")
        report.append(f"Total Participants: {stats['participant_count']}")
        report.append(f"Total Sessions: {stats['session_count']}")
        report.append(f"Completed Sessions: {stats['completed_sessions']}")

        if stats['session_count'] > 0:
            completion_rate = (stats['completed_sessions'] / stats['session_count']) * 100
            report.append(f"Completion Rate: {completion_rate:.1f}%")

        report.append("")
        report.append("=== Task Statistics ===")

        for task_name, task_stats in stats['task_statistics'].items():
            display_name = TaskType.get_display_name(TaskType(task_name))
            report.append(f"\n{display_name}:")
            report.append(f"  Trials: {task_stats['trial_count']}")
            report.append(f"  Avg Risk Level: {task_stats['avg_risk']:.3f}")
            report.append(f"  Avg Points: {task_stats['avg_points']:.1f}")
            report.append(f"  Success Rate: {task_stats['success_rate'] * 100:.1f}%")

        self.stats_text.insert("1.0", "\n".join(report))

    def generate_experiment_code(self):
        """Generate a unique experiment code."""
        # Generate format: EXP + random 3-digit number + random letter
        while True:
            code = f"EXP{random.randint(100, 999)}{random.choice(string.ascii_uppercase)}"

            # Check if code already exists
            existing = self.db_manager.get_experiment(experiment_code=code)
            if not existing:
                self.code_var.set(code)
                break