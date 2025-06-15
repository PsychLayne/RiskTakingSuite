"""
Participant Manager UI for Risk Tasks Client
Handles participant creation, editing, and management interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime
import re
from typing import Optional, Callable

from database.db_manager import DatabaseManager
from database.models import Participant, Gender

class ParticipantManager(ctk.CTkFrame):
    """UI component for managing participants."""

    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_participant_id = None

        # Setup UI
        self.setup_ui()

        # Load participants
        self.refresh()

    def setup_ui(self):
        """Setup the participant manager interface."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Participant Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Main container with two columns
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Left column - Participant list
        left_frame = ctk.CTkFrame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Search bar
        search_frame = ctk.CTkFrame(left_frame)
        search_frame.pack(fill="x", pady=(0, 10))

        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search)
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Enter participant code..."
        )
        self.search_entry.pack(side="left", fill="x", expand=True)

        # Participant list with scrollbar
        list_frame = ctk.CTkFrame(left_frame)
        list_frame.pack(fill="both", expand=True)

        # Create Treeview for participant list
        columns = ("Code", "Age", "Gender", "Sessions", "Created")
        self.participant_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=15
        )

        # Configure columns
        self.participant_tree.heading("Code", text="Participant Code")
        self.participant_tree.heading("Age", text="Age")
        self.participant_tree.heading("Gender", text="Gender")
        self.participant_tree.heading("Sessions", text="Sessions")
        self.participant_tree.heading("Created", text="Created Date")

        self.participant_tree.column("Code", width=150)
        self.participant_tree.column("Age", width=60)
        self.participant_tree.column("Gender", width=100)
        self.participant_tree.column("Sessions", width=80)
        self.participant_tree.column("Created", width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.participant_tree.yview
        )
        self.participant_tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        self.participant_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind selection event
        self.participant_tree.bind("<<TreeviewSelect>>", self.on_participant_select)

        # Right column - Participant details
        right_frame = ctk.CTkFrame(main_container, width=400)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.pack_propagate(False)

        # Details section
        details_label = ctk.CTkLabel(
            right_frame,
            text="Participant Details",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        details_label.pack(pady=10)

        # Form frame
        form_frame = ctk.CTkFrame(right_frame)
        form_frame.pack(fill="x", padx=20, pady=10)

        # Participant code
        code_label = ctk.CTkLabel(form_frame, text="Participant Code:")
        code_label.grid(row=0, column=0, sticky="e", padx=5, pady=5)

        self.code_var = tk.StringVar()
        self.code_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.code_var,
            placeholder_text="e.g., P001"
        )
        self.code_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Age
        age_label = ctk.CTkLabel(form_frame, text="Age:")
        age_label.grid(row=1, column=0, sticky="e", padx=5, pady=5)

        self.age_var = tk.StringVar()
        self.age_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.age_var,
            placeholder_text="Optional"
        )
        self.age_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Gender
        gender_label = ctk.CTkLabel(form_frame, text="Gender:")
        gender_label.grid(row=2, column=0, sticky="e", padx=5, pady=5)

        self.gender_var = tk.StringVar()
        self.gender_menu = ctk.CTkOptionMenu(
            form_frame,
            variable=self.gender_var,
            values=["Not specified"] + [g.value.replace("_", " ").title() for g in Gender]
        )
        self.gender_menu.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Notes
        notes_label = ctk.CTkLabel(form_frame, text="Notes:")
        notes_label.grid(row=3, column=0, sticky="ne", padx=5, pady=5)

        self.notes_text = ctk.CTkTextbox(form_frame, height=100)
        self.notes_text.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ctk.CTkFrame(right_frame)
        button_frame.pack(fill="x", padx=20, pady=20)

        self.add_button = ctk.CTkButton(
            button_frame,
            text="Add Participant",
            command=self.add_participant
        )
        self.add_button.pack(side="left", padx=5)

        self.update_button = ctk.CTkButton(
            button_frame,
            text="Update",
            command=self.update_participant,
            state="disabled"
        )
        self.update_button.pack(side="left", padx=5)

        self.delete_button = ctk.CTkButton(
            button_frame,
            text="Delete",
            command=self.delete_participant,
            state="disabled",
            fg_color="darkred"
        )
        self.delete_button.pack(side="left", padx=5)

        self.clear_button = ctk.CTkButton(
            button_frame,
            text="Clear",
            command=self.clear_form,
            fg_color="gray"
        )
        self.clear_button.pack(side="left", padx=5)

        # Session info (shown when participant selected)
        self.session_frame = ctk.CTkFrame(right_frame)
        self.session_frame.pack(fill="x", padx=20, pady=10)

        session_label = ctk.CTkLabel(
            self.session_frame,
            text="Session Information",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        session_label.pack(pady=5)

        self.session_info_label = ctk.CTkLabel(
            self.session_frame,
            text="Select a participant to view sessions"
        )
        self.session_info_label.pack(pady=5)

        # Statistics section
        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(fill="x", padx=20, pady=10)

        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="Loading statistics...",
            font=ctk.CTkFont(size=14)
        )
        self.stats_label.pack(pady=10)

    def refresh(self):
        """Refresh the participant list."""
        # Clear current items
        for item in self.participant_tree.get_children():
            self.participant_tree.delete(item)

        # Get all participants
        participants = self.db_manager.get_all_participants()

        # Filter by search term
        search_term = self.search_var.get().lower()
        if search_term:
            participants = [
                p for p in participants
                if search_term in p['participant_code'].lower()
            ]

        # Add to tree
        for participant in participants:
            created_date = datetime.fromisoformat(participant['created_date'])
            created_str = created_date.strftime("%Y-%m-%d")

            gender_display = participant['gender'] or "Not specified"
            if gender_display in [g.value for g in Gender]:
                gender_display = gender_display.replace("_", " ").title()

            sessions_display = f"{participant['completed_sessions']}/{participant['session_count']}"

            self.participant_tree.insert(
                "",
                "end",
                values=(
                    participant['participant_code'],
                    participant['age'] or "-",
                    gender_display,
                    sessions_display,
                    created_str
                ),
                tags=(participant['id'],)
            )

        # Update statistics
        self.update_statistics()

    def update_statistics(self):
        """Update the statistics display."""
        stats = self.db_manager.get_statistics()
        participants = self.db_manager.get_all_participants()

        # Calculate additional statistics
        total_participants = stats['total_participants']
        active_participants = len([p for p in participants if p['session_count'] > 0])

        stats_text = (
            f"Total Participants: {total_participants} | "
            f"Active: {active_participants} | "
            f"Total Sessions: {stats['completed_sessions']} completed, "
            f"{stats['active_sessions']} active"
        )

        self.stats_label.configure(text=stats_text)

    def on_search(self, *args):
        """Handle search input change."""
        self.refresh()

    def on_participant_select(self, event):
        """Handle participant selection from list."""
        selection = self.participant_tree.selection()
        if not selection:
            return

        # Get participant ID from tags
        item = self.participant_tree.item(selection[0])
        participant_id = item['tags'][0]

        # Load participant details
        participant = self.db_manager.get_participant(participant_id=participant_id)
        if participant:
            self.selected_participant_id = participant_id
            self.load_participant_details(participant)

    def load_participant_details(self, participant: dict):
        """Load participant details into the form."""
        # Clear form first
        self.clear_form(keep_selection=True)

        # Load data
        self.code_var.set(participant['participant_code'])
        self.code_entry.configure(state="disabled")  # Can't change code

        if participant['age']:
            self.age_var.set(str(participant['age']))

        if participant['gender']:
            gender_display = participant['gender'].replace("_", " ").title()
            self.gender_var.set(gender_display)
        else:
            self.gender_var.set("Not specified")

        if participant['notes']:
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", participant['notes'])

        # Enable update button, disable add button
        self.update_button.configure(state="normal")
        self.delete_button.configure(state="normal")
        self.add_button.configure(state="disabled")

        # Load session information
        sessions = self.db_manager.get_participant_sessions(participant['id'])
        self.display_session_info(sessions)

    def display_session_info(self, sessions: list):
        """Display session information for selected participant."""
        if not sessions:
            info_text = "No sessions scheduled yet"
        else:
            info_lines = []
            for session in sessions:
                session_date = datetime.fromisoformat(session['session_date'])
                status = "Completed" if session['completed'] else "Pending"
                tasks = ", ".join([
                    task.replace("_", " ").title()
                    for task in session['tasks_assigned']
                ])

                info_lines.append(
                    f"Session {session['session_number']}: {status}\n"
                    f"  Date: {session_date.strftime('%Y-%m-%d %H:%M')}\n"
                    f"  Tasks: {tasks}\n"
                    f"  Trials: {session['trial_count']}"
                )

            info_text = "\n\n".join(info_lines)

        self.session_info_label.configure(text=info_text)

    def clear_form(self, keep_selection=False):
        """Clear the form fields."""
        self.code_var.set("")
        self.code_entry.configure(state="normal")
        self.age_var.set("")
        self.gender_var.set("Not specified")
        self.notes_text.delete("1.0", "end")

        if not keep_selection:
            self.selected_participant_id = None
            self.update_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            self.add_button.configure(state="normal")
            self.session_info_label.configure(text="Select a participant to view sessions")

    def validate_form(self) -> tuple[bool, str]:
        """Validate form data before saving."""
        # Check participant code
        code = self.code_var.get().strip()
        if not code:
            return False, "Participant code is required"

        # Validate code format (alphanumeric and hyphens/underscores)
        if not re.match(r'^[A-Za-z0-9_-]+$', code):
            return False, "Participant code can only contain letters, numbers, hyphens, and underscores"

        # Check age if provided
        age_str = self.age_var.get().strip()
        if age_str:
            try:
                age = int(age_str)
                if age < 0 or age > 150:
                    return False, "Age must be between 0 and 150"
            except ValueError:
                return False, "Age must be a number"

        return True, ""

    def add_participant(self):
        """Add a new participant."""
        # Validate form
        is_valid, error_msg = self.validate_form()
        if not is_valid:
            messagebox.showerror("Validation Error", error_msg)
            return

        # Prepare data
        code = self.code_var.get().strip()
        age_str = self.age_var.get().strip()
        age = int(age_str) if age_str else None

        gender = self.gender_var.get()
        if gender == "Not specified":
            gender = None
        else:
            # Convert back to enum value
            gender = gender.lower().replace(" ", "_")

        notes = self.notes_text.get("1.0", "end-1c").strip()
        notes = notes if notes else None

        # Add to database
        try:
            participant_id = self.db_manager.add_participant(
                participant_code=code,
                age=age,
                gender=gender,
                notes=notes
            )

            messagebox.showinfo(
                "Success",
                f"Participant {code} added successfully!"
            )

            # Clear form and refresh
            self.clear_form()
            self.refresh()

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add participant: {e}")

    def update_participant(self):
        """Update selected participant."""
        if not self.selected_participant_id:
            return

        # Validate form (excluding code validation since it can't be changed)
        age_str = self.age_var.get().strip()
        if age_str:
            try:
                age = int(age_str)
                if age < 0 or age > 150:
                    messagebox.showerror("Validation Error", "Age must be between 0 and 150")
                    return
            except ValueError:
                messagebox.showerror("Validation Error", "Age must be a number")
                return
        else:
            age = None

        # Prepare data
        gender = self.gender_var.get()
        if gender == "Not specified":
            gender = None
        else:
            gender = gender.lower().replace(" ", "_")

        notes = self.notes_text.get("1.0", "end-1c").strip()
        notes = notes if notes else None

        # Update in database
        try:
            self.db_manager.update_participant(
                participant_id=self.selected_participant_id,
                age=age,
                gender=gender,
                notes=notes
            )

            messagebox.showinfo(
                "Success",
                "Participant updated successfully!"
            )

            # Refresh list
            self.refresh()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update participant: {e}")

    def delete_participant(self):
        """Delete selected participant."""
        if not self.selected_participant_id:
            return

        # Get participant code for confirmation
        participant = self.db_manager.get_participant(participant_id=self.selected_participant_id)
        if not participant:
            return

        # Check if participant has sessions
        sessions = self.db_manager.get_participant_sessions(self.selected_participant_id)

        warning_msg = f"Are you sure you want to delete participant '{participant['participant_code']}'?"
        if sessions:
            warning_msg += f"\n\nThis participant has {len(sessions)} session(s) with data."
            warning_msg += "\nAll associated data will be permanently deleted!"

        result = messagebox.askyesno(
            "Confirm Deletion",
            warning_msg,
            icon="warning"
        )

        if result:
            try:
                # Delete participant and all associated data
                self.db_manager.delete_participant(self.selected_participant_id)

                # Also remove task assignments
                from utils.task_scheduler import TaskScheduler
                task_scheduler = TaskScheduler()
                task_scheduler.reset_participant_assignments(self.selected_participant_id)

                messagebox.showinfo(
                    "Success",
                    f"Participant '{participant['participant_code']}' deleted successfully"
                )

                # Clear form and refresh
                self.clear_form()
                self.refresh()

            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete participant: {e}")