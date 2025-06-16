"""
Participant Interface for Risk Tasks Client - FIXED VERSION
Handles 0 session gap for immediate sessions and proper experiment task mapping.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime, timedelta
import subprocess
import sys
import os
from pathlib import Path
import json
from typing import Tuple, List

from database.db_manager import DatabaseManager
from database.models import Participant, Session, TaskType, Gender
from utils.task_scheduler import TaskScheduler


class ParticipantInterface(ctk.CTk):
    """Simplified interface for participants."""

    def __init__(self, launcher_ref=None):
        super().__init__()

        self.launcher_ref = launcher_ref
        self.db_manager = DatabaseManager()
        self.db_manager.initialize()
        self.task_scheduler = TaskScheduler()

        self.current_participant_id = None
        self.current_session_id = None
        self.current_experiment = None

        # Window setup
        self.title("Risk Tasks - Participant")
        self.geometry("900x700")
        self.resizable(False, False)

        # Center window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Setup UI
        self.setup_ui()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Setup the participant interface."""
        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Show login screen initially
        self.show_login_screen()

    def show_login_screen(self):
        """Show the initial login/registration screen."""
        # Clear container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Title
        title_label = ctk.CTkLabel(
            self.main_container,
            text="Welcome to the Risk Assessment Study",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(30, 40))

        # Options frame
        options_frame = ctk.CTkFrame(self.main_container)
        options_frame.pack(expand=True)

        # New participant section
        new_frame = ctk.CTkFrame(options_frame)
        new_frame.grid(row=0, column=0, padx=20, pady=20)

        new_label = ctk.CTkLabel(
            new_frame,
            text="New Participant",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        new_label.pack(pady=(20, 15))

        new_btn = ctk.CTkButton(
            new_frame,
            text="Start New",
            command=self.show_registration_screen,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        new_btn.pack(pady=(0, 20))

        # Separator
        separator = ttk.Separator(options_frame, orient="vertical")
        separator.grid(row=0, column=1, sticky="ns", padx=20)

        # Returning participant section
        returning_frame = ctk.CTkFrame(options_frame)
        returning_frame.grid(row=0, column=2, padx=20, pady=20)

        returning_label = ctk.CTkLabel(
            returning_frame,
            text="Returning Participant",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        returning_label.pack(pady=(20, 15))

        code_label = ctk.CTkLabel(
            returning_frame,
            text="Enter your participant code:",
            font=ctk.CTkFont(size=14)
        )
        code_label.pack(pady=(0, 5))

        # Store reference to the entry widget directly
        self.code_entry = ctk.CTkEntry(
            returning_frame,
            width=200,
            font=ctk.CTkFont(size=14),
            placeholder_text="e.g., P001"
        )
        self.code_entry.pack(pady=5)

        def on_code_submit(event=None):
            self.login_returning_participant()

        self.code_entry.bind("<Return>", on_code_submit)

        continue_btn = ctk.CTkButton(
            returning_frame,
            text="Continue",
            command=self.login_returning_participant,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        continue_btn.pack(pady=(10, 20))

        # Back button
        back_btn = ctk.CTkButton(
            self.main_container,
            text="← Back",
            command=self.return_to_launcher,
            width=100,
            height=40,
            fg_color="gray"
        )
        back_btn.pack(pady=(0, 20))

    def show_registration_screen(self):
        """Show registration screen for new participants."""
        # Clear container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Title
        title_label = ctk.CTkLabel(
            self.main_container,
            text="New Participant Registration",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(30, 40))

        # Form frame
        form_frame = ctk.CTkFrame(self.main_container)
        form_frame.pack(expand=True)

        # Experiment code input
        exp_code_label = ctk.CTkLabel(
            form_frame,
            text="Experiment Code:",
            font=ctk.CTkFont(size=16)
        )
        exp_code_label.grid(row=0, column=0, sticky="e", padx=(20, 10), pady=10)

        self.exp_code_entry = ctk.CTkEntry(
            form_frame,
            width=200,
            font=ctk.CTkFont(size=14),
            placeholder_text="Enter experiment code"
        )
        self.exp_code_entry.grid(row=0, column=1, padx=(0, 20), pady=10)

        # Age input
        age_label = ctk.CTkLabel(
            form_frame,
            text="Age:",
            font=ctk.CTkFont(size=16)
        )
        age_label.grid(row=1, column=0, sticky="e", padx=(20, 10), pady=10)

        self.age_entry = ctk.CTkEntry(
            form_frame,
            width=200,
            font=ctk.CTkFont(size=14),
            placeholder_text="Enter your age"
        )
        self.age_entry.grid(row=1, column=1, padx=(0, 20), pady=10)

        # Gender input
        gender_label = ctk.CTkLabel(
            form_frame,
            text="Gender:",
            font=ctk.CTkFont(size=16)
        )
        gender_label.grid(row=2, column=0, sticky="e", padx=(20, 10), pady=10)

        self.gender_menu = ctk.CTkOptionMenu(
            form_frame,
            values=["Male", "Female", "Other", "Prefer not to say"],
            width=200,
            font=ctk.CTkFont(size=14)
        )
        self.gender_menu.set("Prefer not to say")
        self.gender_menu.grid(row=2, column=1, padx=(0, 20), pady=10)

        # Buttons
        button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        button_frame.pack(pady=40)

        register_btn = ctk.CTkButton(
            button_frame,
            text="Begin Study",
            command=self.register_new_participant,
            width=150,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        register_btn.pack(side="left", padx=10)

        back_btn = ctk.CTkButton(
            button_frame,
            text="Back",
            command=self.show_login_screen,
            width=150,
            height=50,
            font=ctk.CTkFont(size=16),
            fg_color="gray"
        )
        back_btn.pack(side="left", padx=10)

    def register_new_participant(self):
        """Register a new participant and enroll in experiment."""
        # Get experiment code
        exp_code = self.exp_code_entry.get().strip()
        if not exp_code:
            messagebox.showerror("Error", "Please enter an experiment code")
            return

        # Verify experiment exists and is active
        experiment = self.db_manager.get_experiment(experiment_code=exp_code)
        if not experiment:
            messagebox.showerror("Error", "Invalid experiment code")
            return

        if not experiment['is_active']:
            messagebox.showerror("Error", "This experiment is not currently active")
            return

        # Check enrollment dates
        now = datetime.now()
        if experiment['start_date']:
            start_date = datetime.fromisoformat(experiment['start_date'])
            if now < start_date:
                messagebox.showerror("Error", "This experiment has not started yet")
                return

        if experiment['end_date']:
            end_date = datetime.fromisoformat(experiment['end_date'])
            if now > end_date:
                messagebox.showerror("Error", "This experiment has ended")
                return

        # Get age
        age_str = self.age_entry.get().strip()
        if not age_str:
            messagebox.showerror("Error", "Please enter your age")
            return

        try:
            age = int(age_str)
            if age < 18 or age > 100:
                messagebox.showerror("Error", "Age must be between 18 and 100")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid age")
            return

        # Get gender
        gender_selection = self.gender_menu.get()
        gender_map = {
            "Male": "male",
            "Female": "female",
            "Other": "other",
            "Prefer not to say": "prefer_not_to_say"
        }
        gender = gender_map.get(gender_selection, "prefer_not_to_say")

        try:
            # Generate participant code
            participant_code = self.generate_participant_code()

            # Add participant to database
            participant_id = self.db_manager.add_participant(
                participant_code=participant_code,
                age=age,
                gender=gender,
                notes=f"Enrolled in experiment: {exp_code}"
            )

            # Enroll in experiment
            self.db_manager.enroll_participant(exp_code, participant_id)

            self.current_participant_id = participant_id
            self.current_experiment = experiment

            # Show participant code
            messagebox.showinfo(
                "Registration Complete",
                f"Your participant code is: {participant_code}\n\n"
                f"You have been enrolled in: {experiment['name']}\n\n"
                "Please remember your participant code for future sessions."
            )

            # Start first session automatically
            self.start_new_session()

        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")

    def generate_participant_code(self):
        """Generate a unique participant code."""
        participants = self.db_manager.get_all_participants()

        # Find the highest participant number
        max_num = 0
        for p in participants:
            code = p['participant_code']
            if code.startswith('P') and code[1:].isdigit():
                num = int(code[1:])
                max_num = max(max_num, num)

        # Generate next code
        next_num = max_num + 1
        return f"P{next_num:03d}"

    def login_returning_participant(self):
        """Login a returning participant."""
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showerror("Error", "Please enter your participant code")
            return

        # Find participant
        participant = self.db_manager.get_participant(participant_code=code)
        if not participant:
            messagebox.showerror("Error", f"Participant code '{code}' not found")
            return

        self.current_participant_id = participant['id']

        # Get participant's experiment
        experiment = self.db_manager.get_participant_experiment(participant['id'])
        if not experiment:
            messagebox.showerror(
                "Error",
                "You are not enrolled in any experiment. Please register as a new participant."
            )
            self.show_login_screen()
            return

        self.current_experiment = experiment

        # Check if experiment is still active
        if not experiment['is_active']:
            messagebox.showinfo(
                "Experiment Ended",
                f"The experiment '{experiment['name']}' has ended.\n"
                "Thank you for your participation!"
            )
            self.show_login_screen()
            return

        # Check if they can start a new session based on experiment config
        if self.can_schedule_session_for_experiment(participant['id'], experiment):
            self.start_new_session()
        else:
            # Check for incomplete sessions
            sessions = self.db_manager.get_participant_sessions(participant['id'])
            incomplete_sessions = [s for s in sessions if not s['completed']]

            if incomplete_sessions:
                # Resume the most recent incomplete session
                session = incomplete_sessions[-1]
                self.current_session_id = session['id']
                self.show_session_screen(session['tasks_assigned'])
            else:
                # Check if waiting period
                exp_config = experiment['config'].get('experiment', {})
                session_gap_days = exp_config.get('session_gap_days', 14)

                if sessions:
                    last_session_date = datetime.fromisoformat(sessions[-1]['session_date'])
                    days_since = (datetime.now() - last_session_date).days

                    # If session gap is 0, allow immediate sessions
                    if session_gap_days == 0:
                        # Check if they've reached max sessions
                        max_sessions = 2  # Could be configurable
                        if len(sessions) >= max_sessions:
                            messagebox.showinfo(
                                "Study Complete",
                                "You have completed all sessions in this study.\n"
                                "Thank you for your participation!"
                            )
                        else:
                            # Allow starting a new session immediately
                            self.start_new_session()
                            return
                    elif days_since < session_gap_days:
                        messagebox.showinfo(
                            "Too Soon",
                            f"Please wait {session_gap_days - days_since} more days before starting your next session.\n"
                            f"Your next session will be available on {(last_session_date + timedelta(days=session_gap_days)).strftime('%Y-%m-%d')}."
                        )
                    else:
                        messagebox.showinfo(
                            "Study Complete",
                            "You have completed all sessions in this study.\n"
                            "Thank you for your participation!"
                        )
                else:
                    messagebox.showinfo(
                        "Study Complete",
                        "You have completed all sessions in this study.\n"
                        "Thank you for your participation!"
                    )
                self.show_login_screen()

    def can_schedule_session_for_experiment(self, participant_id: int, experiment: dict) -> bool:
        """Check if participant can schedule a new session based on experiment rules."""
        sessions = self.db_manager.get_participant_sessions(participant_id)
        exp_config = experiment['config'].get('experiment', {})

        # Check max sessions (typically 2)
        max_sessions = 2  # Could be configurable per experiment
        if len(sessions) >= max_sessions:
            return False

        # Check session gap
        if sessions:
            last_session = sessions[-1]
            if not last_session['completed']:
                return False  # Must complete current session first

            last_session_date = datetime.fromisoformat(last_session['session_date'])
            session_gap_days = exp_config.get('session_gap_days', 14)

            # If session gap is 0, allow immediate sessions
            if session_gap_days == 0:
                return True

            days_since = (datetime.now() - last_session_date).days

            if days_since < session_gap_days:
                return False

        return True

    def store_task_instance_assignment(self, session_id: int, instance_ids: list):
        """Store which task instances were assigned to a session."""
        # Store in a file
        assignments_file = Path("data/session_task_instances.json")

        try:
            if assignments_file.exists():
                with open(assignments_file, 'r') as f:
                    assignments = json.load(f)
            else:
                assignments = {}

            assignments[str(session_id)] = instance_ids

            assignments_file.parent.mkdir(exist_ok=True)
            with open(assignments_file, 'w') as f:
                json.dump(assignments, f, indent=2)

        except Exception as e:
            print(f"Error storing task instance assignments: {e}")

    def get_task_instance_assignment(self, session_id: int) -> list:
        """Get task instances assigned to a session."""
        assignments_file = Path("data/session_task_instances.json")

        try:
            if assignments_file.exists():
                with open(assignments_file, 'r') as f:
                    assignments = json.load(f)
                    return assignments.get(str(session_id), [])
        except Exception as e:
            print(f"Error loading task instance assignments: {e}")

        return []

    def get_tasks_and_instances_for_session(self, experiment: dict, session_number: int) -> Tuple[List[str], List[str]]:
        """Get both task types and instance IDs for a session."""
        exp_config = experiment['config'].get('experiment', {})
        task_instances = experiment['config'].get('task_instances', {})

        if not task_instances:
            # Fallback for old format
            tasks = self.get_actual_task_types_from_experiment(experiment, session_number)
            return tasks, []

        # Check for fixed sequence first
        task_sequence = exp_config.get('task_sequence', {})
        if task_sequence.get('type') == 'fixed':
            sequences = task_sequence.get('sequences', {})
            session_key = str(session_number)
            if session_key in sequences:
                instance_ids = sequences[session_key]
                tasks = []
                for instance_id in instance_ids:
                    if instance_id in task_instances:
                        task_type = task_instances[instance_id].get('task_type')
                        if task_type:
                            tasks.append(task_type)
                return tasks, instance_ids

        # Random assignment
        enabled_instances = exp_config.get('enabled_task_instances', list(task_instances.keys()))
        tasks_per_session = exp_config.get('tasks_per_session', 2)

        # Get all previous instance assignments for this participant
        sessions = self.db_manager.get_participant_sessions(self.current_participant_id)
        used_instances = set()

        for session in sessions:
            if session['id'] != self.current_session_id:
                session_instances = self.get_task_instance_assignment(session['id'])
                used_instances.update(session_instances)

        # Get available instances
        available_instances = [inst for inst in enabled_instances if inst not in used_instances]

        # Select instances
        if len(available_instances) >= tasks_per_session:
            import random
            selected_instances = random.sample(available_instances, tasks_per_session)
        else:
            # This shouldn't happen with proper validation
            raise ValueError(
                f"Not enough unused task instances. Need {tasks_per_session} but only "
                f"{len(available_instances)} available. Total instances: {len(enabled_instances)}, "
                f"Used: {len(used_instances)}"
            )

        # Convert to task types
        tasks = []
        for instance_id in selected_instances:
            task_type = task_instances[instance_id].get('task_type')
            if task_type:
                tasks.append(task_type)

        return tasks, selected_instances

    def get_actual_task_types_from_experiment(self, experiment: dict, session_number: int) -> list:
        """Extract actual task types from experiment configuration - backward compatibility."""
        exp_config = experiment['config'].get('experiment', {})

        # For backward compatibility with experiments that don't use instances
        enabled_tasks = exp_config.get('enabled_tasks', [])
        if enabled_tasks:
            tasks_per_session = exp_config.get('tasks_per_session', 2)

            # Get previously assigned tasks
            sessions = self.db_manager.get_participant_sessions(self.current_participant_id)
            assigned_tasks = set()
            for session in sessions:
                if session['id'] != self.current_session_id:
                    assigned_tasks.update(session['tasks_assigned'])

            # Get available tasks
            available_tasks = [t for t in enabled_tasks if t not in assigned_tasks]

            if len(available_tasks) >= tasks_per_session:
                import random
                return random.sample(available_tasks, tasks_per_session)
            else:
                # Use all available and fill from assigned if needed
                import random
                selected = available_tasks.copy()
                if len(selected) < tasks_per_session:
                    already_assigned = list(assigned_tasks)
                    random.shuffle(already_assigned)
                    needed = tasks_per_session - len(selected)
                    selected.extend(already_assigned[:needed])
                return selected

        return []

    def start_new_session(self):
        """Start a new session for the current participant with experiment config."""
        if not self.current_participant_id or not self.current_experiment:
            return

        try:
            # Get next session number
            sessions = self.db_manager.get_participant_sessions(self.current_participant_id)
            session_number = len(sessions) + 1

            # Get tasks and instance IDs based on experiment configuration
            tasks, instance_ids = self.get_tasks_and_instances_for_session(self.current_experiment, session_number)

            if not tasks:
                messagebox.showerror(
                    "Configuration Error",
                    "No tasks configured for this experiment session"
                )
                return

            # Debug print to verify task assignment
            print(f"Session {session_number} tasks: {tasks}")
            print(f"Session {session_number} instances: {instance_ids}")

            # Create session in database with experiment ID
            session_id = self.db_manager.create_session_for_experiment(
                participant_id=self.current_participant_id,
                session_number=session_number,
                tasks=tasks,
                experiment_id=self.current_experiment['id']
            )

            self.current_session_id = session_id

            # Store instance assignments if we have them
            if instance_ids:
                self.store_task_instance_assignment(session_id, instance_ids)

            # Show session screen
            self.show_session_screen(tasks)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start session: {e}")
            import traceback
            traceback.print_exc()
            self.show_login_screen()

    def show_session_screen(self, tasks):
        """Show the session screen with experiment info."""
        # Clear container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Get participant info
        participant = self.db_manager.get_participant(participant_id=self.current_participant_id)

        # Title with experiment name
        title_label = ctk.CTkLabel(
            self.main_container,
            text=f"Welcome, {participant['participant_code']}",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(30, 10))

        # Experiment info
        exp_label = ctk.CTkLabel(
            self.main_container,
            text=f"Study: {self.current_experiment['name']}",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        exp_label.pack(pady=(0, 10))

        # Session info
        sessions = self.db_manager.get_participant_sessions(self.current_participant_id)
        current_session = next(s for s in sessions if s['id'] == self.current_session_id)

        session_label = ctk.CTkLabel(
            self.main_container,
            text=f"Session {current_session['session_number']}",
            font=ctk.CTkFont(size=18)
        )
        session_label.pack(pady=(0, 30))

        # Instructions
        instructions_label = ctk.CTkLabel(
            self.main_container,
            text="Please complete the following tasks:",
            font=ctk.CTkFont(size=16)
        )
        instructions_label.pack(pady=(0, 20))

        # Task buttons frame
        tasks_frame = ctk.CTkFrame(self.main_container)
        tasks_frame.pack(expand=True, pady=20)

        # Get completed tasks
        trials = self.db_manager.get_session_trials(self.current_session_id)
        completed_tasks = set()

        # Get required trials from experiment config
        exp_config = self.current_experiment['config'].get('experiment', {})
        required_trials = exp_config.get('total_trials_per_task', 30)

        for task in tasks:
            task_trials = [t for t in trials if t['task_name'] == task]
            if len(task_trials) >= required_trials:
                completed_tasks.add(task)

        # Get task instance assignments for this session
        instance_ids = self.get_task_instance_assignment(self.current_session_id)

        # Create task buttons
        self.task_buttons = {}
        for i, task in enumerate(tasks):
            display_name = TaskType.get_display_name(TaskType(task))

            # If we have instance assignments, get the specific instance for this task
            if instance_ids and i < len(instance_ids):
                instance_id = instance_ids[i]
                task_instances = self.current_experiment['config'].get('task_instances', {})
                if instance_id in task_instances:
                    instance_display = task_instances[instance_id].get('display_name', display_name)
                    display_name = instance_display

            if task in completed_tasks:
                button_text = f"✓ {display_name}"
                button_state = "disabled"
                button_color = "gray"
            else:
                button_text = display_name
                button_state = "normal"
                button_color = None

            btn = ctk.CTkButton(
                tasks_frame,
                text=button_text,
                command=lambda t=task, idx=i: self.launch_task_with_instance(t, idx),
                state=button_state,
                fg_color=button_color,
                width=250,
                height=80,
                font=ctk.CTkFont(size=18)
            )
            btn.grid(row=i, column=0, padx=20, pady=10)
            self.task_buttons[task] = btn

        # Progress info
        progress_label = ctk.CTkLabel(
            self.main_container,
            text=f"Completed: {len(completed_tasks)}/{len(tasks)} tasks",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        progress_label.pack(pady=10)

        # Check if session is complete
        if len(completed_tasks) == len(tasks):
            self.db_manager.complete_session(self.current_session_id)
            complete_label = ctk.CTkLabel(
                self.main_container,
                text="Session Complete! Thank you!",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="green"
            )
            complete_label.pack(pady=10)

            # Check if immediate sessions are allowed
            exp_config = self.current_experiment['config'].get('experiment', {})
            session_gap_days = exp_config.get('session_gap_days', 14)

            if session_gap_days == 0:
                # Show option to start next session immediately
                sessions = self.db_manager.get_participant_sessions(self.current_participant_id)
                max_sessions = 2  # Could be configurable

                if len(sessions) < max_sessions:
                    next_session_btn = ctk.CTkButton(
                        self.main_container,
                        text="Start Next Session",
                        command=self.start_new_session,
                        width=200,
                        height=50,
                        fg_color="green"
                    )
                    next_session_btn.pack(pady=10)

            # Add return button
            return_btn = ctk.CTkButton(
                self.main_container,
                text="Return to Login",
                command=self.show_login_screen,
                width=200,
                height=50
            )
            return_btn.pack(pady=10)
        else:
            # Refresh button
            refresh_btn = ctk.CTkButton(
                self.main_container,
                text="🔄 Refresh",
                command=lambda: self.show_session_screen(tasks),
                width=120,
                height=40,
                fg_color="orange"
            )
            refresh_btn.pack(pady=(20, 10))

            # Logout button
            logout_btn = ctk.CTkButton(
                self.main_container,
                text="Save & Exit",
                command=self.logout,
                width=120,
                height=40,
                fg_color="gray"
            )
            logout_btn.pack(pady=(0, 20))

    def launch_task_with_instance(self, task_name: str, task_index: int):
        """Launch task with specific instance configuration."""
        # Get instance ID for this task index
        instance_ids = self.get_task_instance_assignment(self.current_session_id)
        instance_id = None

        if instance_ids and task_index < len(instance_ids):
            instance_id = instance_ids[task_index]

        self.launch_task(task_name, instance_id)

    def launch_task(self, task_name: str, instance_id: str = None):
        """Launch the specified task with experiment config."""
        # Map task names to their Python files
        task_files = {
            "bart": "bart_task.py",
            "ice_fishing": "ice_task.py",
            "mountain_mining": "mining_task.py",
            "spinning_bottle": "stb_task.py"
        }

        if task_name not in task_files:
            messagebox.showerror("Error", f"Unknown task: {task_name}")
            return

        # Get task file path
        task_file = Path("tasks") / task_files[task_name]

        if not task_file.exists():
            messagebox.showerror(
                "Error",
                f"Task file not found: {task_file}\n"
                f"Please ensure the task files are in the 'tasks' directory."
            )
            return

        # Save experiment config temporarily for the task to use
        temp_config_path = Path("config/current_experiment.json")
        task_instance_id = instance_id

        try:
            # If we have an experiment, use its config
            if self.current_experiment:
                config_to_save = self.current_experiment['config'].copy()

                # Find the task instance configuration
                task_instances = config_to_save.get('task_instances', {})

                # If no specific instance ID provided, find the first one for this task type
                if not task_instance_id:
                    for inst_id, instance in task_instances.items():
                        if instance.get('task_type') == task_name:
                            task_instance_id = inst_id
                            break

                # Create a merged config that includes task-specific settings
                if 'tasks' not in config_to_save:
                    config_to_save['tasks'] = {}

                # If we found a task instance, extract its config
                if task_instance_id and task_instance_id in task_instances:
                    instance = task_instances[task_instance_id]
                    # Extract config (excluding metadata fields)
                    instance_config = {
                        k: v for k, v in instance.items()
                        if k not in ['task_type', 'display_name']
                    }
                    # IMPORTANT: Override the default task config with instance config
                    config_to_save['tasks'][task_name] = instance_config
                    print(f"Using instance {task_instance_id} config: {instance_config}")

            else:
                # Otherwise, load the default settings
                default_settings_path = Path("config/settings.json")
                if default_settings_path.exists():
                    with open(default_settings_path, 'r') as f:
                        config_to_save = json.load(f)
                else:
                    messagebox.showerror("Error", "No configuration found")
                    return

            # Save the config file
            with open(temp_config_path, 'w') as f:
                json.dump(config_to_save, f, indent=2)

            print(f"Saved config to: {temp_config_path}")
            print(f"Task config content: {json.dumps(config_to_save.get('tasks', {}).get(task_name, {}), indent=2)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save experiment config: {e}")
            import traceback
            traceback.print_exc()
            return

        # Prepare environment variables
        env = {
            **os.environ,
            "SESSION_ID": str(self.current_session_id),
            "PARTICIPANT_ID": str(self.current_participant_id),
            "TASK_NAME": task_name,
            "EXPERIMENT_CONFIG": str(temp_config_path.absolute())
        }

        # Add task instance ID if we have one
        if task_instance_id:
            env["TASK_INSTANCE_ID"] = task_instance_id
            print(f"Set TASK_INSTANCE_ID={task_instance_id}")

        # Add experiment ID if we have one
        if self.current_experiment:
            env["EXPERIMENT_ID"] = str(self.current_experiment['id'])

        # Launch the task
        try:
            display_name = TaskType.get_display_name(TaskType(task_name))
            messagebox.showinfo(
                "Launching Task",
                f"Starting {display_name}...\n"
                f"The task will open in fullscreen mode."
            )

            # Hide this window
            self.withdraw()

            # Launch task and wait for it to complete
            process = subprocess.Popen(
                [sys.executable, str(task_file)],
                env=env
            )

            # Wait for task to complete
            process.wait()

            # Show window again and refresh
            self.deiconify()

            # Clean up temp config
            try:
                temp_config_path.unlink()
            except:
                pass

            # Get updated task list
            sessions = self.db_manager.get_participant_sessions(self.current_participant_id)
            current_session = next(s for s in sessions if s['id'] == self.current_session_id)
            self.show_session_screen(current_session['tasks_assigned'])

        except Exception as e:
            self.deiconify()
            messagebox.showerror("Error", f"Failed to launch task: {e}")

    def logout(self):
        """Save progress and return to login screen."""
        messagebox.showinfo(
            "Progress Saved",
            "Your progress has been saved. You can continue later."
        )
        self.current_participant_id = None
        self.current_session_id = None
        self.current_experiment = None
        self.show_login_screen()

    def return_to_launcher(self):
        """Return to the main launcher."""
        if self.launcher_ref:
            self.launcher_ref.deiconify()
        self.destroy()

    def on_closing(self):
        """Handle window close event."""
        if self.launcher_ref:
            self.launcher_ref.deiconify()
        self.db_manager.close()
        self.destroy()


if __name__ == "__main__":
    # If run directly, create standalone window
    app = ParticipantInterface()
    app.mainloop()