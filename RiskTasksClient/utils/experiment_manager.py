"""
Experiment Manager for Risk Tasks Client
Handles experiment creation, configuration, validation, and participant enrollment.
"""

import json
import random
import string
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

from database.db_manager import DatabaseManager
from database.models import TaskType
from utils.task_scheduler import TaskScheduler

logger = logging.getLogger(__name__)


class ExperimentManager:
    """Manages experiments including creation, configuration, and participant enrollment."""

    def __init__(self, db_manager: DatabaseManager, task_scheduler: TaskScheduler = None):
        self.db_manager = db_manager
        self.task_scheduler = task_scheduler or TaskScheduler()

        # Configuration constraints
        self.MAX_SESSIONS = 2
        self.MIN_SESSIONS = 1
        self.MAX_TASKS_PER_SESSION = 4
        self.MIN_TASKS_PER_SESSION = 1

        # Available task types
        self.AVAILABLE_TASKS = [task.value for task in TaskType]

        # Default task configurations
        self.default_task_configs = self._load_default_task_configs()

    def _load_default_task_configs(self) -> Dict:
        """Load default task configurations from settings."""
        config_path = Path("config/settings.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                    return settings.get('tasks', {})
            except Exception as e:
                logger.error(f"Error loading default task configs: {e}")

        # Return hardcoded defaults if file not found
        return {
            "bart": {
                "max_pumps": 48,
                "points_per_pump": 5,
                "explosion_range": [8, 48],
                "keyboard_input_mode": False,
                "balloon_color": "Red",
                "random_colors": False
            },
            "ice_fishing": {
                "max_fish": 64,
                "points_per_fish": 5
            },
            "mountain_mining": {
                "max_ore": 64,
                "points_per_ore": 5
            },
            "spinning_bottle": {
                "segments": 16,
                "points_per_add": 5,
                "spin_speed_range": [12.0, 18.0],
                "win_color": "Green",
                "loss_color": "Red"
            }
        }

    def create_experiment(self, name: str, code: str = None, config: Dict = None) -> Tuple[bool, int, str]:
        """
        Create a new experiment with the given configuration.
        Returns (success, experiment_id, message)
        """
        try:
            # Validate configuration
            if config:
                is_valid, errors = self.validate_experiment_config(config)
                if not is_valid:
                    return False, 0, f"Invalid configuration: {', '.join(errors)}"

            # Create experiment in database
            experiment_id = self.db_manager.create_experiment(
                name=name,
                code=code,
                description=config.get('description') if config else None,
                num_sessions=config.get('num_sessions', 1) if config else 1,
                randomize_order=config.get('randomize_order', False) if config else False,
                created_by=config.get('created_by') if config else None
            )

            # Create experiment structure if config provided
            if config and 'sessions' in config:
                for session_num, session_config in config['sessions'].items():
                    # Create experiment session
                    experiment_session_id = self.db_manager.create_experiment_session(
                        experiment_id,
                        int(session_num),
                        len(session_config.get('tasks', []))
                    )

                    # Add tasks to session
                    for i, task_config in enumerate(session_config.get('tasks', [])):
                        task_type = task_config['type']
                        task_order = i + 1 if not config.get('randomize_order') else 0

                        # Merge default config with custom config
                        final_config = self.default_task_configs.get(task_type, {}).copy()
                        if 'config' in task_config:
                            final_config.update(task_config['config'])

                        self.db_manager.add_experiment_task(
                            experiment_session_id,
                            task_type,
                            task_order,
                            final_config
                        )

            experiment = self.db_manager.get_experiment(experiment_id)
            logger.info(f"Created experiment '{name}' with ID {experiment_id} and code {experiment['code']}")

            return True, experiment_id, f"Experiment created successfully. Code: {experiment['code']}"

        except Exception as e:
            logger.error(f"Error creating experiment: {e}")
            return False, 0, str(e)

    def get_experiment(self, experiment_id: int) -> Optional[Dict]:
        """Get experiment details with full structure."""
        experiment = self.db_manager.get_experiment(experiment_id)
        if not experiment:
            return None

        # Add sessions and tasks
        experiment['sessions'] = self.db_manager.get_experiment_sessions(experiment_id)

        # Add enrollment statistics
        experiment['statistics'] = self.db_manager.get_experiment_statistics(experiment_id)

        return experiment

    def update_experiment(self, experiment_id: int, config: Dict) -> Tuple[bool, str]:
        """
        Update experiment configuration.
        Note: This only updates metadata, not the structure.
        """
        try:
            # Validate if structure changes are attempted
            experiment = self.get_experiment(experiment_id)
            if not experiment:
                return False, "Experiment not found"

            # Check if experiment has active participants
            if experiment['statistics']['total_enrolled'] > 0:
                # Only allow updating name, description, and active status
                allowed_updates = {}
                if 'name' in config:
                    allowed_updates['name'] = config['name']
                if 'description' in config:
                    allowed_updates['description'] = config['description']
                if 'active' in config:
                    allowed_updates['active'] = config['active']

                if not allowed_updates:
                    return False, "No valid updates provided"

                self.db_manager.update_experiment(experiment_id, **allowed_updates)
                return True, "Experiment updated successfully (structure cannot be changed after enrollment)"
            else:
                # No participants enrolled, allow full update
                # This would require deleting and recreating sessions/tasks
                # For now, just update metadata
                self.db_manager.update_experiment(
                    experiment_id,
                    name=config.get('name', experiment['name']),
                    description=config.get('description', experiment['description']),
                    num_sessions=config.get('num_sessions', experiment['num_sessions']),
                    randomize_order=config.get('randomize_order', experiment['randomize_order']),
                    active=config.get('active', experiment['active'])
                )

                return True, "Experiment metadata updated successfully"

        except Exception as e:
            logger.error(f"Error updating experiment: {e}")
            return False, str(e)

    def delete_experiment(self, experiment_id: int) -> Tuple[bool, str]:
        """Delete an experiment if it has no enrolled participants."""
        try:
            experiment = self.get_experiment(experiment_id)
            if not experiment:
                return False, "Experiment not found"

            # Check if experiment has enrolled participants
            if experiment['statistics']['total_enrolled'] > 0:
                return False, f"Cannot delete experiment with {experiment['statistics']['total_enrolled']} enrolled participants"

            self.db_manager.delete_experiment(experiment_id)
            return True, "Experiment deleted successfully"

        except Exception as e:
            logger.error(f"Error deleting experiment: {e}")
            return False, str(e)

    def enroll_participant(self, participant_id: int, experiment_code: str) -> Tuple[bool, str]:
        """Enroll a participant in an experiment using the experiment code."""
        try:
            # Get experiment by code
            experiment = self.db_manager.get_experiment_by_code(experiment_code)
            if not experiment:
                return False, "Invalid experiment code"

            # Check if experiment is active
            if not experiment['active']:
                return False, "This experiment is not currently active"

            # Check if participant is already enrolled in an experiment
            participant = self.db_manager.get_participant(participant_id=participant_id)
            if participant and participant['experiment_id']:
                return False, "Participant is already enrolled in an experiment"

            # Enroll participant
            self.db_manager.enroll_participant_in_experiment(participant_id, experiment['id'])

            # Create first session for participant
            self._create_participant_session(participant_id, experiment['id'], 1)

            return True, f"Successfully enrolled in experiment: {experiment['name']}"

        except Exception as e:
            logger.error(f"Error enrolling participant: {e}")
            return False, str(e)

    def enroll_participant_by_code(self, participant_code: str, experiment_code: str) -> Tuple[bool, str]:
        """Enroll a participant using both participant code and experiment code."""
        # Get participant
        participant = self.db_manager.get_participant(participant_code=participant_code)
        if not participant:
            return False, "Invalid participant code"

        return self.enroll_participant(participant['id'], experiment_code)

    def _create_participant_session(self, participant_id: int, experiment_id: int, session_number: int):
        """Create a session for a participant based on experiment configuration."""
        # Get experiment sessions
        experiment_sessions = self.db_manager.get_experiment_sessions(experiment_id)

        # Find the corresponding session template
        session_template = None
        for es in experiment_sessions:
            if es['session_number'] == session_number:
                session_template = es
                break

        if not session_template:
            raise ValueError(f"No session template found for session {session_number}")

        # Get experiment configuration
        experiment = self.db_manager.get_experiment(experiment_id)

        # Get tasks for this session
        tasks = []
        task_configs = {}

        for task in session_template['tasks']:
            tasks.append(task['task_type'])
            if task['task_config']:
                task_configs[task['task_type']] = task['task_config']

        # Randomize task order if configured
        if experiment['randomize_order']:
            random.shuffle(tasks)

        # Create the session
        session_id = self.db_manager.create_session(
            participant_id,
            session_number,
            tasks,
            session_template['id']
        )

        # Store task configurations for the session
        # This could be extended to store configs in a session_task_configs table
        logger.info(f"Created session {session_number} for participant {participant_id} in experiment {experiment_id}")

    def get_participant_next_session(self, participant_id: int) -> Optional[int]:
        """Get the next session number for a participant in their experiment."""
        participant = self.db_manager.get_participant(participant_id=participant_id)
        if not participant or not participant['experiment_id']:
            return None

        # Get participant's progress
        progress = self.db_manager.get_participant_experiment_progress(
            participant_id,
            participant['experiment_id']
        )

        if not progress:
            return None

        # Check if all sessions completed
        if progress['completed_sessions'] >= progress['num_sessions']:
            return None

        # Return next session number
        return progress['completed_sessions'] + 1

    def create_participant_next_session(self, participant_id: int) -> Tuple[bool, int, str]:
        """
        Create the next session for a participant in their experiment.
        Returns (success, session_id, message)
        """
        try:
            participant = self.db_manager.get_participant(participant_id=participant_id)
            if not participant or not participant['experiment_id']:
                return False, 0, "Participant not enrolled in an experiment"

            next_session_num = self.get_participant_next_session(participant_id)
            if not next_session_num:
                return False, 0, "All sessions completed for this experiment"

            # Check session gap requirement
            sessions = self.db_manager.get_participant_sessions(participant_id)
            if sessions:
                last_session = max(sessions, key=lambda s: s['session_number'])
                if last_session and not last_session['completed']:
                    return False, 0, f"Please complete session {last_session['session_number']} first"

                # Check time gap
                if last_session and last_session['completed']:
                    from datetime import datetime
                    last_date = datetime.fromisoformat(last_session['end_time'])
                    days_since = (datetime.now() - last_date).days

                    # Load config for session gap
                    config_path = Path("config/settings.json")
                    required_gap = 14  # default
                    if config_path.exists():
                        with open(config_path, 'r') as f:
                            settings = json.load(f)
                            required_gap = settings.get('experiment', {}).get('session_gap_days', 14)

                    if days_since < required_gap:
                        days_remaining = required_gap - days_since
                        return False, 0, f"Please wait {days_remaining} more days before starting the next session"

            # Create the session
            self._create_participant_session(
                participant_id,
                participant['experiment_id'],
                next_session_num
            )

            # Get the created session
            sessions = self.db_manager.get_participant_sessions(participant_id)
            new_session = next(s for s in sessions if s['session_number'] == next_session_num)

            return True, new_session['id'], f"Session {next_session_num} created successfully"

        except Exception as e:
            logger.error(f"Error creating next session: {e}")
            return False, 0, str(e)

    def get_experiment_progress(self, experiment_id: int) -> Dict:
        """Get detailed progress information for an experiment."""
        return self.db_manager.get_experiment_statistics(experiment_id)

    def validate_experiment_config(self, config: Dict) -> Tuple[bool, List[str]]:
        """Validate experiment configuration."""
        errors = []

        # Check required fields
        if 'name' not in config or not config['name']:
            errors.append("Experiment name is required")

        # Check number of sessions
        num_sessions = config.get('num_sessions', 1)
        if num_sessions < self.MIN_SESSIONS or num_sessions > self.MAX_SESSIONS:
            errors.append(f"Number of sessions must be between {self.MIN_SESSIONS} and {self.MAX_SESSIONS}")

        # Check sessions configuration
        if 'sessions' in config:
            if len(config['sessions']) != num_sessions:
                errors.append(
                    f"Number of session configurations ({len(config['sessions'])}) must match num_sessions ({num_sessions})")

            # Validate each session
            all_tasks_used = set()

            for session_num, session_config in config['sessions'].items():
                try:
                    session_num_int = int(session_num)
                    if session_num_int < 1 or session_num_int > num_sessions:
                        errors.append(f"Invalid session number: {session_num}")
                except ValueError:
                    errors.append(f"Session number must be an integer: {session_num}")

                # Check tasks in session
                if 'tasks' not in session_config or not session_config['tasks']:
                    errors.append(f"Session {session_num} must have at least one task")
                    continue

                tasks = session_config['tasks']
                if len(tasks) < self.MIN_TASKS_PER_SESSION or len(tasks) > self.MAX_TASKS_PER_SESSION:
                    errors.append(
                        f"Session {session_num} must have between {self.MIN_TASKS_PER_SESSION} and {self.MAX_TASKS_PER_SESSION} tasks")

                # Check task validity and uniqueness
                for task in tasks:
                    if 'type' not in task:
                        errors.append(f"Task in session {session_num} missing type")
                        continue

                    task_type = task['type']
                    if task_type not in self.AVAILABLE_TASKS:
                        errors.append(f"Invalid task type in session {session_num}: {task_type}")

                    # Check for duplicate tasks across sessions
                    if task_type in all_tasks_used:
                        errors.append(f"Task {task_type} is used in multiple sessions")
                    all_tasks_used.add(task_type)

                    # Validate task config if provided
                    if 'config' in task and task['config']:
                        config_errors = self._validate_task_config(task_type, task['config'])
                        errors.extend(config_errors)

        return len(errors) == 0, errors

    def _validate_task_config(self, task_type: str, config: Dict) -> List[str]:
        """Validate task-specific configuration."""
        errors = []

        if task_type == 'bart':
            if 'max_pumps' in config and (config['max_pumps'] < 1 or config['max_pumps'] > 128):
                errors.append("BART: max_pumps must be between 1 and 128")

            if 'explosion_range' in config:
                if len(config['explosion_range']) != 2:
                    errors.append("BART: explosion_range must be a list of two values")
                elif config['explosion_range'][0] >= config['explosion_range'][1]:
                    errors.append("BART: explosion_range minimum must be less than maximum")

            if 'balloon_color' in config:
                valid_colors = ["Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Pink"]
                if config['balloon_color'] not in valid_colors:
                    errors.append(f"BART: invalid balloon_color. Must be one of: {', '.join(valid_colors)}")

        elif task_type == 'ice_fishing':
            if 'max_fish' in config and (config['max_fish'] < 1 or config['max_fish'] > 100):
                errors.append("Ice Fishing: max_fish must be between 1 and 100")

        elif task_type == 'mountain_mining':
            if 'max_ore' in config and (config['max_ore'] < 1 or config['max_ore'] > 100):
                errors.append("Mountain Mining: max_ore must be between 1 and 100")

        elif task_type == 'spinning_bottle':
            if 'segments' in config and config['segments'] not in [8, 16, 32]:
                errors.append("Spinning Bottle: segments must be 8, 16, or 32")

            if 'spin_speed_range' in config:
                if len(config['spin_speed_range']) != 2:
                    errors.append("Spinning Bottle: spin_speed_range must be a list of two values")
                elif config['spin_speed_range'][0] >= config['spin_speed_range'][1]:
                    errors.append("Spinning Bottle: spin_speed_range minimum must be less than maximum")

            valid_colors = ["Green", "Red", "Blue", "Yellow", "Orange", "Purple"]
            if 'win_color' in config and config['win_color'] not in valid_colors:
                errors.append(f"Spinning Bottle: invalid win_color. Must be one of: {', '.join(valid_colors)}")
            if 'loss_color' in config and config['loss_color'] not in valid_colors:
                errors.append(f"Spinning Bottle: invalid loss_color. Must be one of: {', '.join(valid_colors)}")

        return errors

    def export_experiment_template(self, experiment_id: int) -> Optional[Dict]:
        """Export experiment configuration as a reusable template."""
        return self.db_manager.export_experiment_template(experiment_id)

    def import_experiment_template(self, template_data: Dict, created_by: str = None) -> Tuple[bool, int, str]:
        """
        Import an experiment from a template.
        Returns (success, experiment_id, message)
        """
        try:
            # Validate template
            is_valid, errors = self.validate_experiment_config(template_data)
            if not is_valid:
                return False, 0, f"Invalid template: {', '.join(errors)}"

            # Import using database manager
            experiment_id = self.db_manager.import_experiment_template(template_data, created_by)

            experiment = self.db_manager.get_experiment(experiment_id)
            return True, experiment_id, f"Experiment imported successfully. Code: {experiment['code']}"

        except Exception as e:
            logger.error(f"Error importing template: {e}")
            return False, 0, str(e)

    def duplicate_experiment(self, experiment_id: int, new_name: str) -> Tuple[bool, int, str]:
        """
        Duplicate an existing experiment with a new name.
        Returns (success, new_experiment_id, message)
        """
        try:
            # Export existing experiment as template
            template = self.export_experiment_template(experiment_id)
            if not template:
                return False, 0, "Failed to export experiment template"

            # Update name
            template['name'] = new_name

            # Import as new experiment
            return self.import_experiment_template(template)

        except Exception as e:
            logger.error(f"Error duplicating experiment: {e}")
            return False, 0, str(e)

    def get_available_experiments(self, active_only: bool = True) -> List[Dict]:
        """Get list of available experiments."""
        experiments = self.db_manager.get_all_experiments()

        if active_only:
            experiments = [e for e in experiments if e['active']]

        return experiments

    def get_participant_experiment_info(self, participant_id: int) -> Optional[Dict]:
        """Get experiment information for a participant."""
        participant = self.db_manager.get_participant(participant_id=participant_id)
        if not participant or not participant['experiment_id']:
            return None

        experiment = self.get_experiment(participant['experiment_id'])
        if not experiment:
            return None

        # Add participant's progress
        progress = self.db_manager.get_participant_experiment_progress(
            participant_id,
            participant['experiment_id']
        )
        experiment['participant_progress'] = progress

        return experiment

    def bulk_enroll_participants(self, participant_ids: List[int],
                                 experiment_id: int) -> Tuple[int, List[str]]:
        """
        Enroll multiple participants in an experiment.
        Returns (success_count, error_messages)
        """
        success_count = 0
        errors = []

        experiment = self.db_manager.get_experiment(experiment_id)
        if not experiment:
            return 0, ["Experiment not found"]

        for participant_id in participant_ids:
            try:
                participant = self.db_manager.get_participant(participant_id=participant_id)
                if not participant:
                    errors.append(f"Participant {participant_id} not found")
                    continue

                if participant['experiment_id']:
                    errors.append(f"Participant {participant['participant_code']} already enrolled in an experiment")
                    continue

                # Enroll participant
                self.db_manager.enroll_participant_in_experiment(participant_id, experiment_id)

                # Create first session
                self._create_participant_session(participant_id, experiment_id, 1)

                success_count += 1

            except Exception as e:
                errors.append(f"Error enrolling participant {participant_id}: {str(e)}")

        return success_count, errors

    def get_experiment_data_export(self, experiment_id: int) -> Dict:
        """Get all data for an experiment formatted for export."""
        return self.db_manager.export_experiment_data(experiment_id)

    def search_experiments(self, search_term: str = None,
                           active_only: bool = True,
                           created_by: str = None) -> List[Dict]:
        """Search for experiments based on criteria."""
        experiments = self.get_available_experiments(active_only)

        # Filter by search term
        if search_term:
            search_lower = search_term.lower()
            experiments = [
                e for e in experiments
                if search_lower in e['name'].lower() or
                   search_lower in e['code'].lower() or
                   (e['description'] and search_lower in e['description'].lower())
            ]

        # Filter by creator
        if created_by:
            experiments = [e for e in experiments if e['created_by'] == created_by]

        return experiments