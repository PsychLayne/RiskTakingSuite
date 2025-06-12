"""
Task Scheduler for Risk Tasks Client
Handles random task assignment and ensures balanced distribution across participants.
"""

import random
from typing import List, Dict, Tuple
from collections import defaultdict
import json
from pathlib import Path
import logging

from database.models import TaskType

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages task assignment and scheduling for participants."""

    def __init__(self, assignments_file: str = "data/task_assignments.json"):
        self.assignments_file = Path(assignments_file)
        self.assignments = self.load_assignments()
        self.task_distribution = defaultdict(int)
        self._calculate_distribution()

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
        Ensures no duplicate tasks across sessions for the same participant.
        """
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

        logger.info(f"Assigned tasks {selected_tasks} to participant {participant_id} for session {session_number}")

        return selected_tasks

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
        participant_key = str(participant_id)

        if participant_key not in self.assignments:
            return {}

        # Convert string keys back to integers for session numbers
        return {
            int(session_num): tasks
            for session_num, tasks in self.assignments[participant_key].items()
        }

    def get_next_session_number(self, participant_id: int) -> int:
        """Get the next session number for a participant."""
        assignments = self.get_participant_assignments(participant_id)

        if not assignments:
            return 1

        return max(assignments.keys()) + 1

    def can_schedule_session(self, participant_id: int,
                             max_sessions: int = 2) -> bool:
        """Check if participant can schedule another session."""
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
            'participants_by_session_count': defaultdict(int)
        }

        # Count participants by number of sessions
        for sessions in self.assignments.values():
            session_count = len(sessions)
            summary['participants_by_session_count'][session_count] += 1

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