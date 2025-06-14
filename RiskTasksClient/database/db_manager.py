"""
Database Manager for Risk Tasks Client
Handles all database operations including initialization, queries, and data management.
Now includes experiment management functionality.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional, Tuple
import logging
import random
import string

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations for the Risk Tasks Client."""

    def __init__(self, db_path: str = "data/participants.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.connection = None
        self.cursor = None

    def initialize(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            self.cursor = self.connection.cursor()

            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")

            # Create tables
            self.create_tables()

            logger.info(f"Database initialized at {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def create_tables(self):
        """Create all required database tables."""
        # Participants table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_code TEXT UNIQUE NOT NULL,
                age INTEGER,
                gender TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                experiment_id INTEGER,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            )
        """)

        # Sessions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER NOT NULL,
                session_number INTEGER NOT NULL,
                session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tasks_assigned TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                experiment_session_id INTEGER,
                FOREIGN KEY (participant_id) REFERENCES participants(id),
                FOREIGN KEY (experiment_session_id) REFERENCES experiment_sessions(id),
                UNIQUE(participant_id, session_number)
            )
        """)

        # Trial data table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trial_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                trial_number INTEGER NOT NULL,
                risk_level REAL,
                points_earned INTEGER,
                outcome TEXT,
                reaction_time REAL,
                additional_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        # New experiment tables
        # Experiments table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                description TEXT,
                num_sessions INTEGER DEFAULT 1,
                randomize_order BOOLEAN DEFAULT 0,
                active BOOLEAN DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        """)

        # Experiment sessions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                session_number INTEGER NOT NULL,
                num_tasks INTEGER DEFAULT 2,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id),
                UNIQUE(experiment_id, session_number)
            )
        """)

        # Experiment tasks table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_session_id INTEGER NOT NULL,
                task_type TEXT NOT NULL,
                task_order INTEGER NOT NULL,
                task_config_json TEXT,
                FOREIGN KEY (experiment_session_id) REFERENCES experiment_sessions(id)
            )
        """)

        # Participant experiments table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS participant_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER NOT NULL,
                experiment_id INTEGER NOT NULL,
                enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_session INTEGER DEFAULT 1,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (participant_id) REFERENCES participants(id),
                FOREIGN KEY (experiment_id) REFERENCES experiments(id),
                UNIQUE(participant_id, experiment_id)
            )
        """)

        # Create indices for better performance
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trial_session 
            ON trial_data(session_id)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_participant 
            ON sessions(participant_id)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiment_code 
            ON experiments(code)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_participant_experiment 
            ON participant_experiments(participant_id, experiment_id)
        """)

        self.connection.commit()

    # --- Participant Management ---

    def add_participant(self, participant_code: str, age: int = None,
                       gender: str = None, notes: str = None, experiment_code: str = None) -> int:
        """Add a new participant to the database with optional experiment enrollment."""
        try:
            # Check if experiment code is provided
            experiment_id = None
            if experiment_code:
                experiment = self.get_experiment_by_code(experiment_code)
                if experiment:
                    experiment_id = experiment['id']
                else:
                    raise ValueError(f"Invalid experiment code: {experiment_code}")

            # Insert participant
            self.cursor.execute("""
                INSERT INTO participants (participant_code, age, gender, notes, experiment_id)
                VALUES (?, ?, ?, ?, ?)
            """, (participant_code, age, gender, notes, experiment_id))

            self.connection.commit()
            participant_id = self.cursor.lastrowid

            # If experiment code provided, enroll participant
            if experiment_id:
                self.enroll_participant_in_experiment(participant_id, experiment_id)

            logger.info(f"Added participant {participant_code} with ID {participant_id}")
            return participant_id

        except sqlite3.IntegrityError:
            logger.error(f"Participant with code {participant_code} already exists")
            raise ValueError(f"Participant code {participant_code} already exists")

    def get_participant(self, participant_id: int = None,
                       participant_code: str = None) -> Optional[Dict]:
        """Get participant by ID or code."""
        if participant_id:
            query = "SELECT * FROM participants WHERE id = ?"
            params = (participant_id,)
        elif participant_code:
            query = "SELECT * FROM participants WHERE participant_code = ?"
            params = (participant_code,)
        else:
            return None

        self.cursor.execute(query, params)
        row = self.cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_all_participants(self) -> List[Dict]:
        """Get all participants."""
        self.cursor.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT s.id) as session_count,
                   SUM(CASE WHEN s.completed = 1 THEN 1 ELSE 0 END) as completed_sessions,
                   e.name as experiment_name,
                   e.code as experiment_code
            FROM participants p
            LEFT JOIN sessions s ON p.id = s.participant_id
            LEFT JOIN experiments e ON p.experiment_id = e.id
            GROUP BY p.id
            ORDER BY p.created_date DESC
        """)

        return [dict(row) for row in self.cursor.fetchall()]

    def update_participant(self, participant_id: int, **kwargs):
        """Update participant information."""
        allowed_fields = ['age', 'gender', 'notes', 'experiment_id']
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return

        query = "UPDATE participants SET "
        query += ", ".join([f"{field} = ?" for field in update_fields.keys()])
        query += " WHERE id = ?"

        values = list(update_fields.values()) + [participant_id]

        self.cursor.execute(query, values)
        self.connection.commit()
        logger.info(f"Updated participant {participant_id}")

    def delete_participant(self, participant_id: int):
        """Delete a participant and all associated data."""
        try:
            # First delete all trial data for this participant's sessions
            self.cursor.execute("""
                DELETE FROM trial_data 
                WHERE session_id IN (
                    SELECT id FROM sessions WHERE participant_id = ?
                )
            """, (participant_id,))

            # Delete all sessions for this participant
            self.cursor.execute("""
                DELETE FROM sessions WHERE participant_id = ?
            """, (participant_id,))

            # Delete participant experiment enrollments
            self.cursor.execute("""
                DELETE FROM participant_experiments WHERE participant_id = ?
            """, (participant_id,))

            # Delete the participant
            self.cursor.execute("""
                DELETE FROM participants WHERE id = ?
            """, (participant_id,))

            self.connection.commit()
            logger.info(f"Deleted participant {participant_id} and all associated data")

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Error deleting participant {participant_id}: {e}")
            raise

    # --- Session Management ---

    def create_session(self, participant_id: int, session_number: int,
                      tasks: List[str], experiment_session_id: int = None) -> int:
        """Create a new session for a participant."""
        tasks_json = json.dumps(tasks)

        try:
            self.cursor.execute("""
                INSERT INTO sessions (participant_id, session_number, tasks_assigned, 
                                    start_time, experiment_session_id)
                VALUES (?, ?, ?, ?, ?)
            """, (participant_id, session_number, tasks_json, datetime.now(), experiment_session_id))

            self.connection.commit()
            session_id = self.cursor.lastrowid
            logger.info(f"Created session {session_id} for participant {participant_id}")
            return session_id

        except sqlite3.IntegrityError:
            logger.error(f"Session {session_number} already exists for participant {participant_id}")
            raise ValueError(f"Session {session_number} already exists for this participant")

    def get_participant_sessions(self, participant_id: int) -> List[Dict]:
        """Get all sessions for a participant."""
        self.cursor.execute("""
            SELECT s.*, 
                   COUNT(DISTINCT t.id) as trial_count,
                   COUNT(DISTINCT t.task_name) as tasks_completed
            FROM sessions s
            LEFT JOIN trial_data t ON s.id = t.session_id
            WHERE s.participant_id = ?
            GROUP BY s.id
            ORDER BY s.session_number
        """, (participant_id,))

        sessions = []
        for row in self.cursor.fetchall():
            session = dict(row)
            session['tasks_assigned'] = json.loads(session['tasks_assigned'])
            sessions.append(session)

        return sessions

    def complete_session(self, session_id: int):
        """Mark a session as completed."""
        self.cursor.execute("""
            UPDATE sessions 
            SET completed = 1, end_time = ?
            WHERE id = ?
        """, (datetime.now(), session_id))

        # Check if this completes an experiment for the participant
        self.cursor.execute("""
            SELECT p.id as participant_id, p.experiment_id, s.experiment_session_id
            FROM sessions s
            JOIN participants p ON s.participant_id = p.id
            WHERE s.id = ?
        """, (session_id,))

        result = self.cursor.fetchone()
        if result and result['experiment_id']:
            self.check_experiment_completion(result['participant_id'], result['experiment_id'])

        self.connection.commit()
        logger.info(f"Completed session {session_id}")

    def get_pending_sessions(self) -> List[Dict]:
        """Get all incomplete sessions."""
        self.cursor.execute("""
            SELECT s.*, p.participant_code
            FROM sessions s
            JOIN participants p ON s.participant_id = p.id
            WHERE s.completed = 0
            ORDER BY s.session_date DESC
        """)

        sessions = []
        for row in self.cursor.fetchall():
            session = dict(row)
            session['tasks_assigned'] = json.loads(session['tasks_assigned'])
            sessions.append(session)

        return sessions

    # --- Trial Data Management ---

    def add_trial_data(self, session_id: int, task_name: str, trial_number: int,
                      risk_level: float, points_earned: int, outcome: str,
                      reaction_time: float = None, additional_data: Dict = None):
        """Add trial data for a session."""
        additional_json = json.dumps(additional_data) if additional_data else None

        self.cursor.execute("""
            INSERT INTO trial_data 
            (session_id, task_name, trial_number, risk_level, points_earned, 
             outcome, reaction_time, additional_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, task_name, trial_number, risk_level, points_earned,
              outcome, reaction_time, additional_json))

        self.connection.commit()

    def get_session_trials(self, session_id: int) -> List[Dict]:
        """Get all trials for a session."""
        self.cursor.execute("""
            SELECT * FROM trial_data
            WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))

        trials = []
        for row in self.cursor.fetchall():
            trial = dict(row)
            if trial['additional_data']:
                trial['additional_data'] = json.loads(trial['additional_data'])
            trials.append(trial)

        return trials

    # --- Experiment Management ---

    def create_experiment(self, name: str, code: str = None, description: str = None,
                         num_sessions: int = 1, randomize_order: bool = False,
                         created_by: str = None) -> int:
        """Create a new experiment."""
        # Generate code if not provided
        if not code:
            code = self.generate_experiment_code()

        try:
            self.cursor.execute("""
                INSERT INTO experiments (name, code, description, num_sessions, 
                                       randomize_order, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, code, description, num_sessions, randomize_order, created_by))

            self.connection.commit()
            experiment_id = self.cursor.lastrowid
            logger.info(f"Created experiment '{name}' with ID {experiment_id} and code {code}")
            return experiment_id

        except sqlite3.IntegrityError:
            logger.error(f"Experiment with code {code} already exists")
            raise ValueError(f"Experiment code {code} already exists")

    def get_experiment(self, experiment_id: int) -> Optional[Dict]:
        """Get experiment by ID."""
        self.cursor.execute("""
            SELECT * FROM experiments WHERE id = ?
        """, (experiment_id,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_experiment_by_code(self, code: str) -> Optional[Dict]:
        """Get experiment by code."""
        self.cursor.execute("""
            SELECT * FROM experiments WHERE code = ?
        """, (code,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def update_experiment(self, experiment_id: int, **kwargs):
        """Update experiment details."""
        allowed_fields = ['name', 'description', 'num_sessions', 'randomize_order', 'active']
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return

        query = "UPDATE experiments SET "
        query += ", ".join([f"{field} = ?" for field in update_fields.keys()])
        query += " WHERE id = ?"

        values = list(update_fields.values()) + [experiment_id]

        self.cursor.execute(query, values)
        self.connection.commit()
        logger.info(f"Updated experiment {experiment_id}")

    def delete_experiment(self, experiment_id: int):
        """Delete an experiment and all associated data."""
        try:
            # First, get all sessions associated with this experiment
            self.cursor.execute("""
                SELECT s.id 
                FROM sessions s
                JOIN experiment_sessions es ON s.experiment_session_id = es.id
                WHERE es.experiment_id = ?
            """, (experiment_id,))

            session_ids = [row[0] for row in self.cursor.fetchall()]

            # Delete trial data for these sessions
            for session_id in session_ids:
                self.cursor.execute("""
                    DELETE FROM trial_data WHERE session_id = ?
                """, (session_id,))

            # Delete sessions
            self.cursor.execute("""
                DELETE FROM sessions 
                WHERE experiment_session_id IN (
                    SELECT id FROM experiment_sessions WHERE experiment_id = ?
                )
            """, (experiment_id,))

            # Delete experiment tasks
            self.cursor.execute("""
                DELETE FROM experiment_tasks 
                WHERE experiment_session_id IN (
                    SELECT id FROM experiment_sessions WHERE experiment_id = ?
                )
            """, (experiment_id,))

            # Delete experiment sessions
            self.cursor.execute("""
                DELETE FROM experiment_sessions WHERE experiment_id = ?
            """, (experiment_id,))

            # Delete participant enrollments
            self.cursor.execute("""
                DELETE FROM participant_experiments WHERE experiment_id = ?
            """, (experiment_id,))

            # Update participants to remove experiment_id
            self.cursor.execute("""
                UPDATE participants SET experiment_id = NULL WHERE experiment_id = ?
            """, (experiment_id,))

            # Finally, delete the experiment
            self.cursor.execute("""
                DELETE FROM experiments WHERE id = ?
            """, (experiment_id,))

            self.connection.commit()
            logger.info(f"Deleted experiment {experiment_id} and all associated data")

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Error deleting experiment {experiment_id}: {e}")
            raise

    def get_all_experiments(self) -> List[Dict]:
        """Get all experiments with enrollment statistics."""
        self.cursor.execute("""
            SELECT e.*,
                   COUNT(DISTINCT pe.participant_id) as enrolled_count,
                   SUM(CASE WHEN pe.completed = 1 THEN 1 ELSE 0 END) as completed_count
            FROM experiments e
            LEFT JOIN participant_experiments pe ON e.id = pe.experiment_id
            GROUP BY e.id
            ORDER BY e.created_date DESC
        """)

        return [dict(row) for row in self.cursor.fetchall()]

    def create_experiment_session(self, experiment_id: int, session_number: int,
                                 num_tasks: int = 2) -> int:
        """Create a session template for an experiment."""
        try:
            self.cursor.execute("""
                INSERT INTO experiment_sessions (experiment_id, session_number, num_tasks)
                VALUES (?, ?, ?)
            """, (experiment_id, session_number, num_tasks))

            self.connection.commit()
            return self.cursor.lastrowid

        except sqlite3.IntegrityError:
            raise ValueError(f"Session {session_number} already exists for this experiment")

    def add_experiment_task(self, experiment_session_id: int, task_type: str,
                           task_order: int, task_config: Dict = None):
        """Add a task to an experiment session."""
        config_json = json.dumps(task_config) if task_config else None

        self.cursor.execute("""
            INSERT INTO experiment_tasks (experiment_session_id, task_type, 
                                        task_order, task_config_json)
            VALUES (?, ?, ?, ?)
        """, (experiment_session_id, task_type, task_order, config_json))

        self.connection.commit()

    def get_experiment_sessions(self, experiment_id: int) -> List[Dict]:
        """Get all sessions for an experiment."""
        self.cursor.execute("""
            SELECT es.*, COUNT(et.id) as task_count
            FROM experiment_sessions es
            LEFT JOIN experiment_tasks et ON es.id = et.experiment_session_id
            WHERE es.experiment_id = ?
            GROUP BY es.id
            ORDER BY es.session_number
        """, (experiment_id,))

        sessions = []
        for row in self.cursor.fetchall():
            session = dict(row)
            # Get tasks for this session
            session['tasks'] = self.get_experiment_session_tasks(session['id'])
            sessions.append(session)

        return sessions

    def get_experiment_session_tasks(self, experiment_session_id: int) -> List[Dict]:
        """Get all tasks for an experiment session."""
        self.cursor.execute("""
            SELECT * FROM experiment_tasks
            WHERE experiment_session_id = ?
            ORDER BY task_order
        """, (experiment_session_id,))

        tasks = []
        for row in self.cursor.fetchall():
            task = dict(row)
            if task['task_config_json']:
                task['task_config'] = json.loads(task['task_config_json'])
            else:
                task['task_config'] = {}
            tasks.append(task)

        return tasks

    def enroll_participant_in_experiment(self, participant_id: int, experiment_id: int):
        """Enroll a participant in an experiment."""
        try:
            self.cursor.execute("""
                INSERT INTO participant_experiments (participant_id, experiment_id)
                VALUES (?, ?)
            """, (participant_id, experiment_id))

            # Update participant's experiment_id
            self.cursor.execute("""
                UPDATE participants SET experiment_id = ? WHERE id = ?
            """, (experiment_id, participant_id))

            self.connection.commit()
            logger.info(f"Enrolled participant {participant_id} in experiment {experiment_id}")

        except sqlite3.IntegrityError:
            logger.warning(f"Participant {participant_id} already enrolled in experiment {experiment_id}")

    def get_experiment_participants(self, experiment_id: int) -> List[Dict]:
        """Get all participants enrolled in an experiment."""
        self.cursor.execute("""
            SELECT p.*, pe.enrolled_date, pe.current_session, pe.completed
            FROM participants p
            JOIN participant_experiments pe ON p.id = pe.participant_id
            WHERE pe.experiment_id = ?
            ORDER BY pe.enrolled_date DESC
        """, (experiment_id,))

        return [dict(row) for row in self.cursor.fetchall()]

    def get_participant_experiment_progress(self, participant_id: int,
                                          experiment_id: int) -> Optional[Dict]:
        """Get a participant's progress in an experiment."""
        self.cursor.execute("""
            SELECT pe.*, e.num_sessions, e.name as experiment_name
            FROM participant_experiments pe
            JOIN experiments e ON pe.experiment_id = e.id
            WHERE pe.participant_id = ? AND pe.experiment_id = ?
        """, (participant_id, experiment_id))

        row = self.cursor.fetchone()
        if row:
            progress = dict(row)
            # Get completed sessions
            self.cursor.execute("""
                SELECT COUNT(*) as completed_sessions
                FROM sessions s
                JOIN experiment_sessions es ON s.experiment_session_id = es.id
                WHERE s.participant_id = ? AND es.experiment_id = ? AND s.completed = 1
            """, (participant_id, experiment_id))

            result = self.cursor.fetchone()
            progress['completed_sessions'] = result['completed_sessions'] if result else 0
            progress['progress_percentage'] = (progress['completed_sessions'] / progress['num_sessions']) * 100

            return progress

        return None

    def check_experiment_completion(self, participant_id: int, experiment_id: int):
        """Check if a participant has completed all sessions in an experiment."""
        progress = self.get_participant_experiment_progress(participant_id, experiment_id)

        if progress and progress['completed_sessions'] >= progress['num_sessions']:
            self.cursor.execute("""
                UPDATE participant_experiments 
                SET completed = 1 
                WHERE participant_id = ? AND experiment_id = ?
            """, (participant_id, experiment_id))
            self.connection.commit()
            logger.info(f"Participant {participant_id} completed experiment {experiment_id}")

    def generate_experiment_code(self) -> str:
        """Generate a unique experiment code."""
        while True:
            # Generate a 6-character alphanumeric code
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

            # Check if code already exists
            self.cursor.execute("SELECT id FROM experiments WHERE code = ?", (code,))
            if not self.cursor.fetchone():
                return code

    def validate_experiment_config(self, config: Dict) -> Tuple[bool, List[str]]:
        """Validate experiment configuration."""
        errors = []

        # Check required fields
        if 'name' not in config or not config['name']:
            errors.append("Experiment name is required")

        if 'num_sessions' not in config or config['num_sessions'] < 1 or config['num_sessions'] > 2:
            errors.append("Number of sessions must be 1 or 2")

        # Check sessions configuration
        if 'sessions' in config:
            for session_num, session_config in config['sessions'].items():
                if 'tasks' not in session_config or not session_config['tasks']:
                    errors.append(f"Session {session_num} must have at least one task")

                if len(session_config['tasks']) > 4:
                    errors.append(f"Session {session_num} cannot have more than 4 tasks")

        return len(errors) == 0, errors

    def export_experiment_template(self, experiment_id: int) -> Dict:
        """Export experiment configuration as a template."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None

        sessions = self.get_experiment_sessions(experiment_id)

        template = {
            'name': experiment['name'],
            'description': experiment['description'],
            'num_sessions': experiment['num_sessions'],
            'randomize_order': bool(experiment['randomize_order']),
            'sessions': {}
        }

        for session in sessions:
            template['sessions'][session['session_number']] = {
                'num_tasks': session['num_tasks'],
                'tasks': []
            }

            for task in session['tasks']:
                template['sessions'][session['session_number']]['tasks'].append({
                    'type': task['task_type'],
                    'order': task['task_order'],
                    'config': task['task_config']
                })

        return template

    def import_experiment_template(self, template: Dict, created_by: str = None) -> int:
        """Import an experiment from a template."""
        # Validate template
        is_valid, errors = self.validate_experiment_config(template)
        if not is_valid:
            raise ValueError(f"Invalid template: {', '.join(errors)}")

        # Create experiment
        experiment_id = self.create_experiment(
            name=template['name'],
            description=template.get('description'),
            num_sessions=template['num_sessions'],
            randomize_order=template.get('randomize_order', False),
            created_by=created_by
        )

        # Create sessions and tasks
        for session_num, session_config in template['sessions'].items():
            session_id = self.create_experiment_session(
                experiment_id,
                int(session_num),
                len(session_config['tasks'])
            )

            for task in session_config['tasks']:
                self.add_experiment_task(
                    session_id,
                    task['type'],
                    task['order'],
                    task.get('config')
                )

        return experiment_id

    # --- Statistics and Analytics ---

    def get_statistics(self) -> Dict:
        """Get overall statistics for the dashboard."""
        stats = {}

        # Total participants
        self.cursor.execute("SELECT COUNT(*) FROM participants")
        stats['total_participants'] = self.cursor.fetchone()[0]

        # Active sessions
        self.cursor.execute("SELECT COUNT(*) FROM sessions WHERE completed = 0")
        stats['active_sessions'] = self.cursor.fetchone()[0]

        # Completed sessions
        self.cursor.execute("SELECT COUNT(*) FROM sessions WHERE completed = 1")
        stats['completed_sessions'] = self.cursor.fetchone()[0]

        # Total trials
        self.cursor.execute("SELECT COUNT(*) FROM trial_data")
        stats['total_trials'] = self.cursor.fetchone()[0]

        # Experiment statistics
        self.cursor.execute("SELECT COUNT(*) FROM experiments WHERE active = 1")
        stats['active_experiments'] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(DISTINCT participant_id) FROM participant_experiments")
        stats['participants_in_experiments'] = self.cursor.fetchone()[0]

        return stats

    def get_experiment_statistics(self, experiment_id: int) -> Dict:
        """Get statistics for a specific experiment."""
        stats = {}

        # Basic experiment info
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return stats

        stats['experiment'] = experiment

        # Enrollment statistics
        self.cursor.execute("""
            SELECT COUNT(*) as total_enrolled,
                   SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                   AVG(current_session) as avg_progress
            FROM participant_experiments
            WHERE experiment_id = ?
        """, (experiment_id,))

        enrollment_stats = dict(self.cursor.fetchone())
        stats.update(enrollment_stats)

        # Session completion rates
        self.cursor.execute("""
            SELECT es.session_number,
                   COUNT(DISTINCT s.participant_id) as started,
                   SUM(CASE WHEN s.completed = 1 THEN 1 ELSE 0 END) as completed
            FROM experiment_sessions es
            LEFT JOIN sessions s ON s.experiment_session_id = es.id
            WHERE es.experiment_id = ?
            GROUP BY es.session_number
        """, (experiment_id,))

        stats['session_stats'] = [dict(row) for row in self.cursor.fetchall()]

        # Task performance
        self.cursor.execute("""
            SELECT et.task_type,
                   COUNT(DISTINCT td.id) as trial_count,
                   AVG(td.risk_level) as avg_risk,
                   AVG(td.points_earned) as avg_points
            FROM experiment_tasks et
            JOIN experiment_sessions es ON et.experiment_session_id = es.id
            LEFT JOIN sessions s ON s.experiment_session_id = es.id
            LEFT JOIN trial_data td ON td.session_id = s.id AND td.task_name = et.task_type
            WHERE es.experiment_id = ?
            GROUP BY et.task_type
        """, (experiment_id,))

        stats['task_performance'] = [dict(row) for row in self.cursor.fetchall()]

        return stats

    def get_task_statistics(self, task_name: str = None) -> Dict:
        """Get statistics for a specific task or all tasks."""
        if task_name:
            query = """
                SELECT 
                    task_name,
                    COUNT(*) as trial_count,
                    AVG(risk_level) as avg_risk,
                    AVG(points_earned) as avg_points,
                    SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
                FROM trial_data
                WHERE task_name = ?
                GROUP BY task_name
            """
            params = (task_name,)
        else:
            query = """
                SELECT 
                    task_name,
                    COUNT(*) as trial_count,
                    AVG(risk_level) as avg_risk,
                    AVG(points_earned) as avg_points,
                    SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
                FROM trial_data
                GROUP BY task_name
            """
            params = ()

        self.cursor.execute(query, params)

        stats = {}
        for row in self.cursor.fetchall():
            task_stats = dict(row)
            stats[task_stats['task_name']] = task_stats

        return stats

    def get_recent_activities(self, limit: int = 10) -> List[str]:
        """Get recent activities for the dashboard."""
        activities = []

        # Recent participants
        self.cursor.execute("""
            SELECT participant_code, created_date 
            FROM participants 
            ORDER BY created_date DESC 
            LIMIT ?
        """, (limit // 3,))

        for row in self.cursor.fetchall():
            date = datetime.fromisoformat(row['created_date']).strftime("%Y-%m-%d %H:%M")
            activities.append(f"[{date}] New participant: {row['participant_code']}")

        # Recent sessions
        self.cursor.execute("""
            SELECT s.session_number, s.session_date, s.completed, p.participant_code
            FROM sessions s
            JOIN participants p ON s.participant_id = p.id
            ORDER BY s.session_date DESC
            LIMIT ?
        """, (limit // 3,))

        for row in self.cursor.fetchall():
            date = datetime.fromisoformat(row['session_date']).strftime("%Y-%m-%d %H:%M")
            status = "Completed" if row['completed'] else "Started"
            activities.append(f"[{date}] {status} session {row['session_number']} for {row['participant_code']}")

        # Recent experiments
        self.cursor.execute("""
            SELECT name, code, created_date
            FROM experiments
            ORDER BY created_date DESC
            LIMIT ?
        """, (limit // 3,))

        for row in self.cursor.fetchall():
            date = datetime.fromisoformat(row['created_date']).strftime("%Y-%m-%d %H:%M")
            activities.append(f"[{date}] Created experiment: {row['name']} (Code: {row['code']})")

        # Sort activities by date
        activities.sort(reverse=True)

        return activities[:limit]

    # --- Data Export ---

    def export_participant_data(self, participant_id: int) -> Dict:
        """Export all data for a participant."""
        participant = self.get_participant(participant_id=participant_id)
        if not participant:
            return None

        sessions = self.get_participant_sessions(participant_id)

        # Get all trial data for each session
        for session in sessions:
            session['trials'] = self.get_session_trials(session['id'])

        # Get experiment info if enrolled
        experiment_info = None
        if participant['experiment_id']:
            experiment_info = self.get_experiment(participant['experiment_id'])
            progress = self.get_participant_experiment_progress(participant_id, participant['experiment_id'])
            if progress:
                experiment_info['progress'] = progress

        return {
            'participant': participant,
            'sessions': sessions,
            'experiment': experiment_info
        }

    def export_experiment_data(self, experiment_id: int) -> Dict:
        """Export all data for an experiment."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None

        # Get experiment structure
        sessions = self.get_experiment_sessions(experiment_id)

        # Get participants
        participants = self.get_experiment_participants(experiment_id)

        # Get all trial data
        trial_data = []
        for participant in participants:
            participant_sessions = self.get_participant_sessions(participant['id'])
            for session in participant_sessions:
                if session.get('experiment_session_id'):
                    trials = self.get_session_trials(session['id'])
                    for trial in trials:
                        trial['participant_code'] = participant['participant_code']
                        trial['session_number'] = session['session_number']
                        trial_data.append(trial)

        return {
            'experiment': experiment,
            'structure': sessions,
            'participants': participants,
            'trial_data': trial_data,
            'statistics': self.get_experiment_statistics(experiment_id)
        }

    # --- Cleanup ---

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def __del__(self):
        """Ensure database connection is closed."""
        self.close()