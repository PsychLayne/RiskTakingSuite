"""
Data Viewer for Risk Tasks Client - Modified Version
Provides data analysis, visualization, and export functionality.
Features checkbox-based task selection and simplified analysis options.
Updated to handle standardized data fields across all tasks.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import csv
import json
from typing import Dict, List, Optional
import seaborn as sns

from database.db_manager import DatabaseManager
from database.models import TaskType

# Set matplotlib style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class DataViewer(ctk.CTkFrame):
    """UI component for data analysis and visualization."""

    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_participant_id = None
        self.current_experiment_id = None
        self.current_data = None
        self.view_all_var = tk.BooleanVar(value=False)  # Keep for compatibility

        # Task selection variables
        self.task_vars = {}
        for task in TaskType:
            self.task_vars[task.value] = tk.BooleanVar(value=True)  # All tasks selected by default

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the data viewer interface."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Data Analysis",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Main container with three columns
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Left panel - Participant selection and filters
        left_panel = ctk.CTkFrame(main_container, width=250)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        self.create_filter_panel(left_panel)

        # Middle panel - Data visualization
        middle_panel = ctk.CTkFrame(main_container)
        middle_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.create_visualization_panel(middle_panel)

        # Right panel - Statistics and export
        right_panel = ctk.CTkFrame(main_container, width=300)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        self.create_stats_panel(right_panel)

    def create_filter_panel(self, parent):
        """Create the filter and selection panel."""
        # Section header
        filter_label = ctk.CTkLabel(
            parent,
            text="Filters",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        filter_label.pack(pady=10)

        # View mode selection
        view_mode_frame = ctk.CTkFrame(parent)
        view_mode_frame.pack(fill="x", padx=10, pady=10)

        view_mode_label = ctk.CTkLabel(
            view_mode_frame,
            text="View Mode:",
            anchor="w"
        )
        view_mode_label.pack(fill="x", pady=(0, 5))

        self.view_mode_var = tk.StringVar(value="Participant")
        view_mode_menu = ctk.CTkOptionMenu(
            view_mode_frame,
            variable=self.view_mode_var,
            values=["Participant", "All Participants", "Experiment"],
            command=self.on_view_mode_changed,
            width=200
        )
        view_mode_menu.pack(fill="x")

        # Participant selection
        self.participant_frame = ctk.CTkFrame(parent)
        self.participant_frame.pack(fill="x", padx=10, pady=10)

        participant_label = ctk.CTkLabel(
            self.participant_frame,
            text="Participant:",
            anchor="w"
        )
        participant_label.pack(fill="x", pady=(0, 5))

        self.participant_var = tk.StringVar()
        self.participant_menu = ctk.CTkComboBox(
            self.participant_frame,
            variable=self.participant_var,
            command=self.on_participant_selected,
            width=200
        )
        self.participant_menu.pack(fill="x")

        # Experiment selection (initially hidden)
        self.experiment_frame = ctk.CTkFrame(parent)

        experiment_label = ctk.CTkLabel(
            self.experiment_frame,
            text="Experiment:",
            anchor="w"
        )
        experiment_label.pack(fill="x", pady=(0, 5))

        self.experiment_var = tk.StringVar()
        self.experiment_menu = ctk.CTkComboBox(
            self.experiment_frame,
            variable=self.experiment_var,
            command=self.on_experiment_selected,
            width=200
        )
        self.experiment_menu.pack(fill="x")

        # Task selection with checkboxes
        task_frame = ctk.CTkFrame(parent)
        task_frame.pack(fill="x", padx=10, pady=10)

        task_label = ctk.CTkLabel(
            task_frame,
            text="Select Tasks:",
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        )
        task_label.pack(fill="x", pady=(0, 5))

        # Checkbox frame
        checkbox_frame = ctk.CTkFrame(task_frame)
        checkbox_frame.pack(fill="x", pady=5)

        # Create checkboxes for each task
        for task in TaskType:
            checkbox = ctk.CTkCheckBox(
                checkbox_frame,
                text=TaskType.get_display_name(task),
                variable=self.task_vars[task.value],
                command=self.on_task_selection_changed,
                width=180
            )
            checkbox.pack(anchor="w", pady=2)

        # Select/Deselect all buttons
        button_frame = ctk.CTkFrame(task_frame)
        button_frame.pack(fill="x", pady=5)

        select_all_btn = ctk.CTkButton(
            button_frame,
            text="Select All",
            command=self.select_all_tasks,
            width=80,
            height=25
        )
        select_all_btn.pack(side="left", padx=5)

        deselect_all_btn = ctk.CTkButton(
            button_frame,
            text="Deselect All",
            command=self.deselect_all_tasks,
            width=80,
            height=25
        )
        deselect_all_btn.pack(side="left", padx=5)

        # Session filter
        session_frame = ctk.CTkFrame(parent)
        session_frame.pack(fill="x", padx=10, pady=10)

        session_label = ctk.CTkLabel(
            session_frame,
            text="Session Filter:",
            anchor="w"
        )
        session_label.pack(fill="x", pady=(0, 5))

        self.session_var = tk.StringVar(value="All Sessions")
        self.session_menu = ctk.CTkOptionMenu(
            session_frame,
            variable=self.session_var,
            values=["All Sessions"],
            command=self.on_filter_changed,
            width=200
        )
        self.session_menu.pack(fill="x")

        # Analysis type - simplified to your 3 options
        analysis_frame = ctk.CTkFrame(parent)
        analysis_frame.pack(fill="x", padx=10, pady=10)

        analysis_label = ctk.CTkLabel(
            analysis_frame,
            text="Analysis Type:",
            anchor="w"
        )
        analysis_label.pack(fill="x", pady=(0, 5))

        self.analysis_var = tk.StringVar(value="Risk Profile")
        analysis_values = [
            "Risk Profile",
            "Raw Actions/Pumps",
            "Correlation Matrix"
        ]
        self.analysis_menu = ctk.CTkOptionMenu(
            analysis_frame,
            variable=self.analysis_var,
            values=analysis_values,
            command=self.on_analysis_changed,
            width=200
        )
        self.analysis_menu.pack(fill="x")

        # Refresh button
        refresh_button = ctk.CTkButton(
            parent,
            text="Refresh Data",
            command=self.refresh,
            width=200
        )
        refresh_button.pack(pady=20)

    def select_all_tasks(self):
        """Select all task checkboxes."""
        for var in self.task_vars.values():
            var.set(True)
        self.on_task_selection_changed()

    def deselect_all_tasks(self):
        """Deselect all task checkboxes."""
        for var in self.task_vars.values():
            var.set(False)
        self.on_task_selection_changed()

    def on_task_selection_changed(self):
        """Handle task selection changes."""
        # Check if at least one task is selected
        if not any(var.get() for var in self.task_vars.values()):
            messagebox.showwarning("No Tasks Selected", "Please select at least one task")
            return

        if self.current_participant_id or self.view_all_var.get() or self.current_experiment_id:
            self.load_data()
            self.update_visualization()
            self.update_statistics()

    def create_visualization_panel(self, parent):
        """Create the visualization panel."""
        # Header
        viz_label = ctk.CTkLabel(
            parent,
            text="Data Visualization",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        viz_label.pack(pady=10)

        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.patch.set_facecolor('#2b2b2b')

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Create toolbar
        toolbar_frame = ctk.CTkFrame(parent)
        toolbar_frame.pack(fill="x", padx=10)

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

    def create_stats_panel(self, parent):
        """Create the statistics and export panel."""
        # Header
        stats_label = ctk.CTkLabel(
            parent,
            text="Statistics",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        stats_label.pack(pady=10)

        # Statistics display
        self.stats_frame = ctk.CTkScrollableFrame(parent, height=300)
        self.stats_frame.pack(fill="x", padx=10, pady=10)

        self.stats_text = ctk.CTkTextbox(self.stats_frame, height=250)
        self.stats_text.pack(fill="both", expand=True)

        # Export section
        export_label = ctk.CTkLabel(
            parent,
            text="Export Options",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        export_label.pack(pady=(20, 10))

        export_frame = ctk.CTkFrame(parent)
        export_frame.pack(fill="x", padx=10, pady=10)

        # Export buttons
        export_csv_btn = ctk.CTkButton(
            export_frame,
            text="Export to CSV",
            command=self.export_csv,
            width=120
        )
        export_csv_btn.grid(row=0, column=0, padx=5, pady=5)

        export_excel_btn = ctk.CTkButton(
            export_frame,
            text="Export to Excel",
            command=self.export_excel,
            width=120
        )
        export_excel_btn.grid(row=0, column=1, padx=5, pady=5)

        export_json_btn = ctk.CTkButton(
            export_frame,
            text="Export to JSON",
            command=self.export_json,
            width=120
        )
        export_json_btn.grid(row=1, column=0, padx=5, pady=5)

        save_plot_btn = ctk.CTkButton(
            export_frame,
            text="Save Plot",
            command=self.save_plot,
            width=120
        )
        save_plot_btn.grid(row=1, column=1, padx=5, pady=5)

        # Report generation
        report_label = ctk.CTkLabel(
            parent,
            text="Reports",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        report_label.pack(pady=(20, 10))

        report_frame = ctk.CTkFrame(parent)
        report_frame.pack(fill="x", padx=10, pady=10)

        participant_report_btn = ctk.CTkButton(
            report_frame,
            text="Participant Report",
            command=self.generate_participant_report,
            width=250
        )
        participant_report_btn.pack(pady=5)

        summary_report_btn = ctk.CTkButton(
            report_frame,
            text="Summary Report",
            command=self.generate_summary_report,
            width=250
        )
        summary_report_btn.pack(pady=5)

    def get_selected_tasks(self) -> List[str]:
        """Get list of currently selected tasks."""
        return [task for task, var in self.task_vars.items() if var.get()]

    def refresh(self):
        """Refresh all data and update displays."""
        view_mode = self.view_mode_var.get()

        if view_mode == "Participant":
            self.load_participants()
            if self.current_participant_id:
                self.load_data()
                self.update_visualization()
                self.update_statistics()
        elif view_mode == "All Participants":
            self.load_data()
            self.update_visualization()
            self.update_statistics()
        elif view_mode == "Experiment":
            self.load_experiments()
            if self.current_experiment_id:
                self.load_data()
                self.update_visualization()
                self.update_statistics()

    def on_view_mode_changed(self, choice):
        """Handle view mode change."""
        if choice == "Participant":
            self.participant_frame.pack(fill="x", padx=10, pady=10)
            self.experiment_frame.pack_forget()
            self.view_all_var.set(False)
            self.load_participants()
            self.current_experiment_id = None
            if self.current_participant_id:
                self.load_participant_sessions()
        elif choice == "All Participants":
            self.participant_frame.pack_forget()
            self.experiment_frame.pack_forget()
            self.view_all_var.set(True)
            self.current_participant_id = None
            self.current_experiment_id = None
            self.session_var.set("All Sessions")
            self.session_menu.configure(values=["All Sessions"])
        elif choice == "Experiment":
            self.participant_frame.pack_forget()
            self.experiment_frame.pack(fill="x", padx=10, pady=10)
            self.view_all_var.set(False)
            self.current_participant_id = None
            self.load_experiments()
            self.session_var.set("All Sessions")
            self.session_menu.configure(values=["All Sessions"])

        self.refresh()

    def load_experiments(self):
        """Load experiments into the dropdown."""
        experiments = self.db_manager.get_active_experiments()

        values = ["Select experiment..."]
        self.experiment_map = {}

        for exp in experiments:
            display_text = f"{exp['experiment_code']}: {exp['name']} ({exp['enrolled_count']} participants)"
            values.append(display_text)
            self.experiment_map[display_text] = exp['id']

        self.experiment_menu.configure(values=values)
        if not self.current_experiment_id:
            self.experiment_menu.set("Select experiment...")

    def on_experiment_selected(self, choice):
        """Handle experiment selection."""
        if choice in self.experiment_map:
            self.current_experiment_id = self.experiment_map[choice]
            self.refresh()

    def load_participants(self):
        """Load participants into the dropdown."""
        participants = self.db_manager.get_all_participants()

        values = ["Select participant..."]
        self.participant_map = {}

        for p in participants:
            display_text = f"{p['participant_code']} ({p['completed_sessions']} sessions)"
            values.append(display_text)
            self.participant_map[display_text] = p['id']

        self.participant_menu.configure(values=values)
        if not self.current_participant_id:
            self.participant_menu.set("Select participant...")

    def on_participant_selected(self, choice):
        """Handle participant selection."""
        if choice in self.participant_map:
            self.current_participant_id = self.participant_map[choice]
            self.view_all_var.set(False)
            self.load_participant_sessions()
            self.refresh()

    def load_participant_sessions(self):
        """Load sessions for the selected participant."""
        if not self.current_participant_id:
            return

        sessions = self.db_manager.get_participant_sessions(self.current_participant_id)

        session_values = ["All Sessions"]
        for session in sessions:
            session_values.append(f"Session {session['session_number']}")

        self.session_menu.configure(values=session_values)
        self.session_var.set("All Sessions")

    def on_filter_changed(self, *args):
        """Handle filter changes."""
        if self.current_participant_id or self.view_all_var.get() or self.current_experiment_id:
            self.load_data()
            self.update_visualization()
            self.update_statistics()

    def on_analysis_changed(self, *args):
        """Handle analysis type change."""
        self.update_visualization()

    def load_data(self):
        """Load data based on current filters."""
        view_mode = self.view_mode_var.get()

        if view_mode == "All Participants":
            # Load data for all participants
            self.current_data = self.load_all_participants_data()
        elif view_mode == "Participant" and self.current_participant_id:
            # Load data for single participant
            self.current_data = self.load_single_participant_data()
        elif view_mode == "Experiment" and self.current_experiment_id:
            # Load data for experiment
            self.current_data = self.load_experiment_data()
        else:
            self.current_data = None

    def extract_action_count(self, trial_data: dict, additional: dict) -> int:
        """Extract action count from additional data with standardized field support."""
        task_name = trial_data.get('task_name', '')

        # First try the standardized 'actions' field
        if 'actions' in additional:
            return additional['actions']

        # Fall back to task-specific fields for backward compatibility
        if task_name == 'bart':
            return additional.get('pumps', 0)
        elif task_name == 'ice_fishing':
            return additional.get('fish_caught', 0)
        elif task_name == 'mountain_mining':
            # Check both possible aliases
            return additional.get('ore_mined', additional.get('ore_collected', 0))
        elif task_name == 'spinning_bottle':
            # Check all possible aliases
            return additional.get('segments_added', additional.get('red_segments', 0))

        return 0

    def load_experiment_data(self):
        """Load data for all participants in an experiment."""
        data = []
        selected_tasks = self.get_selected_tasks()

        # Get experiment details
        experiment = self.db_manager.get_experiment(experiment_id=self.current_experiment_id)
        if not experiment:
            return None

        # Get all participants enrolled in this experiment
        participants = self.db_manager.get_all_participants()

        for participant in participants:
            # Check if participant is enrolled in this experiment
            participant_experiment = self.db_manager.get_participant_experiment(participant['id'])
            if not participant_experiment or participant_experiment['id'] != self.current_experiment_id:
                continue

            sessions = self.db_manager.get_participant_sessions(participant['id'])

            # Filter sessions that belong to this experiment
            for session in sessions:
                # Check if session has experiment_id
                if session.get('experiment_id') != self.current_experiment_id:
                    continue

                trials = self.db_manager.get_session_trials(session['id'])

                # Apply task filter
                trials = [t for t in trials if t['task_name'] in selected_tasks]

                for trial in trials:
                    trial_data = {
                        'participant_id': participant['id'],
                        'participant_code': participant['participant_code'],
                        'experiment_id': self.current_experiment_id,
                        'experiment_code': experiment['experiment_code'],
                        'session_id': session['id'],
                        'session_number': session['session_number'],
                        'task_name': trial['task_name'],
                        'trial_number': trial['trial_number'],
                        'risk_level': trial['risk_level'],
                        'points_earned': trial['points_earned'],
                        'outcome': trial['outcome'],
                        'reaction_time': trial['reaction_time'],
                        'timestamp': trial['timestamp']
                    }

                    # Parse additional_data if it exists
                    if trial.get('additional_data'):
                        try:
                            additional = json.loads(trial['additional_data']) if isinstance(trial['additional_data'], str) else trial['additional_data']
                            trial_data['additional_data'] = additional

                            # Extract action count using standardized method
                            trial_data['actions'] = self.extract_action_count(trial_data, additional)

                            # Extract other standardized fields if available
                            trial_data['action_limit'] = additional.get('action_limit', None)
                            trial_data['potential_points'] = additional.get('potential_points', None)
                            trial_data['total_banked'] = additional.get('total_banked', None)
                        except:
                            trial_data['actions'] = None
                    else:
                        trial_data['actions'] = None

                    data.append(trial_data)

        return pd.DataFrame(data) if data else None

    def load_single_participant_data(self):
        """Load data for a single participant."""
        data = []
        selected_tasks = self.get_selected_tasks()

        sessions = self.db_manager.get_participant_sessions(self.current_participant_id)

        # Apply session filter
        session_filter = self.session_var.get()
        if session_filter != "All Sessions":
            session_num = int(session_filter.split()[1])
            sessions = [s for s in sessions if s['session_number'] == session_num]

        for session in sessions:
            trials = self.db_manager.get_session_trials(session['id'])

            # Apply task filter
            trials = [t for t in trials if t['task_name'] in selected_tasks]

            for trial in trials:
                trial_data = {
                    'participant_id': self.current_participant_id,
                    'session_id': session['id'],
                    'session_number': session['session_number'],
                    'task_name': trial['task_name'],
                    'trial_number': trial['trial_number'],
                    'risk_level': trial['risk_level'],
                    'points_earned': trial['points_earned'],
                    'outcome': trial['outcome'],
                    'reaction_time': trial['reaction_time'],
                    'timestamp': trial['timestamp']
                }

                # Parse additional_data if it exists
                if trial.get('additional_data'):
                    try:
                        additional = json.loads(trial['additional_data']) if isinstance(trial['additional_data'], str) else trial['additional_data']
                        trial_data['additional_data'] = additional

                        # Extract action count using standardized method
                        trial_data['actions'] = self.extract_action_count(trial_data, additional)

                        # Extract other standardized fields if available
                        trial_data['action_limit'] = additional.get('action_limit', None)
                        trial_data['potential_points'] = additional.get('potential_points', None)
                        trial_data['total_banked'] = additional.get('total_banked', None)
                    except:
                        trial_data['actions'] = None
                else:
                    trial_data['actions'] = None

                data.append(trial_data)

        return pd.DataFrame(data) if data else None

    def load_all_participants_data(self):
        """Load data for all participants."""
        data = []
        selected_tasks = self.get_selected_tasks()

        participants = self.db_manager.get_all_participants()

        for participant in participants:
            sessions = self.db_manager.get_participant_sessions(participant['id'])

            for session in sessions:
                trials = self.db_manager.get_session_trials(session['id'])

                # Apply task filter
                trials = [t for t in trials if t['task_name'] in selected_tasks]

                for trial in trials:
                    trial_data = {
                        'participant_id': participant['id'],
                        'participant_code': participant['participant_code'],
                        'session_id': session['id'],
                        'session_number': session['session_number'],
                        'task_name': trial['task_name'],
                        'trial_number': trial['trial_number'],
                        'risk_level': trial['risk_level'],
                        'points_earned': trial['points_earned'],
                        'outcome': trial['outcome'],
                        'reaction_time': trial['reaction_time'],
                        'timestamp': trial['timestamp']
                    }

                    # Parse additional_data if it exists
                    if trial.get('additional_data'):
                        try:
                            additional = json.loads(trial['additional_data']) if isinstance(trial['additional_data'], str) else trial['additional_data']
                            trial_data['additional_data'] = additional

                            # Extract action count using standardized method
                            trial_data['actions'] = self.extract_action_count(trial_data, additional)

                            # Extract other standardized fields if available
                            trial_data['action_limit'] = additional.get('action_limit', None)
                            trial_data['potential_points'] = additional.get('potential_points', None)
                            trial_data['total_banked'] = additional.get('total_banked', None)
                        except:
                            trial_data['actions'] = None
                    else:
                        trial_data['actions'] = None

                    data.append(trial_data)

        return pd.DataFrame(data) if data else None

    def update_visualization(self):
        """Update the visualization based on selected analysis type."""
        self.figure.clear()

        if self.current_data is None or self.current_data.empty:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No data to display',
                    ha='center', va='center', fontsize=16, color='white')
            ax.set_facecolor('#2b2b2b')
            self.canvas.draw()
            return

        analysis_type = self.analysis_var.get()

        if analysis_type == "Risk Profile":
            self.plot_risk_profile()
        elif analysis_type == "Raw Actions/Pumps":
            self.plot_raw_actions()
        elif analysis_type == "Correlation Matrix":
            self.plot_correlation_matrix()

        self.canvas.draw()

    def plot_risk_profile(self):
        """Plot risk-taking profile over trials."""
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#3b3b3b')

        view_mode = self.view_mode_var.get()

        if view_mode in ["All Participants", "Experiment"]:
            # Plot average risk profile for multiple participants
            avg_risk = self.current_data.groupby('trial_number')['risk_level'].mean()
            std_risk = self.current_data.groupby('trial_number')['risk_level'].std()

            ax.plot(avg_risk.index, avg_risk.values, 'b-', linewidth=2, label='Average')
            ax.fill_between(avg_risk.index,
                            avg_risk.values - std_risk.values,
                            avg_risk.values + std_risk.values,
                            alpha=0.3, color='blue', label='±1 SD')

            # Add participant count to title
            n_participants = self.current_data['participant_id'].nunique()
            title_suffix = f" (n={n_participants})"
        else:
            # Plot risk profile for single participant
            title_suffix = ""
            for task in self.current_data['task_name'].unique():
                task_data = self.current_data[self.current_data['task_name'] == task]
                display_name = TaskType.get_display_name(TaskType(task))
                ax.plot(task_data['trial_number'], task_data['risk_level'],
                        marker='o', label=display_name, linewidth=2, markersize=6)

        ax.set_xlabel('Trial Number', fontsize=12, color='white')
        ax.set_ylabel('Risk Level', fontsize=12, color='white')

        # Create title based on selected tasks
        selected_tasks = self.get_selected_tasks()
        if len(selected_tasks) == len(self.task_vars):
            task_info = "All Tasks"
        else:
            task_info = f"{len(selected_tasks)} Tasks"

        if view_mode == "Experiment" and self.current_experiment_id:
            exp = self.db_manager.get_experiment(experiment_id=self.current_experiment_id)
            ax.set_title(f'Risk Profile - {exp["name"]} ({task_info}){title_suffix}',
                        fontsize=14, color='white', pad=20)
        else:
            ax.set_title(f'Risk-Taking Profile ({task_info}){title_suffix}',
                        fontsize=14, color='white', pad=20)

        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.tick_params(colors='white')

        # Set y-axis limits
        ax.set_ylim(0, 1.1)

    def plot_raw_actions(self):
        """Plot raw number of actions/pumps over trials."""
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#3b3b3b')

        view_mode = self.view_mode_var.get()

        # Filter out rows where actions is None
        valid_data = self.current_data[self.current_data['actions'].notna()]

        if valid_data.empty:
            ax.text(0.5, 0.5, 'No action data available\n(This requires trials with additional_data)',
                    ha='center', va='center', fontsize=14, color='white')
            return

        if view_mode in ["All Participants", "Experiment"]:
            # Plot average actions for multiple participants
            avg_actions = valid_data.groupby('trial_number')['actions'].mean()
            std_actions = valid_data.groupby('trial_number')['actions'].std()

            ax.plot(avg_actions.index, avg_actions.values, 'b-', linewidth=2, label='Average')
            ax.fill_between(avg_actions.index,
                            avg_actions.values - std_actions.values,
                            avg_actions.values + std_actions.values,
                            alpha=0.3, color='blue', label='±1 SD')

            # Add participant count to title
            n_participants = valid_data['participant_id'].nunique()
            title_suffix = f" (n={n_participants})"
        else:
            # Plot actions for single participant by task
            title_suffix = ""

            for task in valid_data['task_name'].unique():
                task_data = valid_data[valid_data['task_name'] == task]
                display_name = TaskType.get_display_name(TaskType(task))

                ax.plot(task_data['trial_number'], task_data['actions'],
                        marker='o', label=display_name, linewidth=2, markersize=6)

        ax.set_xlabel('Trial Number', fontsize=12, color='white')
        ax.set_ylabel('Number of Actions', fontsize=12, color='white')

        # Create title based on selected tasks
        selected_tasks = self.get_selected_tasks()
        if len(selected_tasks) == len(self.task_vars):
            task_info = "All Tasks"
        else:
            task_info = f"{len(selected_tasks)} Tasks"

        if view_mode == "Experiment" and self.current_experiment_id:
            exp = self.db_manager.get_experiment(experiment_id=self.current_experiment_id)
            ax.set_title(f'Raw Actions/Pumps - {exp["name"]} ({task_info}){title_suffix}',
                        fontsize=14, color='white', pad=20)
        else:
            ax.set_title(f'Raw Actions/Pumps Over Trials ({task_info}){title_suffix}',
                        fontsize=14, color='white', pad=20)

        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.tick_params(colors='white')

    def plot_correlation_matrix(self):
        """Plot correlation matrix of risk metrics."""
        ax = self.figure.add_subplot(111)

        view_mode = self.view_mode_var.get()

        # Prepare data for correlation
        if view_mode in ["All Participants", "Experiment"]:
            index_cols = ['participant_id', 'session_number']
        else:
            index_cols = ['session_number', 'trial_number']

        corr_data = self.current_data.pivot_table(
            index=index_cols,
            columns='task_name',
            values='risk_level',
            aggfunc='mean'
        )

        if corr_data.empty or len(corr_data.columns) < 2:
            ax.text(0.5, 0.5, 'Not enough data for correlation analysis\n(Need at least 2 tasks selected)',
                    ha='center', va='center', fontsize=16, color='white')
            ax.set_facecolor('#2b2b2b')
            return

        # Rename columns to display names
        corr_data.columns = [TaskType.get_display_name(TaskType(col)) for col in corr_data.columns]

        # Calculate correlation
        correlation = corr_data.corr()

        # Create heatmap
        im = ax.imshow(correlation, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)

        # Set ticks and labels
        ax.set_xticks(np.arange(len(correlation.columns)))
        ax.set_yticks(np.arange(len(correlation.columns)))
        ax.set_xticklabels(correlation.columns, rotation=45, ha='right', color='white')
        ax.set_yticklabels(correlation.columns, color='white')

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.ax.tick_params(colors='white')

        # Add correlation values
        for i in range(len(correlation)):
            for j in range(len(correlation)):
                text = ax.text(j, i, f'{correlation.iloc[i, j]:.2f}',
                               ha="center", va="center",
                               color="black" if abs(correlation.iloc[i, j]) < 0.5 else "white")

        # Create title based on selected tasks
        selected_tasks = self.get_selected_tasks()
        if len(selected_tasks) == len(self.task_vars):
            task_info = "All Tasks"
        else:
            task_info = f"{len(selected_tasks)} Selected Tasks"

        if view_mode == "Experiment" and self.current_experiment_id:
            exp = self.db_manager.get_experiment(experiment_id=self.current_experiment_id)
            ax.set_title(f'Task Correlation Matrix - {exp["name"]} ({task_info})',
                        fontsize=14, color='white', pad=20)
        else:
            ax.set_title(f'Task Correlation Matrix ({task_info})',
                        fontsize=14, color='white', pad=20)

    def update_statistics(self):
        """Update statistics display."""
        self.stats_text.delete("1.0", tk.END)

        if self.current_data is None or self.current_data.empty:
            self.stats_text.insert("1.0", "No data available")
            return

        stats_lines = []
        view_mode = self.view_mode_var.get()

        # Add view mode specific header
        if view_mode == "Experiment" and self.current_experiment_id:
            exp = self.db_manager.get_experiment(experiment_id=self.current_experiment_id)
            stats_lines.append(f"=== Experiment: {exp['name']} ===")
            stats_lines.append(f"Code: {exp['experiment_code']}")
            stats_lines.append(f"Participants: {self.current_data['participant_id'].nunique()}")
            stats_lines.append(f"Sessions: {self.current_data['session_id'].nunique()}\n")
        elif view_mode == "All Participants":
            stats_lines.append("=== All Participants ===")
            stats_lines.append(f"Total Participants: {self.current_data['participant_id'].nunique()}")
            stats_lines.append(f"Total Sessions: {self.current_data['session_id'].nunique()}\n")

        # Overall statistics
        stats_lines.append("=== Overall Statistics ===")
        stats_lines.append(f"Total Trials: {len(self.current_data)}")
        stats_lines.append(f"Total Points: {self.current_data['points_earned'].sum()}")
        stats_lines.append(f"Average Risk Level: {self.current_data['risk_level'].mean():.3f}")
        stats_lines.append(f"Success Rate: {(self.current_data['outcome'] == 'success').mean():.1%}")

        if 'reaction_time' in self.current_data and self.current_data['reaction_time'].notna().any():
            stats_lines.append(f"Avg Reaction Time: {self.current_data['reaction_time'].mean():.2f}s")

        # Selected tasks info
        selected_tasks = self.get_selected_tasks()
        stats_lines.append(f"\nSelected Tasks: {len(selected_tasks)}/{len(self.task_vars)}")

        # Task-specific statistics
        stats_lines.append("\n=== Task Statistics ===")
        for task in self.current_data['task_name'].unique():
            task_data = self.current_data[self.current_data['task_name'] == task]
            display_name = TaskType.get_display_name(TaskType(task))

            stats_lines.append(f"\n{display_name}:")
            stats_lines.append(f"  Trials: {len(task_data)}")
            stats_lines.append(f"  Points: {task_data['points_earned'].sum()}")
            stats_lines.append(f"  Avg Risk: {task_data['risk_level'].mean():.3f}")
            stats_lines.append(f"  Success Rate: {(task_data['outcome'] == 'success').mean():.1%}")

            # Add average actions if available
            if 'actions' in task_data and task_data['actions'].notna().any():
                stats_lines.append(f"  Avg Actions: {task_data['actions'].mean():.1f}")

            # Add standardized field statistics if available
            if 'action_limit' in task_data and task_data['action_limit'].notna().any():
                stats_lines.append(f"  Avg Action Limit: {task_data['action_limit'].mean():.1f}")

            if 'potential_points' in task_data and task_data['potential_points'].notna().any():
                avg_potential = task_data['potential_points'].mean()
                avg_earned = task_data['points_earned'].mean()
                efficiency = (avg_earned / avg_potential * 100) if avg_potential > 0 else 0
                stats_lines.append(f"  Point Efficiency: {efficiency:.1f}%")

        # Risk profile categorization
        avg_risk = self.current_data['risk_level'].mean()
        if avg_risk < 0.33:
            risk_category = "Conservative"
        elif avg_risk < 0.67:
            risk_category = "Moderate"
        else:
            risk_category = "Risk-Taking"

        stats_lines.append(f"\n=== Risk Profile ===")
        stats_lines.append(f"Category: {risk_category}")
        stats_lines.append(f"Risk Consistency (SD): {self.current_data['risk_level'].std():.3f}")

        self.stats_text.insert("1.0", "\n".join(stats_lines))

    def export_csv(self):
        """Export current data to CSV."""
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("No Data", "No data to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                self.current_data.to_csv(filename, index=False)
                messagebox.showinfo("Success", f"Data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")

    def export_excel(self):
        """Export current data to Excel."""
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("No Data", "No data to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if filename:
            try:
                with pd.ExcelWriter(filename) as writer:
                    # Raw data
                    self.current_data.to_excel(writer, sheet_name='Raw Data', index=False)

                    # Summary statistics
                    summary_stats = self.current_data.groupby('task_name').agg({
                        'risk_level': ['mean', 'std'],
                        'points_earned': ['sum', 'mean'],
                        'outcome': lambda x: (x == 'success').mean()
                    })
                    summary_stats.columns = ['_'.join(col) for col in summary_stats.columns]
                    summary_stats.to_excel(writer, sheet_name='Summary Statistics')

                    # Add actions statistics if available
                    if 'actions' in self.current_data.columns:
                        action_stats = self.current_data.groupby('task_name')['actions'].agg(['mean', 'std', 'min', 'max'])
                        action_stats.to_excel(writer, sheet_name='Action Statistics')

                messagebox.showinfo("Success", f"Data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")

    def export_json(self):
        """Export current data to JSON."""
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("No Data", "No data to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                self.current_data.to_json(filename, orient='records', indent=2)
                messagebox.showinfo("Success", f"Data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")

    def save_plot(self):
        """Save current plot to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf"),
                ("SVG files", "*.svg"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight',
                                    facecolor=self.figure.get_facecolor())
                messagebox.showinfo("Success", f"Plot saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save plot: {e}")

    def generate_participant_report(self):
        """Generate detailed participant report."""
        view_mode = self.view_mode_var.get()

        if view_mode == "Participant" and not self.current_participant_id:
            messagebox.showwarning("No Selection", "Please select a participant first")
            return
        elif view_mode == "Experiment" and not self.current_experiment_id:
            messagebox.showwarning("No Selection", "Please select an experiment first")
            return
        elif view_mode == "All Participants":
            messagebox.showinfo("Info", "Use 'Summary Report' for all participants view")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                if view_mode == "Participant":
                    participant_data = self.db_manager.export_participant_data(self.current_participant_id)

                    with open(filename, 'w') as f:
                        f.write("PARTICIPANT REPORT\n")
                        f.write("=" * 50 + "\n\n")

                        # Participant info
                        p_info = participant_data['participant']
                        f.write(f"Participant Code: {p_info['participant_code']}\n")
                        f.write(f"Age: {p_info['age'] or 'Not specified'}\n")
                        f.write(f"Gender: {p_info['gender'] or 'Not specified'}\n")
                        f.write(f"Created: {p_info['created_date']}\n")
                        f.write(f"Notes: {p_info['notes'] or 'None'}\n\n")

                        # Selected tasks info
                        selected_tasks = self.get_selected_tasks()
                        f.write(f"Analysis includes {len(selected_tasks)} tasks:\n")
                        for task in selected_tasks:
                            f.write(f"  - {TaskType.get_display_name(TaskType(task))}\n")
                        f.write("\n")

                        # Session details
                        f.write("SESSIONS\n")
                        f.write("-" * 30 + "\n")

                        for session in participant_data['sessions']:
                            f.write(f"\nSession {session['session_number']}:\n")
                            f.write(f"  Date: {session['session_date']}\n")
                            f.write(f"  Status: {'Completed' if session['completed'] else 'Incomplete'}\n")
                            f.write(f"  Tasks: {', '.join(session['tasks_assigned'])}\n")
                            f.write(f"  Trials: {len(session['trials'])}\n")

                elif view_mode == "Experiment":
                    # Generate experiment report
                    exp = self.db_manager.get_experiment(experiment_id=self.current_experiment_id)
                    stats = self.db_manager.get_experiment_statistics(self.current_experiment_id)

                    with open(filename, 'w') as f:
                        f.write("EXPERIMENT REPORT\n")
                        f.write("=" * 50 + "\n\n")

                        f.write(f"Experiment: {exp['name']}\n")
                        f.write(f"Code: {exp['experiment_code']}\n")
                        f.write(f"Status: {'Active' if exp['is_active'] else 'Inactive'}\n")
                        f.write(f"Created: {exp['created_date']}\n\n")

                        # Selected tasks info
                        selected_tasks = self.get_selected_tasks()
                        f.write(f"Analysis includes {len(selected_tasks)} tasks:\n")
                        for task in selected_tasks:
                            f.write(f"  - {TaskType.get_display_name(TaskType(task))}\n")
                        f.write("\n")

                        f.write("ENROLLMENT STATISTICS\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"Total Participants: {stats['participant_count']}\n")
                        f.write(f"Total Sessions: {stats['session_count']}\n")
                        f.write(f"Completed Sessions: {stats['completed_sessions']}\n\n")

                        f.write("TASK STATISTICS\n")
                        f.write("-" * 30 + "\n")

                        for task_name, task_stats in stats['task_statistics'].items():
                            if task_name in selected_tasks:
                                display_name = TaskType.get_display_name(TaskType(task_name))
                                f.write(f"\n{display_name}:\n")
                                f.write(f"  Trials: {task_stats['trial_count']}\n")
                                f.write(f"  Avg Risk: {task_stats['avg_risk']:.3f}\n")
                                f.write(f"  Avg Points: {task_stats['avg_points']:.1f}\n")
                                f.write(f"  Success Rate: {task_stats['success_rate'] * 100:.1f}%\n")

                messagebox.showinfo("Success", f"Report saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate report: {e}")

    def generate_summary_report(self):
        """Generate summary report for all participants."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                stats = self.db_manager.get_statistics()
                task_stats = self.db_manager.get_task_statistics()

                with open(filename, 'w') as f:
                    f.write("EXPERIMENT SUMMARY REPORT\n")
                    f.write("=" * 50 + "\n\n")

                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    f.write("OVERALL STATISTICS\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"Total Participants: {stats['total_participants']}\n")
                    f.write(f"Completed Sessions: {stats['completed_sessions']}\n")
                    f.write(f"Active Sessions: {stats['active_sessions']}\n")
                    f.write(f"Total Trials: {stats['total_trials']}\n\n")

                    # Selected tasks info
                    selected_tasks = self.get_selected_tasks()
                    f.write(f"Analysis includes {len(selected_tasks)} tasks:\n")
                    for task in selected_tasks:
                        f.write(f"  - {TaskType.get_display_name(TaskType(task))}\n")
                    f.write("\n")

                    f.write("TASK STATISTICS\n")
                    f.write("-" * 30 + "\n")

                    for task_name, task_data in task_stats.items():
                        if task_name in selected_tasks:
                            display_name = TaskType.get_display_name(TaskType(task_name))
                            f.write(f"\n{display_name}:\n")
                            f.write(f"  Trials: {task_data['trial_count']}\n")
                            f.write(f"  Avg Risk: {task_data['avg_risk']:.3f}\n")
                            f.write(f"  Avg Points: {task_data['avg_points']:.1f}\n")
                            f.write(f"  Success Rate: {task_data['success_rate']:.1%}\n")

                messagebox.showinfo("Success", f"Report saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate report: {e}")