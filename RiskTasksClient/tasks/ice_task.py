import pygame
import sys
import random
import math
import time
import os
from pathlib import Path

# Get session and participant info from environment
session_id_str = os.environ.get('SESSION_ID', '0')
participant_id_str = os.environ.get('PARTICIPANT_ID', '0')

# Convert to int, handling 'None' string
SESSION_ID = 0 if session_id_str in ['None', 'null', ''] else int(session_id_str)
PARTICIPANT_ID = 0 if participant_id_str in ['None', 'null', ''] else int(participant_id_str)
TASK_NAME = os.environ.get('TASK_NAME', 'ice_fishing')

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
        task_config = config.get('tasks', {}).get('ice_fishing', {})
else:
    # Default configuration
    task_config = {
        "max_fish": 64,
        "points_per_fish": 5
    }

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
TOTAL_TRIALS = config.get('experiment', {}).get('total_trials_per_task', 30)

# Task-specific constants from config
MAX_FISH = task_config.get('max_fish', 64)
POINTS_PER_FISH = task_config.get('points_per_fish', 5)

# Enhanced Color Palette (Arctic Theme)
COLOR_BACKGROUND_GRADIENT_START = (60, 90, 130)
COLOR_BACKGROUND_GRADIENT_END = (173, 216, 230)
COLOR_MOUNTAIN_FAR = (170, 170, 190)
COLOR_MOUNTAIN_MID = (140, 130, 150)
COLOR_MOUNTAIN_NEAR = (101, 67, 33)
COLOR_MOUNTAIN_DETAIL = (81, 57, 23)
COLOR_MOUNTAIN_SNOW = (255, 255, 255)
COLOR_MOUNTAIN_SNOW_SHADOW = (230, 230, 245)
COLOR_RAVINE_GRADIENT_TOP = (40, 40, 50)
COLOR_RAVINE_GRADIENT_BOTTOM = (10, 10, 20)
COLOR_ROPE = (160, 82, 45)
COLOR_ROPE_2 = (0, 0, 80)
COLOR_ROPE_STRESSED = (220, 80, 60)
COLOR_ROPE_SHADOW = (120, 62, 35)
COLOR_BUCKET_METAL = (140, 140, 150)
COLOR_BUCKET_DARK = (90, 90, 100)
COLOR_BUCKET_HIGHLIGHT = (200, 200, 210)
COLOR_BUCKET_RUST = (165, 42, 42)
COLOR_ORE_GOLD = (255, 215, 0)
COLOR_ORE_GOLD_SHADOW = (218, 165, 32)
COLOR_ORE_SILVER = (192, 192, 192)
COLOR_ORE_SILVER_SHADOW = (169, 169, 169)
COLOR_ORE_COPPER = (184, 115, 51)
COLOR_ORE_COPPER_SHADOW = (150, 90, 40)
COLOR_TRUCK_RED = (220, 38, 38)
COLOR_TRUCK_DARK = (150, 20, 20)
COLOR_TRUCK_WINDOW = (100, 149, 237)
COLOR_TRUCK_CHROME = (192, 192, 192)
COLOR_WHEEL = (40, 40, 40)
COLOR_UI_BG = (20, 25, 40)
COLOR_UI_BG_LIGHT = (40, 45, 60)
COLOR_UI_TEXT = (248, 248, 242)
COLOR_UI_ACCENT = (255, 220, 50)
COLOR_BUTTON_NORMAL = (80, 250, 123)
COLOR_BUTTON_HOVER = (120, 255, 160)
COLOR_BUTTON_SEND = (100, 149, 237)
COLOR_BUTTON_SEND_HOVER = (140, 180, 255)
COLOR_BUTTON_SHADOW = (40, 40, 50)
COLOR_DANGER_LOW = (80, 250, 123)
COLOR_DANGER_MID = (255, 220, 50)
COLOR_DANGER_HIGH = (255, 85, 85)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Set up display for fullscreen based on config
fullscreen_mode = config.get('display', {}).get('fullscreen', True)
if fullscreen_mode:
    infoObject = pygame.display.Info()
    WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SRCALPHA)
else:
    WIDTH, HEIGHT = 1200, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Penguin Fishing: Risk Assessment")
clock = pygame.time.Clock()

# Fonts
try:
    FONT_FAMILY = "Arial"
    if "Calibri" in pygame.font.get_fonts():
        FONT_FAMILY = "Calibri"
    elif "Segoe UI" in pygame.font.get_fonts():
        FONT_FAMILY = "Segoe UI"

    font = pygame.font.SysFont(FONT_FAMILY, 36)
    small_font = pygame.font.SysFont(FONT_FAMILY, 24)
    large_font = pygame.font.SysFont(FONT_FAMILY, 48)
    huge_font = pygame.font.SysFont(FONT_FAMILY, 64, bold=True)
    tiny_font = pygame.font.SysFont(FONT_FAMILY, 20)
except:
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    large_font = pygame.font.SysFont(None, 48)
    huge_font = pygame.font.SysFont(None, 64, bold=True)
    tiny_font = pygame.font.SysFont(None, 20)

# Initialize database connection
db_manager = DatabaseManager()
db_manager.initialize()


