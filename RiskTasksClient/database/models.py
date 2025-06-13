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
            'end_time': self.end_time.isoformat() if self.end_time else None
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
class ExperimentConfig:
    """Configuration for the experiment."""
    total_trials_per_task: int = 30
    session_gap_days: int = 14
    max_session_duration: int = 60  # minutes
    tasks_per_session: int = 2

    # Task-specific configurations
    bart_config: Dict = field(default_factory=lambda: {
        "max_pumps": 48,
        "points_per_pump": 5,
        "explosion_range": [8, 48]
    })

    ice_fishing_config: Dict = field(default_factory=lambda: {
        "max_fish": 64,
        "points_per_fish": 5,
        "break_probability_function": "linear"
    })

    mountain_mining_config: Dict = field(default_factory=lambda: {
        "max_ore": 64,
        "points_per_ore": 5,
        "snap_probability_function": "linear"
    })

    spinning_bottle_config: Dict = field(default_factory=lambda: {
        "segments": 16,
        "points_per_add": 5,
        "spin_speed_range": [12.0, 18.0]
    })

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            'total_trials_per_task': self.total_trials_per_task,
            'session_gap_days': self.session_gap_days,
            'max_session_duration': self.max_session_duration,
            'tasks_per_session': self.tasks_per_session,
            'bart_config': self.bart_config,
            'ice_fishing_config': self.ice_fishing_config,
            'mountain_mining_config': self.mountain_mining_config,
            'spinning_bottle_config': self.spinning_bottle_config
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ExperimentConfig':
        """Create configuration from dictionary."""
        return cls(**data)

    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'ExperimentConfig':
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


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