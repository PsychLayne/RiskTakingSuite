"""
Database Manager for Risk Tasks Client
Handles all database operations including initialization, queries, and data management.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional, Tuple
import logging

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
                notes TEXT
            )
        """)

        # Experiments table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                config TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                max_participants INTEGER,
                created_by TEXT
            )
        """)

        # Experiment enrollment table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_enrollment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                participant_id INTEGER NOT NULL,
                enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id),
                FOREIGN KEY (participant_id) REFERENCES participants(id),
                UNIQUE(experiment_id, participant_id)
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
                experiment_id INTEGER REFERENCES experiments(id),
                FOREIGN KEY (participant_id) REFERENCES participants(id),
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
            ON experiments(experiment_code)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_enrollment 
            ON experiment_enrollment(experiment_id, participant_id)
        """)

        self.connection.commit()

    # --- Participant Management ---

    def add_participant(self, participant_code: str, age: int = None,
                       gender: str = None, notes: str = None) -> int:
        """Add a new participant to the database."""
        try:
            self.cursor.execute("""
                INSERT INTO participants (participant_code, age, gender, notes)
                VALUES (?, ?, ?, ?)
            """, (participant_code, age, gender, notes))

            self.connection.commit()
            participant_id = self.cursor.lastrowid
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
                   SUM(CASE WHEN s.completed = 1 THEN 1 ELSE 0 END) as completed_sessions
            FROM participants p
            LEFT JOIN sessions s ON p.id = s.participant_id
            GROUP BY p.id
            ORDER BY p.created_date DESC
        """)

        return [dict(row) for row in self.cursor.fetchall()]

    def update_participant(self, participant_id: int, **kwargs):
        """Update participant information."""
        allowed_fields = ['age', 'gender', 'notes']
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

            # Delete experiment enrollments
            self.cursor.execute("""
                DELETE FROM experiment_enrollment WHERE participant_id = ?
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

    # --- Experiment Management ---

    def create_experiment(self, experiment_code: str, name: str, config: Dict,
                         description: str = None, start_date: datetime = None,
                         end_date: datetime = None, max_participants: int = None,
                         created_by: str = None) -> int:
        """Create a new experiment."""
        try:
            config_json = json.dumps(config)

            self.cursor.execute("""
                INSERT INTO experiments 
                (experiment_code, name, description, config, start_date, 
                 end_date, max_participants, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (experiment_code, name, description, config_json,
                  start_date, end_date, max_participants, created_by))

            self.connection.commit()
            experiment_id = self.cursor.lastrowid
            logger.info(f"Created experiment {experiment_code} with ID {experiment_id}")
            return experiment_id

        except sqlite3.IntegrityError:
            logger.error(f"Experiment with code {experiment_code} already exists")
            raise ValueError(f"Experiment code {experiment_code} already exists")

    def get_experiment(self, experiment_id: int = None,
                      experiment_code: str = None) -> Optional[Dict]:
        """Get experiment by ID or code."""
        if experiment_id:
            query = "SELECT * FROM experiments WHERE id = ?"
            params = (experiment_id,)
        elif experiment_code:
            query = "SELECT * FROM experiments WHERE experiment_code = ?"
            params = (experiment_code,)
        else:
            return None

        self.cursor.execute(query, params)
        row = self.cursor.fetchone()

        if row:
            experiment = dict(row)
            experiment['config'] = json.loads(experiment['config'])
            return experiment
        return None

    def get_active_experiments(self) -> List[Dict]:
        """Get all active experiments."""
        self.cursor.execute("""
            SELECT e.*, 
                   COUNT(DISTINCT ee.participant_id) as enrolled_count
            FROM experiments e
            LEFT JOIN experiment_enrollment ee ON e.id = ee.experiment_id
            WHERE e.is_active = 1
            GROUP BY e.id
            ORDER BY e.created_date DESC
        """)

        experiments = []
        for row in self.cursor.fetchall():
            experiment = dict(row)
            experiment['config'] = json.loads(experiment['config'])
            experiments.append(experiment)

        return experiments

    def enroll_participant(self, experiment_code: str, participant_id: int) -> bool:
        """Enroll a participant in an experiment."""
        try:
            # Get experiment
            experiment = self.get_experiment(experiment_code=experiment_code)
            if not experiment:
                raise ValueError(f"Experiment with code {experiment_code} not found")

            # Check if experiment is active and open for enrollment
            if not experiment['is_active']:
                raise ValueError("Experiment is not active")

            # Check enrollment limits
            if experiment['max_participants']:
                self.cursor.execute("""
                    SELECT COUNT(*) FROM experiment_enrollment 
                    WHERE experiment_id = ?
                """, (experiment['id'],))

                current_count = self.cursor.fetchone()[0]
                if current_count >= experiment['max_participants']:
                    raise ValueError("Experiment has reached maximum participants")

            # Enroll participant
            self.cursor.execute("""
                INSERT INTO experiment_enrollment (experiment_id, participant_id)
                VALUES (?, ?)
            """, (experiment['id'], participant_id))

            self.connection.commit()
            logger.info(f"Enrolled participant {participant_id} in experiment {experiment_code}")
            return True

        except sqlite3.IntegrityError:
            logger.error(f"Participant {participant_id} already enrolled in experiment {experiment_code}")
            raise ValueError("Participant already enrolled in this experiment")

    def get_participant_experiment(self, participant_id: int) -> Optional[Dict]:
        """Get the experiment a participant is enrolled in."""
        self.cursor.execute("""
            SELECT e.* FROM experiments e
            JOIN experiment_enrollment ee ON e.id = ee.experiment_id
            WHERE ee.participant_id = ?
        """, (participant_id,))

        row = self.cursor.fetchone()
        if row:
            experiment = dict(row)
            experiment['config'] = json.loads(experiment['config'])
            return experiment
        return None

    def update_experiment(self, experiment_id: int, **kwargs):
        """Update experiment information."""
        allowed_fields = ['name', 'description', 'config', 'start_date',
                          'end_date', 'is_active', 'max_participants']
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return

        # Handle config serialization
        if 'config' in update_fields:
            update_fields['config'] = json.dumps(update_fields['config'])

        query = "UPDATE experiments SET "
        query += ", ".join([f"{field} = ?" for field in update_fields.keys()])
        query += " WHERE id = ?"

        values = list(update_fields.values()) + [experiment_id]

        self.cursor.execute(query, values)
        self.connection.commit()
        logger.info(f"Updated experiment {experiment_id}")

    def get_experiment_statistics(self, experiment_id: int) -> Dict:
        """Get statistics for a specific experiment."""
        stats = {}

        # Get participant count
        self.cursor.execute("""
            SELECT COUNT(DISTINCT ee.participant_id) as participant_count,
                   COUNT(DISTINCT s.id) as session_count,
                   COUNT(DISTINCT CASE WHEN s.completed = 1 THEN s.id END) as completed_sessions
            FROM experiment_enrollment ee
            LEFT JOIN sessions s ON ee.participant_id = s.participant_id 
                                 AND s.experiment_id = ?
            WHERE ee.experiment_id = ?
        """, (experiment_id, experiment_id))

        row = self.cursor.fetchone()
        stats.update(dict(row))

        # Get trial statistics by task
        self.cursor.execute("""
            SELECT t.task_name,
                   COUNT(*) as trial_count,
                   AVG(t.risk_level) as avg_risk,
                   AVG(t.points_earned) as avg_points,
                   SUM(CASE WHEN t.outcome = 'success' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM trial_data t
            JOIN sessions s ON t.session_id = s.id
            WHERE s.experiment_id = ?
            GROUP BY t.task_name
        """, (experiment_id,))

        task_stats = {}
        for row in self.cursor.fetchall():
            task_stats[row['task_name']] = dict(row)

        stats['task_statistics'] = task_stats

        return stats

    # --- Session Management ---

    def create_session(self, participant_id: int, session_number: int,
                      tasks: List[str]) -> int:
        """Create a new session for a participant."""
        tasks_json = json.dumps(tasks)

        try:
            self.cursor.execute("""
                INSERT INTO sessions (participant_id, session_number, tasks_assigned, start_time)
                VALUES (?, ?, ?, ?)
            """, (participant_id, session_number, tasks_json, datetime.now()))

            self.connection.commit()
            session_id = self.cursor.lastrowid
            logger.info(f"Created session {session_id} for participant {participant_id}")
            return session_id

        except sqlite3.IntegrityError:
            logger.error(f"Session {session_number} already exists for participant {participant_id}")
            raise ValueError(f"Session {session_number} already exists for this participant")

    def create_session_for_experiment(self, participant_id: int, session_number: int,
                                     tasks: List[str], experiment_id: int) -> int:
        """Create a new session linked to an experiment."""
        tasks_json = json.dumps(tasks)

        try:
            self.cursor.execute("""
                INSERT INTO sessions 
                (participant_id, session_number, tasks_assigned, start_time, experiment_id)
                VALUES (?, ?, ?, ?, ?)
            """, (participant_id, session_number, tasks_json, datetime.now(), experiment_id))

            self.connection.commit()
            session_id = self.cursor.lastrowid
            logger.info(f"Created session {session_id} for participant {participant_id} in experiment {experiment_id}")
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

        return {
            'participant': participant,
            'sessions': sessions
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