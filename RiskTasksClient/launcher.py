#!/usr/bin/env python3
"""
Risk Tasks Client Launcher
Main entry point that separates participant and researcher access.
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import subprocess

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RiskTasksLauncher(ctk.CTk):
    """Main launcher window for role selection."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Risk Tasks Study")
        self.geometry("600x400")
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

    def setup_ui(self):
        """Setup the launcher interface."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Risk Assessment Study",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(40, 20))

        subtitle_label = ctk.CTkLabel(
            self,
            text="Please select your role:",
            font=ctk.CTkFont(size=18)
        )
        subtitle_label.pack(pady=(0, 40))

        # Buttons frame
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(expand=True)

        # Participant button
        participant_btn = ctk.CTkButton(
            buttons_frame,
            text="👤 Participant",
            command=self.launch_participant,
            width=200,
            height=80,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144870"
        )
        participant_btn.grid(row=0, column=0, padx=20, pady=10)

        participant_info = ctk.CTkLabel(
            buttons_frame,
            text="Start or continue\nyour session",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        participant_info.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Researcher button
        researcher_btn = ctk.CTkButton(
            buttons_frame,
            text="🔬 Researcher",
            command=self.launch_researcher,
            width=200,
            height=80,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#2d572c",
            hover_color="#1e3a1e"
        )
        researcher_btn.grid(row=0, column=1, padx=20, pady=10)

        researcher_info = ctk.CTkLabel(
            buttons_frame,
            text="Access study\nmanagement",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        researcher_info.grid(row=1, column=1, padx=20, pady=(0, 20))

        # Exit button
        exit_btn = ctk.CTkButton(
            self,
            text="Exit",
            command=self.quit,
            width=120,
            height=40,
            fg_color="darkred",
            hover_color="red"
        )
        exit_btn.pack(pady=(0, 30))

    def launch_participant(self):
        """Launch the participant interface."""
        self.withdraw()  # Hide launcher

        # Import and create participant interface
        from participant_interface import ParticipantInterface
        participant_app = ParticipantInterface(self)
        participant_app.mainloop()

    def launch_researcher(self):
        """Launch the researcher interface with password protection."""
        # Create password dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Researcher Access")
        dialog.geometry("400x200")
        dialog.resizable(False, False)

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (100)
        dialog.geometry(f'400x200+{x}+{y}')

        # Make dialog modal
        dialog.transient(self)
        dialog.grab_set()

        # Password prompt
        prompt_label = ctk.CTkLabel(
            dialog,
            text="Enter researcher password:",
            font=ctk.CTkFont(size=16)
        )
        prompt_label.pack(pady=(30, 10))

        password_var = tk.StringVar()
        password_entry = ctk.CTkEntry(
            dialog,
            textvariable=password_var,
            show="*",
            width=250,
            font=ctk.CTkFont(size=14)
        )
        password_entry.pack(pady=10)
        password_entry.focus()

        def check_password(event=None):
            if password_var.get() == "PIZZA":
                dialog.destroy()
                self.withdraw()  # Hide launcher

                # Launch the researcher interface (existing main.py)
                try:
                    subprocess.Popen([sys.executable, "main.py"])
                    self.after(1000, self.quit)  # Close launcher after launching main
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to launch researcher interface: {e}")
                    self.deiconify()  # Show launcher again
            else:
                messagebox.showerror("Access Denied", "Incorrect password")
                password_entry.delete(0, tk.END)
                password_entry.focus()

        # Bind Enter key
        password_entry.bind("<Return>", check_password)

        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)

        ok_btn = ctk.CTkButton(
            button_frame,
            text="OK",
            command=check_password,
            width=100
        )
        ok_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            fg_color="gray"
        )
        cancel_btn.pack(side="left", padx=10)

        # Handle dialog close
        def on_close():
            dialog.destroy()
            self.deiconify()  # Show launcher again

        dialog.protocol("WM_DELETE_WINDOW", on_close)


def main():
    """Main entry point for the application."""
    # Create necessary directories
    directories = ["config", "data", "logs", "tasks", "data/backups"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True, parents=True)

    # Create and run the launcher
    app = RiskTasksLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()