class FlyingFish:
    """Animated fish that flies from water to sled"""

    def __init__(self, start_pos, target_pos):
        self.x, self.y = start_pos
        self.start_x, self.start_y = start_pos
        self.target_x, self.target_y = target_pos
        self.color = random.choice([COLOR_FISH_SILVER, COLOR_FISH_BLUE, COLOR_FISH_ORANGE])
        self.size = random.randint(14, 20)  # Scaled up from 8-12
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-15, 15)

        self.progress = 0.0
        self.speed = 0.03

        self.x_dist = self.target_x - self.start_x
        self.y_dist = self.target_y - self.start_y
        self.arc_height = -abs(self.x_dist / 2)

    def update(self):
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 1.0
            return True

        # Parabolic arc motion
        self.x = self.start_x + self.x_dist * self.progress
        arc = 4 * self.arc_height * self.progress * (1 - self.progress)
        self.y = self.start_y + self.y_dist * self.progress + arc

        self.rotation += self.rotation_speed
        return False

    def draw(self, surface):
        # Draw fish body
        angle_rad = math.radians(self.rotation)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Fish body (ellipse approximation with points)
        body_points = []
        for i in range(8):
            angle = i * math.pi / 4
            rx = self.size * 1.5 * math.cos(angle)
            ry = self.size * 0.7 * math.sin(angle)
            # Rotate point
            x = self.x + rx * cos_a - ry * sin_a
            y = self.y + rx * sin_a + ry * cos_a
            body_points.append((x, y))

        pygame.draw.polygon(surface, self.color, body_points)

        # Tail
        tail_x = self.x - self.size * 1.2 * cos_a
        tail_y = self.y - self.size * 1.2 * sin_a
        tail_points = [
            (tail_x, tail_y),
            (tail_x - self.size * 0.8 * cos_a + self.size * 0.6 * sin_a,
             tail_y - self.size * 0.8 * sin_a - self.size * 0.6 * cos_a),
            (tail_x - self.size * 0.8 * cos_a - self.size * 0.6 * sin_a,
             tail_y - self.size * 0.8 * sin_a + self.size * 0.6 * cos_a)
        ]
        pygame.draw.polygon(surface, self.color, tail_points)


class Particle:
    """Water splash and other particle effects"""

    def __init__(self, x, y, dx, dy, color, life, size):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.5  # Gravity
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            alpha = self.life / self.max_life
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)),
                               max(1, int(self.size * alpha)))


