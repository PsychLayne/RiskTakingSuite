"""
Backup Manager for Risk Tasks Client
Handles automated database backups and restoration.
"""

import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json
import zipfile
import threading
import time
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backups and restoration."""

    def __init__(self, db_manager, backup_dir: str = "data/backups"):
        self.db_manager = db_manager
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True, parents=True)

        self.backup_thread = None
        self.stop_backup_event = threading.Event()
        self.is_backing_up = False

        # Backup settings
        self.max_backups = 10  # Maximum number of backups to keep
        self.backup_interval_hours = 24

        # Initialize backup log
        self.log_file = self.backup_dir / "backup_log.json"
        self.backup_log = self.load_backup_log()

    def load_backup_log(self) -> List[dict]:
        """Load backup history log."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading backup log: {e}")
                return []
        return []

    def save_backup_log(self):
        """Save backup history log."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.backup_log, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving backup log: {e}")

    def create_backup(self, description: str = "Manual backup") -> Tuple[bool, str]:
        """
        Create a backup of the database and associated files.
        Returns (success, message) tuple.
        """
        if self.is_backing_up:
            return False, "Backup already in progress"

        self.is_backing_up = True

        try:
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)

            # 1. Backup database
            db_backup_path = backup_path / "participants.db"

            # Close database connection temporarily
            self.db_manager.close()

            # Copy database file
            db_source = Path(self.db_manager.db_path)
            if db_source.exists():
                shutil.copy2(db_source, db_backup_path)

            # Reopen database connection
            self.db_manager.initialize()

            # 2. Backup configuration files
            config_dir = Path("config")
            if config_dir.exists():
                backup_config_dir = backup_path / "config"
                shutil.copytree(config_dir, backup_config_dir)

            # 3. Backup task assignments
            assignments_file = Path("data/task_assignments.json")
            if assignments_file.exists():
                shutil.copy2(assignments_file, backup_path / "task_assignments.json")

            # 4. Create metadata file
            metadata = {
                "timestamp": timestamp,
                "description": description,
                "database_size": db_backup_path.stat().st_size if db_backup_path.exists() else 0,
                "statistics": self.db_manager.get_statistics(),
                "version": "1.0"
            }

            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            # 5. Create ZIP archive
            zip_path = self.backup_dir / f"{backup_name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in backup_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(backup_path)
                        zipf.write(file_path, arcname)

            # Remove temporary backup directory
            shutil.rmtree(backup_path)

            # Update backup log
            backup_entry = {
                "timestamp": timestamp,
                "filename": f"{backup_name}.zip",
                "size": zip_path.stat().st_size,
                "description": description,
                "statistics": metadata["statistics"]
            }
            self.backup_log.append(backup_entry)
            self.save_backup_log()

            # Clean up old backups
            self.cleanup_old_backups()

            logger.info(f"Backup created successfully: {zip_path}")
            return True, f"Backup created: {backup_name}.zip"

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False, f"Backup failed: {str(e)}"

        finally:
            self.is_backing_up = False

    def restore_backup(self, backup_filename: str) -> Tuple[bool, str]:
        """
        Restore database and files from a backup.
        Returns (success, message) tuple.
        """
        backup_path = self.backup_dir / backup_filename

        if not backup_path.exists():
            return False, f"Backup file not found: {backup_filename}"

        try:
            # Create temporary extraction directory
            temp_dir = self.backup_dir / "temp_restore"
            temp_dir.mkdir(exist_ok=True)

            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)

            # Read metadata
            metadata_file = temp_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {"description": "Unknown backup"}

            # Confirm restoration
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Confirm Restoration",
                f"Are you sure you want to restore from backup?\n\n"
                f"Backup: {backup_filename}\n"
                f"Created: {metadata.get('timestamp', 'Unknown')}\n"
                f"Description: {metadata.get('description', 'Unknown')}\n\n"
                f"This will overwrite current data!"
            )

            if not result:
                shutil.rmtree(temp_dir)
                return False, "Restoration cancelled"

            # Create backup of current data before restoration
            self.create_backup("Pre-restoration backup")

            # Close database connection
            self.db_manager.close()

            # Restore database
            db_backup = temp_dir / "participants.db"
            if db_backup.exists():
                db_target = Path(self.db_manager.db_path)
                db_target.parent.mkdir(exist_ok=True)
                shutil.copy2(db_backup, db_target)

            # Restore configuration
            config_backup = temp_dir / "config"
            if config_backup.exists():
                config_target = Path("config")
                if config_target.exists():
                    shutil.rmtree(config_target)
                shutil.copytree(config_backup, config_target)

            # Restore task assignments
            assignments_backup = temp_dir / "task_assignments.json"
            if assignments_backup.exists():
                assignments_target = Path("data/task_assignments.json")
                shutil.copy2(assignments_backup, assignments_target)

            # Clean up
            shutil.rmtree(temp_dir)

            # Reinitialize database
            self.db_manager.initialize()

            logger.info(f"Backup restored successfully: {backup_filename}")
            return True, f"Backup restored successfully from {backup_filename}"

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            # Try to reinitialize database
            try:
                self.db_manager.initialize()
            except:
                pass
            return False, f"Restore failed: {str(e)}"

    def cleanup_old_backups(self):
        """Remove old backups exceeding the maximum count."""
        # Get all backup files
        backup_files = list(self.backup_dir.glob("backup_*.zip"))
        backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Keep only the most recent backups
        if len(backup_files) > self.max_backups:
            for old_backup in backup_files[self.max_backups:]:
                try:
                    old_backup.unlink()
                    # Remove from log
                    self.backup_log = [
                        entry for entry in self.backup_log
                        if entry['filename'] != old_backup.name
                    ]
                    logger.info(f"Removed old backup: {old_backup.name}")
                except Exception as e:
                    logger.error(f"Error removing old backup {old_backup.name}: {e}")

            self.save_backup_log()

    def start_auto_backup(self, interval_hours: int = 24):
        """Start automatic backup thread."""
        self.backup_interval_hours = interval_hours
        self.stop_backup_event.clear()

        if self.backup_thread and self.backup_thread.is_alive():
            logger.warning("Auto backup already running")
            return

        self.backup_thread = threading.Thread(
            target=self._auto_backup_worker,
            daemon=True
        )
        self.backup_thread.start()
        logger.info(f"Auto backup started with {interval_hours} hour interval")

    def stop_auto_backup(self):
        """Stop automatic backup thread."""
        self.stop_backup_event.set()
        if self.backup_thread:
            self.backup_thread.join(timeout=5)
        logger.info("Auto backup stopped")

    def _auto_backup_worker(self):
        """Worker thread for automatic backups."""
        while not self.stop_backup_event.is_set():
            # Wait for the specified interval
            if self.stop_backup_event.wait(self.backup_interval_hours * 3600):
                break  # Stop event was set

            # Perform backup
            success, message = self.create_backup("Automatic backup")
            if success:
                logger.info(f"Automatic backup completed: {message}")
            else:
                logger.error(f"Automatic backup failed: {message}")

    def get_backup_list(self) -> List[dict]:
        """Get list of available backups with metadata."""
        backups = []

        for backup_file in self.backup_dir.glob("backup_*.zip"):
            # Find entry in log
            log_entry = None
            for entry in self.backup_log:
                if entry['filename'] == backup_file.name:
                    log_entry = entry
                    break

            if log_entry:
                backups.append(log_entry)
            else:
                # Create basic entry if not in log
                stat = backup_file.stat()
                backups.append({
                    "filename": backup_file.name,
                    "size": stat.st_size,
                    "timestamp": datetime.fromtimestamp(stat.st_mtime).strftime("%Y%m%d_%H%M%S"),
                    "description": "Unknown backup"
                })

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)

        return backups

    def verify_backup(self, backup_filename: str) -> Tuple[bool, str]:
        """Verify integrity of a backup file."""
        backup_path = self.backup_dir / backup_filename

        if not backup_path.exists():
            return False, "Backup file not found"

        try:
            # Test ZIP integrity
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                bad_files = zipf.testzip()
                if bad_files:
                    return False, f"Corrupted files in backup: {bad_files}"

                # Check for required files
                namelist = zipf.namelist()
                required_files = ["participants.db", "metadata.json"]

                for required in required_files:
                    if required not in namelist:
                        return False, f"Missing required file: {required}"

            return True, "Backup verified successfully"

        except Exception as e:
            return False, f"Verification failed: {str(e)}"

    def export_backup_info(self, filepath: str):
        """Export backup information to a file."""
        try:
            backup_info = {
                "export_date": datetime.now().isoformat(),
                "backup_directory": str(self.backup_dir),
                "max_backups": self.max_backups,
                "auto_backup_enabled": self.backup_thread is not None and self.backup_thread.is_alive(),
                "backup_interval_hours": self.backup_interval_hours,
                "backups": self.get_backup_list()
            }

            with open(filepath, 'w') as f:
                json.dump(backup_info, f, indent=2)

            return True, f"Backup info exported to {filepath}"

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def get_backup_statistics(self) -> dict:
        """Get statistics about backups."""
        backups = self.get_backup_list()

        if not backups:
            return {
                "total_backups": 0,
                "total_size": 0,
                "oldest_backup": None,
                "newest_backup": None,
                "average_size": 0
            }

        total_size = sum(b['size'] for b in backups)

        return {
            "total_backups": len(backups),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_backup": backups[-1]['timestamp'] if backups else None,
            "newest_backup": backups[0]['timestamp'] if backups else None,
            "average_size_mb": round(total_size / len(backups) / (1024 * 1024), 2) if backups else 0
        }