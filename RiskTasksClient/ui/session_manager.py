"""
Session Monitor for Risk Tasks Client - Streamlined Version
Focuses on active session monitoring and operational tasks.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime, timedelta
import csv
from pathlib import Path

from database.db_manager import DatabaseManager
from database.models import TaskType


class SessionMonitor(ctk.CTkFrame):
    """Streamlined session monitoring focused on operational oversight."""

    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_session_id = None

        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        """Setup the session monitor interface."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Session Monitor",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Top controls
        controls_frame = ctk.CTkFrame(self)
        controls_frame.pack(fill="x", padx=20, pady=10)

        # Experiment filter
        exp_label = ctk.CTkLabel(controls_frame, text="Filter by Experiment:")
        exp_label.pack(side="left", padx=5)

        self.experiment_var = tk.StringVar(value="All Experiments")
        self.experiment_menu = ctk.CTkComboBox(
            controls_frame,
            variable=self.experiment_var,
            command=self.on_experiment_filter_changed,
            width=250
        )
        self.experiment_menu.pack(side="left", padx=10)

        # Status filter
        status_label = ctk.CTkLabel(controls_frame, text="Status:")
        status_label.pack(side="left", padx=(20, 5))

        self.status_var = tk.StringVar(value="Active")
        status_menu = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.status_var,
            values=["Active", "Completed Today", "All"],
            command=self.refresh
        )
        status_menu.pack(side="left", padx=5)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh",
            command=self.refresh,
            width=100
        )
        refresh_btn.pack(side="right", padx=5)

        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ctk.CTkCheckBox(
            controls_frame,
            text="Auto-refresh (30s)",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        auto_refresh_check.pack(side="right", padx=10)

        # Quick stats
        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(fill="x", padx=20, pady=10)

        self.stats_labels = {}
        for key, text in [
            ('active', '🟢 Active: 0'),
            ('overdue', '🔴 Overdue: 0'),
            ('completed_today', '✅ Completed Today: 0'),
            ('avg_duration', '⏱️ Avg Duration: --')
        ]:
            label = ctk.CTkLabel(
                stats_frame,
                text=text,
                font=ctk.CTkFont(size=14)
            )
            label.pack(side="left", padx=15)
            self.stats_labels[key] = label

        # Session list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create Treeview
        columns = ("Participant", "Experiment", "Session", "Started", "Duration", "Progress", "Status")
        self.session_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=15
        )

        # Configure columns
        self.session_tree.heading("Participant", text="Participant")
        self.session_tree.heading("Experiment", text="Experiment")
        self.session_tree.heading("Session", text="Session")
        self.session_tree.heading("Started", text="Started")
        self.session_tree.heading("Duration", text="Duration")
        self.session_tree.heading("Progress", text="Progress")
        self.session_tree.heading("Status", text="Status")

        self.session_tree.column("Participant", width=100)
        self.session_tree.column("Experiment", width=120)
        self.session_tree.column("Session", width=70)
        self.session_tree.column("Started", width=130)
        self.session_tree.column("Duration", width=80)
        self.session_tree.column("Progress", width=200)
        self.session_tree.column("Status", width=80)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.session_tree.yview
        )
        self.session_tree.configure(yscrollcommand=scrollbar.set)

        self.session_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind selection
        self.session_tree.bind("<<TreeviewSelect>>", self.on_session_select)
        # Double-click to view details
        self.session_tree.bind("<Double-Button-1>", lambda e: self.view_details())

        # Action buttons
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=20, pady=10)

        self.view_btn = ctk.CTkButton(
            action_frame,
            text="👁️ View Details",
            command=self.view_details,
            state="disabled",
            width=120
        )
        self.view_btn.pack(side="left", padx=5)

        self.export_btn = ctk.CTkButton(
            action_frame,
            text="📥 Export Data",
            command=self.export_session,
            state="disabled",
            width=120
        )
        self.export_btn.pack(side="left", padx=5)

        self.complete_btn = ctk.CTkButton(
            action_frame,
            text="✓ Mark Complete",
            command=self.mark_complete,
            state="disabled",
            width=130,
            fg_color="green"
        )
        self.complete_btn.pack(side="left", padx=5)

        # Export all button (always enabled)
        export_all_btn = ctk.CTkButton(
            action_frame,
            text="📊 Export All Data",
            command=self.export_all_sessions,
            width=130,
            fg_color="gray"
        )
        export_all_btn.pack(side="right", padx=5)

        # Load experiments
        self.load_experiments()

        # Start auto-refresh
        self.toggle_auto_refresh()

    def load_experiments(self):
        """Load experiments for filtering."""
        experiments = self.db_manager.get_active_experiments()

        values = ["All Experiments"]
        self.experiment_map = {}

        for exp in experiments:
            display = f"{exp['experiment_code']}: {exp['name']}"
            values.append(display)
            self.experiment_map[display] = exp['id']

        self.experiment_menu.configure(values=values)

    def on_experiment_filter_changed(self, choice):
        """Handle experiment filter change."""
        self.refresh()

    def refresh(self, *args):
        """Refresh the session list."""
        # Clear current items
        for item in self.session_tree.get_children():
            self.session_tree.delete(item)

        # Get filter values
        status_filter = self.status_var.get()
        exp_filter = self.experiment_var.get()

        # Get experiment ID if filtered
        experiment_id = None
        if exp_filter != "All Experiments" and exp_filter in self.experiment_map:
            experiment_id = self.experiment_map[exp_filter]

        # Get sessions based on status
        if status_filter == "Active":
            sessions = self.get_active_sessions(experiment_id)
        elif status_filter == "Completed Today":
            sessions = self.get_completed_today_sessions(experiment_id)
        else:  # All
            sessions = self.get_all_recent_sessions(experiment_id)

        # Update statistics
        self.update_statistics(sessions)

        # Add sessions to tree
        for session in sessions:
            self.add_session_to_tree(session)

        # Apply styling
        self.session_tree.tag_configure("overdue", foreground="red")
        self.session_tree.tag_configure("active", foreground="green")
        self.session_tree.tag_configure("completed", foreground="gray")

    def get_active_sessions(self, experiment_id=None):
        """Get active sessions, optionally filtered by experiment."""
        all_pending = self.db_manager.get_pending_sessions()

        if experiment_id:
            # Filter by experiment
            filtered = []
            for session in all_pending:
                # Get participant's experiment
                participant = self.db_manager.get_participant(
                    participant_code=session['participant_code']
                )
                if participant:
                    participant_exp = self.db_manager.get_participant_experiment(
                        participant['id']
                    )
                    if participant_exp and participant_exp['id'] == experiment_id:
                        session['experiment_name'] = participant_exp['name']
                        session['experiment_code'] = participant_exp['experiment_code']
                        filtered.append(session)
            return filtered
        else:
            # Add experiment info to all sessions
            for session in all_pending:
                participant = self.db_manager.get_participant(
                    participant_code=session['participant_code']
                )
                if participant:
                    participant_exp = self.db_manager.get_participant_experiment(
                        participant['id']
                    )
                    if participant_exp:
                        session['experiment_name'] = participant_exp['name']
                        session['experiment_code'] = participant_exp['experiment_code']
                    else:
                        session['experiment_name'] = "None"
                        session['experiment_code'] = "N/A"
            return all_pending

    def get_completed_today_sessions(self, experiment_id=None):
        """Get sessions completed today."""
        today = datetime.now().date()
        completed_today = []

        participants = self.db_manager.get_all_participants()
        for participant in participants:
            # Check experiment filter
            if experiment_id:
                participant_exp = self.db_manager.get_participant_experiment(
                    participant['id']
                )
                if not participant_exp or participant_exp['id'] != experiment_id:
                    continue

            sessions = self.db_manager.get_participant_sessions(participant['id'])
            for session in sessions:
                if session['completed'] and session.get('end_time'):
                    end_date = datetime.fromisoformat(session['end_time']).date()
                    if end_date == today:
                        session['participant_code'] = participant['participant_code']

                        # Add experiment info
                        participant_exp = self.db_manager.get_participant_experiment(
                            participant['id']
                        )
                        if participant_exp:
                            session['experiment_name'] = participant_exp['name']
                            session['experiment_code'] = participant_exp['experiment_code']
                        else:
                            session['experiment_name'] = "None"
                            session['experiment_code'] = "N/A"

                        completed_today.append(session)

        return completed_today

    def get_all_recent_sessions(self, experiment_id=None):
        """Get all sessions from the last 7 days."""
        week_ago = datetime.now() - timedelta(days=7)
        recent_sessions = []

        participants = self.db_manager.get_all_participants()
        for participant in participants:
            # Check experiment filter
            if experiment_id:
                participant_exp = self.db_manager.get_participant_experiment(
                    participant['id']
                )
                if not participant_exp or participant_exp['id'] != experiment_id:
                    continue

            sessions = self.db_manager.get_participant_sessions(participant['id'])
            for session in sessions:
                session_date = datetime.fromisoformat(session['session_date'])
                if session_date >= week_ago:
                    session['participant_code'] = participant['participant_code']

                    # Add experiment info
                    participant_exp = self.db_manager.get_participant_experiment(
                        participant['id']
                    )
                    if participant_exp:
                        session['experiment_name'] = participant_exp['name']
                        session['experiment_code'] = participant_exp['experiment_code']
                    else:
                        session['experiment_name'] = "None"
                        session['experiment_code'] = "N/A"

                    recent_sessions.append(session)

        return recent_sessions

    def add_session_to_tree(self, session):
        """Add a session to the tree view."""
        session_date = datetime.fromisoformat(session['session_date'])

        # Calculate duration
        duration = "In Progress"
        if session.get('start_time') and session.get('end_time'):
            start = datetime.fromisoformat(session['start_time'])
            end = datetime.fromisoformat(session['end_time'])
            duration_mins = int((end - start).total_seconds() / 60)
            duration = f"{duration_mins} min"
        elif session.get('start_time'):
            start = datetime.fromisoformat(session['start_time'])
            duration_mins = int((datetime.now() - start).total_seconds() / 60)
            duration = f"{duration_mins} min"

        # Calculate progress
        trials = self.db_manager.get_session_trials(session['id'])
        task_progress = {}
        for trial in trials:
            if trial['task_name'] not in task_progress:
                task_progress[trial['task_name']] = 0
            task_progress[trial['task_name']] += 1

        # Format progress
        progress_parts = []
        for task in session['tasks_assigned']:
            count = task_progress.get(task, 0)
            task_display = TaskType.get_display_name(TaskType(task))[:10]  # Abbreviated
            progress_parts.append(f"{task_display}: {count}/30")

        progress = " | ".join(progress_parts)

        # Determine status and tag
        if session['completed']:
            status = "Completed"
            tag = "completed"
        else:
            days_old = (datetime.now() - session_date).days
            if days_old > 14:
                status = "Overdue"
                tag = "overdue"
            else:
                status = "Active"
                tag = "active"

        # Get experiment info
        exp_code = session.get('experiment_code', 'N/A')

        # Insert into tree
        self.session_tree.insert(
            "",
            "end",
            values=(
                session['participant_code'],
                exp_code,
                f"S{session['session_number']}",
                session_date.strftime("%m/%d %H:%M"),
                duration,
                progress,
                status
            ),
            tags=(session['id'], tag)
        )

    def update_statistics(self, sessions):
        """Update the statistics labels."""
        active_count = sum(1 for s in sessions if not s['completed'])
        overdue_count = sum(1 for s in sessions
                           if not s['completed'] and
                           (datetime.now() - datetime.fromisoformat(s['session_date'])).days > 14)
        completed_today = sum(1 for s in sessions
                             if s['completed'] and s.get('end_time') and
                             datetime.fromisoformat(s['end_time']).date() == datetime.now().date())

        # Calculate average duration
        durations = []
        for s in sessions:
            if s.get('start_time') and s.get('end_time'):
                start = datetime.fromisoformat(s['start_time'])
                end = datetime.fromisoformat(s['end_time'])
                durations.append((end - start).total_seconds() / 60)

        avg_duration = sum(durations) / len(durations) if durations else 0

        # Update labels
        self.stats_labels['active'].configure(text=f"🟢 Active: {active_count}")
        self.stats_labels['overdue'].configure(text=f"🔴 Overdue: {overdue_count}")
        self.stats_labels['completed_today'].configure(text=f"✅ Completed Today: {completed_today}")
        self.stats_labels['avg_duration'].configure(
            text=f"⏱️ Avg Duration: {avg_duration:.1f} min" if avg_duration else "⏱️ Avg Duration: --"
        )

    def on_session_select(self, event):
        """Handle session selection."""
        selection = self.session_tree.selection()
        if selection:
            item = self.session_tree.item(selection[0])
            self.current_session_id = item['tags'][0]

            # Enable buttons based on status
            status = item['values'][6]  # Status column

            self.view_btn.configure(state="normal")
            self.export_btn.configure(state="normal")

            if status != "Completed":
                self.complete_btn.configure(state="normal")
            else:
                self.complete_btn.configure(state="disabled")
        else:
            self.view_btn.configure(state="disabled")
            self.export_btn.configure(state="disabled")
            self.complete_btn.configure(state="disabled")

    def view_details(self):
        """View detailed session information."""
        if not self.current_session_id:
            return

        # Create details window
        details_window = ctk.CTkToplevel(self)
        details_window.title("Session Details")
        details_window.geometry("600x500")
        details_window.transient(self)
        details_window.grab_set()

        # Get session data
        session = None
        all_sessions = self.get_all_recent_sessions()
        for s in all_sessions:
            if s['id'] == self.current_session_id:
                session = s
                break

        if not session:
            messagebox.showerror("Error", "Session not found")
            details_window.destroy()
            return

        # Get trials
        trials = self.db_manager.get_session_trials(session['id'])

        # Display details
        info_text = ctk.CTkTextbox(details_window, height=400)
        info_text.pack(fill="both", expand=True, padx=20, pady=20)

        # Build details text
        details = []
        details.append(f"PARTICIPANT: {session['participant_code']}")
        details.append(f"EXPERIMENT: {session.get('experiment_name', 'None')}")
        details.append(f"SESSION: {session['session_number']}")
        details.append(f"STATUS: {'Completed' if session['completed'] else 'Active'}")
        details.append(f"\nSTARTED: {session['session_date']}")

        if session.get('end_time'):
            details.append(f"ENDED: {session['end_time']}")

        details.append(f"\nTASKS ASSIGNED:")
        for task in session['tasks_assigned']:
            details.append(f"  - {TaskType.get_display_name(TaskType(task))}")

        details.append(f"\nTRIAL SUMMARY:")

        # Group trials by task
        task_trials = {}
        for trial in trials:
            if trial['task_name'] not in task_trials:
                task_trials[trial['task_name']] = []
            task_trials[trial['task_name']].append(trial)

        for task, task_trial_list in task_trials.items():
            details.append(f"\n{TaskType.get_display_name(TaskType(task))}:")
            details.append(f"  Trials: {len(task_trial_list)}/30")

            if task_trial_list:
                avg_risk = sum(t['risk_level'] for t in task_trial_list) / len(task_trial_list)
                total_points = sum(t['points_earned'] for t in task_trial_list)
                success_rate = sum(1 for t in task_trial_list if t['outcome'] == 'success') / len(task_trial_list)

                details.append(f"  Avg Risk Level: {avg_risk:.3f}")
                details.append(f"  Total Points: {total_points}")
                details.append(f"  Success Rate: {success_rate:.1%}")

        info_text.insert("1.0", "\n".join(details))
        info_text.configure(state="disabled")

        # Close button
        close_btn = ctk.CTkButton(
            details_window,
            text="Close",
            command=details_window.destroy
        )
        close_btn.pack(pady=10)

    def export_session(self):
        """Export selected session data."""
        if not self.current_session_id:
            return

        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                trials = self.db_manager.get_session_trials(self.current_session_id)

                with open(filename, 'w', newline='') as f:
                    fieldnames = ['session_id', 'task_name', 'trial_number',
                                 'risk_level', 'points_earned', 'outcome',
                                 'reaction_time', 'timestamp']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for trial in trials:
                        writer.writerow({
                            'session_id': trial['session_id'],
                            'task_name': trial['task_name'],
                            'trial_number': trial['trial_number'],
                            'risk_level': trial['risk_level'],
                            'points_earned': trial['points_earned'],
                            'outcome': trial['outcome'],
                            'reaction_time': trial['reaction_time'],
                            'timestamp': trial['timestamp']
                        })

                messagebox.showinfo("Success", f"Session data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

    def mark_complete(self):
        """Mark selected session as complete."""
        if not self.current_session_id:
            return

        result = messagebox.askyesno(
            "Confirm",
            "Mark this session as complete?\n\nThis action cannot be undone."
        )

        if result:
            self.db_manager.complete_session(self.current_session_id)
            messagebox.showinfo("Success", "Session marked as complete")
            self.refresh()

    def export_all_sessions(self):
        """Export all visible sessions."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                # Get current filter
                exp_filter = self.experiment_var.get()
                experiment_id = None
                if exp_filter != "All Experiments" and exp_filter in self.experiment_map:
                    experiment_id = self.experiment_map[exp_filter]

                # Get all sessions based on current filter
                status_filter = self.status_var.get()
                if status_filter == "Active":
                    sessions = self.get_active_sessions(experiment_id)
                elif status_filter == "Completed Today":
                    sessions = self.get_completed_today_sessions(experiment_id)
                else:
                    sessions = self.get_all_recent_sessions(experiment_id)

                # Export summary
                with open(filename, 'w', newline='') as f:
                    fieldnames = ['participant_code', 'experiment', 'session_number',
                                 'status', 'started', 'duration_minutes', 'trials_completed']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for session in sessions:
                        # Calculate duration
                        duration = None
                        if session.get('start_time') and session.get('end_time'):
                            start = datetime.fromisoformat(session['start_time'])
                            end = datetime.fromisoformat(session['end_time'])
                            duration = int((end - start).total_seconds() / 60)

                        # Count trials
                        trials = self.db_manager.get_session_trials(session['id'])

                        writer.writerow({
                            'participant_code': session['participant_code'],
                            'experiment': session.get('experiment_code', 'N/A'),
                            'session_number': session['session_number'],
                            'status': 'Completed' if session['completed'] else 'Active',
                            'started': session['session_date'],
                            'duration_minutes': duration,
                            'trials_completed': len(trials)
                        })

                messagebox.showinfo("Success", f"Session data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

    def toggle_auto_refresh(self):
        """Toggle automatic refresh."""
        if self.auto_refresh_var.get():
            self.schedule_refresh()
        else:
            # Cancel any pending refresh
            if hasattr(self, 'refresh_job'):
                self.after_cancel(self.refresh_job)

    def schedule_refresh(self):
        """Schedule next automatic refresh."""
        if self.auto_refresh_var.get():
            self.refresh()
            # Schedule next refresh in 30 seconds
            self.refresh_job = self.after(30000, self.schedule_refresh)