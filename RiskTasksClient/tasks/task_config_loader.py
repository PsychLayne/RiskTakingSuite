import os
import json
from pathlib import Path
from typing import Dict, Tuple, Any


def load_task_config(task_name: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Load task configuration with experiment-specific overrides.
    Now supports task instances where the same task can have different parameters.

    Args:
        task_name: Name of the task (bart, ice_fishing, mountain_mining, spinning_bottle)

    Returns:
        Tuple of (full_config, task_config, experiment_config)
    """
    # Check if we're in test mode
    test_mode = os.environ.get('TEST_MODE', 'false').lower() == 'true'
    custom_config_path = os.environ.get('CONFIG_PATH')

    # Check for experiment-specific config
    experiment_config_path = os.environ.get('EXPERIMENT_CONFIG')

    # Check if we're running a specific task instance
    task_instance_id = os.environ.get('TASK_INSTANCE_ID')

    if test_mode and custom_config_path:
        config_path = Path(custom_config_path)
    elif experiment_config_path:
        # Load experiment-specific configuration
        config_path = Path(experiment_config_path)
    else:
        # Load default configuration
        config_path = Path(__file__).parent.parent / "config" / "settings.json"

    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Extract experiment-level settings
        exp_config = config.get('experiment', {})

        # Handle task instances (new format)
        if 'task_instances' in config and task_instance_id:
            # New format with task instances
            instance_config = config['task_instances'].get(task_instance_id, {})

            # Verify this instance is for the correct task type
            if instance_config.get('task_type') == task_name:
                # Build task config from instance
                task_config = {
                    k: v for k, v in instance_config.items()
                    if k not in ['task_type', 'display_name']
                }
            else:
                # Instance ID doesn't match task type, use defaults
                task_config = {}
        else:
            # Legacy format or no instance specified
            task_config = config.get('tasks', {}).get(task_name, {})

        return config, task_config, exp_config
    else:
        # Return default configurations
        return get_default_config(task_name)


def get_default_config(task_name: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Get default configuration for a task."""

    # Default experiment config
    default_exp_config = {
        'total_trials_per_task': 30,
        'session_gap_days': 14,
        'max_session_duration': 60
    }

    # Default task configs
    default_task_configs = {
        'bart': {
            'max_pumps': 64,
            'points_per_pump': 5,
            'explosion_range': [1, 64],
            'keyboard_input_mode': False,
            'balloon_color': 'Red',
            'random_colors': False
        },
        'ice_fishing': {
            'max_fish': 64,
            'points_per_fish': 5,
            'break_probability_function': 'linear'
        },
        'mountain_mining': {
            'max_ore': 64,
            'points_per_ore': 5,
            'snap_probability_function': 'linear'
        },
        'spinning_bottle': {
            'segments': 16,
            'points_per_add': 5,
            'spin_speed_range': [12.0, 18.0],
            'win_color': 'Green',
            'loss_color': 'Red'
        }
    }

    # Default display config
    default_display_config = {
        'fullscreen': True,
        'resolution': '1920x1080'
    }

    # Build full default config
    default_config = {
        'experiment': default_exp_config,
        'display': default_display_config,
        'tasks': default_task_configs
    }

    task_config = default_task_configs.get(task_name, {})

    return default_config, task_config, default_exp_config