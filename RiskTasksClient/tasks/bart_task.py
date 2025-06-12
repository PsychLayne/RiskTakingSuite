import pygame
import sys
import random
import time
import math
import os
from pathlib import Path

# Get session and participant info from environment
# Handle cases where env vars might be 'None' string or not set
session_id_str = os.environ.get('SESSION_ID', '0')
participant_id_str = os.environ.get('PARTICIPANT_ID', '0')

# Convert to int, handling 'None' string
SESSION_ID = 0 if session_id_str in ['None', 'null', ''] else int(session_id_str)
PARTICIPANT_ID = 0 if participant_id_str in ['None', 'null', ''] else int(participant_id_str)
TASK_NAME = os.environ.get('TASK_NAME', 'bart')

# Add parent directory to path to import from database
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager
from database.models import TrialData, TrialOutcome

# Initialize pygame
pygame.init()

# Load configuration
import json

# Check if we're in test mode with a custom config
test_mode = os.environ.get('TEST_MODE', 'false').lower() == 'true'
custom_config_path = os.environ.get('CONFIG_PATH')

if test_mode and custom_config_path:
    config_path = Path(custom_config_path)
else:
    config_path = Path(__file__).parent.parent / "config" / "settings.json"

if config_path.exists():
    with open(config_path, 'r') as f:
        config = json.load(f)
        task_config = config.get('tasks', {}).get('bart', {})
        # Get the new keyboard input mode setting
        keyboard_input_mode = task_config.get('keyboard_input_mode', False)
        # Get balloon color settings
        balloon_color_name = task_config.get('balloon_color', 'Red')
        random_colors = task_config.get('random_colors', False)
else:
    # Default configuration
    task_config = {
        "max_pumps": 48,
        "points_per_pump": 5,
        "explosion_range": [8, 48],
        "keyboard_input_mode": False,
        "balloon_color": "Red",
        "random_colors": False
    }
    keyboard_input_mode = False
    balloon_color_name = "Red"
    random_colors = False

# --- Constants ---
INFO = pygame.display.Info()
SCREEN_WIDTH = INFO.current_w
SCREEN_HEIGHT = INFO.current_h
FPS = 60
TOTAL_TRIALS = config.get('experiment', {}).get('total_trials_per_task', 30)

# Task-specific constants from config
MAX_PUMPS = task_config.get('max_pumps', 48)
POINTS_PER_PUMP = task_config.get('points_per_pump', 5)
EXPLOSION_RANGE = task_config.get('explosion_range', [8, 48])

# --- Colors ---
COLOR_BACKGROUND = (240, 248, 255)
COLOR_TEXT = (40, 42, 54)
COLOR_SCORE_BOX = (255, 255, 255)
COLOR_SCORE_BOX_BORDER = (200, 200, 220)

# Balloon color mapping
BALLOON_COLOR_MAP = {
    "Red": (220, 20, 60),
    "Blue": (30, 144, 255),
    "Green": (34, 139, 34),
    "Yellow": (255, 215, 0),
    "Orange": (255, 140, 0),
    "Purple": (147, 112, 219),
    "Pink": (255, 192, 203)
}

# Set default balloon color from config
BALLOON_COLOR_BASE = BALLOON_COLOR_MAP.get(balloon_color_name, (220, 20, 60))
BALLOON_COLOR_HIGHLIGHT = (255, 255, 255, 60)

# List of available colors for random selection
RANDOM_BALLOON_COLORS = list(BALLOON_COLOR_MAP.values())

AIR_TANK_COLOR = (119, 136, 153)
AIR_TANK_HIGHLIGHT = (176, 196, 222)
AIR_HOSE_COLOR = (47, 79, 79)
PUMP_BUTTON_COLOR = (0, 150, 136)
PUMP_BUTTON_HOVER = (0, 178, 161)
COLLECT_BUTTON_COLOR = (33, 150, 243)
COLLECT_BUTTON_HOVER = (66, 165, 245)
BUTTON_TEXT_COLOR = (255, 255, 255)
BUTTON_SHADOW_COLOR = (40, 40, 50, 150)
INPUT_BOX_COLOR = (255, 255, 255)
INPUT_BOX_BORDER = (100, 100, 100)
INPUT_BOX_ACTIVE = (50, 150, 255)
WHITE = (255, 255, 255)

