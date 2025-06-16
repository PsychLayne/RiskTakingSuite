"""
Data Models for Risk Tasks Client
Defines the structure and validation for database entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum
import json


class Gender(Enum):
    """Gender enumeration for participants."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class TaskType(Enum):
    """Available risk assessment tasks."""
    BART = "bart"  # Balloon Analogue Risk Task
    ICE_FISHING = "ice_fishing"  # Penguin Ice Fishing
    MOUNTAIN_MINING = "mountain_mining"  # Mountain Mining
    SPINNING_BOTTLE = "spinning_bottle"  # Spinning Bottle Task

    @classmethod
    def get_display_name(cls, task_type):
        """Get human-readable display name for task type."""
        display_names = {
            cls.BART: "Balloon Task (BART)",
            cls.ICE_FISHING: "Ice Fishing",
            cls.MOUNTAIN_MINING: "Mountain Mining",
            cls.SPINNING_BOTTLE: "Spinning Bottle"
        }
        return display_names.get(task_type, task_type.value)


class TrialOutcome(Enum):
    """Possible outcomes for a trial."""
    SUCCESS = "success"
    FAILURE = "failure"
    COLLECTED = "collected"  # For tasks where user can collect early
    TIMEOUT = "timeout"


@dataclass
class Participant:
    """Participant data model."""
    id: Optional[int] = None
    participant_code: str = ""
    age: Optional[int] = None
    gender: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate participant data after initialization."""
        if not self.participant_code:
            raise ValueError("Participant code is required")

        if self.age is not None and (self.age < 0 or self.age > 150):
            raise ValueError("Age must be between 0 and 150")

        if self.gender and self.gender not in [g.value for g in Gender]:
            raise ValueError(f"Invalid gender. Must be one of: {[g.value for g in Gender]}")

    def to_dict(self) -> Dict:
        """Convert participant to dictionary."""
        return {
            'id': self.id,
            'participant_code': self.participant_code,
            'age': self.age,
            'gender': self.gender,
            'created_date': self.created_date.isoformat(),
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Participant':
        """Create participant from dictionary."""
        if 'created_date' in data and isinstance(data['created_date'], str):
            data['created_date'] = datetime.fromisoformat(data['created_date'])
        return cls(**data)


@dataclass
class Session:
    """Session data model."""
    id: Optional[int] = None
    participant_id: int = None
    session_number: int = 1
    session_date: datetime = field(default_factory=datetime.now)
    tasks_assigned: List[str] = field(default_factory=list)
    completed: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    experiment_id: Optional[int] = None  # Added for experiment support

    def __post_init__(self):
        """Validate session data after initialization."""
        if self.participant_id is None:
            raise ValueError("Participant ID is required")

        if self.session_number < 1:
            raise ValueError("Session number must be positive")

        if not self.tasks_assigned:
            raise ValueError("At least one task must be assigned")

        # Validate task types
        valid_tasks = [t.value for t in TaskType]
        for task in self.tasks_assigned:
            if task not in valid_tasks:
                raise ValueError(f"Invalid task type: {task}")

    def get_duration(self) -> Optional[float]:
        """Get session duration in minutes."""
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds() / 60
            return round(duration, 2)
        return None

    def is_overdue(self, max_gap_days: int = 14) -> bool:
        """Check if session is overdue based on configured gap."""
        if self.completed:
            return False

        days_since = (datetime.now() - self.session_date).days
        return days_since > max_gap_days

    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            'id': self.id,
            'participant_id': self.participant_id,
            'session_number': self.session_number,
            'session_date': self.session_date.isoformat(),
            'tasks_assigned': self.tasks_assigned,
            'completed': self.completed,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'experiment_id': self.experiment_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        """Create session from dictionary."""
        # Convert datetime strings
        for date_field in ['session_date', 'start_time', 'end_time']:
            if date_field in data and data[date_field]:
                if isinstance(data[date_field], str):
                    data[date_field] = datetime.fromisoformat(data[date_field])

        return cls(**data)


@dataclass
class TrialData:
    """Trial data model for individual task trials."""
    id: Optional[int] = None
    session_id: int = None
    task_name: str = ""
    trial_number: int = 1
    risk_level: float = 0.0
    points_earned: int = 0
    outcome: str = ""
    reaction_time: Optional[float] = None
    additional_data: Optional[Dict] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate trial data after initialization."""
        if self.session_id is None:
            raise ValueError("Session ID is required")

        if not self.task_name:
            raise ValueError("Task name is required")

        if self.task_name not in [t.value for t in TaskType]:
            raise ValueError(f"Invalid task name: {self.task_name}")

        if self.trial_number < 1:
            raise ValueError("Trial number must be positive")

        if not 0 <= self.risk_level <= 1:
            raise ValueError("Risk level must be between 0 and 1")

        if self.points_earned < 0:
            raise ValueError("Points earned cannot be negative")

        if self.outcome and self.outcome not in [o.value for o in TrialOutcome]:
            raise ValueError(f"Invalid outcome: {self.outcome}")

    def get_task_specific_data(self, key: str, default=None):
        """Get task-specific data from additional_data field."""
        if self.additional_data and key in self.additional_data:
            return self.additional_data[key]
        return default

    def set_task_specific_data(self, key: str, value):
        """Set task-specific data in additional_data field."""
        if self.additional_data is None:
            self.additional_data = {}
        self.additional_data[key] = value

    def to_dict(self) -> Dict:
        """Convert trial data to dictionary."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'task_name': self.task_name,
            'trial_number': self.trial_number,
            'risk_level': self.risk_level,
            'points_earned': self.points_earned,
            'outcome': self.outcome,
            'reaction_time': self.reaction_time,
            'additional_data': self.additional_data,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TrialData':
        """Create trial data from dictionary."""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Experiment:
    """Experiment data model."""
    id: Optional[int] = None
    experiment_code: str = ""
    name: str = ""
    description: Optional[str] = None
    config: Dict = field(default_factory=dict)
    created_date: datetime = field(default_factory=datetime.now)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    max_participants: Optional[int] = None
    created_by: Optional[str] = None

    def __post_init__(self):
        """Validate experiment data after initialization."""
        if not self.experiment_code:
            raise ValueError("Experiment code is required")

        if not self.name:
            raise ValueError("Experiment name is required")

        # Validate experiment code format (alphanumeric, no spaces)
        if not self.experiment_code.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Experiment code must be alphanumeric (hyphens and underscores allowed)")

        # Validate config has required fields
        required_config = ['experiment', 'tasks', 'display', 'data']
        for field in required_config:
            if field not in self.config:
                raise ValueError(f"Config must include '{field}' section")

    def is_enrollment_open(self) -> bool:
        """Check if experiment is open for enrollment."""
        if not self.is_active:
            return False

        now = datetime.now()

        # Check start date
        if self.start_date and now < self.start_date:
            return False

        # Check end date
        if self.end_date and now > self.end_date:
            return False

        return True

    def get_task_sequence(self, session_number: int) -> List[str]:
        """Get the task sequence for a given session."""
        task_config = self.config.get('experiment', {}).get('task_sequence', {})

        # Check if using fixed sequence
        if task_config.get('type') == 'fixed':
            sequences = task_config.get('sequences', {})
            session_key = str(session_number)
            if session_key in sequences:
                return sequences[session_key]

        # Default to empty list (will use random assignment)
        return []

    def to_dict(self) -> Dict:
        """Convert experiment to dictionary."""
        return {
            'id': self.id,
            'experiment_code': self.experiment_code,
            'name': self.name,
            'description': self.description,
            'config': self.config,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'max_participants': self.max_participants,
            'created_by': self.created_by
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Experiment':
        """Create experiment from dictionary."""
        # Convert datetime strings
        for date_field in ['created_date', 'start_date', 'end_date']:
            if date_field in data and data[date_field]:
                if isinstance(data[date_field], str):
                    data[date_field] = datetime.fromisoformat(data[date_field])

        return cls(**data)


@dataclass
class ExperimentConfig:
    """Extended configuration for experiments."""
    # Base configuration
    base_config: Dict = field(default_factory=dict)

    # Experiment-specific overrides
    total_trials_per_task: Optional[int] = None
    session_gap_days: Optional[int] = None
    max_session_duration: Optional[int] = None
    tasks_per_session: Optional[int] = None

    # Task sequence configuration
    task_sequence_type: str = "random"  # "random" or "fixed"
    fixed_sequences: Optional[Dict[int, List[str]]] = None

    # Task-specific parameter overrides
    task_overrides: Dict[str, Dict] = field(default_factory=dict)

    # Inclusion/exclusion of tasks
    enabled_tasks: Optional[List[str]] = None
    disabled_tasks: Optional[List[str]] = None

    def merge_with_base(self, base_config: Dict) -> Dict:
        """Merge experiment config with base config."""
        import copy
        merged = copy.deepcopy(base_config)

        # Apply experiment-level overrides
        if self.total_trials_per_task is not None:
            merged['experiment']['total_trials_per_task'] = self.total_trials_per_task
        if self.session_gap_days is not None:
            merged['experiment']['session_gap_days'] = self.session_gap_days
        if self.max_session_duration is not None:
            merged['experiment']['max_session_duration'] = self.max_session_duration
        if self.tasks_per_session is not None:
            merged['experiment']['tasks_per_session'] = self.tasks_per_session

        # Apply task sequence configuration
        merged['experiment']['task_sequence'] = {
            'type': self.task_sequence_type,
            'sequences': self.fixed_sequences or {}
        }

        # Apply task-specific overrides
        if 'tasks' not in merged:
            merged['tasks'] = {}

        for task_name, overrides in self.task_overrides.items():
            if task_name not in merged['tasks']:
                merged['tasks'][task_name] = {}
            merged['tasks'][task_name].update(overrides)

        # Apply task enable/disable
        if self.enabled_tasks is not None:
            merged['experiment']['enabled_tasks'] = self.enabled_tasks
        if self.disabled_tasks is not None:
            merged['experiment']['disabled_tasks'] = self.disabled_tasks

        return merged


@dataclass
class ExperimentEnrollment:
    """Experiment enrollment model."""
    id: Optional[int] = None
    experiment_id: int = None
    participant_id: int = None
    enrollment_date: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate enrollment data after initialization."""
        if self.experiment_id is None:
            raise ValueError("Experiment ID is required")

        if self.participant_id is None:
            raise ValueError("Participant ID is required")

    def to_dict(self) -> Dict:
        """Convert enrollment to dictionary."""
        return {
            'id': self.id,
            'experiment_id': self.experiment_id,
            'participant_id': self.participant_id,
            'enrollment_date': self.enrollment_date.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ExperimentEnrollment':
        """Create enrollment from dictionary."""
        if 'enrollment_date' in data and isinstance(data['enrollment_date'], str):
            data['enrollment_date'] = datetime.fromisoformat(data['enrollment_date'])
        return cls(**data)


@dataclass
class ParticipantStatistics:
    """Statistics for a participant across all tasks."""
    participant_id: int
    total_sessions: int = 0
    completed_sessions: int = 0
    total_trials: int = 0
    total_points: int = 0

    # Task-specific statistics
    task_stats: Dict[str, Dict] = field(default_factory=dict)

    # Risk profile metrics
    average_risk_level: float = 0.0
    risk_consistency: float = 0.0  # Standard deviation of risk levels

    def calculate_risk_profile(self):
        """Calculate overall risk profile from task statistics."""
        all_risk_levels = []

        for task_name, stats in self.task_stats.items():
            if 'risk_levels' in stats:
                all_risk_levels.extend(stats['risk_levels'])

        if all_risk_levels:
            import numpy as np
            self.average_risk_level = np.mean(all_risk_levels)
            self.risk_consistency = np.std(all_risk_levels)

    def get_risk_category(self) -> str:
        """Categorize participant's risk profile."""
        if self.average_risk_level < 0.33:
            return "Conservative"
        elif self.average_risk_level < 0.67:
            return "Moderate"
        else:
            return "Risk-Taking"

    def to_dict(self) -> Dict:
        """Convert statistics to dictionary."""
        return {
            'participant_id': self.participant_id,
            'total_sessions': self.total_sessions,
            'completed_sessions': self.completed_sessions,
            'total_trials': self.total_trials,
            'total_points': self.total_points,
            'task_stats': self.task_stats,
            'average_risk_level': self.average_risk_level,
            'risk_consistency': self.risk_consistency,
            'risk_category': self.get_risk_category()
        }


@dataclass
class ExperimentStatistics:
    """Statistics for an experiment."""
    experiment_id: int
    participant_count: int = 0
    completed_participants: int = 0
    total_sessions: int = 0
    completed_sessions: int = 0
    total_trials: int = 0

    # Task-level statistics
    task_stats: Dict[str, Dict] = field(default_factory=dict)

    # Completion rates
    session_completion_rate: float = 0.0
    participant_completion_rate: float = 0.0

    # Risk metrics across all participants
    average_risk_level: float = 0.0
    risk_variance: float = 0.0

    def calculate_completion_rates(self):
        """Calculate completion rates."""
        if self.total_sessions > 0:
            self.session_completion_rate = self.completed_sessions / self.total_sessions

        if self.participant_count > 0:
            self.participant_completion_rate = self.completed_participants / self.participant_count

    def to_dict(self) -> Dict:
        """Convert statistics to dictionary."""
        return {
            'experiment_id': self.experiment_id,
            'participant_count': self.participant_count,
            'completed_participants': self.completed_participants,
            'total_sessions': self.total_sessions,
            'completed_sessions': self.completed_sessions,
            'total_trials': self.total_trials,
            'task_stats': self.task_stats,
            'session_completion_rate': self.session_completion_rate,
            'participant_completion_rate': self.participant_completion_rate,
            'average_risk_level': self.average_risk_level,
            'risk_variance': self.risk_variance
        }