"""
Session Manager UI for Risk Tasks Client
Handles session creation, task launching, and session management.
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

from database.db_manager import DatabaseManager
from database.models import TaskType, Session
from utils.task_scheduler import TaskScheduler

class SessionManager(ctk.CTkFrame):
    """UI component for managing experimental sessions."""

    def __init__(self, parent, db_manager: DatabaseManager, task_scheduler: TaskScheduler):
        super().__init__(parent)
        self.db_manager = db_manager
        self.task_scheduler = task_scheduler
        self.current_session_id = None
        self.current_participant_id = None

        # Setup UI
        self.setup_ui()

        # Load data
        self.refresh()

    def setup_ui(self):
        """Setup the session manager interface."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Session Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Top section - Start new session
        new_session_frame = ctk.CTkFrame(main_container)
        new_session_frame.pack(fill="x", pady=(0, 20))

        new_session_label = ctk.CTkLabel(
            new_session_frame,
            text="Start New Session",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        new_session_label.pack(pady=10)

        # Participant selection
        selection_frame = ctk.CTkFrame(new_session_frame)
        selection_frame.pack(fill="x", padx=20, pady=10)

        participant_label = ctk.CTkLabel(selection_frame, text="Select Participant:")
        participant_label.pack(side="left", padx=(0, 10))

        self.participant_var = tk.StringVar()
        self.participant_menu = ctk.CTkComboBox(
            selection_frame,
            variable=self.participant_var,
            command=self.on_participant_selected,
            width=300
        )
        self.participant_menu.pack(side="left", padx=(0, 20))

        self.start_session_button = ctk.CTkButton(
            selection_frame,
            text="Start Session",
            command=self.start_new_session,
            state="disabled",
            width=150
        )
        self.start_session_button.pack(side="left")

        # Add refresh button
        refresh_participants_btn = ctk.CTkButton(
            selection_frame,
            text="🔄 Refresh",
            command=self.refresh,
            width=80
        )
        refresh_participants_btn.pack(side="left", padx=(10, 0))

        # Session info display
        self.session_info_frame = ctk.CTkFrame(new_session_frame)
        self.session_info_frame.pack(fill="x", padx=20, pady=10)

        self.session_info_label = ctk.CTkLabel(
            self.session_info_frame,
            text="Select a participant to see session information",
            font=ctk.CTkFont(size=14)
        )
        self.session_info_label.pack(pady=10)

        # Middle section - Active sessions
        active_frame = ctk.CTkFrame(main_container)
        active_frame.pack(fill="both", expand=True, pady=(0, 20))

        active_label = ctk.CTkLabel(
            active_frame,
            text="Active Sessions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        active_label.pack(pady=10)

        # Active sessions list
        list_frame = ctk.CTkFrame(active_frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create Treeview for active sessions
        columns = ("Participant", "Session", "Date", "Tasks", "Progress")
        self.active_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=8
        )

        # Configure columns
        self.active_tree.heading("Participant", text="Participant")
        self.active_tree.heading("Session", text="Session #")
        self.active_tree.heading("Date", text="Start Date")
        self.active_tree.heading("Tasks", text="Tasks")
        self.active_tree.heading("Progress", text="Progress")

        self.active_tree.column("Participant", width=150)
        self.active_tree.column("Session", width=80)
        self.active_tree.column("Date", width=150)
        self.active_tree.column("Tasks", width=250)
        self.active_tree.column("Progress", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.active_tree.yview
        )
        self.active_tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        self.active_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind selection event
        self.active_tree.bind("<<TreeviewSelect>>", self.on_active_session_select)

        # Active session controls
        control_frame = ctk.CTkFrame(active_frame)
        control_frame.pack(fill="x", padx=20, pady=10)

        self.resume_button = ctk.CTkButton(
            control_frame,
            text="Resume Session",
            command=self.resume_session,
            state="disabled"
        )
        self.resume_button.pack(side="left", padx=5)

        self.complete_button = ctk.CTkButton(
            control_frame,
            text="Mark Complete",
            command=self.mark_complete,
            state="disabled",
            fg_color="green"
        )
        self.complete_button.pack(side="left", padx=5)

        # Bottom section - Task launch area
        self.task_frame = ctk.CTkFrame(main_container)
        self.task_frame.pack(fill="x")

        task_label = ctk.CTkLabel(
            self.task_frame,
            text="Task Launcher",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        task_label.pack(pady=10)

        self.task_info_label = ctk.CTkLabel(
            self.task_frame,
            text="Start or resume a session to launch tasks",
            font=ctk.CTkFont(size=14)
        )
        self.task_info_label.pack(pady=10)

        self.task_buttons_frame = ctk.CTkFrame(self.task_frame)
        self.task_buttons_frame.pack(pady=10)

    def refresh(self):
        """Refresh all data in the session manager."""
        self.load_participants()
        self.load_active_sessions()

    def load_participants(self):
        """Load participants into the dropdown."""
        participants = self.db_manager.get_all_participants()

        # Filter to show only participants who can schedule sessions
        eligible_participants = []
        ineligible_count = 0

        for p in participants:
            participant_sessions = self.db_manager.get_participant_sessions(p['id'])
            completed_sessions = [s for s in participant_sessions if s['completed']]

            # Check if participant can schedule more sessions
            if self.task_scheduler.can_schedule_session(p['id']):
                sessions_info = f"{len(completed_sessions)}/{p['session_count']} sessions"
                display_text = f"{p['participant_code']} ({sessions_info})"
                eligible_participants.append((display_text, p['id']))
            else:
                ineligible_count += 1

        if eligible_participants:
            values = [p[0] for p in eligible_participants]
            self.participant_menu.configure(values=values)
            self.participant_menu.set("Select a participant...")

            # Store mapping of display text to participant ID
            self.participant_map = {p[0]: p[1] for p in eligible_participants}
        else:
            self.participant_menu.configure(values=["No eligible participants"])
            self.participant_menu.set("No eligible participants")
            self.participant_map = {}

        # Show info about ineligible participants
        if ineligible_count > 0:
            info_text = f"({ineligible_count} participants have completed all sessions)"
            self.session_info_label.configure(
                text=f"Select a participant to see session information\n{info_text}"
            )

    def load_active_sessions(self):
        """Load active (incomplete) sessions."""
        # Clear current items
        for item in self.active_tree.get_children():
            self.active_tree.delete(item)

        # Get pending sessions
        pending_sessions = self.db_manager.get_pending_sessions()

        for session in pending_sessions:
            # Calculate progress
            trials = self.db_manager.get_session_trials(session['id'])
            tasks_with_trials = set(t['task_name'] for t in trials)
            progress = f"{len(tasks_with_trials)}/{len(session['tasks_assigned'])}"

            # Format date
            session_date = datetime.fromisoformat(session['session_date'])
            date_str = session_date.strftime("%Y-%m-%d %H:%M")

            # Format tasks
            tasks_str = ", ".join([
                TaskType.get_display_name(TaskType(task))
                for task in session['tasks_assigned']
            ])

            # Check if overdue
            is_overdue = (datetime.now() - session_date).days > 14

            self.active_tree.insert(
                "",
                "end",
                values=(
                    session['participant_code'],
                    f"Session {session['session_number']}",
                    date_str,
                    tasks_str,
                    progress
                ),
                tags=(session['id'], "overdue" if is_overdue else "normal")
            )

        # Color overdue sessions
        self.active_tree.tag_configure("overdue", foreground="red")

    def on_participant_selected(self, choice):
        """Handle participant selection."""
        if choice in self.participant_map:
            self.current_participant_id = self.participant_map[choice]
            self.load_participant_session_info()
            self.start_session_button.configure(state="normal")
        else:
            self.current_participant_id = None
            self.start_session_button.configure(state="disabled")

    def load_participant_session_info(self):
        """Load session information for selected participant."""
        if not self.current_participant_id:
            return

        # Get participant's sessions
        sessions = self.db_manager.get_participant_sessions(self.current_participant_id)

        # Get next session number
        next_session = self.task_scheduler.get_next_session_number(self.current_participant_id)

        # Check if participant can schedule more sessions
        can_schedule = next_session <= 2  # Maximum 2 sessions per participant

        if can_schedule:
            # Get assigned tasks for next session
            try:
                assigned_tasks = self.task_scheduler.get_participant_assignments(
                    self.current_participant_id
                ).get(next_session, [])

                # If no tasks assigned yet, we'll assign them when starting the session
                if not assigned_tasks:
                    # Preview what tasks would be assigned (without actually assigning them)
                    all_tasks = self.task_scheduler.get_available_tasks()
                    previously_assigned = set()
                    assignments = self.task_scheduler.get_participant_assignments(self.current_participant_id)
                    for session_tasks in assignments.values():
                        previously_assigned.update(session_tasks)

                    available_tasks = [task for task in all_tasks if task not in previously_assigned]

                    if len(available_tasks) >= 2:
                        tasks_display = [
                            TaskType.get_display_name(TaskType(task))
                            for task in available_tasks[:2]  # Show first 2 available tasks as preview
                        ]
                        info_text = (
                            f"✅ Ready to start Session #{next_session}\n"
                            f"Available tasks: {', '.join(tasks_display)} (and others)\n"
                            f"Tasks will be randomly assigned when session starts\n"
                        )
                    else:
                        info_text = f"❌ Cannot schedule session: Not enough tasks available"
                        self.start_session_button.configure(state="disabled")
                else:
                    tasks_display = [
                        TaskType.get_display_name(TaskType(task))
                        for task in assigned_tasks
                    ]
                    info_text = (
                        f"✅ Ready to start Session #{next_session}\n"
                        f"Tasks to complete: {', '.join(tasks_display)}\n"
                    )

                if sessions:
                    last_session = sessions[-1]
                    if not last_session['completed']:
                        info_text += f"\n⚠️ Note: Session {last_session['session_number']} is still incomplete"
                    else:
                        last_date = datetime.fromisoformat(last_session['session_date'])
                        days_since = (datetime.now() - last_date).days
                        info_text += f"\nDays since last session: {days_since}"

                        if days_since < 14:
                            info_text += f"\n⚠️ Recommended to wait {14 - days_since} more days"

            except Exception as e:
                info_text = f"❌ Error checking tasks: {e}"
                self.start_session_button.configure(state="disabled")
        else:
            info_text = "✅ All sessions completed for this participant!"
            self.start_session_button.configure(state="disabled")

            # Show completed sessions info
            if sessions:
                info_text += "\n\nCompleted sessions:"
                for session in sessions:
                    session_date = datetime.fromisoformat(session['session_date'])
                    status = "✓" if session['completed'] else "○"
                    info_text += f"\n{status} Session {session['session_number']} - {session_date.strftime('%Y-%m-%d')}"

        self.session_info_label.configure(text=info_text)

    def start_new_session(self):
        """Start a new session for the selected participant."""
        if not self.current_participant_id:
            return

        # Get next session number
        session_number = self.task_scheduler.get_next_session_number(self.current_participant_id)

        # Get assigned tasks - if none exist, assign them now
        assignments = self.task_scheduler.get_participant_assignments(self.current_participant_id)
        tasks = assignments.get(session_number, [])

        # If no tasks are assigned for this session, assign them now
        if not tasks:
            try:
                tasks = self.task_scheduler.assign_tasks_for_participant(
                    self.current_participant_id,
                    session_number
                )
            except ValueError as e:
                messagebox.showerror("Error", f"Cannot assign tasks: {e}")
                return

        if not tasks:
            messagebox.showerror("Error", "No tasks assigned for this session")
            return

        # Create session in database
        try:
            session_id = self.db_manager.create_session(
                participant_id=self.current_participant_id,
                session_number=session_number,
                tasks=tasks
            )

            self.current_session_id = session_id

            messagebox.showinfo(
                "Session Started",
                f"Session {session_number} started successfully!\n"
                f"Tasks: {', '.join([TaskType.get_display_name(TaskType(t)) for t in tasks])}"
            )

            # Refresh and show task launcher
            self.refresh()
            self.show_task_launcher(session_id, tasks)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start session: {e}")

    def on_active_session_select(self, event):
        """Handle selection of an active session."""
        selection = self.active_tree.selection()
        if not selection:
            return

        # Get session ID from tags
        item = self.active_tree.item(selection[0])
        session_id = item['tags'][0]

        self.current_session_id = session_id
        self.resume_button.configure(state="normal")
        self.complete_button.configure(state="normal")

    def resume_session(self):
        """Resume the selected session."""
        if not self.current_session_id:
            return

        # Get session details
        session = None
        pending_sessions = self.db_manager.get_pending_sessions()
        for s in pending_sessions:
            if s['id'] == self.current_session_id:
                session = s
                break

        if not session:
            return

        # Show task launcher
        self.show_task_launcher(session['id'], session['tasks_assigned'])

    def mark_complete(self):
        """Mark the selected session as complete."""
        if not self.current_session_id:
            return

        result = messagebox.askyesno(
            "Confirm Completion",
            "Are you sure you want to mark this session as complete?\n"
            "This cannot be undone."
        )

        if result:
            self.db_manager.complete_session(self.current_session_id)
            messagebox.showinfo("Success", "Session marked as complete")
            self.refresh()

    def show_task_launcher(self, session_id: int, tasks: list):
        """Show the task launcher interface."""
        # Clear existing task buttons
        for widget in self.task_buttons_frame.winfo_children():
            widget.destroy()

        # Get completed tasks for this session
        trials = self.db_manager.get_session_trials(session_id)
        completed_tasks = set()
        for trial in trials:
            # Check if task has required number of trials
            task_trials = [t for t in trials if t['task_name'] == trial['task_name']]
            if len(task_trials) >= 30:  # Assuming 30 trials per task
                completed_tasks.add(trial['task_name'])

        # Update info label
        self.task_info_label.configure(
            text=f"Session {session_id} - Click a task to launch:"
        )

        # Create task buttons
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
                self.task_buttons_frame,
                text=button_text,
                command=lambda t=task, s=session_id: self.launch_task(t, s),
                state=button_state,
                fg_color=button_color,
                width=200,
                height=50
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=10)

        # Add refresh button
        refresh_btn = ctk.CTkButton(
            self.task_buttons_frame,
            text="🔄 Refresh",
            command=lambda: self.show_task_launcher(session_id, tasks),
            width=100,
            height=40,
            fg_color="orange"
        )
        refresh_btn.grid(row=len(tasks) // 2 + 1, column=0, columnspan=2, pady=20)

    def launch_task(self, task_name: str, session_id: int):
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

        # Prepare environment variables for the task
        import os  # Make sure os is imported
        env = {
            **os.environ,  # Changed from sys.environ to os.environ
            "SESSION_ID": str(session_id),
            "PARTICIPANT_ID": str(self.current_participant_id),
            "TASK_NAME": task_name
        }

        # Launch the task
        try:
            messagebox.showinfo(
                "Launching Task",
                f"Launching {TaskType.get_display_name(TaskType(task_name))}...\n"
                f"The task will open in a new window."
            )

            # Launch as subprocess
            subprocess.Popen(
                [sys.executable, str(task_file)],
                env=env
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch task: {e}")