# --- Setup ---
# Check if we should run in fullscreen based on config
fullscreen_mode = config.get('display', {}).get('fullscreen', True)
if fullscreen_mode:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Balloon Analogue Risk Task")
clock = pygame.time.Clock()

# --- Fonts ---
try:
    FONT_FAMILY = "Arial"
    if "Calibri" in pygame.font.get_fonts(): FONT_FAMILY = "Calibri"
    font = pygame.font.SysFont(FONT_FAMILY, 36)
    small_font = pygame.font.SysFont(FONT_FAMILY, 24)
    large_font = pygame.font.SysFont(FONT_FAMILY, 48, bold=True)
    input_font = pygame.font.SysFont(FONT_FAMILY, 32)
    tiny_font = pygame.font.SysFont(FONT_FAMILY, 18)
except Exception as e:
    print(f"Font loading failed: {e}. Using default.")
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    large_font = pygame.font.SysFont(None, 48, bold=True)
    input_font = pygame.font.SysFont(None, 32)
    tiny_font = pygame.font.SysFont(None, 18)

# Initialize database connection
db_manager = DatabaseManager()
db_manager.initialize()


class Particle:
    """A simple particle for the balloon pop animation."""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(4, 10)
        self.life = 60
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-8, 2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            alpha = max(0, self.life / 60)
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size * alpha))


class Button:
    """A UI button drawn programmatically."""

    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color

        shadow_surf = pygame.Surface((self.rect.width, self.rect.height + 4), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, BUTTON_SHADOW_COLOR, (0, 4, self.rect.width, self.rect.height), border_radius=12)
        surface.blit(shadow_surf, self.rect.topleft)

        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=12)

        text_surf = font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)


class InputBox:
    """Input box for keyboard mode."""

    def __init__(self, x, y, width, height, max_value):
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = INPUT_BOX_BORDER
        self.color_active = INPUT_BOX_ACTIVE
        self.color = self.color_inactive
        self.active = False
        self.text = ''
        self.max_value = max_value
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return 'submit'
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    # Only accept digits
                    if event.unicode.isdigit():
                        new_text = self.text + event.unicode
                        # Check if the new value would exceed max
                        try:
                            if int(new_text) <= self.max_value:
                                self.text = new_text
                        except ValueError:
                            pass
        return None

    def update(self):
        # Update cursor blink
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # Blink every 30 frames (0.5 seconds at 60 FPS)
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, surface):
        # Draw the input box
        pygame.draw.rect(surface, INPUT_BOX_COLOR, self.rect)
        pygame.draw.rect(surface, self.color, self.rect, 3, border_radius=5)

        # Render the text
        text_surface = input_font.render(self.text, True, COLOR_TEXT)
        surface.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))

        # Draw cursor if active
        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 10 + text_surface.get_width()
            cursor_y = self.rect.y + 5
            pygame.draw.line(surface, COLOR_TEXT,
                             (cursor_x, cursor_y),
                             (cursor_x, cursor_y + self.rect.height - 10), 2)

    def get_value(self):
        try:
            return int(self.text) if self.text else 0
        except ValueError:
            return 0

    def clear(self):
        self.text = ''


