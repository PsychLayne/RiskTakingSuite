# Create new file: ui/experiment_builder.py

"""
Experiment Builder UI for Risk Tasks Client
Allows creation and management of experiments with custom parameters.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime, timedelta
import json
import random
import string
from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from database.models import TaskType, Experiment, ExperimentConfig


class ExperimentBuilder(ctk.CTkFrame):
    """UI component for building and managing experiments."""

    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_experiment_id = None
        self.temp_config = {}

        # Setup UI
        self.setup_ui()

        # Load experiments
        self.refresh()

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

        # Tab 2: Create/Edit Experiment
        self.builder_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.builder_frame, text="Builder")
        self.create_builder_tab()

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

    def create_builder_tab(self):
        """Create the experiment builder tab."""
        # Create scrollable frame
        self.builder_scroll = ctk.CTkScrollableFrame(self.builder_frame)
        self.builder_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Basic Information Section
        self.create_basic_info_section()

        # Experiment Parameters Section
        self.create_parameters_section()

        # Task Configuration Section
        self.create_task_config_section()

        # Task Sequence Section
        self.create_sequence_section()

        # Save/Cancel buttons
        button_frame = ctk.CTkFrame(self.builder_frame)
        button_frame.pack(fill="x", padx=20, pady=20)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Experiment",
            command=self.save_experiment,
            width=150
        )
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel_edit,
            width=150,
            fg_color="gray"
        )
        cancel_btn.pack(side="left", padx=10)

        generate_code_btn = ctk.CTkButton(
            button_frame,
            text="Generate Code",
            command=self.generate_experiment_code,
            width=150,
            fg_color="orange"
        )
        generate_code_btn.pack(side="right", padx=10)

    def create_basic_info_section(self):
        """Create basic information section."""
        section_label = ctk.CTkLabel(
            self.builder_scroll,
            text="Basic Information",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_label.pack(anchor="w", pady=(20, 10))

        info_frame = ctk.CTkFrame(self.builder_scroll)
        info_frame.pack(fill="x", pady=10)

        # Experiment code
        code_frame = ctk.CTkFrame(info_frame)
        code_frame.pack(fill="x", padx=20, pady=5)

        code_label = ctk.CTkLabel(code_frame, text="Experiment Code:", width=150, anchor="w")
        code_label.pack(side="left")

        self.code_var = tk.StringVar()
        self.code_entry = ctk.CTkEntry(
            code_frame,
            textvariable=self.code_var,
            placeholder_text="e.g., EXP001"
        )
        self.code_entry.pack(side="left", fill="x", expand=True, padx=10)

        # Name
        name_frame = ctk.CTkFrame(info_frame)
        name_frame.pack(fill="x", padx=20, pady=5)

        name_label = ctk.CTkLabel(name_frame, text="Name:", width=150, anchor="w")
        name_label.pack(side="left")

        self.name_var = tk.StringVar()
        name_entry = ctk.CTkEntry(
            name_frame,
            textvariable=self.name_var,
            placeholder_text="Experiment name"
        )
        name_entry.pack(side="left", fill="x", expand=True, padx=10)

        # Description
        desc_frame = ctk.CTkFrame(info_frame)
        desc_frame.pack(fill="x", padx=20, pady=5)

        desc_label = ctk.CTkLabel(desc_frame, text="Description:", width=150, anchor="nw")
        desc_label.pack(side="left")

        self.desc_text = ctk.CTkTextbox(desc_frame, height=80)
        self.desc_text.pack(side="left", fill="x", expand=True, padx=10)

        # Dates
        dates_frame = ctk.CTkFrame(info_frame)
        dates_frame.pack(fill="x", padx=20, pady=5)

        # Start date
        start_label = ctk.CTkLabel(dates_frame, text="Start Date:", width=150, anchor="w")
        start_label.pack(side="left")

        self.start_date_var = tk.StringVar()
        start_entry = ctk.CTkEntry(
            dates_frame,
            textvariable=self.start_date_var,
            placeholder_text="YYYY-MM-DD (optional)"
        )
        start_entry.pack(side="left", padx=10)

        # End date
        end_label = ctk.CTkLabel(dates_frame, text="End Date:", width=100, anchor="w")
        end_label.pack(side="left", padx=(20, 0))

        self.end_date_var = tk.StringVar()
        end_entry = ctk.CTkEntry(
            dates_frame,
            textvariable=self.end_date_var,
            placeholder_text="YYYY-MM-DD (optional)"
        )
        end_entry.pack(side="left", padx=10)

        # Max participants
        max_frame = ctk.CTkFrame(info_frame)
        max_frame.pack(fill="x", padx=20, pady=5)

        max_label = ctk.CTkLabel(max_frame, text="Max Participants:", width=150, anchor="w")
        max_label.pack(side="left")

        self.max_participants_var = tk.StringVar()
        max_entry = ctk.CTkEntry(
            max_frame,
            textvariable=self.max_participants_var,
            placeholder_text="Leave empty for unlimited"
        )
        max_entry.pack(side="left", padx=10)

    def create_parameters_section(self):
        """Create experiment parameters section."""
        section_label = ctk.CTkLabel(
            self.builder_scroll,
            text="Experiment Parameters",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_label.pack(anchor="w", pady=(20, 10))

        params_frame = ctk.CTkFrame(self.builder_scroll)
        params_frame.pack(fill="x", pady=10)

        # Trials per task
        trials_frame = ctk.CTkFrame(params_frame)
        trials_frame.pack(fill="x", padx=20, pady=5)

        trials_label = ctk.CTkLabel(trials_frame, text="Trials per task:", width=200, anchor="w")
        trials_label.pack(side="left")

        self.trials_var = tk.IntVar(value=30)
        trials_spin = ctk.CTkEntry(trials_frame, textvariable=self.trials_var, width=100)
        trials_spin.pack(side="left", padx=10)

        # Session gap
        gap_frame = ctk.CTkFrame(params_frame)
        gap_frame.pack(fill="x", padx=20, pady=5)

        gap_label = ctk.CTkLabel(gap_frame, text="Session gap (days):", width=200, anchor="w")
        gap_label.pack(side="left")

        self.gap_var = tk.IntVar(value=14)
        gap_spin = ctk.CTkEntry(gap_frame, textvariable=self.gap_var, width=100)
        gap_spin.pack(side="left", padx=10)

        # Tasks per session
        tasks_frame = ctk.CTkFrame(params_frame)
        tasks_frame.pack(fill="x", padx=20, pady=5)

        tasks_label = ctk.CTkLabel(tasks_frame, text="Tasks per session:", width=200, anchor="w")
        tasks_label.pack(side="left")

        self.tasks_per_session_var = tk.IntVar(value=2)
        tasks_spin = ctk.CTkEntry(tasks_frame, textvariable=self.tasks_per_session_var, width=100)
        tasks_spin.pack(side="left", padx=10)

    def create_task_config_section(self):
        """Create task configuration section."""
        section_label = ctk.CTkLabel(
            self.builder_scroll,
            text="Task Configuration",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_label.pack(anchor="w", pady=(20, 10))

        # Task enable/disable
        tasks_frame = ctk.CTkFrame(self.builder_scroll)
        tasks_frame.pack(fill="x", pady=10)

        enable_label = ctk.CTkLabel(
            tasks_frame,
            text="Select tasks to include in this experiment:",
            font=ctk.CTkFont(size=14)
        )
        enable_label.pack(anchor="w", padx=20, pady=10)

        # Create checkboxes for each task with edit buttons
        self.task_vars = {}
        self.task_overrides = {}  # Store task-specific overrides
        checkbox_frame = ctk.CTkFrame(tasks_frame)
        checkbox_frame.pack(fill="x", padx=40, pady=10)

        for task in TaskType:
            # Create a frame for each task row
            task_row_frame = ctk.CTkFrame(checkbox_frame)
            task_row_frame.pack(fill="x", pady=5)

            var = tk.BooleanVar(value=True)
            self.task_vars[task.value] = var

            checkbox = ctk.CTkCheckBox(
                task_row_frame,
                text=TaskType.get_display_name(task),
                variable=var,
                command=self.on_task_toggle,
                width=200
            )
            checkbox.pack(side="left")

            # Add edit button for this specific task
            edit_btn = ctk.CTkButton(
                task_row_frame,
                text="Edit",
                command=lambda t=task.value: self.show_task_override_dialog(t),
                width=60,
                height=28,
                fg_color="gray60",
                hover_color="gray70"
            )
            edit_btn.pack(side="left", padx=(10, 0))

            # Initialize empty overrides for this task
            self.task_overrides[task.value] = {}

    def create_sequence_section(self):
        """Create task sequence configuration section."""
        section_label = ctk.CTkLabel(
            self.builder_scroll,
            text="Task Sequence",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_label.pack(anchor="w", pady=(20, 10))

        sequence_frame = ctk.CTkFrame(self.builder_scroll)
        sequence_frame.pack(fill="x", pady=10)

        # Sequence type selection
        type_frame = ctk.CTkFrame(sequence_frame)
        type_frame.pack(fill="x", padx=20, pady=10)

        type_label = ctk.CTkLabel(type_frame, text="Sequence Type:", width=150, anchor="w")
        type_label.pack(side="left")

        self.sequence_type_var = tk.StringVar(value="random")

        random_radio = ctk.CTkRadioButton(
            type_frame,
            text="Random (balanced)",
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

        # Fixed sequence configuration (initially hidden)
        self.fixed_sequence_frame = ctk.CTkFrame(sequence_frame)

        sequence_info = ctk.CTkLabel(
            self.fixed_sequence_frame,
            text="Define the exact task order for each session:",
            font=ctk.CTkFont(size=14)
        )
        sequence_info.pack(anchor="w", padx=20, pady=10)

        # We'll add sequence inputs dynamically based on tasks per session
        self.sequence_inputs_frame = ctk.CTkFrame(self.fixed_sequence_frame)
        self.sequence_inputs_frame.pack(fill="x", padx=40, pady=10)

    def on_task_toggle(self):
        """Handle task checkbox toggle."""
        # Update enabled tasks count
        enabled_count = sum(1 for var in self.task_vars.values() if var.get())

        # Ensure at least one task is enabled
        if enabled_count == 0:
            messagebox.showwarning(
                "Invalid Configuration",
                "At least one task must be enabled"
            )
            # Re-enable the last unchecked task
            for var in self.task_vars.values():
                if not var.get():
                    var.set(True)
                    break

    def on_sequence_type_change(self):
        """Handle sequence type change."""
        if self.sequence_type_var.get() == "fixed":
            self.fixed_sequence_frame.pack(fill="x", padx=20, pady=10)
            self.update_sequence_inputs()
        else:
            self.fixed_sequence_frame.pack_forget()

    def update_sequence_inputs(self):
        """Update fixed sequence input fields."""
        # Clear existing inputs
        for widget in self.sequence_inputs_frame.winfo_children():
            widget.destroy()

        # Get enabled tasks
        enabled_tasks = [task for task, var in self.task_vars.items() if var.get()]
        tasks_per_session = self.tasks_per_session_var.get()

        if not enabled_tasks:
            return

        # Create dropdowns for 2 sessions
        self.sequence_vars = {}

        for session in range(1, 3):  # Assuming 2 sessions
            session_label = ctk.CTkLabel(
                self.sequence_inputs_frame,
                text=f"Session {session}:",
                font=ctk.CTkFont(weight="bold")
            )
            session_label.grid(row=session - 1, column=0, sticky="w", pady=10)

            self.sequence_vars[session] = []

            for task_num in range(tasks_per_session):
                task_var = tk.StringVar()
                self.sequence_vars[session].append(task_var)

                task_menu = ctk.CTkOptionMenu(
                    self.sequence_inputs_frame,
                    variable=task_var,
                    values=[TaskType.get_display_name(TaskType(t)) for t in enabled_tasks],
                    width=150
                )
                task_menu.grid(row=session - 1, column=task_num + 1, padx=5, pady=5)

    def show_task_override_dialog(self, task_key: str):
        """Show dialog for specific task parameter overrides."""
        # Check if task is enabled
        if not self.task_vars.get(task_key, tk.BooleanVar()).get():
            messagebox.showinfo("Task Disabled", "Please enable this task first to configure its parameters.")
            return

        dialog = ctk.CTkToplevel(self)
        task_display_name = TaskType.get_display_name(TaskType(task_key))
        dialog.title(f"{task_display_name} Parameters")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()

        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text=f"{task_display_name} Configuration",
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

        # Store override widgets for this task
        override_widgets = {}

        # Task-specific configurations
        if task_key == 'bart':
            self._create_bart_overrides(scroll_frame, override_widgets)
        elif task_key == 'ice_fishing':
            self._create_ice_fishing_overrides(scroll_frame, override_widgets)
        elif task_key == 'mountain_mining':
            self._create_mining_overrides(scroll_frame, override_widgets)
        elif task_key == 'spinning_bottle':
            self._create_stb_overrides(scroll_frame, override_widgets)

        # Load existing overrides if any
        if task_key in self.task_overrides:
            for param, value in self.task_overrides[task_key].items():
                if param in override_widgets:
                    override_widgets[param].set(str(value))

        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", pady=20)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=lambda: self.save_task_overrides(dialog, task_key, override_widgets),
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

    def save_task_overrides(self, dialog, task_key, widgets):
        """Save task-specific overrides."""
        # Validate and save overrides
        overrides = {}

        for param, widget in widgets.items():
            value = widget.get()

            # Skip empty values (use defaults)
            if isinstance(widget, tk.StringVar) and not value.strip():
                continue

            # Convert to appropriate type
            if param in ['max_pumps', 'max_fish', 'max_ore', 'points_per_pump',
                         'points_per_fish', 'points_per_ore', 'points_per_add',
                         'segments', 'explosion_min', 'explosion_max']:
                try:
                    overrides[param] = int(value)
                except ValueError:
                    messagebox.showerror("Invalid Value", f"{param} must be a number")
                    return
            elif param in ['speed_min', 'speed_max']:
                try:
                    overrides[param] = float(value)
                except ValueError:
                    messagebox.showerror("Invalid Value", f"{param} must be a number")
                    return
            elif isinstance(widget, tk.BooleanVar):
                overrides[param] = value
            else:
                overrides[param] = value

        # Store overrides
        self.task_overrides[task_key] = overrides
        dialog.destroy()

        # Show confirmation
        if overrides:
            messagebox.showinfo("Success", f"{TaskType.get_display_name(TaskType(task_key))} parameters saved!")
        else:
            messagebox.showinfo("Info", "Using default parameters (no overrides set)")

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

        # Parameters
        self.trials_var.set(exp_config.get('total_trials_per_task', 30))
        self.gap_var.set(exp_config.get('session_gap_days', 14))
        self.tasks_per_session_var.set(exp_config.get('tasks_per_session', 2))

        # Task enables
        enabled_tasks = exp_config.get('enabled_tasks')
        if enabled_tasks:
            for task, var in self.task_vars.items():
                var.set(task in enabled_tasks)

        # Load task-specific overrides
        task_configs = config.get('tasks', {})
        self.task_overrides = {}

        for task_key, task_config in task_configs.items():
            overrides = {}

            if task_key == 'bart':
                if 'max_pumps' in task_config:
                    overrides['max_pumps'] = task_config['max_pumps']
                if 'points_per_pump' in task_config:
                    overrides['points_per_pump'] = task_config['points_per_pump']
                if 'explosion_range' in task_config:
                    overrides['explosion_min'] = task_config['explosion_range'][0]
                    overrides['explosion_max'] = task_config['explosion_range'][1]
                if 'keyboard_input_mode' in task_config:
                    overrides['keyboard_input_mode'] = task_config['keyboard_input_mode']
                if 'balloon_color' in task_config:
                    overrides['balloon_color'] = task_config['balloon_color']
                if 'random_colors' in task_config:
                    overrides['random_colors'] = task_config['random_colors']

            elif task_key == 'ice_fishing':
                if 'max_fish' in task_config:
                    overrides['max_fish'] = task_config['max_fish']
                if 'points_per_fish' in task_config:
                    overrides['points_per_fish'] = task_config['points_per_fish']

            elif task_key == 'mountain_mining':
                if 'max_ore' in task_config:
                    overrides['max_ore'] = task_config['max_ore']
                if 'points_per_ore' in task_config:
                    overrides['points_per_ore'] = task_config['points_per_ore']

            elif task_key == 'spinning_bottle':
                if 'segments' in task_config:
                    overrides['segments'] = task_config['segments']
                if 'points_per_add' in task_config:
                    overrides['points_per_add'] = task_config['points_per_add']
                if 'spin_speed_range' in task_config:
                    overrides['speed_min'] = task_config['spin_speed_range'][0]
                    overrides['speed_max'] = task_config['spin_speed_range'][1]
                if 'win_color' in task_config:
                    overrides['win_color'] = task_config['win_color']
                if 'loss_color' in task_config:
                    overrides['loss_color'] = task_config['loss_color']

            if overrides:
                self.task_overrides[task_key] = overrides

        # Sequence type
        sequence_config = exp_config.get('task_sequence', {})
        self.sequence_type_var.set(sequence_config.get('type', 'random'))
        self.on_sequence_type_change()

        # Load fixed sequences if applicable
        if sequence_config.get('type') == 'fixed' and 'sequences' in sequence_config:
            # Populate sequence dropdowns
            pass

    def clear_builder_form(self):
        """Clear the builder form."""
        self.code_var.set("")
        self.code_entry.configure(state="normal")
        self.name_var.set("")
        self.desc_text.delete("1.0", "end")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.max_participants_var.set("")

        # Reset to defaults
        self.trials_var.set(30)
        self.gap_var.set(14)
        self.tasks_per_session_var.set(2)

        # Enable all tasks
        for var in self.task_vars.values():
            var.set(True)

        # Clear task overrides
        self.task_overrides = {}

        self.sequence_type_var.set("random")
        self.on_sequence_type_change()

    def save_experiment(self):
        """Save the current experiment."""
        # Validate form
        if not self.code_var.get().strip():
            messagebox.showerror("Error", "Experiment code is required")
            return

        if not self.name_var.get().strip():
            messagebox.showerror("Error", "Experiment name is required")
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
        if self.max_participants_var.get():
            try:
                max_participants = int(self.max_participants_var.get())
            except ValueError:
                messagebox.showerror("Error", "Max participants must be a number")
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
                    created_by="Admin"  # Could get from logged-in user
                )
                messagebox.showinfo("Success", "Experiment created successfully!")

            # Refresh and go back to list
            self.refresh()
            self.notebook.select(0)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save experiment: {e}")

    def build_experiment_config(self) -> Dict:
        """Build the experiment configuration."""
        # Get enabled tasks
        enabled_tasks = [task for task, var in self.task_vars.items() if var.get()]

        config = {
            "experiment": {
                "total_trials_per_task": self.trials_var.get(),
                "session_gap_days": self.gap_var.get(),
                "tasks_per_session": self.tasks_per_session_var.get(),
                "enabled_tasks": enabled_tasks,
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
            "tasks": {}  # Task-specific configs will be populated below
        }

        # Add task-specific overrides
        for task_key, overrides in self.task_overrides.items():
            if overrides:  # Only add if there are actual overrides
                config["tasks"][task_key] = {}

                # Map override parameters to config structure
                if task_key == 'bart':
                    if 'max_pumps' in overrides:
                        config["tasks"][task_key]['max_pumps'] = overrides['max_pumps']
                    if 'points_per_pump' in overrides:
                        config["tasks"][task_key]['points_per_pump'] = overrides['points_per_pump']
                    if 'explosion_min' in overrides and 'explosion_max' in overrides:
                        config["tasks"][task_key]['explosion_range'] = [
                            overrides['explosion_min'],
                            overrides['explosion_max']
                        ]
                    if 'keyboard_input_mode' in overrides:
                        config["tasks"][task_key]['keyboard_input_mode'] = overrides['keyboard_input_mode']
                    if 'balloon_color' in overrides:
                        config["tasks"][task_key]['balloon_color'] = overrides['balloon_color']
                    if 'random_colors' in overrides:
                        config["tasks"][task_key]['random_colors'] = overrides['random_colors']

                elif task_key == 'ice_fishing':
                    if 'max_fish' in overrides:
                        config["tasks"][task_key]['max_fish'] = overrides['max_fish']
                    if 'points_per_fish' in overrides:
                        config["tasks"][task_key]['points_per_fish'] = overrides['points_per_fish']

                elif task_key == 'mountain_mining':
                    if 'max_ore' in overrides:
                        config["tasks"][task_key]['max_ore'] = overrides['max_ore']
                    if 'points_per_ore' in overrides:
                        config["tasks"][task_key]['points_per_ore'] = overrides['points_per_ore']

                elif task_key == 'spinning_bottle':
                    if 'segments' in overrides:
                        config["tasks"][task_key]['segments'] = overrides['segments']
                    if 'points_per_add' in overrides:
                        config["tasks"][task_key]['points_per_add'] = overrides['points_per_add']
                    if 'speed_min' in overrides and 'speed_max' in overrides:
                        config["tasks"][task_key]['spin_speed_range'] = [
                            overrides['speed_min'],
                            overrides['speed_max']
                        ]
                    if 'win_color' in overrides:
                        config["tasks"][task_key]['win_color'] = overrides['win_color']
                    if 'loss_color' in overrides:
                        config["tasks"][task_key]['loss_color'] = overrides['loss_color']

        # Add fixed sequences if applicable
        if self.sequence_type_var.get() == "fixed" and hasattr(self, 'sequence_vars'):
            sequences = {}
            for session, vars in self.sequence_vars.items():
                # Convert display names back to task keys
                task_sequence = []
                for var in vars:
                    display_name = var.get()
                    for task in TaskType:
                        if TaskType.get_display_name(task) == display_name:
                            task_sequence.append(task.value)
                            break
                sequences[str(session)] = task_sequence

            config["experiment"]["task_sequence"]["sequences"] = sequences

        return config

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