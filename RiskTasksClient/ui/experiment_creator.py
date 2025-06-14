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

from database.db_manager import DatabaseManager
from database.models import TaskType
from utils.experiment_manager import ExperimentManager


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
        """Create Step 2: Session Configuration (placeholder)."""
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
        """Create Step 3: Review & Create (placeholder)."""
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
            # Validate Step 2 (will be implemented with full Step 2)
            pass

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

        # Create layout based on number of sessions
        num_sessions = self.sessions_var.get()
        tasks_per_session = self.tasks_var.get()

        if num_sessions == 1:
            # Single column layout
            self.create_session_config(self.session_config_container, 1, tasks_per_session)
        else:
            # Split-screen layout with tabs
            tab_view = ctk.CTkTabview(self.session_config_container)
            tab_view.pack(fill="both", expand=True)

            for i in range(1, num_sessions + 1):
                tab = tab_view.add(f"Session {i}")
                self.create_session_config(tab, i, tasks_per_session)

    def create_session_config(self, parent, session_num: int, max_tasks: int):
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
        if not self.randomize_var.get():
            instruction_label = ctk.CTkLabel(
                parent,
                text="Drag tasks to reorder. Click + to add tasks.",
                text_color="gray"
            )
            instruction_label.pack(pady=5)

        # Task list container
        task_container = ctk.CTkFrame(parent)
        task_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Placeholder for task items
        placeholder_label = ctk.CTkLabel(
            task_container,
            text=f"Click '+' to add up to {max_tasks} tasks",
            text_color="gray"
        )
        placeholder_label.pack(expand=True)

        # Add task button
        add_button = ctk.CTkButton(
            task_container,
            text="+ Add Task",
            command=lambda: self.show_task_selection(session_num),
            width=200,
            height=50
        )
        add_button.pack(pady=20)

        # Initialize session in config
        if str(session_num) not in self.experiment_config['sessions']:
            self.experiment_config['sessions'][str(session_num)] = {
                'tasks': []
            }

    def show_task_selection(self, session_num: int):
        """Show task selection modal."""
        # Placeholder - will be implemented in next step
        messagebox.showinfo("Add Task", f"Task selection for Session {session_num} - To be implemented")

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
            ("Code:", self.experiment_config.get('code', 'Auto-generate')),
            ("Description:", self.experiment_config.get('description', 'None')),
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

    def save_draft(self):
        """Save current configuration as draft."""
        messagebox.showinfo("Save Draft", "Draft saving functionality to be implemented")

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

        # Show first step
        self.show_step(1)

    def on_cancel(self):
        """Handle cancel button click."""
        if messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel? All progress will be lost."):
            self.reset_wizard()