class BalloonTask:
    def __init__(self):
        self.trial = 1
        self.total_score = 0
        self.trial_start_time = None
        self.keyboard_mode = keyboard_input_mode
        self.random_colors = random_colors
        self.current_balloon_color = BALLOON_COLOR_BASE

        # Generate explosion points for all trials based on config
        self.max_pumps_for_trials = [
            random.randint(EXPLOSION_RANGE[0], EXPLOSION_RANGE[1])
            for _ in range(TOTAL_TRIALS)
        ]

        button_width = 250
        button_height = 80
        button_y = SCREEN_HEIGHT - 150

        # Air tank positioning
        self.tank_width = 100
        self.tank_height = 200
        self.tank_x = SCREEN_WIDTH / 2 - self.tank_width / 2
        self.tank_y = SCREEN_HEIGHT - self.tank_height - 20

        if self.keyboard_mode:
            # In keyboard mode, input box positioned to the left of the air tank
            input_box_x = self.tank_x - 220  # Position to the left of tank
            input_box_y = self.tank_y + self.tank_height / 2 - 25  # Vertically centered with tank
            self.input_box = InputBox(input_box_x, input_box_y, 200, 50, MAX_PUMPS)
        else:
            # Original click mode
            self.pump_button = Button(SCREEN_WIDTH * 0.25 - button_width / 2, button_y, button_width, button_height,
                                      "Pump",
                                      PUMP_BUTTON_COLOR, PUMP_BUTTON_HOVER)
            self.collect_button = Button(SCREEN_WIDTH * 0.75 - button_width / 2, button_y, button_width, button_height,
                                         "Collect", COLLECT_BUTTON_COLOR, COLLECT_BUTTON_HOVER)

        self.particles = []
        self.state = "instructions"

        # Appearance parameters
        self.base_radius = 60
        self.growth_per_pump = 5

        # Balloon's anchor is moved higher up the screen
        self.balloon_anchor = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50)

        # Trajectory-based animation parameters
        self.sway_angle = 0
        self.sway_speed = 0.02
        self.sway_amplitude = 12
        self.pump_velocity_boost = 0.0

        # Keyboard mode specific variables
        self.decision_made = False  # Track if participant has made their decision
        self.pumping_complete = False  # Track if pumping animation is done

        self.reset_trial()

    @property
    def balloon_center_x(self):
        return self.balloon_anchor[0] + math.sin(self.sway_angle) * self.sway_amplitude

    @property
    def balloon_center_y(self):
        return self.balloon_anchor[1]

    @property
    def current_radius(self):
        return self.base_radius + self.pumps * self.growth_per_pump

    def reset_trial(self):
        if self.trial > TOTAL_TRIALS:
            self.state = "end"
            self.save_final_data()
            return

        self.pumps = 0
        self.points_this_trial = 0
        self.max_pumps_this_trial = self.max_pumps_for_trials[self.trial - 1]
        self.state = "active"
        self.sway_angle = 0
        self.pump_velocity_boost = 0.0
        self.trial_start_time = time.time()

        # Select balloon color for this trial
        if self.random_colors:
            # Pick a random color from the available colors
            self.current_balloon_color = random.choice(RANDOM_BALLOON_COLORS)
        else:
            # Use the configured color
            self.current_balloon_color = BALLOON_COLOR_BASE

        # Reset keyboard mode specific variables
        if self.keyboard_mode:
            self.input_box.clear()
            self.decision_made = False
            self.pumping_complete = False

    def handle_pump(self):
        """Handle single pump in click mode."""
        if self.state != "active" or self.keyboard_mode:
            return
        self.pumps += 1
        self.points_this_trial += POINTS_PER_PUMP

        boost_amount = 0.15
        self.pump_velocity_boost += boost_amount * random.choice([-1, 1])

        if self.pumps >= self.max_pumps_this_trial:
            self.pop_balloon()

    def handle_set_pumps(self, target_pumps):
        """Handle setting pumps in keyboard mode - auto-collect after animation."""
        if self.state != "active" or not self.keyboard_mode or self.decision_made:
            return

        target_pumps = max(0, min(target_pumps, MAX_PUMPS))

        if target_pumps <= 0:
            return  # Invalid input

        # Mark decision as made - participant can only do this once per balloon
        self.decision_made = True

        # Start pumping animation to the target (slower animation)
        self.target_pumps = target_pumps
        self.animating_pumps = True
        # Slower animation: spread over more frames for smoother experience
        self.pump_animation_speed = max(1, (target_pumps - self.pumps) // 60)  # Animate over ~60 frames instead of 30
        if self.pump_animation_speed == 0:
            self.pump_animation_speed = 1  # Ensure at least 1 pump per frame for small numbers
        self.pumping_complete = False

    def handle_collect(self):
        if self.state != "active" or self.pumps == 0:
            return

        # Calculate reaction time
        reaction_time = time.time() - self.trial_start_time if self.trial_start_time else None

        self.total_score += self.points_this_trial

        # Log to database
        self.log_trial_to_db(
            self.pumps,
            self.points_this_trial,
            TrialOutcome.COLLECTED,
            reaction_time
        )

        self.state = "banked"
        self.trial += 1

    def pop_balloon(self):
        # Calculate reaction time
        reaction_time = time.time() - self.trial_start_time if self.trial_start_time else None

        # Log to database
        self.log_trial_to_db(
            self.pumps,
            0,  # No points earned on pop
            TrialOutcome.FAILURE,
            reaction_time
        )

        self.state = "popped"
        self.trial += 1

        # Create particle explosion with current balloon color
        radius_x = self.current_radius * 0.9
        radius_y = self.current_radius * 1.0
        for _ in range(80):
            angle = random.uniform(0, 2 * math.pi)
            x = self.balloon_center_x + radius_x * math.cos(angle)
            y = self.balloon_center_y + radius_y * math.sin(angle)
            self.particles.append(Particle(x, y, self.current_balloon_color))

    def log_trial_to_db(self, pumps, points, outcome, reaction_time):
        """Log trial data to the database."""
        # Don't log to database in test mode
        if SESSION_ID == 0 or test_mode:
            if test_mode:
                print(f"TEST MODE - Trial {self.trial}: Pumps={pumps}, Points={points}, Outcome={outcome.value}")
            return

        try:
            # Calculate risk level (0-1 scale)
            risk_level = pumps / MAX_PUMPS

            # Get balloon color name for this trial
            balloon_color_used = "Unknown"
            for color_name, color_rgb in BALLOON_COLOR_MAP.items():
                if color_rgb == self.current_balloon_color:
                    balloon_color_used = color_name
                    break

            # Create additional data
            additional_data = {
                "max_pumps_possible": self.max_pumps_this_trial,
                "explosion_point": self.max_pumps_this_trial,
                "total_score_so_far": self.total_score,
                "input_mode": "keyboard" if self.keyboard_mode else "click",
                "balloon_color": balloon_color_used,
                "random_colors": self.random_colors
            }

            # Add trial data to database
            db_manager.add_trial_data(
                session_id=SESSION_ID,
                task_name=TASK_NAME,
                trial_number=self.trial,
                risk_level=risk_level,
                points_earned=points,
                outcome=outcome.value,
                reaction_time=reaction_time,
                additional_data=additional_data
            )

        except Exception as e:
            print(f"Error logging trial to database: {e}")

    def save_final_data(self):
        """Save final summary data when task is complete."""
        if SESSION_ID == 0 or test_mode:
            if test_mode:
                print(
                    f"TEST MODE COMPLETE - Total score: {self.total_score}, Mode: {'Keyboard' if self.keyboard_mode else 'Click'}")
            return

        try:
            # You could add a summary entry or update session info here
            print(f"Task completed. Total score: {self.total_score}")
        except Exception as e:
            print(f"Error saving final data: {e}")

    def update(self, mouse_pos):
        if not self.keyboard_mode:
            self.pump_button.check_hover(mouse_pos)
            self.collect_button.check_hover(mouse_pos)
        else:
            self.input_box.update()

        self.sway_angle += self.sway_speed + self.pump_velocity_boost

        if abs(self.pump_velocity_boost) > 0:
            self.pump_velocity_boost *= 0.92
            if abs(self.pump_velocity_boost) < 0.001:
                self.pump_velocity_boost = 0

        # Handle pump animation in keyboard mode
        if self.keyboard_mode and hasattr(self, 'animating_pumps') and self.animating_pumps:
            if self.pumps < self.target_pumps:
                prev_pumps = self.pumps
                self.pumps = min(self.pumps + self.pump_animation_speed, self.target_pumps)
                self.points_this_trial += (self.pumps - prev_pumps) * POINTS_PER_PUMP

                # Add some visual feedback
                if self.pumps != prev_pumps:
                    boost_amount = 0.1
                    self.pump_velocity_boost += boost_amount * random.choice([-1, 1])

                # Check for explosion during animation
                if self.pumps >= self.max_pumps_this_trial:
                    self.pop_balloon()
                    self.animating_pumps = False
                    return
            else:
                # Pumping animation complete - auto-collect
                self.animating_pumps = False
                self.pumping_complete = True
                # Auto-collect the money
                self.handle_collect()

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

    def draw_instructions(self, surface):
        surface.fill(COLOR_BACKGROUND)
        title = large_font.render("Balloon Pumping Game", True, COLOR_TEXT)
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 150)))

        instructions = [
            f"You will be presented with {TOTAL_TRIALS} balloons.",
            f"Each pump earns {POINTS_PER_PUMP} cents.",
        ]

        if self.keyboard_mode:
            instructions.extend([
                "Type the number of pumps you want in the input box.",
                "Press ENTER to pump the balloon to that amount.",
                "The money will be automatically collected after pumping.",
                "You can only make ONE decision per balloon.",
            ])
        else:
            instructions.extend([
                "Click 'Pump' to inflate the balloon and earn money.",
                "At any point, you can click 'Collect' to bank the money from that balloon.",
            ])

        instructions.extend([
            "However, each balloon has a random popping point!",
            "If the balloon pops, you lose all the money from that balloon.",
            "Your goal is to earn as much money as possible.",
            "",
            "Press ENTER to begin."
        ])

        y_pos = 250
        for line in instructions:
            text = font.render(line, True, COLOR_TEXT)
            surface.blit(text, text.get_rect(center=(SCREEN_WIDTH / 2, y_pos)))
            y_pos += 50

    def draw_end_screen(self, surface):
        surface.fill(COLOR_BACKGROUND)

        if test_mode:
            title = large_font.render("Test Complete!", True, COLOR_TEXT)
        else:
            title = large_font.render("Task Complete!", True, COLOR_TEXT)
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 200)))

        final_score = font.render(f"Your final score is: {self.total_score} cents", True, COLOR_TEXT)
        surface.blit(final_score, final_score.get_rect(center=(SCREEN_WIDTH / 2, 350)))

        mode_text = small_font.render(f"Input mode: {'Keyboard' if self.keyboard_mode else 'Click'}", True, COLOR_TEXT)
        surface.blit(mode_text, mode_text.get_rect(center=(SCREEN_WIDTH / 2, 400)))

        if test_mode:
            info_text = small_font.render("This was a test run - no data was saved.", True, COLOR_TEXT)
        else:
            info_text = small_font.render("Data has been saved to the database.", True, COLOR_TEXT)
        surface.blit(info_text, info_text.get_rect(center=(SCREEN_WIDTH / 2, 450)))

        exit_text = font.render("Press ESC to exit.", True, COLOR_TEXT)
        surface.blit(exit_text, exit_text.get_rect(center=(SCREEN_WIDTH / 2, 600)))

    def draw_balloon(self, surface):
        radius_x = self.current_radius * 0.9
        radius_y = self.current_radius * 1.0
        center_x, center_y = int(self.balloon_center_x), int(self.balloon_center_y)

        # Use current balloon color
        pygame.draw.ellipse(surface, self.current_balloon_color,
                            (center_x - radius_x, center_y - radius_y, 2 * radius_x, 2 * radius_y))

        highlight_surf = pygame.Surface((radius_x * 2, radius_y * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(highlight_surf, BALLOON_COLOR_HIGHLIGHT,
                            (radius_x * 0.2, radius_y * 0.2, radius_x * 1.2, radius_y * 1.2))
        surface.blit(highlight_surf, (center_x - radius_x, center_y - radius_y))

        knot_radius = 10
        knot_y = center_y + radius_y
        pygame.draw.circle(surface, self.current_balloon_color, (center_x, int(knot_y)), knot_radius)

    def draw_air_tank(self, surface):
        tank_rect = pygame.Rect(self.tank_x, self.tank_y, self.tank_width, self.tank_height)
        pygame.draw.rect(surface, AIR_TANK_COLOR, tank_rect, border_top_left_radius=15, border_top_right_radius=15)

        highlight_rect = pygame.Rect(self.tank_x + 10, self.tank_y + 10, self.tank_width - 20, self.tank_height - 20)
        pygame.draw.rect(surface, AIR_TANK_HIGHLIGHT, highlight_rect, border_top_left_radius=10,
                         border_top_right_radius=10)

        nozzle_width = 20
        nozzle_height = 30
        nozzle_x = self.tank_x + self.tank_width / 2 - nozzle_width / 2
        nozzle_y = self.tank_y - nozzle_height
        pygame.draw.rect(surface, (47, 79, 79), (nozzle_x, nozzle_y, nozzle_width, nozzle_height),
                         border_top_left_radius=5, border_top_right_radius=5)

    def draw_hose(self, surface):
        knot_y = int(self.balloon_center_y + self.current_radius * 1.0) + 10
        nozzle_x = self.tank_x + self.tank_width / 2
        nozzle_y = self.tank_y - 20

        start_point = (nozzle_x, nozzle_y)
        end_point = (int(self.balloon_center_x), knot_y)

        control_point_x = (start_point[0] + end_point[0]) / 2 + 20 * math.sin(self.sway_angle * 0.5)
        control_point_y = start_point[1] + (end_point[1] - start_point[1]) * 0.3

        points = []
        for i in range(21):
            t = i / 20
            x = (1 - t) ** 2 * start_point[0] + 2 * (1 - t) * t * control_point_x + t ** 2 * end_point[0]
            y = (1 - t) ** 2 * start_point[1] + 2 * (1 - t) * t * control_point_y + t ** 2 * end_point[1]
            points.append((x, y))

        pygame.draw.lines(surface, AIR_HOSE_COLOR, False, points, 8)

    def draw(self, surface):
        surface.fill(COLOR_BACKGROUND)

        panel_width, panel_height, panel_y = 350, 120, 30

        total_panel_rect = pygame.Rect(30, panel_y, panel_width, panel_height)
        pygame.draw.rect(surface, WHITE, total_panel_rect, border_radius=15)
        pygame.draw.rect(surface, COLOR_SCORE_BOX_BORDER, total_panel_rect, 3, border_radius=15)
        total_title = small_font.render("Total Winnings", True, COLOR_TEXT)
        surface.blit(total_title, (total_panel_rect.x + 20, total_panel_rect.y + 20))
        total_val = large_font.render(f"{self.total_score}¢", True, COLOR_TEXT)
        surface.blit(total_val, total_val.get_rect(midleft=(total_panel_rect.x + 25, total_panel_rect.centery + 10)))

        current_panel_rect = pygame.Rect(SCREEN_WIDTH - panel_width - 30, panel_y, panel_width, panel_height)
        pygame.draw.rect(surface, WHITE, current_panel_rect, border_radius=15)
        pygame.draw.rect(surface, COLOR_SCORE_BOX_BORDER, current_panel_rect, 3, border_radius=15)
        current_title = small_font.render("This Balloon", True, COLOR_TEXT)
        surface.blit(current_title, (current_panel_rect.x + 20, current_panel_rect.y + 20))
        current_val = large_font.render(f"{self.points_this_trial}¢", True, COLOR_TEXT)
        surface.blit(current_val,
                     current_val.get_rect(midleft=(current_panel_rect.x + 25, current_panel_rect.centery + 10)))

        if self.state == "active":
            self.draw_air_tank(surface)
            self.draw_hose(surface)
            self.draw_balloon(surface)
        elif self.state == "popped":
            for p in self.particles: p.draw(surface)
            feedback = large_font.render("POP!", True, self.current_balloon_color)
            surface.blit(feedback, feedback.get_rect(center=(self.balloon_anchor[0], self.balloon_anchor[1])))
        elif self.state == "banked":
            feedback = large_font.render("Collected!", True, COLLECT_BUTTON_COLOR)
            surface.blit(feedback, feedback.get_rect(center=(self.balloon_anchor[0], self.balloon_anchor[1])))

        if self.state == "active":
            if self.keyboard_mode:
                # Only show input box if decision hasn't been made yet
                if not self.decision_made:
                    # Input label positioned above the input box (to the left of tank)
                    input_label = small_font.render("Enter pumps:", True, COLOR_TEXT)
                    label_x = self.input_box.rect.x
                    label_y = self.input_box.rect.y - 30
                    surface.blit(input_label, (label_x, label_y))

                    self.input_box.draw(surface)

                    # Instruction below input box
                    instruction_text = tiny_font.render("Press ENTER", True, COLOR_TEXT)
                    instr_x = self.input_box.rect.x
                    instr_y = self.input_box.rect.y + self.input_box.rect.height + 5
                    surface.blit(instruction_text, (instr_x, instr_y))
                elif hasattr(self, 'animating_pumps') and self.animating_pumps:
                    # Show pumping animation status near the input area
                    status_text = small_font.render("Pumping...", True, COLOR_TEXT)
                    status_x = self.input_box.rect.x
                    status_y = self.input_box.rect.y + 10
                    surface.blit(status_text, (status_x, status_y))
                elif self.pumping_complete:
                    # Show that money was collected near the input area
                    collected_text = small_font.render("Collected!", True, COLLECT_BUTTON_COLOR)
                    collected_x = self.input_box.rect.x
                    collected_y = self.input_box.rect.y + 10
                    surface.blit(collected_text, (collected_x, collected_y))
            else:
                # Original click mode buttons
                self.pump_button.draw(surface)
                if self.pumps > 0:
                    self.collect_button.draw(surface)

                # Show current pumps only in click mode
                pumps_text = font.render(f"Current pumps: {self.pumps}", True, COLOR_TEXT)
                surface.blit(pumps_text, pumps_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 300)))
        else:
            next_text = font.render("Press ENTER for next balloon", True, COLOR_TEXT)
            surface.blit(next_text, next_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 250)))

        trial_text = font.render(f"Balloon: {self.trial} / {TOTAL_TRIALS}", True, COLOR_TEXT)
        surface.blit(trial_text, trial_text.get_rect(center=(SCREEN_WIDTH / 2, 80)))


def main():
    game = BalloonTask()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_RETURN:
                    if game.state == "instructions":
                        game.state = "active"
                    elif game.state in ["popped", "banked"]:
                        game.reset_trial()

            # Handle input box events in keyboard mode
            if game.keyboard_mode and game.state == "active" and not game.decision_made:
                result = game.input_box.handle_event(event)
                if result == 'submit':
                    target_pumps = game.input_box.get_value()
                    if target_pumps > 0:
                        game.handle_set_pumps(target_pumps)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == "active":
                    if game.keyboard_mode:
                        # In keyboard mode, no buttons to click - only input box interaction
                        pass
                    else:
                        # Original click mode
                        if game.pump_button.rect.collidepoint(mouse_pos):
                            game.handle_pump()
                        if game.pumps > 0 and game.collect_button.rect.collidepoint(mouse_pos):
                            game.handle_collect()

        game.update(mouse_pos)

        if game.state == "instructions":
            game.draw_instructions(screen)
        elif game.state == "end":
            game.draw_end_screen(screen)
        else:
            game.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    # Close database connection
    db_manager.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()