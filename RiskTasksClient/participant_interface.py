"""
Participant Interface for Risk Tasks Client
Simplified interface for participants to start and continue sessions.
Now supports experiment enrollment via experiment codes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime
import subprocess
import sys
import os
from pathlib import Path
import json

from database.db_manager import DatabaseManager
from database.models import Participant, Session, TaskType, Gender
from utils.task_scheduler import TaskScheduler
from utils.experiment_manager import ExperimentManager


class ParticipantInterface(ctk.CTk):
    """Simplified interface for participants with experiment support."""

    def __init__(self, launcher_ref=None):
        super().__init__()

        self.launcher_ref = launcher_ref
        self.db_manager = DatabaseManager()
        self.db_manager.initialize()
        self.task_scheduler = TaskScheduler()
        self.experiment_manager = ExperimentManager(self.db_manager, self.task_scheduler)

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

        # Experiment code input (NEW)
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
            placeholder_text="Optional (e.g., ABC123)"
        )
        self.exp_code_entry.grid(row=0, column=1, padx=(0, 20), pady=10)

        # Info label for experiment code
        exp_info_label = ctk.CTkLabel(
            form_frame,
            text="Leave blank for standard protocol",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        exp_info_label.grid(row=1, column=1, sticky="w", padx=(5, 20), pady=(0, 10))

        # Age input
        age_label = ctk.CTkLabel(
            form_frame,
            text="Age:",
            font=ctk.CTkFont(size=16)
        )
        age_label.grid(row=2, column=0, sticky="e", padx=(20, 10), pady=10)

        self.age_entry = ctk.CTkEntry(
            form_frame,
            width=200,
            font=ctk.CTkFont(size=14),
            placeholder_text="Enter your age"
        )
        self.age_entry.grid(row=2, column=1, padx=(0, 20), pady=10)

        # Gender input
        gender_label = ctk.CTkLabel(
            form_frame,
            text="Gender:",
            font=ctk.CTkFont(size=16)
        )
        gender_label.grid(row=3, column=0, sticky="e", padx=(20, 10), pady=10)

        self.gender_menu = ctk.CTkOptionMenu(
            form_frame,
            values=["Male", "Female", "Other", "Prefer not to say"],
            width=200,
            font=ctk.CTkFont(size=14)
        )
        self.gender_menu.set("Prefer not to say")
        self.gender_menu.grid(row=3, column=1, padx=(0, 20), pady=10)

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
        """Register a new participant and start their first session."""
        # Get experiment code if provided
        exp_code = self.exp_code_entry.get().strip() if hasattr(self, 'exp_code_entry') else ""

        # Validate experiment code if provided
        if exp_code:
            experiment = self.db_manager.get_experiment_by_code(exp_code)
            if not experiment:
                messagebox.showerror("Error", "Invalid experiment code")
                return
            if not experiment['active']:
                messagebox.showerror("Error", "This experiment is not currently active")
                return

        # Get age value
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

        # Map gender selection to database format
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

            # Add participant to database with experiment code
            participant_id = self.db_manager.add_participant(
                participant_code=participant_code,
                age=age,
                gender=gender,
                notes="Registered via participant interface",
                experiment_code=exp_code if exp_code else None
            )

            self.current_participant_id = participant_id

            # Show participant code
            if exp_code:
                experiment = self.db_manager.get_experiment_by_code(exp_code)
                messagebox.showinfo(
                    "Registration Complete",
                    f"Your participant code is: {participant_code}\n\n"
                    f"You have been enrolled in: {experiment['name']}\n\n"
                    "Please remember this code for future sessions."
                )
            else:
                messagebox.showinfo(
                    "Registration Complete",
                    f"Your participant code is: {participant_code}\n\n"
                    "Please remember this code for future sessions."
                )

            # Start first session
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

        # Check if participant is enrolled in an experiment
        if participant['experiment_id']:
            self.current_experiment = self.experiment_manager.get_participant_experiment_info(participant['id'])

        # Check if they can start a new session
        can_start_new = False

        if self.current_experiment:
            # For experiment participants, check experiment progress
            next_session = self.experiment_manager.get_participant_next_session(participant['id'])
            can_start_new = next_session is not None
        else:
            # For non-experiment participants, use old logic
            can_start_new = self.task_scheduler.can_schedule_session(participant['id'])

        if can_start_new:
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
                if self.current_experiment:
                    messagebox.showinfo(
                        "Experiment Complete",
                        f"You have completed all sessions in the '{self.current_experiment['name']}' experiment.\n"
                        "Thank you for your participation!"
                    )
                else:
                    messagebox.showinfo(
                        "Study Complete",
                        "You have completed all sessions in this study.\n"
                        "Thank you for your participation!"
                    )
                self.show_login_screen()

    def start_new_session(self):
        """Start a new session for the current participant."""
        if not self.current_participant_id:
            return

        try:
            # Get participant info
            participant = self.db_manager.get_participant(participant_id=self.current_participant_id)

            if participant['experiment_id']:
                # Participant is in an experiment
                success, session_id, message = self.experiment_manager.create_participant_next_session(
                    self.current_participant_id
                )

                if not success:
                    messagebox.showinfo("Cannot Start Session", message)
                    self.show_login_screen()
                    return

                self.current_session_id = session_id

                # Get the session details
                sessions = self.db_manager.get_participant_sessions(self.current_participant_id)
                current_session = next(s for s in sessions if s['id'] == session_id)

                # Show session screen
                self.show_session_screen(current_session['tasks_assigned'])

            else:
                # Non-experiment participant - use old logic
                # Get next session number
                session_number = self.task_scheduler.get_next_session_number(self.current_participant_id)

                # Check if participant has incomplete sessions
                sessions = self.db_manager.get_participant_sessions(self.current_participant_id)
                incomplete_sessions = [s for s in sessions if not s['completed']]

                if incomplete_sessions:
                    result = messagebox.askyesno(
                        "Incomplete Session",
                        f"You have an incomplete session (Session {incomplete_sessions[-1]['session_number']}).\n"
                        "Would you like to continue that session instead?"
                    )

                    if result:
                        session = incomplete_sessions[-1]
                        self.current_session_id = session['id']
                        self.show_session_screen(session['tasks_assigned'])
                        return

                # Check session gap requirement
                if sessions and sessions[-1]['completed']:
                    last_session_date = datetime.fromisoformat(sessions[-1]['session_date'])
                    days_since = (datetime.now() - last_session_date).days

                    # Load config for session gap
                    config_path = Path("config/settings.json")
                    if config_path.exists():
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                            required_gap = config.get('experiment', {}).get('session_gap_days', 14)
                    else:
                        required_gap = 14

                    if days_since < required_gap:
                        messagebox.showinfo(
                            "Too Soon",
                            f"Please wait {required_gap - days_since} more days before starting your next session.\n"
                            f"Your next session will be available on {(last_session_date + timedelta(days=required_gap)).strftime('%Y-%m-%d')}."
                        )
                        self.show_login_screen()
                        return

                # Assign tasks for new session
                tasks = self.task_scheduler.assign_tasks_for_participant(
                    self.current_participant_id,
                    session_number
                )

                # Create session in database
                session_id = self.db_manager.create_session(
                    participant_id=self.current_participant_id,
                    session_number=session_number,
                    tasks=tasks
                )

                self.current_session_id = session_id

                # Show session screen
                self.show_session_screen(tasks)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start session: {e}")
            self.show_login_screen()

    def show_session_screen(self, tasks):
        """Show the session screen with task buttons."""
        # Clear container
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Get participant info
        participant = self.db_manager.get_participant(participant_id=self.current_participant_id)

        # Title
        title_label = ctk.CTkLabel(
            self.main_container,
            text=f"Welcome, {participant['participant_code']}",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(30, 10))

        # Show experiment info if enrolled
        if participant['experiment_id']:
            experiment = self.db_manager.get_experiment(participant['experiment_id'])
            exp_label = ctk.CTkLabel(
                self.main_container,
                text=f"Experiment: {experiment['name']}",
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

        # Load config for trials per task
        config_path = Path("config/settings.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                required_trials = config.get('experiment', {}).get('total_trials_per_task', 30)
        else:
            required_trials = 30

        for task in tasks:
            task_trials = [t for t in trials if t['task_name'] == task]
            if len(task_trials) >= required_trials:
                completed_tasks.add(task)

        # Create task buttons
        self.task_buttons = {}
        for i, task in enumerate(tasks):
            display_name = TaskType.get_display_name(TaskType(task))

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
                command=lambda t=task: self.launch_task(t),
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

            # Check if experiment is complete
            if participant['experiment_id']:
                progress = self.db_manager.get_participant_experiment_progress(
                    participant['id'],
                    participant['experiment_id']
                )
                if progress and progress['completed']:
                    exp_complete_label = ctk.CTkLabel(
                        self.main_container,
                        text="You have completed the entire experiment!",
                        font=ctk.CTkFont(size=16, weight="bold"),
                        text_color="blue"
                    )
                    exp_complete_label.pack(pady=5)

            # Add return button
            return_btn = ctk.CTkButton(
                self.main_container,
                text="Return to Login",
                command=self.show_login_screen,
                width=200,
                height=50
            )
            return_btn.pack(pady=20)
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

    def launch_task(self, task_name):
        """Launch the specified task."""
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

        # Check if this is an experiment participant and get task config
        participant = self.db_manager.get_participant(participant_id=self.current_participant_id)
        task_config = None

        if participant['experiment_id'] and self.current_session_id:
            # Get experiment task configuration
            session = None
            sessions = self.db_manager.get_participant_sessions(self.current_participant_id)
            for s in sessions:
                if s['id'] == self.current_session_id:
                    session = s
                    break

            if session and session.get('experiment_session_id'):
                # Get task config from experiment
                exp_tasks = self.db_manager.get_experiment_session_tasks(session['experiment_session_id'])
                for exp_task in exp_tasks:
                    if exp_task['task_type'] == task_name:
                        task_config = exp_task.get('task_config', {})
                        break

        # Save task config to temporary file if exists
        temp_config_path = None
        if task_config:
            temp_config_path = Path("config/temp_task_config.json")
            try:
                # Load existing settings
                config_path = Path("config/settings.json")
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        full_config = json.load(f)
                else:
                    full_config = {"tasks": {}}

                # Update with experiment-specific config
                if "tasks" not in full_config:
                    full_config["tasks"] = {}
                full_config["tasks"][task_name] = task_config

                # Save to temp file
                with open(temp_config_path, 'w') as f:
                    json.dump(full_config, f, indent=4)

            except Exception as e:
                print(f"Warning: Could not save task config: {e}")
                temp_config_path = None

        # Prepare environment variables
        env = {
            **os.environ,
            "SESSION_ID": str(self.current_session_id),
            "PARTICIPANT_ID": str(self.current_participant_id),
            "TASK_NAME": task_name
        }

        # Add custom config path if available
        if temp_config_path:
            env["CONFIG_PATH"] = str(temp_config_path.absolute())

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

            # Clean up temp config file
            if temp_config_path and temp_config_path.exists():
                try:
                    temp_config_path.unlink()
                except:
                    pass

            # Show window again and refresh
            self.deiconify()

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