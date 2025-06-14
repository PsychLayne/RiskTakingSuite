"""
Task Scheduler for Risk Tasks Client
Handles random task assignment and ensures balanced distribution across participants.
Now supports experiment-based task assignments.
"""

import random
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import json
from pathlib import Path
import logging

from database.models import TaskType
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages task assignment and scheduling for participants."""

    def __init__(self, assignments_file: str = "data/task_assignments.json", db_manager: DatabaseManager = None):
        self.assignments_file = Path(assignments_file)
        self.assignments = self.load_assignments()
        self.task_distribution = defaultdict(int)
        self._calculate_distribution()
        self.db_manager = db_manager

    def load_assignments(self) -> Dict:
        """Load existing task assignments from file."""
        if self.assignments_file.exists():
            try:
                with open(self.assignments_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading assignments: {e}")
                return {}
        return {}

    def save_assignments(self):
        """Save task assignments to file."""
        try:
            self.assignments_file.parent.mkdir(exist_ok=True)
            with open(self.assignments_file, 'w') as f:
                json.dump(self.assignments, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving assignments: {e}")

    def _calculate_distribution(self):
        """Calculate current distribution of tasks."""
        self.task_distribution.clear()

        for participant_assignments in self.assignments.values():
            for session_tasks in participant_assignments.values():
                for task in session_tasks:
                    self.task_distribution[task] += 1

    def get_available_tasks(self) -> List[str]:
        """Get list of all available tasks."""
        return [task.value for task in TaskType]

    def assign_tasks_for_participant(self, participant_id: int,
                                     session_number: int,
                                     tasks_per_session: int = 2) -> List[str]:
        """
        Assign random tasks for a participant's session.
        Checks for experiment enrollment first, then falls back to random assignment.
        """
        # Check if participant is in an experiment
        if self.db_manager:
            participant = self.db_manager.get_participant(participant_id=participant_id)
            if participant and participant.get('experiment_id'):
                # Get experiment tasks for this session
                experiment_tasks = self._get_experiment_tasks(participant_id, session_number)
                if experiment_tasks:
                    logger.info(f"Using experiment tasks for participant {participant_id}: {experiment_tasks}")
                    return experiment_tasks

        # Fall back to original random assignment for non-experiment participants
        participant_key = str(participant_id)

        # Initialize participant entry if not exists
        if participant_key not in self.assignments:
            self.assignments[participant_key] = {}

        # Get previously assigned tasks for this participant
        previously_assigned = set()
        for session_tasks in self.assignments[participant_key].values():
            previously_assigned.update(session_tasks)

        # Get available tasks (not yet assigned to this participant)
        all_tasks = self.get_available_tasks()
        available_tasks = [task for task in all_tasks if task not in previously_assigned]

        # Check if we have enough tasks available
        if len(available_tasks) < tasks_per_session:
            raise ValueError(
                f"Not enough unassigned tasks available. "
                f"Need {tasks_per_session}, but only {len(available_tasks)} available."
            )

        # Select tasks with balanced distribution in mind
        selected_tasks = self._select_balanced_tasks(available_tasks, tasks_per_session)

        # Save assignment
        session_key = str(session_number)
        self.assignments[participant_key][session_key] = selected_tasks

        # Update distribution
        for task in selected_tasks:
            self.task_distribution[task] += 1

        # Save to file
        self.save_assignments()

        logger.info(f"Assigned random tasks {selected_tasks} to participant {participant_id} for session {session_number}")

        return selected_tasks

    def _get_experiment_tasks(self, participant_id: int, session_number: int) -> Optional[List[str]]:
        """Get tasks for a participant in an experiment."""
        if not self.db_manager:
            return None

        try:
            # Get participant's experiment info
            participant = self.db_manager.get_participant(participant_id=participant_id)
            if not participant or not participant.get('experiment_id'):
                return None

            # Get experiment sessions
            experiment_sessions = self.db_manager.get_experiment_sessions(participant['experiment_id'])

            # Find the session template for this session number
            session_template = None
            for es in experiment_sessions:
                if es['session_number'] == session_number:
                    session_template = es
                    break

            if not session_template:
                return None

            # Get tasks for this session
            tasks = []
            for task in session_template['tasks']:
                tasks.append(task['task_type'])

            # Check if randomization is enabled
            experiment = self.db_manager.get_experiment(participant['experiment_id'])
            if experiment and experiment.get('randomize_order'):
                # For randomized experiments, we need to maintain consistency
                # Use participant ID and session number as seed for reproducible randomization
                random.seed(f"{participant_id}-{session_number}")
                random.shuffle(tasks)
                random.seed()  # Reset seed

            return tasks

        except Exception as e:
            logger.error(f"Error getting experiment tasks: {e}")
            return None

    def _select_balanced_tasks(self, available_tasks: List[str],
                               count: int) -> List[str]:
        """
        Select tasks while trying to maintain balanced distribution.
        Tasks with lower usage are prioritized.
        """
        # Sort available tasks by current usage (ascending)
        task_usage = [(task, self.task_distribution.get(task, 0))
                      for task in available_tasks]
        task_usage.sort(key=lambda x: x[1])

        # Group tasks by usage count
        usage_groups = defaultdict(list)
        for task, usage in task_usage:
            usage_groups[usage].append(task)

        selected_tasks = []

        # Select from groups with lowest usage first
        for usage in sorted(usage_groups.keys()):
            tasks_in_group = usage_groups[usage]
            random.shuffle(tasks_in_group)

            while tasks_in_group and len(selected_tasks) < count:
                selected_tasks.append(tasks_in_group.pop())

        return selected_tasks

    def get_participant_assignments(self, participant_id: int) -> Dict[int, List[str]]:
        """Get all task assignments for a participant."""
        # Check if participant is in an experiment first
        if self.db_manager:
            participant = self.db_manager.get_participant(participant_id=participant_id)
            if participant and participant.get('experiment_id'):
                return self._get_experiment_assignments(participant_id)

        # Fall back to file-based assignments
        participant_key = str(participant_id)

        if participant_key not in self.assignments:
            return {}

        # Convert string keys back to integers for session numbers
        return {
            int(session_num): tasks
            for session_num, tasks in self.assignments[participant_key].items()
        }

    def _get_experiment_assignments(self, participant_id: int) -> Dict[int, List[str]]:
        """Get all task assignments for an experiment participant."""
        assignments = {}

        try:
            participant = self.db_manager.get_participant(participant_id=participant_id)
            if not participant or not participant.get('experiment_id'):
                return {}

            # Get all sessions for this participant
            sessions = self.db_manager.get_participant_sessions(participant_id)

            for session in sessions:
                session_number = session['session_number']
                tasks = self._get_experiment_tasks(participant_id, session_number)
                if tasks:
                    assignments[session_number] = tasks

            return assignments

        except Exception as e:
            logger.error(f"Error getting experiment assignments: {e}")
            return {}

    def get_next_session_number(self, participant_id: int) -> int:
        """Get the next session number for a participant."""
        assignments = self.get_participant_assignments(participant_id)

        if not assignments:
            return 1

        return max(assignments.keys()) + 1

    def can_schedule_session(self, participant_id: int,
                             max_sessions: int = 2) -> bool:
        """Check if participant can schedule another session."""
        # Check if participant is in an experiment
        if self.db_manager:
            participant = self.db_manager.get_participant(participant_id=participant_id)
            if participant and participant.get('experiment_id'):
                # For experiment participants, check experiment progress
                progress = self.db_manager.get_participant_experiment_progress(
                    participant_id,
                    participant['experiment_id']
                )
                if progress:
                    return progress['completed_sessions'] < progress['num_sessions']

        # Fall back to traditional check
        assignments = self.get_participant_assignments(participant_id)
        return len(assignments) < max_sessions

    def get_task_distribution_stats(self) -> Dict[str, Dict]:
        """Get statistics about task distribution."""
        all_tasks = self.get_available_tasks()

        stats = {}
        for task in all_tasks:
            count = self.task_distribution.get(task, 0)
            stats[task] = {
                'count': count,
                'display_name': TaskType.get_display_name(TaskType(task)),
                'percentage': 0.0
            }

        # Calculate percentages
        total_assignments = sum(stat['count'] for stat in stats.values())
        if total_assignments > 0:
            for task_stats in stats.values():
                task_stats['percentage'] = (task_stats['count'] / total_assignments) * 100

        return stats

    def reset_participant_assignments(self, participant_id: int):
        """Reset all assignments for a participant (use with caution)."""
        # Check if participant is in an experiment
        if self.db_manager:
            participant = self.db_manager.get_participant(participant_id=participant_id)
            if participant and participant.get('experiment_id'):
                logger.warning(f"Cannot reset assignments for experiment participant {participant_id}")
                return

        # Only reset for non-experiment participants
        participant_key = str(participant_id)

        if participant_key in self.assignments:
            # Update distribution before removing
            for session_tasks in self.assignments[participant_key].values():
                for task in session_tasks:
                    self.task_distribution[task] -= 1

            # Remove participant assignments
            del self.assignments[participant_key]
            self.save_assignments()

            logger.warning(f"Reset all assignments for participant {participant_id}")

    def validate_assignments(self) -> Tuple[bool, List[str]]:
        """
        Validate all assignments for consistency.
        Returns (is_valid, list_of_errors)
        """
        errors = []

        for participant_id, sessions in self.assignments.items():
            # Check for duplicate tasks across sessions
            all_tasks = []
            for session_num, tasks in sessions.items():
                all_tasks.extend(tasks)

            if len(all_tasks) != len(set(all_tasks)):
                errors.append(
                    f"Participant {participant_id} has duplicate task assignments"
                )

            # Check for invalid task names
            valid_tasks = self.get_available_tasks()
            for task in all_tasks:
                if task not in valid_tasks:
                    errors.append(
                        f"Invalid task '{task}' assigned to participant {participant_id}"
                    )

        return len(errors) == 0, errors

    def get_assignment_summary(self) -> Dict:
        """Get a summary of all assignments."""
        summary = {
            'total_participants': len(self.assignments),
            'total_sessions': sum(
                len(sessions) for sessions in self.assignments.values()
            ),
            'task_distribution': self.get_task_distribution_stats(),
            'participants_by_session_count': defaultdict(int),
            'experiment_participants': 0,
            'non_experiment_participants': 0
        }

        # Count participants by number of sessions
        for sessions in self.assignments.values():
            session_count = len(sessions)
            summary['participants_by_session_count'][session_count] += 1

        # Count experiment vs non-experiment participants if db_manager available
        if self.db_manager:
            participants = self.db_manager.get_all_participants()
            for p in participants:
                if p.get('experiment_id'):
                    summary['experiment_participants'] += 1
                else:
                    summary['non_experiment_participants'] += 1

        return summary

    def export_assignments(self, filepath: str):
        """Export assignments to a readable format."""
        export_data = {
            'assignments': {},
            'summary': self.get_assignment_summary()
        }

        # Format assignments for readability
        for participant_id, sessions in self.assignments.items():
            export_data['assignments'][f"Participant_{participant_id}"] = {}
            for session_num, tasks in sessions.items():
                task_names = [
                    TaskType.get_display_name(TaskType(task))
                    for task in tasks
                ]
                export_data['assignments'][f"Participant_{participant_id}"][f"Session_{session_num}"] = task_names

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=4)

        logger.info(f"Exported assignments to {filepath}")

    def get_experiment_task_configs(self, participant_id: int, session_number: int, task_type: str) -> Optional[Dict]:
        """Get task configuration for an experiment participant."""
        if not self.db_manager:
            return None

        try:
            participant = self.db_manager.get_participant(participant_id=participant_id)
            if not participant or not participant.get('experiment_id'):
                return None

            # Get the session
            sessions = self.db_manager.get_participant_sessions(participant_id)
            session = next((s for s in sessions if s['session_number'] == session_number), None)

            if not session or not session.get('experiment_session_id'):
                return None

            # Get task configs from experiment
            exp_tasks = self.db_manager.get_experiment_session_tasks(session['experiment_session_id'])
            for exp_task in exp_tasks:
                if exp_task['task_type'] == task_type:
                    return exp_task.get('task_config', {})

            return None

        except Exception as e:
            logger.error(f"Error getting experiment task configs: {e}")
            return None