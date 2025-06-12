"""
Session Manager UI for Risk Tasks Client - Researcher Interface
Handles session monitoring, data export, and session management.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime, timedelta
import pandas as pd
import json
from pathlib import Path
import csv

from database.db_manager import DatabaseManager
from database.models import TaskType, Session
from utils.task_scheduler import TaskScheduler


class SessionManager(ctk.CTkFrame):
    """UI component for monitoring and managing experimental sessions."""

    def __init__(self, parent, db_manager: DatabaseManager, task_scheduler: TaskScheduler):
        super().__init__(parent)
        self.db_manager = db_manager
        self.task_scheduler = task_scheduler
        self.current_session_id = None

        # Setup UI
        self.setup_ui()

        # Load data
        self.refresh()

    def setup_ui(self):
        """Setup the session manager interface."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Session Monitoring & Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Main container with tabs
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Create tab view
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.pack(fill="both", expand=True)

        # Tab 1: Active Sessions
        self.active_tab = self.tabview.add("Active Sessions")
        self.create_active_sessions_tab()

        # Tab 2: Session History
        self.history_tab = self.tabview.add("Session History")
        self.create_history_tab()

        # Tab 3: Session Analytics
        self.analytics_tab = self.tabview.add("Analytics")
        self.create_analytics_tab()

    def create_active_sessions_tab(self):
        """Create the active sessions monitoring tab."""
        # Header with refresh button
        header_frame = ctk.CTkFrame(self.active_tab)
        header_frame.pack(fill="x", pady=(10, 10))

        active_label = ctk.CTkLabel(
            header_frame,
            text="Currently Active Sessions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        active_label.pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            command=self.refresh_active_sessions,
            width=100
        )
        refresh_btn.pack(side="right")

        # Session statistics
        stats_frame = ctk.CTkFrame(self.active_tab)
        stats_frame.pack(fill="x", pady=10)

        self.stats_labels = {}
        stats_data = [
            ('active', 'Active Sessions: 0'),
            ('overdue', 'Overdue: 0'),
            ('today', 'Started Today: 0')
        ]

        for key, text in stats_data:
            label = ctk.CTkLabel(stats_frame, text=text, font=ctk.CTkFont(size=14))
            label.pack(side="left", padx=20)
            self.stats_labels[key] = label

        # Active sessions list
        list_frame = ctk.CTkFrame(self.active_tab)
        list_frame.pack(fill="both", expand=True, pady=10)

        # Create Treeview for active sessions
        columns = ("Participant", "Session", "Started", "Duration", "Progress", "Status")
        self.active_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=12
        )

        # Configure columns
        self.active_tree.heading("Participant", text="Participant")
        self.active_tree.heading("Session", text="Session")
        self.active_tree.heading("Started", text="Started")
        self.active_tree.heading("Duration", text="Duration")
        self.active_tree.heading("Progress", text="Progress")
        self.active_tree.heading("Status", text="Status")

        self.active_tree.column("Participant", width=120)
        self.active_tree.column("Session", width=80)
        self.active_tree.column("Started", width=150)
        self.active_tree.column("Duration", width=100)
        self.active_tree.column("Progress", width=150)
        self.active_tree.column("Status", width=100)

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

        # Action buttons
        action_frame = ctk.CTkFrame(self.active_tab)
        action_frame.pack(fill="x", pady=10)

        self.view_details_btn = ctk.CTkButton(
            action_frame,
            text="View Details",
            command=self.view_session_details,
            state="disabled"
        )
        self.view_details_btn.pack(side="left", padx=5)

        self.export_session_btn = ctk.CTkButton(
            action_frame,
            text="Export Session Data",
            command=self.export_session_data,
            state="disabled"
        )
        self.export_session_btn.pack(side="left", padx=5)

        self.mark_complete_btn = ctk.CTkButton(
            action_frame,
            text="Mark Complete",
            command=self.mark_complete,
            state="disabled",
            fg_color="green"
        )
        self.mark_complete_btn.pack(side="left", padx=5)

        self.send_reminder_btn = ctk.CTkButton(
            action_frame,
            text="Send Reminder",
            command=self.send_reminder,
            state="disabled",
            fg_color="orange"
        )
        self.send_reminder_btn.pack(side="left", padx=5)

    def create_history_tab(self):
        """Create the session history tab."""
        # Filter controls
        filter_frame = ctk.CTkFrame(self.history_tab)
        filter_frame.pack(fill="x", pady=10)

        # Date range filter
        date_label = ctk.CTkLabel(filter_frame, text="Date Range:")
        date_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.date_filter_var = tk.StringVar(value="All Time")
        date_filter = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.date_filter_var,
            values=["All Time", "Today", "This Week", "This Month", "Custom"],
            command=self.on_date_filter_changed
        )
        date_filter.grid(row=0, column=1, padx=5, pady=5)

        # Status filter
        status_label = ctk.CTkLabel(filter_frame, text="Status:")
        status_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.status_filter_var = tk.StringVar(value="All")
        status_filter = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.status_filter_var,
            values=["All", "Completed", "Incomplete", "Overdue"],
            command=self.refresh_history
        )
        status_filter.grid(row=0, column=3, padx=5, pady=5)

        # Search
        search_label = ctk.CTkLabel(filter_frame, text="Search:")
        search_label.grid(row=0, column=4, padx=5, pady=5, sticky="e")

        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            filter_frame,
            textvariable=self.search_var,
            placeholder_text="Participant code..."
        )
        search_entry.grid(row=0, column=5, padx=5, pady=5)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_history())

        # History list
        history_frame = ctk.CTkFrame(self.history_tab)
        history_frame.pack(fill="both", expand=True, pady=10)

        columns = ("ID", "Participant", "Session", "Date", "Duration", "Tasks", "Trials", "Status")
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",
            height=15
        )

        # Configure columns
        for col in columns:
            self.history_tree.heading(col, text=col)
            if col == "ID":
                self.history_tree.column(col, width=50)
            elif col == "Tasks":
                self.history_tree.column(col, width=200)
            else:
                self.history_tree.column(col, width=100)

        # Scrollbar
        h_scrollbar = ttk.Scrollbar(
            history_frame,
            orient="vertical",
            command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=h_scrollbar.set)

        self.history_tree.pack(side="left", fill="both", expand=True)
        h_scrollbar.pack(side="right", fill="y")

        # Export buttons
        export_frame = ctk.CTkFrame(self.history_tab)
        export_frame.pack(fill="x", pady=10)

        export_all_btn = ctk.CTkButton(
            export_frame,
            text="Export All History",
            command=self.export_all_history
        )
        export_all_btn.pack(side="left", padx=5)

        export_filtered_btn = ctk.CTkButton(
            export_frame,
            text="Export Filtered Results",
            command=self.export_filtered_history
        )
        export_filtered_btn.pack(side="left", padx=5)

    def create_analytics_tab(self):
        """Create the session analytics tab."""
        # Summary statistics
        summary_frame = ctk.CTkFrame(self.analytics_tab)
        summary_frame.pack(fill="x", pady=10)

        summary_label = ctk.CTkLabel(
            summary_frame,
            text="Session Statistics",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        summary_label.pack(pady=10)

        self.summary_text = ctk.CTkTextbox(summary_frame, height=200)
        self.summary_text.pack(fill="x", padx=20, pady=10)

        # Completion rates
        rates_frame = ctk.CTkFrame(self.analytics_tab)
        rates_frame.pack(fill="x", pady=10)

        rates_label = ctk.CTkLabel(
            rates_frame,
            text="Completion Rates by Task",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        rates_label.pack(pady=10)

        self.rates_text = ctk.CTkTextbox(rates_frame, height=150)
        self.rates_text.pack(fill="x", padx=20, pady=10)

        # Refresh button
        refresh_analytics_btn = ctk.CTkButton(
            self.analytics_tab,
            text="Refresh Analytics",
            command=self.refresh_analytics,
            width=200
        )
        refresh_analytics_btn.pack(pady=20)

    def refresh(self):
        """Refresh all data."""
        self.refresh_active_sessions()
        self.refresh_history()
        self.refresh_analytics()

    def refresh_active_sessions(self):
        """Refresh the active sessions list."""
        # Clear current items
        for item in self.active_tree.get_children():
            self.active_tree.delete(item)

        # Get pending sessions
        pending_sessions = self.db_manager.get_pending_sessions()

        # Update statistics
        active_count = len(pending_sessions)
        overdue_count = 0
        today_count = 0

        today = datetime.now().date()

        for session in pending_sessions:
            session_date = datetime.fromisoformat(session['session_date'])

            # Check if started today
            if session_date.date() == today:
                today_count += 1

            # Check if overdue (more than 14 days old)
            days_old = (datetime.now() - session_date).days
            is_overdue = days_old > 14
            if is_overdue:
                overdue_count += 1

            # Calculate duration if session has start time
            duration = "N/A"
            if session.get('start_time'):
                start_time = datetime.fromisoformat(session['start_time'])
                duration_mins = int((datetime.now() - start_time).total_seconds() / 60)
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
                task_display = TaskType.get_display_name(TaskType(task))
                progress_parts.append(f"{task_display}: {count}/30")

            progress = " | ".join(progress_parts)

            # Determine status
            status = "Overdue" if is_overdue else "Active"

            # Format tasks
            tasks_str = ", ".join([
                TaskType.get_display_name(TaskType(task))
                for task in session['tasks_assigned']
            ])

            # Insert into tree
            self.active_tree.insert(
                "",
                "end",
                values=(
                    session['participant_code'],
                    f"Session {session['session_number']}",
                    session_date.strftime("%Y-%m-%d %H:%M"),
                    duration,
                    progress,
                    status
                ),
                tags=(session['id'], "overdue" if is_overdue else "normal")
            )

        # Update statistics labels
        self.stats_labels['active'].configure(text=f"Active Sessions: {active_count}")
        self.stats_labels['overdue'].configure(text=f"Overdue: {overdue_count}")
        self.stats_labels['today'].configure(text=f"Started Today: {today_count}")

        # Color code overdue sessions
        self.active_tree.tag_configure("overdue", foreground="red")

    def refresh_history(self):
        """Refresh the session history."""
        # Clear current items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # Get all participants
        participants = self.db_manager.get_all_participants()

        # Apply filters
        search_term = self.search_var.get().lower()
        status_filter = self.status_filter_var.get()
        date_filter = self.date_filter_var.get()

        # Determine date range
        start_date = None
        end_date = datetime.now()

        if date_filter == "Today":
            start_date = datetime.now().replace(hour=0, minute=0, second=0)
        elif date_filter == "This Week":
            start_date = datetime.now() - timedelta(days=7)
        elif date_filter == "This Month":
            start_date = datetime.now() - timedelta(days=30)

        # Process each participant
        for participant in participants:
            # Apply search filter
            if search_term and search_term not in participant['participant_code'].lower():
                continue

            sessions = self.db_manager.get_participant_sessions(participant['id'])

            for session in sessions:
                session_date = datetime.fromisoformat(session['session_date'])

                # Apply date filter
                if start_date and session_date < start_date:
                    continue

                # Apply status filter
                if status_filter == "Completed" and not session['completed']:
                    continue
                elif status_filter == "Incomplete" and session['completed']:
                    continue
                elif status_filter == "Overdue":
                    if session['completed'] or (datetime.now() - session_date).days <= 14:
                        continue

                # Calculate duration
                duration = "N/A"
                if session.get('start_time') and session.get('end_time'):
                    start = datetime.fromisoformat(session['start_time'])
                    end = datetime.fromisoformat(session['end_time'])
                    duration_mins = int((end - start).total_seconds() / 60)
                    duration = f"{duration_mins} min"

                # Get trial count
                trials = self.db_manager.get_session_trials(session['id'])
                trial_count = len(trials)

                # Format tasks
                tasks_str = ", ".join([
                    TaskType.get_display_name(TaskType(task))
                    for task in session['tasks_assigned']
                ])

                # Determine status
                if session['completed']:
                    status = "Completed"
                elif (datetime.now() - session_date).days > 14:
                    status = "Overdue"
                else:
                    status = "Incomplete"

                # Insert into tree
                self.history_tree.insert(
                    "",
                    "end",
                    values=(
                        session['id'],
                        participant['participant_code'],
                        f"Session {session['session_number']}",
                        session_date.strftime("%Y-%m-%d %H:%M"),
                        duration,
                        tasks_str,
                        trial_count,
                        status
                    ),
                    tags=(status.lower(),)
                )

        # Color code by status
        self.history_tree.tag_configure("completed", foreground="green")
        self.history_tree.tag_configure("overdue", foreground="red")
        self.history_tree.tag_configure("incomplete", foreground="orange")

    def refresh_analytics(self):
        """Refresh session analytics."""
        # Get statistics
        stats = self.db_manager.get_statistics()
        task_stats = self.db_manager.get_task_statistics()

        # Summary statistics
        summary_lines = [
            "=== Overall Session Statistics ===\n",
            f"Total Sessions Started: {stats['completed_sessions'] + stats['active_sessions']}",
            f"Completed Sessions: {stats['completed_sessions']}",
            f"Active Sessions: {stats['active_sessions']}",
            f"Completion Rate: {stats['completed_sessions'] / max(1, stats['completed_sessions'] + stats['active_sessions']) * 100:.1f}%",
            f"\nTotal Trials Recorded: {stats['total_trials']}",
            f"Average Trials per Session: {stats['total_trials'] / max(1, stats['completed_sessions']):.1f}"
        ]

        # Calculate average session duration
        all_sessions = []
        participants = self.db_manager.get_all_participants()
        for p in participants:
            sessions = self.db_manager.get_participant_sessions(p['id'])
            all_sessions.extend(sessions)

        completed_sessions = [s for s in all_sessions if s['completed'] and s.get('start_time') and s.get('end_time')]
        if completed_sessions:
            total_duration = 0
            for s in completed_sessions:
                start = datetime.fromisoformat(s['start_time'])
                end = datetime.fromisoformat(s['end_time'])
                total_duration += (end - start).total_seconds()

            avg_duration_mins = total_duration / len(completed_sessions) / 60
            summary_lines.append(f"Average Session Duration: {avg_duration_mins:.1f} minutes")

        # Update summary text
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", "\n".join(summary_lines))

        # Task completion rates
        rates_lines = ["=== Task Completion Rates ===\n"]

        for task_name, task_data in task_stats.items():
            display_name = TaskType.get_display_name(TaskType(task_name))

            # Calculate completion rate (assuming 30 trials = complete)
            complete_count = task_data['trial_count'] // 30
            started_count = len(set(t['session_id'] for p in participants
                                   for s in self.db_manager.get_participant_sessions(p['id'])
                                   for t in self.db_manager.get_session_trials(s['id'])
                                   if t['task_name'] == task_name))

            completion_rate = (complete_count / max(1, started_count)) * 100 if started_count > 0 else 0

            rates_lines.append(f"\n{display_name}:")
            rates_lines.append(f"  Total Trials: {task_data['trial_count']}")
            rates_lines.append(f"  Sessions Started: {started_count}")
            rates_lines.append(f"  Sessions Completed: {complete_count}")
            rates_lines.append(f"  Completion Rate: {completion_rate:.1f}%")
            rates_lines.append(f"  Success Rate: {task_data['success_rate'] * 100:.1f}%")

        # Update rates text
        self.rates_text.delete("1.0", tk.END)
        self.rates_text.insert("1.0", "\n".join(rates_lines))

    def on_active_session_select(self, event):
        """Handle selection of an active session."""
        selection = self.active_tree.selection()
        if selection:
            item = self.active_tree.item(selection[0])
            self.current_session_id = item['tags'][0]

            # Enable action buttons
            self.view_details_btn.configure(state="normal")
            self.export_session_btn.configure(state="normal")
            self.mark_complete_btn.configure(state="normal")
            self.send_reminder_btn.configure(state="normal")
        else:
            # Disable action buttons
            self.view_details_btn.configure(state="disabled")
            self.export_session_btn.configure(state="disabled")
            self.mark_complete_btn.configure(state="disabled")
            self.send_reminder_btn.configure(state="disabled")

    def view_session_details(self):
        """View detailed information about the selected session."""
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

        # Get trials
        trials = self.db_manager.get_session_trials(session['id'])

        # Create details window
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"Session Details - {session['participant_code']} Session {session['session_number']}")
        details_window.geometry("800x600")

        # Session info
        info_frame = ctk.CTkFrame(details_window)
        info_frame.pack(fill="x", padx=20, pady=20)

        info_label = ctk.CTkLabel(
            info_frame,
            text=f"Session Details",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        info_label.pack(pady=10)

        # Details text
        details_text = ctk.CTkTextbox(info_frame, height=150)
        details_text.pack(fill="x", pady=10)

        session_date = datetime.fromisoformat(session['session_date'])
        details_lines = [
            f"Participant: {session['participant_code']}",
            f"Session Number: {session['session_number']}",
            f"Started: {session_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Days Since Start: {(datetime.now() - session_date).days}",
            f"Tasks Assigned: {', '.join([TaskType.get_display_name(TaskType(t)) for t in session['tasks_assigned']])}",
            f"Total Trials Recorded: {len(trials)}"
        ]

        details_text.insert("1.0", "\n".join(details_lines))
        details_text.configure(state="disabled")

        # Trial details by task
        trials_frame = ctk.CTkFrame(details_window)
        trials_frame.pack(fill="both", expand=True, padx=20, pady=20)

        trials_label = ctk.CTkLabel(
            trials_frame,
            text="Trial Progress by Task",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        trials_label.pack(pady=10)

        # Create tree for trials
        columns = ("Task", "Trials", "Avg Risk", "Total Points", "Success Rate")
        trials_tree = ttk.Treeview(
            trials_frame,
            columns=columns,
            show="headings",
            height=8
        )

        for col in columns:
            trials_tree.heading(col, text=col)
            trials_tree.column(col, width=150)

        trials_tree.pack(fill="both", expand=True, pady=10)

        # Aggregate trial data by task
        task_data = {}
        for trial in trials:
            task = trial['task_name']
            if task not in task_data:
                task_data[task] = {
                    'count': 0,
                    'total_risk': 0,
                    'total_points': 0,
                    'successes': 0
                }

            task_data[task]['count'] += 1
            task_data[task]['total_risk'] += trial['risk_level']
            task_data[task]['total_points'] += trial['points_earned']
            if trial['outcome'] == 'success':
                task_data[task]['successes'] += 1

        # Add to tree
        for task in session['tasks_assigned']:
            if task in task_data:
                data = task_data[task]
                avg_risk = data['total_risk'] / data['count']
                success_rate = (data['successes'] / data['count']) * 100

                trials_tree.insert(
                    "",
                    "end",
                    values=(
                        TaskType.get_display_name(TaskType(task)),
                        f"{data['count']}/30",
                        f"{avg_risk:.3f}",
                        data['total_points'],
                        f"{success_rate:.1f}%"
                    )
                )
            else:
                trials_tree.insert(
                    "",
                    "end",
                    values=(
                        TaskType.get_display_name(TaskType(task)),
                        "0/30",
                        "N/A",
                        "0",
                        "N/A"
                    )
                )

        # Close button
        close_btn = ctk.CTkButton(
            details_window,
            text="Close",
            command=details_window.destroy
        )
        close_btn.pack(pady=20)

    def export_session_data(self):
        """Export data for the selected session."""
        if not self.current_session_id:
            return

        # Get session and trial data
        trials = self.db_manager.get_session_trials(self.current_session_id)

        if not trials:
            messagebox.showinfo("No Data", "This session has no trial data to export.")
            return

        # Ask for file location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    fieldnames = ['session_id', 'task_name', 'trial_number', 'risk_level',
                                  'points_earned', 'outcome', 'reaction_time', 'timestamp']
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
                messagebox.showerror("Error", f"Failed to export data: {e}")

    def mark_complete(self):
        """Mark the selected session as complete."""
        if not self.current_session_id:
            return

        result = messagebox.askyesno(
            "Confirm Completion",
            "Are you sure you want to mark this session as complete?\n"
            "This action cannot be undone."
        )

        if result:
            self.db_manager.complete_session(self.current_session_id)
            messagebox.showinfo("Success", "Session marked as complete")
            self.refresh()

    def send_reminder(self):
        """Send a reminder for the selected session (placeholder)."""
        if not self.current_session_id:
            return

        messagebox.showinfo(
            "Reminder Feature",
            "Reminder functionality would be implemented here.\n"
            "This could send an email or notification to the participant."
        )

    def on_date_filter_changed(self, choice):
        """Handle date filter change."""
        if choice == "Custom":
            messagebox.showinfo(
                "Custom Date Range",
                "Custom date range selection would be implemented here."
            )
        else:
            self.refresh_history()

    def export_all_history(self):
        """Export all session history."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                # Get all sessions
                all_sessions = []
                participants = self.db_manager.get_all_participants()

                for participant in participants:
                    sessions = self.db_manager.get_participant_sessions(participant['id'])
                    for session in sessions:
                        session['participant_code'] = participant['participant_code']
                        all_sessions.append(session)

                # Create DataFrame
                df = pd.DataFrame(all_sessions)

                # Add computed columns
                df['duration_minutes'] = df.apply(
                    lambda row: (datetime.fromisoformat(row['end_time']) -
                                datetime.fromisoformat(row['start_time'])).total_seconds() / 60
                    if row.get('start_time') and row.get('end_time') else None,
                    axis=1
                )

                # Export to CSV
                df.to_csv(filename, index=False)
                messagebox.showinfo("Success", f"History exported to {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export history: {e}")

    def export_filtered_history(self):
        """Export filtered session history."""
        # Get visible items from tree
        items = self.history_tree.get_children()

        if not items:
            messagebox.showinfo("No Data", "No data to export.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)

                    # Write headers
                    headers = ["Session ID", "Participant", "Session", "Date",
                              "Duration", "Tasks", "Trials", "Status"]
                    writer.writerow(headers)

                    # Write data
                    for item in items:
                        values = self.history_tree.item(item)['values']
                        writer.writerow(values)

                messagebox.showinfo("Success", f"Filtered data exported to {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")