class Button:
    """Enhanced button with shadow and press animation"""

    def __init__(self, x, y, width, height, text, color=COLOR_BUTTON_NORMAL, hover_color=COLOR_BUTTON_HOVER):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.press_offset = 0

    def draw(self, surface):
        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 5 + self.press_offset
        pygame.draw.rect(surface, COLOR_BUTTON_SHADOW, shadow_rect, border_radius=15)

        # Button
        button_rect = self.rect.copy()
        button_rect.y += self.press_offset
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, button_rect, border_radius=15)

        # Highlight
        highlight_rect = button_rect.copy()
        highlight_rect.height = 20
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surf, (255, 255, 255, 30),
                         (0, 0, highlight_rect.width, highlight_rect.height), border_radius=15)
        surface.blit(highlight_surf, highlight_rect)

        # Border
        pygame.draw.rect(surface, WHITE, button_rect, 3, border_radius=15)

        # Text
        text_surf = font.render(self.text, True, COLOR_BUTTON_TEXT)
        text_rect = text_surf.get_rect(center=button_rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        if self.rect.collidepoint(pos):
            self.press_offset = 2
            return True
        return False

    def release(self):
        self.press_offset = 0


def draw_gradient_rect(surface, color1, color2, rect, vertical=True):
    """Draw a gradient-filled rectangle"""
    if vertical:
        for y in range(rect.height):
            progress = y / rect.height
            r = int(color1[0] + (color2[0] - color1[0]) * progress)
            g = int(color1[1] + (color2[1] - color1[1]) * progress)
            b = int(color1[2] + (color2[2] - color1[2]) * progress)
            pygame.draw.line(surface, (r, g, b),
                             (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))


def draw_penguin(surface, x, y, state="stand", fishing_hole_center=None):
    """Draw animated penguin with fishing rod"""
    animation_timer = pygame.time.get_ticks()

    # Body (scaled up from 50x70 to 80x112)
    body_rect = pygame.Rect(x, y, 80, 112)
    pygame.draw.ellipse(surface, COLOR_PENGUIN_BODY, body_rect)

    # Belly (scaled proportionally)
    belly_rect = pygame.Rect(x + 13, y + 40, 54, 64)
    pygame.draw.ellipse(surface, COLOR_PENGUIN_BELLY, belly_rect)

    # Eyes (scaled up)
    eye_y = y + 32
    pygame.draw.circle(surface, WHITE, (x + 24, eye_y), 10)
    pygame.draw.circle(surface, WHITE, (x + 56, eye_y), 10)
    pygame.draw.circle(surface, BLACK, (x + 24, eye_y), 5)
    pygame.draw.circle(surface, BLACK, (x + 56, eye_y), 5)

    # Beak (scaled up)
    beak_points = [(x + 40, y + 40), (x + 32, y + 48), (x + 48, y + 48)]
    pygame.draw.polygon(surface, COLOR_PENGUIN_BEAK_FEET, beak_points)

    # Feet (scaled up)
    foot_base_y = y + 109
    pygame.draw.ellipse(surface, COLOR_PENGUIN_BEAK_FEET, (x + 6, foot_base_y, 32, 19))
    pygame.draw.ellipse(surface, COLOR_PENGUIN_BEAK_FEET, (x + 42, foot_base_y, 32, 19))

    # Flippers
    if state == "fish" and fishing_hole_center:
        # Right flipper holding rod (pointing upward)
        flipper_x = x + 72
        flipper_y = y + 56

        # Rod extends upward at an angle
        rod_end_x = flipper_x + 32
        rod_end_y = flipper_y - 64

        # Draw flipper
        pygame.draw.line(surface, COLOR_PENGUIN_BODY, (flipper_x, flipper_y),
                         (rod_end_x, rod_end_y), 13)

        # Fishing rod (brown line extending upward)
        rod_color = COLOR_SLED_BODY
        pygame.draw.line(surface, rod_color, (flipper_x, flipper_y),
                         (rod_end_x, rod_end_y), 5)

        # Fishing line (from rod tip down to center of fishing hole)
        line_color = (150, 150, 150)
        pygame.draw.line(surface, line_color, (rod_end_x, rod_end_y),
                         fishing_hole_center, 2)

        # Hook/lure at the end of the line in the water
        pygame.draw.circle(surface, COLOR_UI_TEXT_BAD, fishing_hole_center, 6)

        # Left flipper (normal position)
        pygame.draw.ellipse(surface, COLOR_PENGUIN_BODY, (x - 8, y + 56, 19, 40))
    else:
        # Normal flippers
        pygame.draw.ellipse(surface, COLOR_PENGUIN_BODY, (x - 8, y + 56, 19, 40))
        pygame.draw.ellipse(surface, COLOR_PENGUIN_BODY, (x + 69, y + 56, 19, 40))


def draw_fish_on_sled(surface, x, y, fish_positions):
    """Draw individual fish stacked on the sled"""
    for fx, fy, color in fish_positions:
        fish_x = x + fx
        fish_y = y + fy

        # Fish body (scaled up from 20x10 to 32x16)
        body_width = 32
        body_height = 16
        body_rect = pygame.Rect(fish_x - body_width // 2, fish_y - body_height // 2,
                                body_width, body_height)
        pygame.draw.ellipse(surface, color, body_rect)

        # Tail (scaled proportionally)
        tail_points = [
            (fish_x + body_width // 2, fish_y),
            (fish_x + body_width // 2 + 13, fish_y - 10),
            (fish_x + body_width // 2 + 13, fish_y + 10)
        ]
        pygame.draw.polygon(surface, color, tail_points)

        # Eye (scaled up)
        pygame.draw.circle(surface, WHITE, (fish_x - 8, fish_y), 3)
        pygame.draw.circle(surface, BLACK, (fish_x - 8, fish_y), 2)


def draw_sled(surface, x, y, fish_positions, fallen=False):
    """Draw sled with visible fish stack"""
    sled_width = 200  # Scaled up from 130
    sled_height = 110  # Scaled up from 70
    sled_draw_y = y - sled_height / 2

    if fallen:
        # Draw sled underwater
        water_rect = pygame.Rect(x - sled_width // 2, y - 30, sled_width, 60)
        pygame.draw.rect(surface, COLOR_WATER, water_rect)

        # Scattered debris
        for _ in range(5):
            px = x + random.uniform(-sled_width / 2, sled_width / 2)
            py = y + random.uniform(-15, 30)
            pygame.draw.rect(surface, COLOR_SLED_BODY,
                             (px, py, random.randint(15, 30), random.randint(8, 15)))
    else:
        # Sled base
        base_rect = pygame.Rect(x - sled_width // 2, sled_draw_y, sled_width, sled_height)
        pygame.draw.rect(surface, COLOR_SLED_BODY, base_rect, border_radius=15)
        pygame.draw.rect(surface, COLOR_SLED_DARK, base_rect, 5, border_radius=15)

        # Metal runners
        runner_y = y + sled_height // 2 - 8
        pygame.draw.line(surface, COLOR_SLED_METAL,
                         (x - sled_width // 2 + 15, runner_y),
                         (x + sled_width // 2 - 15, runner_y), 6)

        # Draw fish on sled - they stack from the bottom of the sled
        draw_fish_on_sled(surface, x, sled_draw_y + 70, fish_positions)


def draw_ice_crack(surface, x, y):
    """Draw cracks in ice"""
    for i in range(8):
        angle = i * math.pi / 4 + random.uniform(-0.1, 0.1)
        length = random.randint(50, 80)  # Scaled up from 30-50
        end_x = x + math.cos(angle) * length
        end_y = y + math.sin(angle) * length
        pygame.draw.line(surface, (50, 50, 50), (x, y), (int(end_x), int(end_y)), 5)  # Thicker line


def draw_igloo(surface, x, y):
    """Draws a simple igloo as a cosmetic destination."""
    igloo_color = (230, 250, 255)
    igloo_outline = (180, 200, 220)

    # Main dome shape - LARGER (scaled up from 200x120 to 320x190)
    dome_rect = pygame.Rect(x - 160, y - 130, 320, 190)
    pygame.draw.ellipse(surface, igloo_color, dome_rect)
    pygame.draw.ellipse(surface, igloo_outline, dome_rect, 8)

    # Dark entrance - LARGER (scaled up from 50x35 to 80x55)
    entrance_rect = pygame.Rect(x - 40, y - 55, 80, 55)
    pygame.draw.ellipse(surface, BLACK, entrance_rect)

    # Create a base to make it look seated on the snow - WIDER
    pygame.draw.rect(surface, igloo_color, (x - 160, y - 8, 320, 16))


# Color constants
COLOR_PENGUIN_BODY = (30, 30, 30)
COLOR_PENGUIN_BELLY = (240, 240, 240)
COLOR_PENGUIN_BEAK_FEET = (255, 165, 0)
COLOR_SLED_BODY = (139, 69, 19)
COLOR_SLED_METAL = (140, 140, 150)
COLOR_SLED_DARK = (90, 60, 30)
COLOR_FISH_SILVER = (192, 192, 192)
COLOR_FISH_BLUE = (100, 149, 237)
COLOR_FISH_ORANGE = (255, 140, 90)
COLOR_UI_TEXT_BAD = (255, 85, 85)
COLOR_WATER = (0, 70, 140)
COLOR_WATER_HIGHLIGHT = (100, 149, 237)
COLOR_WATER_DEEP = (0, 50, 100)
COLOR_BUTTON_TEXT = (248, 248, 242)
COLOR_BUTTON_FISH = (80, 250, 123)
COLOR_BUTTON_FISH_HOVER = (120, 255, 160)
COLOR_UI_TEXT_GOOD = (80, 250, 123)
COLOR_ICE_SURFACE = (220, 245, 255)


class Cloud:
    def __init__(self):
        self.x = random.randint(-200, WIDTH + 200)
        self.y = random.randint(50, 300)
        self.speed = random.uniform(0.1, 0.3)
        self.size = random.uniform(0.8, 1.2)
        self.opacity = random.randint(180, 220)

    def update(self):
        self.x += self.speed
        if self.x > WIDTH + 200:
            self.x = -200
            self.y = random.randint(50, 300)

    def draw(self, surface):
        cloud_surf = pygame.Surface((200, 100), pygame.SRCALPHA)
        circles = [
            (50, 50, 35), (100, 50, 40), (150, 50, 35), (70, 40, 30),
            (130, 40, 30), (80, 60, 25), (120, 60, 25)
        ]
        for cx, cy, r in circles:
            pygame.draw.circle(cloud_surf, (255, 255, 255, self.opacity),
                               (int(cx * self.size), int(cy * self.size)), int(r * self.size))
        surface.blit(cloud_surf, (self.x, self.y))


class PenguinGame:
    def __init__(self):
        self.state = "menu"
        self.penguin_x = 400  # Adjusted for larger penguin
        self.penguin_y = 370  # Adjusted for larger penguin
        self.penguin_state = "stand"
        self.sled_x = 200  # Adjusted for larger sled
        self.sled_y = 460  # Adjusted for larger sled
        self.sled_fallen = False

        self.fish_count = 0
        self.fish_positions = []  # Positions of fish on sled
        self.flying_fish = []
        self.total_fish_banked = 0
        self.trial = 1
        self.trial_start_time = None

        self.moving = False
        self.success = None
        self.show_feedback = False
        self.feedback_timer = 0

        self.particles = []
        self.snow_particles = []
        self.initialize_snow()

        # Pre-determine "explosion points" for all trials (selection without replacement)
        self.explosion_points = []
        self.generate_explosion_points()

        # Fishing hole position (adjusted for larger elements)
        self.fishing_hole_x = 550  # Adjusted for larger elements
        self.fishing_hole_y = 550

        # Buttons (adjusted positions for larger elements)
        self.fish_button = Button(470, 650, 200, 60, "Catch Fish",
                                  COLOR_BUTTON_FISH, COLOR_BUTTON_FISH_HOVER)
        self.send_sled_button = Button(150, 650, 200, 60, "Send Sled",
                                       COLOR_BUTTON_SEND, COLOR_BUTTON_SEND_HOVER)
        self.start_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 200,
                                   200, 60, "Start Game")
        self.play_again_button = Button(WIDTH // 2 - 250, HEIGHT - 120,
                                        200, 60, "Play Again")
        self.quit_button = Button(WIDTH // 2 + 50, HEIGHT - 120,
                                  200, 60, "Quit", COLOR_UI_TEXT_BAD, (255, 120, 120))

        self.clouds = [Cloud() for _ in range(5)]
        self.birds = []
        for _ in range(3):
            self.birds.append({
                'x': random.randint(0, WIDTH), 'y': random.randint(100, 400),
                'speed': random.uniform(0.5, 1.5), 'flap': 0
            })

    def generate_explosion_points(self):
        """Generate explosion points for all trials using selection without replacement."""
        self.explosion_points = []
        for _ in range(TOTAL_TRIALS):
            # Each trial has an explosion point between 1 and MAX_FISH
            explosion_point = random.randint(1, MAX_FISH)
            self.explosion_points.append(explosion_point)

    def initialize_snow(self):
        for _ in range(80):
            self.snow_particles.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "size": random.uniform(1, 4),
                "speed": random.uniform(0.5, 1.5)
            })

    def update_snow(self):
        for snow in self.snow_particles:
            snow["y"] += snow["speed"]
            snow["x"] += math.sin(time.time() + snow["y"] * 0.01) * 0.5
            if snow["y"] > HEIGHT:
                snow["y"] = -5
                snow["x"] = random.randint(0, WIDTH)

    def catch_fish(self):
        """Initiate fishing animation"""
        if self.fish_count + len(self.flying_fish) < MAX_FISH and not self.moving:
            # Create water splash at the center of the fishing hole
            for _ in range(20):
                dx = random.uniform(-7, 7)
                dy = random.uniform(-10, -3)
                self.particles.append(
                    Particle(self.fishing_hole_x, self.fishing_hole_y,
                             dx, dy, COLOR_WATER_HIGHLIGHT, 40, random.randint(3, 7))
                )

            # Calculate fish landing position on sled
            # Stack fish in rows - account for fish already caught plus flying fish
            current_total = self.fish_count + len(self.flying_fish)
            row_capacity = 8
            row = current_total // row_capacity
            col = current_total % row_capacity

            target_x = self.sled_x - 60 + col * 16  # Adjusted for larger sled
            target_y = self.sled_y + 10 - row * 18  # Adjusted for larger fish

            # Create flying fish from center of fishing hole
            fish_start = (self.fishing_hole_x, self.fishing_hole_y)
            fish_target = (target_x, target_y)
            self.flying_fish.append(FlyingFish(fish_start, fish_target))

            # Fishing animation state
            self.penguin_state = "fish"

    def send_sled(self):
        """Start sled movement across ice"""
        if self.fish_count > 0 and not self.moving:
            self.moving = True
            self.penguin_state = "walk"
            self.trial_start_time = time.time()  # Record when decision was made

    def update(self):
        self.update_snow()

        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)

        # Update flying fish
        for fish in self.flying_fish[:]:
            if fish.update():
                # Fish landed on sled
                self.fish_count += 1

                # Add to visual positions
                row_capacity = 8
                row = (self.fish_count - 1) // row_capacity
                col = (self.fish_count - 1) % row_capacity

                x_offset = -60 + col * 16  # Adjusted for larger sled
                y_offset = 10 - row * 18  # Adjusted for larger fish

                self.fish_positions.append((x_offset, y_offset, fish.color))
                self.flying_fish.remove(fish)

        # Reset penguin state after fishing animation
        if self.penguin_state == "fish" and not self.flying_fish:
            self.penguin_state = "stand"

        # Handle sled movement and risk calculation
        if self.moving and self.state == "play":
            # Move penguin and sled together only if the trip isn't over
            if not self.sled_fallen and self.penguin_x < WIDTH - 300:
                self.penguin_x += 5  # Increased from 3
                self.sled_x += 5  # Increased from 3

            # Check for fall at midpoint
            mid_x = WIDTH // 2
            end_x = WIDTH - 300  # Adjusted for larger elements

            # --- SINGLE RISK CALCULATION (Selection without replacement) ---
            # This block now runs only ONCE when the sled crosses the midpoint,
            # because self.success is set immediately, preventing re-entry.
            if self.sled_x >= mid_x and self.success is None:
                # Get the predetermined explosion point for this trial
                explosion_point = self.explosion_points[self.trial - 1]

                # Success if fish count is less than explosion point
                if self.fish_count < explosion_point:
                    # SUCCESS is decided here
                    self.success = True
                    self.log_trial(self.trial, self.fish_count, True)
                else:
                    # FAILURE is decided here (fish_count >= explosion_point)
                    self.success = False
                    self.log_trial(self.trial, self.fish_count, False)

            # --- ANIMATE THE OUTCOME ---
            # Animate the failure if it was decided
            if self.success is False and not self.sled_fallen:
                self.sled_fallen = True
                self.show_feedback = True
                self.feedback_timer = 120
                # Create splash at fall point
                for _ in range(30):
                    dx = random.uniform(-8, 8)
                    dy = random.uniform(-10, -3)
                    self.particles.append(
                        Particle(self.sled_x, self.sled_y + 30,
                                 dx, dy, COLOR_WATER_HIGHLIGHT, 60, random.randint(4, 10))
                    )

            # Animate the end of a successful trip
            elif self.success is True and self.penguin_x >= end_x:
                self.show_feedback = True
                self.feedback_timer = 120
                self.total_fish_banked += self.fish_count
                self.moving = False
                self.penguin_state = "stand"

        # Handle feedback timer and trial reset
        if self.show_feedback:
            self.feedback_timer -= 1
            if self.feedback_timer <= 0:
                self.show_feedback = False
                self.trial += 1

                if self.trial > TOTAL_TRIALS:
                    self.state = "results"
                    self.save_final_data()
                else:
                    self.reset_trial()

        # Update birds
        for bird in self.birds:
            bird['x'] += bird['speed']
            bird['y'] += math.sin(bird['x'] * 0.01) * 0.5
            bird['flap'] = (bird['flap'] + 0.2) % (math.pi * 2)
            if bird['x'] > WIDTH + 50:
                bird['x'] = -50
                bird['y'] = random.randint(100, 400)

        # Update clouds
        for cloud in self.clouds:
            cloud.update()

    def reset_trial(self):
        self.penguin_x = 400
        self.penguin_y = 370
        self.penguin_state = "stand"
        self.sled_x = 200
        self.sled_y = 460
        self.sled_fallen = False
        self.fish_count = 0
        self.fish_positions = []
        self.flying_fish = []
        self.moving = False
        self.success = None
        self.particles = []
        self.trial_start_time = None

        # Generate new explosion points if all trials are complete
        if self.trial > TOTAL_TRIALS:
            self.generate_explosion_points()

    def log_trial(self, trial_num, fish_count, success):
        """Log trial data to the database."""
        # Don't log to database in test mode
        if SESSION_ID == 0 or test_mode:
            if test_mode:
                print(f"TEST MODE - Trial {trial_num}: Fish={fish_count}, Success={success}")
            return

        try:
            # Calculate risk level (0-1 scale)
            risk_level = fish_count / MAX_FISH

            # Calculate reaction time
            reaction_time = time.time() - self.trial_start_time if self.trial_start_time else None

            # Determine outcome
            outcome = TrialOutcome.SUCCESS if success else TrialOutcome.FAILURE

            # Points earned
            points = fish_count * POINTS_PER_FISH if success else 0

            # Create additional data
            additional_data = {
                "fish_caught": fish_count,
                "explosion_point": self.explosion_points[trial_num - 1],
                "total_fish_banked": self.total_fish_banked
            }

            # Add trial data to database
            db_manager.add_trial_data(
                session_id=SESSION_ID,
                task_name=TASK_NAME,
                trial_number=trial_num,
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
                print(f"TEST MODE COMPLETE - Total fish banked: {self.total_fish_banked}")
            return

        try:
            # You could add a summary entry or update session info here
            print(f"Task completed. Total fish banked: {self.total_fish_banked}")
        except Exception as e:
            print(f"Error saving final data: {e}")

    def draw_background(self):
        # Sky gradient
        for y in range(HEIGHT // 2 + 50):
            progress = y / (HEIGHT // 2 + 50)
            r = int(COLOR_BACKGROUND_GRADIENT_START[0] +
                    (COLOR_BACKGROUND_GRADIENT_END[0] - COLOR_BACKGROUND_GRADIENT_START[0]) * progress)
            g = int(COLOR_BACKGROUND_GRADIENT_START[1] +
                    (COLOR_BACKGROUND_GRADIENT_END[1] - COLOR_BACKGROUND_GRADIENT_START[1]) * progress)
            b = int(COLOR_BACKGROUND_GRADIENT_START[2] +
                    (COLOR_BACKGROUND_GRADIENT_END[2] - COLOR_BACKGROUND_GRADIENT_START[2]) * progress)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        # Mountains
        pygame.draw.polygon(screen, COLOR_MOUNTAIN_FAR,
                            [(0, 500), (200, 300), (400, 380), (600, 310),
                             (800, 400), (1000, 350), (WIDTH, 450),
                             (WIDTH, 500), (0, 500)])
        pygame.draw.polygon(screen, COLOR_MOUNTAIN_FAR,
                            [(0, 450), (150, 350), (350, 400), (550, 340),
                             (750, 420), (950, 380), (WIDTH, 480),
                             (WIDTH, 500), (0, 500)])

        # Ice surface
        ice_rect = pygame.Rect(0, 500, WIDTH, 100)
        draw_gradient_rect(screen, COLOR_ICE_SURFACE, (200, 220, 240), ice_rect)

        # Draw the destination igloo on the ice
        igloo_x = WIDTH - 200  # Adjusted for larger igloo
        igloo_y = 500  # Positioned on the ice surface line
        draw_igloo(screen, igloo_x, igloo_y)

        # Water
        water_rect = pygame.Rect(0, 600, WIDTH, HEIGHT - 600)
        draw_gradient_rect(screen, COLOR_WATER, COLOR_WATER_DEEP, water_rect)

        # Ice edge
        pygame.draw.line(screen, WHITE, (0, 500), (WIDTH, 500), 3)
        pygame.draw.line(screen, COLOR_WATER_HIGHLIGHT, (0, 600), (WIDTH, 600), 4)

        # Fishing hole (scaled up from 80x40 to 130x65)
        hole_rect = pygame.Rect(self.fishing_hole_x - 65, self.fishing_hole_y - 33, 130, 65)
        pygame.draw.ellipse(screen, COLOR_WATER_DEEP, hole_rect)
        pygame.draw.ellipse(screen, COLOR_WATER, hole_rect, 5)

        # Ice crack if fallen
        if self.sled_fallen:
            crack_x = WIDTH // 2
            crack_y = 520
            draw_ice_crack(screen, crack_x, crack_y)

            # Hole in ice (scaled up)
            hole_rect = pygame.Rect(crack_x - 95, crack_y - 50, 190, 100)
            pygame.draw.ellipse(screen, COLOR_WATER_DEEP, hole_rect)

    def draw_ui(self):
        # Main UI Panel
        panel_rect = pygame.Rect(30, 30, 350, 140)
        panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*COLOR_UI_BG, 200), panel_surf.get_rect(), border_radius=15)
        screen.blit(panel_surf, panel_rect)
        pygame.draw.rect(screen, COLOR_UI_ACCENT, panel_rect, 3, border_radius=15)

        # Fish icon (scaled up)
        pygame.draw.ellipse(screen, COLOR_FISH_BLUE, (55, 50, 48, 24))
        pygame.draw.polygon(screen, COLOR_FISH_BLUE, [(103, 62), (115, 50), (115, 74)])

        # Fish count
        fish_text = font.render(f"On Sled: {self.fish_count}/{MAX_FISH}", True, COLOR_UI_TEXT)
        screen.blit(fish_text, (100, 45))

        # Banked icon
        pygame.draw.rect(screen, COLOR_UI_ACCENT, (55, 100, 20, 25))

        # Banked count
        total_points = self.total_fish_banked * POINTS_PER_FISH
        banked_text = font.render(f"Banked: {total_points} cents", True, COLOR_UI_TEXT)
        screen.blit(banked_text, (100, 105))

        # Trial counter
        trial_panel_rect = pygame.Rect(WIDTH - 250, 30, 220, 80)
        trial_panel_surf = pygame.Surface(trial_panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(trial_panel_surf, (*COLOR_UI_BG, 200), trial_panel_surf.get_rect(), border_radius=15)
        screen.blit(trial_panel_surf, trial_panel_rect)
        pygame.draw.rect(screen, COLOR_UI_ACCENT, trial_panel_rect, 3, border_radius=15)

        trial_text = large_font.render(f"Trial {self.trial}/{TOTAL_TRIALS}", True, COLOR_UI_TEXT)
        screen.blit(trial_text, trial_text.get_rect(center=trial_panel_rect.center))

        # Feedback message
        if self.show_feedback:
            if self.success:
                msg = f"Success! Delivered {self.fish_count} fish ({self.fish_count * POINTS_PER_FISH} cents)"
                msg_color = COLOR_UI_TEXT_GOOD
                bg_color = COLOR_BUTTON_FISH
            else:
                msg = f"Ice broke! Lost {self.fish_count} fish"
                msg_color = COLOR_UI_TEXT_BAD
                bg_color = COLOR_DANGER_HIGH

            msg_surf = large_font.render(msg, True, COLOR_UI_TEXT)
            msg_rect = msg_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))

            # Background panel
            bg_rect = msg_rect.inflate(80, 40)
            panel_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (*bg_color[:3], 200), panel_surf.get_rect(), border_radius=20)
            screen.blit(panel_surf, bg_rect)
            pygame.draw.rect(screen, WHITE, bg_rect, 4, border_radius=20)

            screen.blit(msg_surf, msg_rect)

    def draw_menu(self):
        self.draw_background()

        # Snow
        for snow in self.snow_particles:
            pygame.draw.circle(screen, WHITE,
                               (int(snow["x"]), int(snow["y"])), int(snow["size"]))

        # Title panel
        title_panel_rect = pygame.Rect(WIDTH // 2 - 350, 80, 700, 180)
        draw_gradient_rect(screen, COLOR_UI_BG_LIGHT, COLOR_UI_BG, title_panel_rect)
        pygame.draw.rect(screen, COLOR_UI_ACCENT, title_panel_rect, 4, border_radius=20)

        # Title
        title_shadow = huge_font.render("Penguin Fishing", True, (0, 0, 0, 128))
        title = huge_font.render("Penguin Fishing", True, COLOR_UI_TEXT)
        screen.blit(title_shadow, title_shadow.get_rect(center=(WIDTH // 2 + 3, 140 + 3)))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 140)))

        subtitle = large_font.render("A Risk Assessment Game", True, COLOR_UI_ACCENT)
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 200)))

        # Instructions panel
        inst_panel_rect = pygame.Rect(WIDTH // 2 - 400, 300, 800, 350)
        inst_panel_surf = pygame.Surface(inst_panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(inst_panel_surf, (*COLOR_UI_BG, 180), inst_panel_surf.get_rect(), border_radius=20)
        screen.blit(inst_panel_surf, inst_panel_rect)
        pygame.draw.rect(screen, WHITE, inst_panel_rect, 3, border_radius=20)

        # Instructions
        instructions = [
            ("🐟", "Click 'Catch Fish' to add fish to your sled"),
            ("📈", f"Each fish is worth {POINTS_PER_FISH} cents"),
            ("⚠️", "More fish = higher risk of ice breaking!"),
            ("🛷", "Click 'Send Sled' to cross the ice"),
            ("🎯", f"Complete {TOTAL_TRIALS} trials to finish"),
            ("💡", "Find the balance between risk and reward!")
        ]

        y = 340
        for icon, text in instructions:
            text_surf = font.render(f"{icon}  {text}", True, COLOR_UI_TEXT)
            screen.blit(text_surf, text_surf.get_rect(center=(WIDTH // 2, y)))
            y += 50

        # Penguin decoration (adjusted for new size)
        draw_penguin(screen, WIDTH // 2 - 40, 230, "stand")

        self.start_button.draw(screen)

    def draw_results(self):
        # Background overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_gradient_rect(overlay, (*COLOR_UI_BG, 220), (*COLOR_UI_BG, 180), overlay.get_rect())
        screen.blit(overlay, (0, 0))

        # Results panel
        panel_rect = pygame.Rect(WIDTH // 2 - 450, 50, 900, 650)
        draw_gradient_rect(screen, COLOR_UI_BG_LIGHT, COLOR_UI_BG, panel_rect)
        pygame.draw.rect(screen, COLOR_UI_ACCENT, panel_rect, 5, border_radius=30)

        # Title
        if test_mode:
            title = huge_font.render("Test Complete!", True, COLOR_UI_ACCENT)
        else:
            title = huge_font.render("Experiment Complete!", True, COLOR_UI_ACCENT)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 120)))

        # Final score
        total_points = self.total_fish_banked * POINTS_PER_FISH
        score_text = large_font.render(f"Total Points: {total_points} cents", True, COLOR_UI_TEXT)
        screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, 220)))

        fish_text = font.render(f"Total Fish Banked: {self.total_fish_banked}", True, COLOR_UI_TEXT)
        screen.blit(fish_text, fish_text.get_rect(center=(WIDTH // 2, 280)))

        if test_mode:
            info_text = small_font.render("This was a test run - no data was saved.", True, COLOR_UI_TEXT)
        else:
            info_text = small_font.render("Data has been saved to the database.", True, COLOR_UI_TEXT)
        screen.blit(info_text, info_text.get_rect(center=(WIDTH // 2, 350)))

        # Exit instruction
        exit_text = font.render("Press ESC to exit.", True, COLOR_UI_TEXT)
        screen.blit(exit_text, exit_text.get_rect(center=(WIDTH // 2, HEIGHT - 100)))

    def draw_play(self):
        self.draw_background()

        # Snow
        for snow in self.snow_particles:
            pygame.draw.circle(screen, WHITE,
                               (int(snow["x"]), int(snow["y"])), int(snow["size"]))

        # Draw clouds
        for cloud in self.clouds:
            cloud.draw(screen)

        # Draw birds
        for bird in self.birds:
            wing_offset = math.sin(bird['flap']) * 5
            pygame.draw.lines(screen, (50, 50, 50), False, [
                (bird['x'] - 10, bird['y'] + wing_offset), (bird['x'], bird['y']),
                (bird['x'] + 10, bird['y'] + wing_offset)
            ], 2)

        # Draw sled
        draw_sled(screen, self.sled_x, self.sled_y, self.fish_positions, self.sled_fallen)

        # Draw penguin
        if self.penguin_state == "fish":
            fishing_hole_center = (self.fishing_hole_x, self.fishing_hole_y)
            draw_penguin(screen, self.penguin_x, self.penguin_y, "fish", fishing_hole_center)
        else:
            draw_penguin(screen, self.penguin_x, self.penguin_y, self.penguin_state)

        # Draw the pulling rope if the sled is moving
        if self.moving and not self.sled_fallen:
            rope_color = COLOR_SLED_DARK
            # Anchor point on the penguin's side
            penguin_anchor = (self.penguin_x + 8, self.penguin_y + 72)
            # Anchor point on the front of the sled
            sled_anchor = (self.sled_x + 85, self.sled_y - 16)
            pygame.draw.line(screen, rope_color, penguin_anchor, sled_anchor, 6)

        # Draw flying fish
        for fish in self.flying_fish:
            fish.draw(screen)

        # Draw particles
        for particle in self.particles:
            particle.draw(screen)

        # Draw UI
        self.draw_ui()

        # Draw buttons
        if not self.moving and not self.show_feedback:
            if self.fish_count < MAX_FISH:
                self.fish_button.draw(screen)
            if self.fish_count > 0:
                self.send_sled_button.draw(screen)

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "play":
            self.draw_play()
        elif self.state == "results":
            self.draw_results()


def main():
    game = PenguinGame()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game.state == "menu":
                    if game.start_button.is_clicked(mouse_pos):
                        game.state = "play"
                        game.reset_trial()
                elif game.state == "play":
                    if not game.moving and not game.show_feedback:
                        if game.fish_count < MAX_FISH and game.fish_button.is_clicked(mouse_pos):
                            game.catch_fish()
                        elif game.fish_count > 0 and game.send_sled_button.is_clicked(mouse_pos):
                            game.send_sled()
                elif game.state == "results":
                    if game.play_again_button.is_clicked(mouse_pos):
                        game = PenguinGame()
                        game.state = "play"
                    elif game.quit_button.is_clicked(mouse_pos):
                        running = False
            elif event.type == pygame.MOUSEBUTTONUP:
                # Release all buttons
                game.start_button.release()
                game.fish_button.release()
                game.send_sled_button.release()
                game.play_again_button.release()
                game.quit_button.release()

        # Update hover states
        if game.state == "menu":
            game.start_button.check_hover(mouse_pos)
        elif game.state == "play":
            if not game.moving and not game.show_feedback:
                if game.fish_count < MAX_FISH:
                    game.fish_button.check_hover(mouse_pos)
                if game.fish_count > 0:
                    game.send_sled_button.check_hover(mouse_pos)
        elif game.state == "results":
            game.play_again_button.check_hover(mouse_pos)
            game.quit_button.check_hover(mouse_pos)

        game.update()
        screen.fill(COLOR_BACKGROUND_GRADIENT_START)
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

    # Close database connection
    db_manager.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()