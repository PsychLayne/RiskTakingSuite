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

# Import the unified config loader
sys.path.insert(0, str(Path(__file__).parent))
from task_config_loader import load_task_config

# Initialize pygame
pygame.init()

# Load configuration using unified loader
config, task_config, exp_config = load_task_config('ice_fishing')

# Extract experiment-level settings
TOTAL_TRIALS = exp_config.get('total_trials_per_task', 30)

# Check if we're in test mode
test_mode = os.environ.get('TEST_MODE', 'false').lower() == 'true'

# Task-specific constants from config
MAX_FISH = task_config.get('max_fish', 64)
POINTS_PER_FISH = task_config.get('points_per_fish', 5)

# Display settings from config
fullscreen_mode = config.get('display', {}).get('fullscreen', True)

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

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
COLOR_ICE_SHARD = (200, 230, 255)
COLOR_ICE_CRACK = (150, 180, 200)
COLOR_WATER_FOAM = (245, 250, 255)

# ICE_LEVEL is now at the middle of the screen
ICE_LEVEL = HEIGHT // 2


class IceShard:
    """Flying ice debris from breaking ice"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-12, -4)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-15, 15)
        self.size = random.randint(15, 40)
        self.gravity = 0.5
        self.life = 120

        # Create random polygon shape
        self.points = []
        vertices = random.randint(4, 7)
        for i in range(vertices):
            angle = (i / vertices) * math.pi * 2 + random.uniform(-0.3, 0.3)
            radius = self.size * random.uniform(0.7, 1.0)
            px = radius * math.cos(angle)
            py = radius * math.sin(angle)
            self.points.append((px, py))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.rotation += self.rotation_speed
        self.life -= 1

        # Slow down horizontal movement
        self.vx *= 0.98

        # Float on water surface
        if self.y > ICE_LEVEL + 50:
            self.y = ICE_LEVEL + 50
            self.vy *= -0.3
            self.rotation_speed *= 0.9

    def draw(self, surface):
        if self.life <= 0:
            return

        # Calculate alpha based on life
        alpha = min(255, self.life * 2)

        # Transform points based on rotation
        cos_r = math.cos(math.radians(self.rotation))
        sin_r = math.sin(math.radians(self.rotation))

        transformed_points = []
        for px, py in self.points:
            tx = px * cos_r - py * sin_r + self.x
            ty = px * sin_r + py * cos_r + self.y
            transformed_points.append((tx, ty))

        # Draw ice shard with transparency
        if len(transformed_points) >= 3:
            # Main body
            pygame.draw.polygon(surface, COLOR_ICE_SHARD, transformed_points)
            # Outline
            pygame.draw.polygon(surface, COLOR_ICE_CRACK, transformed_points, 2)

            # Highlight on one edge
            if len(transformed_points) > 2:
                highlight_points = [transformed_points[0], transformed_points[1],
                                    ((transformed_points[0][0] + transformed_points[1][0]) / 2,
                                     (transformed_points[0][1] + transformed_points[1][1]) / 2 - 5)]
                pygame.draw.polygon(surface, WHITE, highlight_points)


class WaterRipple:
    """Expanding ripple effect on water"""

    def __init__(self, x, y, initial_radius=10, max_radius=200, speed=2):
        self.x = x
        self.y = y
        self.radius = initial_radius
        self.max_radius = max_radius
        self.speed = speed
        self.life = 255

    def update(self):
        self.radius += self.speed
        self.life = max(0, 255 - (self.radius / self.max_radius) * 255)

    def draw(self, surface):
        if self.life > 0 and self.radius < self.max_radius:
            # Draw multiple concentric circles for ripple effect
            for i in range(3):
                radius = self.radius - i * 15
                if radius > 0:
                    alpha = self.life * (1 - i * 0.3)
                    color = (*COLOR_WATER_HIGHLIGHT, int(alpha))
                    pygame.draw.circle(surface, color, (int(self.x), int(self.y)),
                                       int(radius), max(1, 3 - i))


class SwimmingFish:
    """Fish swimming underwater"""

    def __init__(self):
        self.reset()

    def reset(self):
        # Start from either left or right edge
        if random.choice([True, False]):
            self.x = -50
            self.direction = 1
        else:
            self.x = WIDTH + 50
            self.direction = -1

        # Random depth below ice
        self.y = ICE_LEVEL + random.randint(50, HEIGHT - ICE_LEVEL - 100)
        self.speed = random.uniform(1, 3) * self.direction
        self.color = random.choice([COLOR_FISH_SILVER, COLOR_FISH_BLUE, COLOR_FISH_ORANGE])
        self.size = random.randint(20, 35)
        self.wobble = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(0.05, 0.1)
        self.wobble_amplitude = random.uniform(5, 15)
        self.scared = False
        self.scare_timer = 0

    def scare(self):
        """Make fish swim away quickly"""
        self.scared = True
        self.scare_timer = 60
        self.speed *= 3

    def update(self):
        if self.scared:
            self.scare_timer -= 1
            if self.scare_timer <= 0:
                self.scared = False
                self.speed /= 3

        self.x += self.speed
        self.wobble += self.wobble_speed

        # Reset when off screen
        if (self.direction > 0 and self.x > WIDTH + 50) or (self.direction < 0 and self.x < -50):
            self.reset()

    def draw(self, surface):
        # Calculate wobble offset
        y_offset = math.sin(self.wobble) * self.wobble_amplitude
        draw_y = self.y + y_offset

        # Fish body
        body_width = self.size
        body_height = self.size // 2
        body_rect = pygame.Rect(self.x - body_width // 2, draw_y - body_height // 2,
                                body_width, body_height)
        pygame.draw.ellipse(surface, self.color, body_rect)

        # Tail
        if self.direction > 0:
            tail_x = self.x - body_width // 2
        else:
            tail_x = self.x + body_width // 2

        tail_points = [
            (tail_x, draw_y),
            (tail_x - self.direction * self.size // 3, draw_y - self.size // 4),
            (tail_x - self.direction * self.size // 3, draw_y + self.size // 4)
        ]
        pygame.draw.polygon(surface, self.color, tail_points)

        # Eye
        eye_x = self.x + self.direction * self.size // 4
        pygame.draw.circle(surface, WHITE, (int(eye_x), int(draw_y)), 3)
        pygame.draw.circle(surface, BLACK, (int(eye_x), int(draw_y)), 2)


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


class EscapingFish:
    """Fish escaping from the fallen sled"""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(20, 30)

        # Random escape direction with slight bias away from center
        center_x = WIDTH // 2
        if x < center_x:
            angle = random.uniform(math.pi * 0.5, math.pi * 1.5)  # Tend to go left
        else:
            angle = random.uniform(-math.pi * 0.5, math.pi * 0.5)  # Tend to go right

        # Add some randomness
        angle += random.uniform(-0.5, 0.5)

        speed = random.uniform(4, 7)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 3  # Initial upward burst

        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-25, 25)
        self.wobble = random.uniform(0, math.pi * 2)
        self.wobble_speed = 0.3
        self.life = 300  # How long before they become regular swimming fish
        self.panic_mode = True

    def update(self):
        # Update position
        self.x += self.vx
        self.y += self.vy

        # Apply gravity/buoyancy
        if self.y < ICE_LEVEL + 60:
            self.vy += 0.4  # Gravity pulls down
        else:
            self.vy *= 0.92  # Water resistance
            if self.panic_mode and self.life < 200:
                self.panic_mode = False
                # Slow down and pick a horizontal direction
                self.vx = random.choice([-2.5, 2.5])
                self.vy *= 0.3

        # Wobble motion
        self.wobble += self.wobble_speed
        self.rotation += self.rotation_speed

        # Gradually slow rotation
        self.rotation_speed *= 0.97

        self.life -= 1

        # Keep fish in water
        if self.y < ICE_LEVEL + 50:
            self.y = ICE_LEVEL + 50
            self.vy = abs(self.vy) * 0.5

    def draw(self, surface):
        # Calculate wobble offset
        y_offset = math.sin(self.wobble) * 5 if not self.panic_mode else 0
        draw_y = self.y + y_offset

        # Draw rotated fish
        angle_rad = math.radians(self.rotation)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Fish body
        body_width = self.size
        body_height = self.size // 2

        # Create rotated rectangle points
        corners = [
            (-body_width / 2, -body_height / 2),
            (body_width / 2, -body_height / 2),
            (body_width / 2, body_height / 2),
            (-body_width / 2, body_height / 2)
        ]

        rotated_corners = []
        for cx, cy in corners:
            rx = cx * cos_a - cy * sin_a + self.x
            ry = cx * sin_a + cy * cos_a + draw_y
            rotated_corners.append((rx, ry))

        # Draw body
        if len(rotated_corners) >= 3:
            pygame.draw.polygon(surface, self.color, rotated_corners)

        # Tail
        tail_base_x = -body_width / 2
        tail_tip_x = -body_width / 2 - self.size / 3
        tail_y1 = -self.size / 4
        tail_y2 = self.size / 4

        # Rotate tail points
        tail_points = []
        for tx, ty in [(tail_base_x, 0), (tail_tip_x, tail_y1), (tail_tip_x, tail_y2)]:
            rx = tx * cos_a - ty * sin_a + self.x
            ry = tx * sin_a + ty * cos_a + draw_y
            tail_points.append((rx, ry))

        pygame.draw.polygon(surface, self.color, tail_points)

        # Eye (simplified for rotation)
        eye_x = self.x + body_width / 4 * cos_a
        eye_y = draw_y + body_width / 4 * sin_a
        pygame.draw.circle(surface, WHITE, (int(eye_x), int(eye_y)), 3)
        pygame.draw.circle(surface, BLACK, (int(eye_x), int(eye_y)), 2)


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

    # Feet (scaled up) - animate for walking
    foot_base_y = y + 109
    if state == "walk":
        # Animated walking feet
        walk_offset = math.sin(animation_timer * 0.01) * 10
        pygame.draw.ellipse(surface, COLOR_PENGUIN_BEAK_FEET,
                            (x + 6 + walk_offset, foot_base_y, 32, 19))
        pygame.draw.ellipse(surface, COLOR_PENGUIN_BEAK_FEET,
                            (x + 42 - walk_offset, foot_base_y, 32, 19))
    else:
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
        # Normal flippers - animate for walking
        if state == "walk":
            flipper_swing = math.sin(animation_timer * 0.01) * 15
            # Left flipper
            pygame.draw.ellipse(surface, COLOR_PENGUIN_BODY,
                                (x - 8 - flipper_swing / 2, y + 56, 19, 40))
            # Right flipper
            pygame.draw.ellipse(surface, COLOR_PENGUIN_BODY,
                                (x + 69 + flipper_swing / 2, y + 56, 19, 40))
        else:
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


def draw_sled(surface, x, y, fish_positions, fallen=False, fall_progress=0):
    """Draw sled with visible fish stack"""
    sled_width = 200  # Scaled up from 130
    sled_height = 110  # Scaled up from 70

    if fallen:
        # Sinking animation
        sink_depth = fall_progress * 100
        rotation = math.sin(fall_progress * 3) * 15  # Wobble while sinking

        # Draw sled underwater with rotation
        sled_y = y + sink_depth

        # Create rotated sled shape
        cos_r = math.cos(math.radians(rotation))
        sin_r = math.sin(math.radians(rotation))

        # Sled corners (relative to center)
        corners = [
            (-sled_width / 2, -sled_height / 2),
            (sled_width / 2, -sled_height / 2),
            (sled_width / 2, sled_height / 2),
            (-sled_width / 2, sled_height / 2)
        ]

        # Transform corners
        transformed = []
        for cx, cy in corners:
            tx = cx * cos_r - cy * sin_r + x
            ty = cx * sin_r + cy * cos_r + sled_y
            transformed.append((tx, ty))

        # Draw sinking sled (empty - fish have escaped)
        pygame.draw.polygon(surface, COLOR_SLED_BODY, transformed)
        pygame.draw.polygon(surface, COLOR_SLED_DARK, transformed, 5)
    else:
        # Normal sled
        sled_draw_y = y - sled_height / 2

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


def draw_ice_crack(surface, x, y, severity=1.0):
    """Draw animated cracks in ice"""
    # Main crack pattern
    num_cracks = int(12 * severity)
    for i in range(num_cracks):
        angle = (i / num_cracks) * math.pi * 2 + random.uniform(-0.2, 0.2)
        length = random.randint(60, 120) * severity

        # Multi-segment crack for more realistic look
        segments = random.randint(2, 4)
        current_x, current_y = x, y

        for seg in range(segments):
            seg_length = length / segments
            seg_angle = angle + random.uniform(-0.3, 0.3)
            end_x = current_x + math.cos(seg_angle) * seg_length
            end_y = current_y + math.sin(seg_angle) * seg_length

            # Main crack line
            pygame.draw.line(surface, COLOR_ICE_CRACK,
                             (current_x, current_y), (int(end_x), int(end_y)),
                             int(5 * severity))

            # Secondary crack lines
            if random.random() < 0.3:
                branch_angle = seg_angle + random.choice([-1, 1]) * random.uniform(0.5, 1.0)
                branch_length = seg_length * 0.5
                branch_x = current_x + math.cos(branch_angle) * branch_length
                branch_y = current_y + math.sin(branch_angle) * branch_length
                pygame.draw.line(surface, COLOR_ICE_CRACK,
                                 (current_x, current_y), (int(branch_x), int(branch_y)), 2)

            current_x, current_y = end_x, end_y


def draw_igloo(surface, x, y):
    """Draws an improved igloo with ice blocks."""
    igloo_color = (230, 250, 255)
    igloo_shadow = (200, 220, 240)
    igloo_outline = (180, 200, 220)
    block_outline = (210, 230, 250)

    # Main dome shape
    dome_rect = pygame.Rect(x - 160, y - 130, 320, 190)
    pygame.draw.ellipse(surface, igloo_color, dome_rect)

    # Draw ice block pattern
    block_height = 20
    for row in range(6):
        y_pos = y - 10 - row * block_height
        # Calculate the width of the igloo at this height
        height_ratio = (row * block_height + 10) / 130
        width_at_height = 320 * math.sqrt(1 - height_ratio * height_ratio)

        if width_at_height > 0:
            # Draw blocks for this row
            block_width = 40
            num_blocks = int(width_at_height / block_width)
            start_x = x - width_at_height / 2

            for block in range(num_blocks):
                block_x = start_x + block * block_width
                # Add slight offset for every other row
                if row % 2 == 1:
                    block_x += block_width / 2

                # Only draw if block is within dome bounds
                if block_x > x - 160 and block_x + block_width < x + 160:
                    block_rect = pygame.Rect(block_x, y_pos - block_height, block_width, block_height)
                    pygame.draw.rect(surface, block_outline, block_rect, 1)

    # Dome outline
    pygame.draw.ellipse(surface, igloo_outline, dome_rect, 5)

    # Dark entrance
    entrance_width = 70
    entrance_height = 50
    entrance_rect = pygame.Rect(x - entrance_width // 2, y - entrance_height, entrance_width, entrance_height)

    # Entrance tunnel depth
    for i in range(5):
        depth_color = (20 + i * 10, 20 + i * 10, 30 + i * 10)
        depth_rect = pygame.Rect(
            x - entrance_width // 2 + i * 2,
            y - entrance_height + i,
            entrance_width - i * 4,
            entrance_height - i
        )
        pygame.draw.ellipse(surface, depth_color, depth_rect)

    # Final dark entrance
    pygame.draw.ellipse(surface, BLACK, entrance_rect)

    # Small flag on top
    flag_pole_bottom = (x, y - 130)
    flag_pole_top = (x, y - 160)
    pygame.draw.line(surface, COLOR_SLED_DARK, flag_pole_bottom, flag_pole_top, 3)

    # Flag
    flag_points = [
        (x, y - 160),
        (x + 25, y - 150),
        (x, y - 140)
    ]
    pygame.draw.polygon(surface, COLOR_UI_TEXT_BAD, flag_points)


class PenguinGame:
    def __init__(self):
        self.state = "menu"
        # Adjusted positions for ice at middle of screen
        self.penguin_x = 400
        self.penguin_y = ICE_LEVEL - 130  # Penguin stands on ice
        self.penguin_state = "stand"
        self.sled_x = 200
        self.sled_y = ICE_LEVEL - 40  # Sled sits on ice
        self.sled_fallen = False
        self.fall_progress = 0
        self.penguin_shock_timer = 0

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
        self.ice_shards = []
        self.water_ripples = []
        self.escaping_fish = []
        self.screen_shake = 0
        self.crack_severity = 0
        self.initialize_snow()

        # Initialize swimming fish
        self.swimming_fish = [SwimmingFish() for _ in range(8)]

        # Pre-determine "explosion points" for all trials (selection without replacement)
        self.explosion_points = []
        self.generate_explosion_points()

        # Fishing hole position (adjusted for ice at middle)
        self.fishing_hole_x = 550
        self.fishing_hole_y = ICE_LEVEL + 50

        # Buttons moved to bottom left
        button_x = 50
        button_y = HEIGHT - 150
        self.fish_button = Button(button_x, button_y, 200, 60, "Catch Fish",
                                  COLOR_BUTTON_FISH, COLOR_BUTTON_FISH_HOVER)
        self.send_sled_button = Button(button_x, button_y + 70, 200, 60, "Send Sled",
                                       COLOR_BUTTON_SEND, COLOR_BUTTON_SEND_HOVER)

        self.start_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 200,
                                   200, 60, "Start Game")
        self.play_again_button = Button(WIDTH // 2 - 250, HEIGHT - 120,
                                        200, 60, "Play Again")
        self.quit_button = Button(WIDTH // 2 + 50, HEIGHT - 120,
                                  200, 60, "Quit", COLOR_UI_TEXT_BAD, (255, 120, 120))

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

    def trigger_ice_break(self):
        """Trigger the dramatic ice breaking animation"""
        self.sled_fallen = True
        self.show_feedback = True
        self.feedback_timer = 180  # Longer timer for more dramatic effect
        self.screen_shake = 30
        self.crack_severity = 0

        # Make penguin jump back in shock
        self.penguin_shock_timer = 60
        self.penguin_state = "shock"

        # Create escaping fish from the sled
        sled_draw_y = self.sled_y - 110 / 2  # Account for sled height
        for fx, fy, color in self.fish_positions:
            # Calculate actual position of fish on sled
            fish_x = self.sled_x + fx
            fish_y = sled_draw_y + 70 + fy  # Match the draw_fish_on_sled offset
            self.escaping_fish.append(EscapingFish(fish_x, fish_y, color))

        # Scare nearby swimming fish
        impact_x = self.sled_x
        for fish in self.swimming_fish:
            if abs(fish.x - impact_x) < 300:
                fish.scare()

        # Create ice shards
        for _ in range(20):
            self.ice_shards.append(IceShard(self.sled_x, ICE_LEVEL))

        # Create initial splash
        for _ in range(50):
            dx = random.uniform(-15, 15)
            dy = random.uniform(-20, -5)
            size = random.randint(5, 15)
            self.particles.append(
                Particle(self.sled_x, ICE_LEVEL + 30,
                         dx, dy, COLOR_WATER_HIGHLIGHT, 80, size)
            )

        # Create foam particles
        for _ in range(30):
            dx = random.uniform(-10, 10)
            dy = random.uniform(-5, 5)
            self.particles.append(
                Particle(self.sled_x, ICE_LEVEL + 40,
                         dx, dy, COLOR_WATER_FOAM, 100, random.randint(8, 20))
            )

        # Create ripples
        self.water_ripples.append(WaterRipple(self.sled_x, ICE_LEVEL + 50, 20, 300, 4))
        self.water_ripples.append(WaterRipple(self.sled_x, ICE_LEVEL + 50, 10, 200, 3))

    def update(self):
        self.update_snow()

        # Update swimming fish
        for fish in self.swimming_fish:
            fish.update()

        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)

        # Update ice shards
        for shard in self.ice_shards[:]:
            shard.update()
            if shard.life <= 0:
                self.ice_shards.remove(shard)

        # Update water ripples
        for ripple in self.water_ripples[:]:
            ripple.update()
            if ripple.life <= 0:
                self.water_ripples.remove(ripple)

        # Update escaping fish
        for fish in self.escaping_fish[:]:
            fish.update()
            if fish.life <= 0:
                # Convert to regular swimming fish
                new_fish = SwimmingFish()
                new_fish.x = fish.x
                new_fish.y = fish.y
                new_fish.color = fish.color
                new_fish.direction = 1 if fish.vx > 0 else -1
                new_fish.speed = abs(fish.vx)
                self.swimming_fish.append(new_fish)
                self.escaping_fish.remove(fish)

        # Update screen shake
        if self.screen_shake > 0:
            self.screen_shake -= 1

        # Update crack severity
        if self.sled_fallen and self.crack_severity < 1.0:
            self.crack_severity = min(1.0, self.crack_severity + 0.05)

        # Update fall progress
        if self.sled_fallen:
            self.fall_progress = min(1.0, self.fall_progress + 0.02)

            # Create bubbles as sled sinks
            if self.fall_progress < 0.8 and random.random() < 0.3:
                bubble_x = self.sled_x + random.uniform(-50, 50)
                bubble_y = self.sled_y + self.fall_progress * 100
                self.particles.append(
                    Particle(bubble_x, bubble_y,
                             random.uniform(-1, 1), -2,
                             COLOR_WATER_FOAM, 60, random.randint(3, 8))
                )

        # Update penguin shock animation
        if self.penguin_shock_timer > 0:
            self.penguin_shock_timer -= 1
            # Move penguin backwards
            if self.penguin_shock_timer > 40:
                self.penguin_x = max(100, self.penguin_x - 8)
            # Return to normal state when done
            if self.penguin_shock_timer == 0:
                self.penguin_state = "stand"

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
            elif not self.sled_fallen:
                # Stop moving if reached destination
                self.moving = False

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
                self.trigger_ice_break()
                self.moving = False  # Stop movement when ice breaks

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

    def reset_trial(self):
        self.penguin_x = 400
        self.penguin_y = ICE_LEVEL - 130
        self.penguin_state = "stand"
        self.sled_x = 200
        self.sled_y = ICE_LEVEL - 40
        self.sled_fallen = False
        self.fall_progress = 0
        self.penguin_shock_timer = 0
        self.fish_count = 0
        self.fish_positions = []
        self.flying_fish = []
        self.moving = False
        self.success = None
        self.particles = []
        self.ice_shards = []
        self.water_ripples = []
        self.escaping_fish = []
        self.screen_shake = 0
        self.crack_severity = 0
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
        # Apply screen shake
        shake_x = 0
        shake_y = 0
        if self.screen_shake > 0:
            shake_x = random.randint(-self.screen_shake, self.screen_shake)
            shake_y = random.randint(-self.screen_shake, self.screen_shake)

        # Create a surface for the background that we can shake
        bg_surface = pygame.Surface((WIDTH, HEIGHT))

        # Sky gradient (upper half)
        for y in range(ICE_LEVEL):
            progress = y / ICE_LEVEL
            r = int(COLOR_BACKGROUND_GRADIENT_START[0] +
                    (COLOR_BACKGROUND_GRADIENT_END[0] - COLOR_BACKGROUND_GRADIENT_START[0]) * progress)
            g = int(COLOR_BACKGROUND_GRADIENT_START[1] +
                    (COLOR_BACKGROUND_GRADIENT_END[1] - COLOR_BACKGROUND_GRADIENT_START[1]) * progress)
            b = int(COLOR_BACKGROUND_GRADIENT_START[2] +
                    (COLOR_BACKGROUND_GRADIENT_END[2] - COLOR_BACKGROUND_GRADIENT_START[2]) * progress)
            pygame.draw.line(bg_surface, (r, g, b), (0, y), (WIDTH, y))

        # Mountains (adjusted to be above ice line)
        mountain_base = ICE_LEVEL - 50
        pygame.draw.polygon(bg_surface, COLOR_MOUNTAIN_FAR,
                            [(0, mountain_base), (200, mountain_base - 200), (400, mountain_base - 120),
                             (600, mountain_base - 190), (800, mountain_base - 100), (1000, mountain_base - 150),
                             (WIDTH, mountain_base - 50), (WIDTH, mountain_base), (0, mountain_base)])

        # Ice surface (thin strip at middle)
        ice_rect = pygame.Rect(0, ICE_LEVEL - 50, WIDTH, 100)
        draw_gradient_rect(bg_surface, COLOR_ICE_SURFACE, (200, 220, 240), ice_rect)

        # Draw the destination igloo on the ice
        igloo_x = WIDTH - 200
        igloo_y = ICE_LEVEL
        draw_igloo(bg_surface, igloo_x, igloo_y)

        # Water (lower half)
        water_rect = pygame.Rect(0, ICE_LEVEL + 50, WIDTH, HEIGHT - ICE_LEVEL - 50)
        draw_gradient_rect(bg_surface, COLOR_WATER, COLOR_WATER_DEEP, water_rect)

        # Ice edge
        pygame.draw.line(bg_surface, WHITE, (0, ICE_LEVEL - 50), (WIDTH, ICE_LEVEL - 50), 3)
        pygame.draw.line(bg_surface, COLOR_WATER_HIGHLIGHT, (0, ICE_LEVEL + 50), (WIDTH, ICE_LEVEL + 50), 4)

        # Fishing hole
        hole_rect = pygame.Rect(self.fishing_hole_x - 65, self.fishing_hole_y - 33, 130, 65)
        pygame.draw.ellipse(bg_surface, COLOR_WATER_DEEP, hole_rect)
        pygame.draw.ellipse(bg_surface, COLOR_WATER, hole_rect, 5)

        # Ice crack if fallen
        if self.sled_fallen:
            crack_x = self.sled_x
            crack_y = ICE_LEVEL + 20
            draw_ice_crack(bg_surface, crack_x, crack_y, self.crack_severity)

            # Hole in ice (grows with crack severity)
            hole_size = int(190 * self.crack_severity)
            if hole_size > 0:
                hole_rect = pygame.Rect(crack_x - hole_size // 2, crack_y - hole_size // 4,
                                        hole_size, hole_size // 2)
                pygame.draw.ellipse(bg_surface, COLOR_WATER_DEEP, hole_rect)

                # Jagged ice edges
                num_points = 16
                edge_points = []
                for i in range(num_points):
                    angle = (i / num_points) * math.pi * 2
                    radius = hole_size / 2 + random.randint(-10, 5)
                    px = crack_x + radius * math.cos(angle) * 1.2
                    py = crack_y + radius * math.sin(angle) * 0.6
                    edge_points.append((px, py))

                # Draw white edge highlight
                for i in range(len(edge_points)):
                    p1 = edge_points[i]
                    p2 = edge_points[(i + 1) % len(edge_points)]
                    pygame.draw.line(bg_surface, WHITE, p1, p2, 3)

        # Draw to main screen with shake
        screen.blit(bg_surface, (shake_x, shake_y))

        # Draw swimming fish (not affected by shake)
        for fish in self.swimming_fish:
            fish.draw(screen)

        # Draw escaping fish
        for fish in self.escaping_fish:
            fish.draw(screen)

        # Draw water ripples
        for ripple in self.water_ripples:
            ripple.draw(screen)

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

        # Draw ice shards
        for shard in self.ice_shards:
            shard.draw(screen)

        # Draw sled
        draw_sled(screen, self.sled_x, self.sled_y, self.fish_positions,
                  self.sled_fallen, self.fall_progress)

        # Draw penguin
        if self.penguin_state == "fish":
            fishing_hole_center = (self.fishing_hole_x, self.fishing_hole_y)
            draw_penguin(screen, self.penguin_x, self.penguin_y, "fish", fishing_hole_center)
        elif self.penguin_state == "shock":
            # Draw penguin in shocked pose (leaning back)
            shock_offset = math.sin(self.penguin_shock_timer * 0.3) * 5
            draw_penguin(screen, self.penguin_x, self.penguin_y + shock_offset, "stand")

            # Draw shock effects (exclamation mark)
            if self.penguin_shock_timer > 30:
                exclaim_y = self.penguin_y - 30
                exclaim_x = self.penguin_x + 40
                # Draw exclamation mark
                pygame.draw.line(screen, COLOR_UI_ACCENT,
                                 (exclaim_x, exclaim_y - 20),
                                 (exclaim_x, exclaim_y - 5), 6)
                pygame.draw.circle(screen, COLOR_UI_ACCENT,
                                   (exclaim_x, exclaim_y + 5), 4)

                # Draw sweat drops
                for i in range(3):
                    drop_x = self.penguin_x + 60 + i * 15
                    drop_y = self.penguin_y + 20 + i * 10
                    pygame.draw.circle(screen, COLOR_WATER_HIGHLIGHT,
                                       (drop_x, drop_y), 3)
        else:
            draw_penguin(screen, self.penguin_x, self.penguin_y, self.penguin_state)

        # Draw the pulling rope if the sled is moving and hasn't fallen
        if self.moving and not self.sled_fallen and self.penguin_state != "shock":
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