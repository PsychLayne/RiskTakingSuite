import pygame
import sys
import random
import math
import time
import csv
from pathlib import Path

# Initialize pygame
pygame.init()

# Game dimensions - 1920x1080 (Full HD)
GAME_WIDTH = 1920
GAME_HEIGHT = 1080
FPS = 60
MAX_TRIALS = 30
MAX_ORE = 64

# Enhanced color palette
COLOR_SKY_GRADIENT_TOP = (135, 206, 250)
COLOR_SKY_GRADIENT_MID = (255, 192, 147)
COLOR_SKY_GRADIENT_BOTTOM = (255, 147, 112)
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

# Fullscreen setup
infoObject = pygame.display.Info()
NATIVE_SCREEN_WIDTH = infoObject.current_w
NATIVE_SCREEN_HEIGHT = infoObject.current_h

screen = pygame.display.set_mode((NATIVE_SCREEN_WIDTH, NATIVE_SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SRCALPHA)
game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)

pygame.display.set_caption("Mountain Miner: Risk Assessment")
clock = pygame.time.Clock()

# Fonts
try:
    FONT_FAMILY = "Arial"
    if "Helvetica" in pygame.font.get_fonts():
        FONT_FAMILY = "Helvetica"

    font = pygame.font.SysFont(FONT_FAMILY, 42)
    small_font = pygame.font.SysFont(FONT_FAMILY, 28)
    large_font = pygame.font.SysFont(FONT_FAMILY, 56)
    huge_font = pygame.font.SysFont(FONT_FAMILY, 72, bold=True)
    tiny_font = pygame.font.SysFont(FONT_FAMILY, 20)
except:
    font = pygame.font.SysFont(None, 42)
    small_font = pygame.font.SysFont(None, 28)
    large_font = pygame.font.SysFont(None, 56)
    huge_font = pygame.font.SysFont(None, 72, bold=True)
    tiny_font = pygame.font.SysFont(None, 20)


def scale_surface_keeping_aspect_ratio(surface_to_scale, target_width, target_height):
    original_width, original_height = surface_to_scale.get_size()
    if original_width == 0 or original_height == 0:
        return surface_to_scale, original_width, original_height

    original_aspect_ratio = original_width / original_height
    target_aspect_ratio = target_width / target_height

    if original_aspect_ratio > target_aspect_ratio:
        scaled_width = target_width
        scaled_height = int(target_width / original_aspect_ratio)
    else:
        scaled_height = target_height
        scaled_width = int(target_height * original_aspect_ratio)

    scaled_width = max(1, scaled_width)
    scaled_height = max(1, scaled_height)

    scaled_surface = pygame.transform.smoothscale(surface_to_scale, (scaled_width, scaled_height))
    return scaled_surface, scaled_width, scaled_height


def draw_gradient_rect(surface, color1, color2, rect, vertical=True):
    """Draw a gradient-filled rectangle"""
    if vertical:
        for y in range(rect.height):
            progress = y / rect.height
            r = int(color1[0] + (color2[0] - color1[0]) * progress)
            g = int(color1[1] + (color2[1] - color1[1]) * progress)
            b = int(color1[2] + (color2[2] - color1[2]) * progress)
            pygame.draw.line(surface, (r, g, b), (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))
    else:
        for x in range(rect.width):
            progress = x / rect.width
            r = int(color1[0] + (color2[0] - color1[0]) * progress)
            g = int(color1[1] + (color2[1] - color1[1]) * progress)
            b = int(color1[2] + (color2[2] - color1[2]) * progress)
            pygame.draw.line(surface, (r, g, b), (rect.x + x, rect.y), (rect.x + x, rect.y + rect.height))


class PickaxeCursor:
    def __init__(self):
        self.x, self.y = 0, 0
        self.base_angle = 45
        self.angle = self.base_angle
        self.is_swinging = False
        self.swing_timer = 0
        # MODIFIED: Animation is faster
        self.swing_duration = 15

        # This will store the fixed screen position of the handle pivot during a swing
        self.swing_pivot_pos = None

        # MODIFIED: Larger surface for a bigger cursor
        self.original_image = pygame.Surface((120, 120), pygame.SRCALPHA)

        # Define key points on the original image, which will be set by draw_pickaxe_on_surface
        self.tip_pos = (0, 0)  # The hotspot (active part)
        self.handle_end_pos = (0, 0)  # The pivot point for the swing animation
        self.draw_pickaxe_on_surface(self.original_image)

        # MODIFIED: Center of the new surface is (60, 60)
        # Vector from image center (60,60) to the tip (hotspot for idle state)
        self.hotspot_offset = pygame.math.Vector2(self.tip_pos) - pygame.math.Vector2(60, 60)

        # Vector from image center (60,60) to the handle end (pivot for swing animation)
        self.pivot_offset = pygame.math.Vector2(self.handle_end_pos) - pygame.math.Vector2(60, 60)

        # Vector from the pivot (handle) to the hotspot (tip), used to calculate swing pivot
        self.pivot_to_hotspot_vector = pygame.math.Vector2(self.tip_pos) - pygame.math.Vector2(self.handle_end_pos)

        self.image = self.original_image
        self.rect = self.image.get_rect()

    def draw_pickaxe_on_surface(self, surface):
        """MODIFIED: Draws a larger pickaxe with a solid black border."""
        # Define geometry and colors
        handle_color = (139, 69, 19)
        head_color = (180, 180, 180)
        border_color = (0, 0, 0)

        # Scaled-up dimensions for a larger cursor
        base_width = 12
        border_size = 4  # Results in a 2px border on each side

        # Position and dimensions centered on the new 120x120 surface
        handle_start = (20, 60)
        handle_end = (85, 60)

        # Define the arc for the head
        arc_rect = pygame.Rect(handle_end[0] - (base_width / 2), handle_end[1] - 38, 28, 76)
        start_angle = -math.pi / 2
        stop_angle = math.pi / 2

        # --- Define a nested function to draw components to avoid repetition ---
        def _draw_pick_components(surf, width, h_color, head_c):
            # Draw the handle
            pygame.draw.line(surf, h_color, handle_start, handle_end, width)
            # Draw the head
            pygame.draw.arc(surf, head_c, arc_rect, start_angle, stop_angle, width)
            # Draw the joint connecting them
            pygame.draw.circle(surf, head_c, handle_end, int(width * 0.8))

        # --- Draw the black border first by drawing the components slightly larger ---
        _draw_pick_components(surface, base_width + border_size, border_color, border_color)

        # --- Draw the main colored pickaxe on top ---
        _draw_pick_components(surface, base_width, handle_color, head_color)

        # --- Define key positions for animation and interaction ---
        # The pivot point for the swing animation is the end of the handle
        self.handle_end_pos = handle_start
        # The active part of the cursor (the hotspot) is the tip of the head
        self.tip_pos = (arc_rect.right - (base_width / 2), arc_rect.centery)

    def swing(self):
        """Starts the swinging animation."""
        if not self.is_swinging:
            self.is_swinging = True
            self.swing_timer = self.swing_duration

            # Calculate and fix the screen position for the pivot (handle end) for this swing.
            rotated_vec = self.pivot_to_hotspot_vector.rotate(-self.angle)
            self.swing_pivot_pos = pygame.math.Vector2(self.x, self.y) - rotated_vec

    def update(self, pos):
        """Updates the pickaxe's position and animation state."""
        self.x, self.y = pos

        if self.is_swinging:
            # --- SWINGING LOGIC ---
            self.swing_timer -= 1
            progress = self.swing_timer / self.swing_duration
            swing_arc = math.sin((1 - progress) * math.pi) * 90
            self.angle = self.base_angle - swing_arc

            if self.swing_timer <= 0:
                self.is_swinging = False

            # Rotate the image and position it based on the fixed pivot point.
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            rotated_pivot_offset = self.pivot_offset.rotate(-self.angle)
            self.rect = self.image.get_rect(center=self.swing_pivot_pos - rotated_pivot_offset)
        else:
            # --- IDLE LOGIC ---
            # The pickaxe follows the mouse, with its tip at the cursor.
            self.angle = self.base_angle
            self.image = pygame.transform.rotate(self.original_image, self.angle)
            rotated_hotspot_offset = self.hotspot_offset.rotate(-self.angle)
            self.rect = self.image.get_rect(center=(self.x, self.y) - rotated_hotspot_offset)

    def draw(self, surface):
        """Draws the pickaxe on the main game surface."""
        surface.blit(self.image, self.rect)


class Particle:
    def __init__(self, x, y, dx, dy, color, life, size):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.3  # Gravity
        self.life -= 1
        self.rotation += self.rotation_speed

    def draw(self, surface):
        if self.life > 0:
            alpha = self.life / self.max_life
            size = int(self.size * alpha)
            if size > 0:
                points = []
                for i in range(6):
                    angle = (i * 60 + self.rotation) * math.pi / 180
                    x = self.x + size * math.cos(angle)
                    y = self.y + size * math.sin(angle)
                    points.append((x, y))

                temp_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                poly_points = [(p[0] - self.x + size, p[1] - self.y + size) for p in points]
                pygame.draw.polygon(temp_surf, (*self.color, int(alpha * 255)), poly_points)
                surface.blit(temp_surf, (self.x - size, self.y - size))


class FlyingOreParticle:
    def __init__(self, start_pos, target_pos):
        self.x, self.y = start_pos
        self.start_x, self.start_y = start_pos
        self.target_x, self.target_y = target_pos
        self.color = random.choice([COLOR_ORE_GOLD, COLOR_ORE_SILVER, COLOR_ORE_COPPER])
        self.size = 8
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-15, 15)

        self.progress = 0.0
        self.speed = 0.04

        self.x_dist = self.target_x - self.start_x
        self.y_dist = self.target_y - self.start_y
        self.arc_height = -abs(self.x_dist / 3)

    def update(self):
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 1.0
            return True

        self.x = self.start_x + self.x_dist * self.progress
        arc = 4 * self.arc_height * self.progress * (1 - self.progress)
        self.y = self.start_y + self.y_dist * self.progress + arc
        self.rotation += self.rotation_speed
        return False

    def draw(self, surface):
        points = []
        for i in range(6):
            angle = (i * 60 + self.rotation) * math.pi / 180
            x = self.x + self.size * math.cos(angle)
            y = self.y + self.size * math.sin(angle)
            points.append((x, y))
        pygame.draw.polygon(surface, self.color, points)


class Button:
    def __init__(self, x, y, width, height, text, color=COLOR_BUTTON_NORMAL, hover_color=COLOR_BUTTON_HOVER):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.press_offset = 0

    def draw(self, surface):
        shadow_rect = self.rect.copy()
        shadow_rect.y += 5 + self.press_offset
        pygame.draw.rect(surface, COLOR_BUTTON_SHADOW, shadow_rect, border_radius=15)

        button_rect = self.rect.copy()
        button_rect.y += self.press_offset
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, button_rect, border_radius=15)

        highlight_rect = button_rect.copy()
        highlight_rect.height = 20
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surf, (255, 255, 255, 30), (0, 0, highlight_rect.width, highlight_rect.height),
                         border_radius=15)
        surface.blit(highlight_surf, highlight_rect)

        pygame.draw.rect(surface, WHITE, button_rect, 3, border_radius=15)

        text_shadow = font.render(self.text, True, (0, 0, 0, 128))
        text_surf = font.render(self.text, True, COLOR_UI_TEXT)
        shadow_rect = text_shadow.get_rect(center=(button_rect.centerx + 2, button_rect.centery + 2))
        text_rect = text_surf.get_rect(center=button_rect.center)
        surface.blit(text_shadow, shadow_rect)
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


class Logger:
    def __init__(self):
        self.data = []
        self.start_time = time.time()

    def log_trial(self, trial_num, ore_count, success):
        self.data.append({
            "Trial": trial_num,
            "OreCount": ore_count,
            "Success": success,
            "Timestamp": time.time() - self.start_time
        })

    def save_csv(self):
        if not self.data:
            return "No data logged."

        data_dir = Path("SRET/experiment_data")
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return f"Error creating directory: {e}"

        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        filename = data_dir / f"mountain_miner_{timestamp_str}.csv"

        try:
            with open(filename, 'w', newline='') as f:
                fieldnames = ["Trial", "OreCount", "Success", "Timestamp"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.data)
            return f"Data saved to {filename.resolve()}"
        except Exception as e:
            return f"Error saving data: {e}"


class Cloud:
    def __init__(self):
        self.x = random.randint(-200, GAME_WIDTH + 200)
        self.y = random.randint(50, 300)
        self.speed = random.uniform(0.1, 0.3)
        self.size = random.uniform(0.8, 1.2)
        self.opacity = random.randint(180, 220)

    def update(self):
        self.x += self.speed
        if self.x > GAME_WIDTH + 200:
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


class MountainMinerGame:
    def __init__(self):
        self.state = "menu"
        self.ore_in_bucket = 0
        self.ore_banked = 0
        self.trial = 1
        self.logger = Logger()
        self.bucket_x = 450
        self.bucket_y = 0
        self.bucket_target_x = 1470
        self.bucket_moving = False
        self.bucket_arrived = False
        self.rope_snapped = False
        self.is_falling = False
        self.snap_point = None
        self.particles = []
        self.animation_timer = 0
        self.rope_sway = 0
        self.ore_positions = []
        self.clouds = [Cloud() for _ in range(5)]
        self.birds = []
        # MODIFIED: Move rock left and down
        self.ore_rock_pos = (260, 570)
        # MODIFIED: Make rock larger
        self.ore_rock_rect = pygame.Rect(self.ore_rock_pos[0] - 100, self.ore_rock_pos[1] - 100, 200, 200)
        self.flying_ores = []
        self.pickaxe = PickaxeCursor()
        self.bucket_sway = 0
        self.bucket_sway_angle = 0
        self.rope_start = (450, 340)
        self.rope_end = (1470, 460)
        self.connector_rope_length = 130
        self.rope_y_at_bucket = 0
        self.send_bucket_button = Button(450, 850, 250, 70, "Send Bucket",
                                         COLOR_BUTTON_SEND, COLOR_BUTTON_SEND_HOVER)
        self.play_button = Button(GAME_WIDTH // 2 - 125, GAME_HEIGHT // 2 + 150, 250, 70, "Start Game")
        self.play_again_button = Button(GAME_WIDTH // 2 - 300, GAME_HEIGHT - 150, 250, 70, "Play Again")
        self.quit_button = Button(GAME_WIDTH // 2 + 50, GAME_HEIGHT - 150, 250, 70, "Quit",
                                  COLOR_DANGER_HIGH, (255, 120, 120))
        self.last_result = None
        self.show_feedback = False
        self.feedback_timer = 0
        for _ in range(3):
            self.birds.append({
                'x': random.randint(0, GAME_WIDTH), 'y': random.randint(100, 400),
                'speed': random.uniform(0.5, 1.5), 'flap': 0
            })

    def add_ore(self):
        if (self.ore_in_bucket + len(self.flying_ores)) < MAX_ORE and not self.bucket_moving:
            bucket_top_center = (self.bucket_x, self.bucket_y)
            ore_start_pos = (self.ore_rock_rect.centerx, self.ore_rock_rect.centery - 20)
            new_ore = FlyingOreParticle(ore_start_pos, bucket_top_center)
            self.flying_ores.append(new_ore)
            for _ in range(7):
                dx, dy = random.uniform(-4, 4), random.uniform(-6, -2)
                color = COLOR_MOUNTAIN_DETAIL
                self.particles.append(
                    Particle(self.ore_rock_rect.centerx, self.ore_rock_rect.centery, dx, dy, color, 30,
                             random.randint(3, 6))
                )

    def send_bucket(self):
        if self.ore_in_bucket > 0 and not self.bucket_moving:
            self.bucket_moving = True
            self.bucket_arrived = False
            self.rope_snapped = False
            snap_probability = self.ore_in_bucket / MAX_ORE
            if random.random() < snap_probability:
                self.rope_snapped = True
                self.snap_point = random.uniform(0.2, 0.5)

    def reset_bucket(self):
        self.bucket_x = self.rope_start[0]
        self.bucket_moving = False
        self.bucket_arrived = False
        self.rope_snapped = False
        self.is_falling = False
        self.ore_in_bucket = 0
        self.ore_positions = []
        self.particles = []
        self.snap_point = None
        self.flying_ores = []

    def complete_trial(self, success):
        self.logger.log_trial(self.trial, self.ore_in_bucket, success)
        if success:
            self.ore_banked += self.ore_in_bucket
            self.last_result = f"Success! Delivered {self.ore_in_bucket} ore"
        else:
            self.last_result = f"Rope snapped! Lost {self.ore_in_bucket} ore"
        self.show_feedback = True
        self.feedback_timer = 120
        self.trial += 1

    def update(self, mouse_pos):
        self.pickaxe.update(mouse_pos)
        self.bucket_sway_angle += 0.05
        self.bucket_sway = math.sin(self.bucket_sway_angle) * 10
        self.animation_timer += 1
        self.rope_sway = math.sin(self.animation_timer * 0.02) * 2
        for cloud in self.clouds: cloud.update()
        for bird in self.birds:
            bird['x'] += bird['speed']
            bird['y'] += math.sin(bird['x'] * 0.01) * 0.5
            bird['flap'] = (bird['flap'] + 0.2) % (math.pi * 2)
            if bird['x'] > GAME_WIDTH + 50:
                bird['x'] = -50
                bird['y'] = random.randint(100, 400)
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)
        for flying_ore in self.flying_ores[:]:
            if flying_ore.update():
                self.ore_in_bucket += 1
                angle = random.uniform(0, 2 * math.pi)
                # MODIFIED: Increase horizontal spread of ore in the larger bucket
                radius = random.uniform(0, 25)
                x = radius * math.cos(angle)
                y = -5 - (self.ore_in_bucket * 0.8)
                self.ore_positions.append((x, y, flying_ore.color))
                self.flying_ores.remove(flying_ore)
        progress = max(0, min(1, (self.bucket_x - self.rope_start[0]) / (self.rope_end[0] - self.rope_start[0])))
        base_sag = 20 + (self.ore_in_bucket / MAX_ORE) * 40
        t = progress
        p0_y, p2_y = self.rope_start[1], self.rope_end[1]
        p1_y = p0_y + (p2_y - p0_y) * 0.5 + base_sag + self.rope_sway
        self.rope_y_at_bucket = (1 - t) ** 2 * p0_y + 2 * (1 - t) * t * p1_y + t ** 2 * p2_y
        if self.is_falling:
            self.bucket_y += 15
        else:
            self.bucket_y = self.rope_y_at_bucket + self.connector_rope_length
        if self.state == "play":
            if self.show_feedback:
                self.feedback_timer -= 1
                if self.feedback_timer <= 0:
                    self.show_feedback = False
                    if self.trial > MAX_TRIALS:
                        self.state = "results"
                        print(self.logger.save_csv())
                    else:
                        self.reset_bucket()
            elif self.bucket_moving and not self.bucket_arrived:
                if self.rope_snapped and progress >= self.snap_point:
                    self.is_falling = True
                    if not self.particles:
                        for _ in range(40):
                            dx, dy = random.uniform(-8, 8), random.uniform(-10, -3)
                            color = random.choice([COLOR_ORE_GOLD, COLOR_ORE_SILVER, COLOR_ORE_COPPER])
                            self.particles.append(
                                Particle(self.bucket_x, self.bucket_y, dx, dy, color, 80, random.randint(4, 8)))
                    if self.bucket_y > GAME_HEIGHT + 100:
                        self.complete_trial(False)
                        self.bucket_arrived = True
                else:
                    self.bucket_x += 6
                    if self.bucket_x >= self.bucket_target_x:
                        self.bucket_arrived = True
                        self.complete_trial(True)

    def draw_background(self, surface):
        for y in range(GAME_HEIGHT):
            if y < GAME_HEIGHT * 0.4:
                p = y / (GAME_HEIGHT * 0.4)
                c = (int(COLOR_SKY_GRADIENT_TOP[i] + (COLOR_SKY_GRADIENT_MID[i] - COLOR_SKY_GRADIENT_TOP[i]) * p) for i
                     in range(3))
            else:
                p = (y - GAME_HEIGHT * 0.4) / (GAME_HEIGHT * 0.6)
                c = (int(COLOR_SKY_GRADIENT_MID[i] + (COLOR_SKY_GRADIENT_BOTTOM[i] - COLOR_SKY_GRADIENT_MID[i]) * p) for
                     i in range(3))
            pygame.draw.line(surface, tuple(c), (0, y), (GAME_WIDTH, y))
        for cloud in self.clouds: cloud.draw(surface)
        for bird in self.birds:
            wing_offset = math.sin(bird['flap']) * 5
            pygame.draw.lines(surface, (50, 50, 50), False, [
                (bird['x'] - 10, bird['y'] + wing_offset), (bird['x'], bird['y']),
                (bird['x'] + 10, bird['y'] + wing_offset)
            ], 2)
        pygame.draw.polygon(surface, COLOR_MOUNTAIN_FAR,
                            [(0, 700), (300, 400), (600, 500), (900, 350), (1200, 450), (1500, 400), (1800, 500),
                             (GAME_WIDTH, 600), (GAME_WIDTH, GAME_HEIGHT), (0, GAME_HEIGHT)])
        pygame.draw.polygon(surface, COLOR_MOUNTAIN_MID,
                            [(0, 750), (200, 550), (500, 600), (800, 500), (1100, 550), (1400, 480), (1700, 580),
                             (GAME_WIDTH, 650), (GAME_WIDTH, GAME_HEIGHT), (0, GAME_HEIGHT)])
        pygame.draw.polygon(surface, COLOR_MOUNTAIN_NEAR,
                            [(0, 600), (100, 550), (250, 500), (400, 480), (550, 490), (650, 510), (650, GAME_HEIGHT),
                             (0, GAME_HEIGHT)])
        pygame.draw.lines(surface, COLOR_MOUNTAIN_DETAIL, False,
                          [(400, 480), (550, 490), (650, 510), (650, GAME_HEIGHT)], 5)

        # MODIFIED: Rock is larger and its points are scaled
        rock_x, rock_y = self.ore_rock_rect.center
        scale = 1.25
        rock_points = [
            (rock_x - 80 * scale, rock_y + 70 * scale), (rock_x - 90 * scale, rock_y + 30 * scale),
            (rock_x - 50 * scale, rock_y - 60 * scale), (rock_x + 10 * scale, rock_y - 80 * scale),
            (rock_x + 75 * scale, rock_y - 55 * scale), (rock_x + 95 * scale, rock_y + 20 * scale),
            (rock_x + 60 * scale, rock_y + 75 * scale)
        ]
        pygame.draw.polygon(surface, COLOR_BUCKET_METAL, rock_points)

        # MODIFIED: Scale detail lines
        detail_line_1 = [
            (rock_x - 40 * scale, rock_y - 5 * scale), (rock_x - 5 * scale, rock_y + 20 * scale),
            (rock_x - 45 * scale, rock_y + 55 * scale)
        ]
        detail_line_2 = [
            (rock_x + 20 * scale, rock_y - 35 * scale), (rock_x + 55 * scale, rock_y),
            (rock_x + 35 * scale, rock_y + 40 * scale)
        ]
        pygame.draw.lines(surface, COLOR_MOUNTAIN_DETAIL, False, detail_line_1, 6)
        pygame.draw.lines(surface, COLOR_MOUNTAIN_DETAIL, False, detail_line_2, 4)
        pygame.draw.polygon(surface, COLOR_MOUNTAIN_DETAIL, rock_points, 8)

        pygame.draw.polygon(surface, COLOR_MOUNTAIN_NEAR,
                            [(1250, 640), (1350, 620), (1450, 600), (1600, 590), (1750, 600), (1850, 620),
                             (GAME_WIDTH, 640), (GAME_WIDTH, GAME_HEIGHT), (1250, GAME_HEIGHT)])
        pygame.draw.lines(surface, COLOR_MOUNTAIN_DETAIL, False,
                          [(1250, GAME_HEIGHT), (1250, 640), (1350, 620), (1450, 600), (1600, 590)], 5)
        pygame.draw.rect(surface, COLOR_ROPE, pygame.Rect(440, 340, 20, 150))
        pygame.draw.circle(surface, COLOR_BUCKET_METAL, (450, 340), 12)
        pygame.draw.circle(surface, COLOR_BUCKET_DARK, (450, 340), 8)
        pygame.draw.rect(surface, COLOR_ROPE, pygame.Rect(1460, 460, 20, 150))
        pygame.draw.circle(surface, COLOR_BUCKET_METAL, (1470, 460), 12)
        pygame.draw.circle(surface, COLOR_BUCKET_DARK, (1470, 460), 8)

    def draw_truck(self, surface):
        x, y = 1400, 560
        shadow_surf = pygame.Surface((180, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50), (0, 0, 180, 20))
        surface.blit(shadow_surf, (x - 10, y + 90))
        bed_rect = pygame.Rect(x + 60, y + 20, 100, 60)
        pygame.draw.rect(surface, COLOR_TRUCK_DARK, bed_rect)
        pygame.draw.rect(surface, COLOR_TRUCK_RED, bed_rect, 3)
        if self.ore_banked > 0:
            ore_text = large_font.render(str(self.ore_banked), True, WHITE)
            ore_rect = ore_text.get_rect(center=(x + 110, y + 50))
            bg_rect = ore_rect.inflate(20, 10)
            pygame.draw.rect(surface, COLOR_UI_BG, bg_rect, border_radius=10)
            pygame.draw.rect(surface, COLOR_UI_ACCENT, bg_rect, 2, border_radius=10)
            surface.blit(ore_text, ore_rect)
        pygame.draw.polygon(surface, COLOR_TRUCK_RED,
                            [(x, y + 80), (x, y + 20), (x + 15, y + 5), (x + 50, y + 5), (x + 60, y + 20),
                             (x + 60, y + 80)])
        pygame.draw.polygon(surface, COLOR_TRUCK_WINDOW,
                            [(x + 8, y + 25), (x + 20, y + 15), (x + 45, y + 15), (x + 52, y + 25)])
        pygame.draw.line(surface, (255, 255, 255, 128), (x + 25, y + 17), (x + 35, y + 17), 2)
        for wx, wy in [(x + 15, y + 85), (x + 45, y + 85), (x + 85, y + 85), (x + 125, y + 85)]:
            pygame.draw.circle(surface, COLOR_WHEEL, (wx, wy), 15)
            pygame.draw.circle(surface, COLOR_TRUCK_CHROME, (wx, wy), 8)

    def draw_rope_system(self, surface):
        start_x, start_y = self.rope_start
        end_x, end_y = self.rope_end
        base_sag = 20 + (self.ore_in_bucket / MAX_ORE) * 40
        points = []
        for i in range(41):
            t = i / 40
            x = (1 - t) * start_x + t * end_x
            p0_y, p2_y = start_y, end_y
            p1_y = p0_y + (p2_y - p0_y) * 0.5 + base_sag + self.rope_sway
            y = (1 - t) ** 2 * p0_y + 2 * (1 - t) * t * p1_y + t ** 2 * p2_y
            points.append((x, y))
        pygame.draw.lines(surface, COLOR_ROPE_SHADOW, False, [(p[0] + 3, p[1] + 3) for p in points], 8)
        pygame.draw.lines(surface, COLOR_ROPE, False, points, 6)

    def draw_bucket(self, surface):
        if self.rope_snapped and self.bucket_y > GAME_HEIGHT + 50: return
        sway_x = self.bucket_x + self.bucket_sway

        # MODIFIED: Larger handle/arc dimensions
        handle_width = 84
        handle_height = 48
        # Position handle relative to the top of the bucket
        handle_rect = pygame.Rect(sway_x - handle_width // 2, self.bucket_y - 24, handle_width, handle_height)

        if not self.is_falling:
            color = COLOR_ROPE_2 if self.ore_in_bucket / MAX_ORE <= 0.5 else COLOR_ROPE_STRESSED
            # MODIFIED: Connector rope attaches to the top of the new, larger handle
            pygame.draw.line(surface, color, (self.bucket_x, self.rope_y_at_bucket),
                             (sway_x, handle_rect.top + 10), 5)  # +10 to connect just below the apex, made thicker

        # MODIFIED: Larger bucket dimensions
        bucket_width = 96
        bucket_height = 72
        bucket_rect = pygame.Rect(sway_x - bucket_width // 2, self.bucket_y, bucket_width, bucket_height)

        draw_gradient_rect(surface, COLOR_BUCKET_HIGHLIGHT, COLOR_BUCKET_DARK, bucket_rect)
        # MODIFIED: Thicker rim
        pygame.draw.rect(surface, COLOR_BUCKET_METAL, (bucket_rect.x, bucket_rect.y, bucket_rect.width, 7))

        # MODIFIED: Ore is drawn lower inside the bucket
        for ox, oy, color in self.ore_positions[:self.ore_in_bucket]:
            # The y-offset is increased to place the ore deeper visually.
            ore_base_y = self.bucket_y + 45 + oy
            pygame.draw.circle(surface, tuple(int(c * 0.7) for c in color),
                               (int(sway_x + ox + 2), int(ore_base_y + 2)), 6)
            pygame.draw.circle(surface, color, (int(sway_x + ox), int(ore_base_y)), 6)

        # Draw the handle itself
        pygame.draw.arc(surface, COLOR_BUCKET_DARK, handle_rect, 0, math.pi, 6)

    def draw_ui(self, surface):
        panel_rect = pygame.Rect(30, 30, 350, 140)
        panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*COLOR_UI_BG, 200), panel_surf.get_rect(), border_radius=15)
        surface.blit(panel_surf, panel_rect)
        pygame.draw.rect(surface, COLOR_UI_ACCENT, panel_rect, 3, border_radius=15)
        pygame.draw.circle(surface, COLOR_ORE_GOLD, (60, 60), 15)
        total_ore = self.ore_in_bucket + len(self.flying_ores)
        ore_text = font.render(f"In Bucket: {total_ore}/{MAX_ORE}", True, COLOR_UI_TEXT)
        surface.blit(ore_text, (90, 45))
        pygame.draw.rect(surface, COLOR_UI_ACCENT, (55, 100, 20, 25))
        banked_text = font.render(f"Banked: {self.ore_banked}", True, COLOR_UI_TEXT)
        surface.blit(banked_text, (90, 105))
        trial_panel_rect = pygame.Rect(GAME_WIDTH - 280, 30, 250, 80)
        trial_panel_surf = pygame.Surface(trial_panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(trial_panel_surf, (*COLOR_UI_BG, 200), trial_panel_surf.get_rect(), border_radius=15)
        surface.blit(trial_panel_surf, trial_panel_rect)
        pygame.draw.rect(surface, COLOR_UI_ACCENT, trial_panel_rect, 3, border_radius=15)
        trial_text = large_font.render(f"Trial {self.trial}/{MAX_TRIALS}", True, COLOR_UI_TEXT)
        surface.blit(trial_text, trial_text.get_rect(center=trial_panel_rect.center))
        if self.show_feedback and self.last_result:
            msg_surf = large_font.render(self.last_result, True, COLOR_UI_TEXT)
            msg_rect = msg_surf.get_rect(center=(GAME_WIDTH // 2, GAME_HEIGHT // 2))
            bg_rect = msg_rect.inflate(80, 40)
            bg_color = COLOR_BUTTON_NORMAL if "Success" in self.last_result else COLOR_DANGER_HIGH
            panel_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (*bg_color, 200), panel_surf.get_rect(), border_radius=20)
            surface.blit(panel_surf, bg_rect)
            pygame.draw.rect(surface, WHITE, bg_rect, 4, border_radius=20)
            surface.blit(msg_surf, msg_rect)

    def draw_menu(self, surface):
        self.draw_background(surface)
        title_panel_rect = pygame.Rect(GAME_WIDTH // 2 - 400, 80, 800, 200)
        draw_gradient_rect(surface, COLOR_UI_BG_LIGHT, COLOR_UI_BG, title_panel_rect)
        pygame.draw.rect(surface, COLOR_UI_ACCENT, title_panel_rect, 4, border_radius=20)
        title_shadow = huge_font.render("Mountain Miner", True, (0, 0, 0, 128))
        title = huge_font.render("Mountain Miner", True, COLOR_UI_TEXT)
        surface.blit(title_shadow, title_shadow.get_rect(center=(GAME_WIDTH // 2 + 3, 150 + 3)))
        surface.blit(title, title.get_rect(center=(GAME_WIDTH // 2, 150)))
        subtitle = large_font.render("A Risk Assessment Game", True, COLOR_UI_ACCENT)
        surface.blit(subtitle, subtitle.get_rect(center=(GAME_WIDTH // 2, 220)))
        inst_panel_rect = pygame.Rect(GAME_WIDTH // 2 - 450, 320, 900, 400)
        inst_panel_surf = pygame.Surface(inst_panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(inst_panel_surf, (*COLOR_UI_BG, 180), inst_panel_surf.get_rect(), border_radius=20)
        surface.blit(inst_panel_surf, inst_panel_rect)
        pygame.draw.rect(surface, WHITE, inst_panel_rect, 3, border_radius=20)
        instructions = [("⛏️", "Click the large rock to mine ore."), ("📦", "Each ore increases your potential reward."),
                        ("⚠️", "More ore = higher risk of the rope snapping!"),
                        ("🚚", "Click 'Send Bucket' to bank your ore."),
                        ("🎯", f"Complete {MAX_TRIALS} trials to finish."),
                        ("💡", "Find the balance between risk and reward!")]
        y = 360
        for icon, text in instructions:
            text_surf = font.render(f"{icon}  {text}", True, COLOR_UI_TEXT)
            surface.blit(text_surf, text_surf.get_rect(center=(GAME_WIDTH // 2, y)))
            y += 55
        self.play_button.draw(surface)

    def draw_results(self, surface):
        overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        draw_gradient_rect(overlay, (*COLOR_UI_BG, 220), (*COLOR_UI_BG, 180), overlay.get_rect())
        surface.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(GAME_WIDTH // 2 - 500, 100, 1000, 700)
        draw_gradient_rect(surface, COLOR_UI_BG_LIGHT, COLOR_UI_BG, panel_rect)
        pygame.draw.rect(surface, COLOR_UI_ACCENT, panel_rect, 5, border_radius=30)
        title = huge_font.render("Mining Complete!", True, COLOR_UI_ACCENT)
        surface.blit(title, title.get_rect(center=(GAME_WIDTH // 2, 180)))
        # Results drawing logic would go here
        self.play_again_button.draw(surface)
        self.quit_button.draw(surface)

    def draw(self, surface):
        if self.state == "menu":
            self.draw_menu(surface)
            self.pickaxe.draw(surface)
        elif self.state == "play":
            self.draw_background(surface)
            self.draw_truck(surface)
            self.draw_rope_system(surface)
            self.draw_bucket(surface)
            for flying_ore in self.flying_ores: flying_ore.draw(surface)
            for particle in self.particles: particle.draw(surface)
            self.draw_ui(surface)
            if not self.bucket_moving and not self.show_feedback and self.ore_in_bucket > 0:
                self.send_bucket_button.draw(surface)
            self.pickaxe.draw(surface)
        elif self.state == "results":
            self.draw_background(surface)
            self.draw_results(surface)
            self.pickaxe.draw(surface)


def main():
    game = MountainMinerGame()
    running = True
    pygame.mouse.set_visible(False)

    while running:
        raw_mouse_pos = pygame.mouse.get_pos()
        scaled_surface, scaled_w, scaled_h = scale_surface_keeping_aspect_ratio(
            game_surface, NATIVE_SCREEN_WIDTH, NATIVE_SCREEN_HEIGHT)
        pos_x = (NATIVE_SCREEN_WIDTH - scaled_w) / 2
        pos_y = (NATIVE_SCREEN_HEIGHT - scaled_h) / 2
        game_mouse_x = (raw_mouse_pos[0] - pos_x) * (GAME_WIDTH / scaled_w) if scaled_w > 0 else 0
        game_mouse_y = (raw_mouse_pos[1] - pos_y) * (GAME_HEIGHT / scaled_h) if scaled_h > 0 else 0
        game_mouse_pos = (int(game_mouse_x), int(game_mouse_y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == "menu":
                    if game.play_button.is_clicked(game_mouse_pos):
                        game.state = "play"
                        game.reset_bucket()
                elif game.state == "play":
                    if not game.bucket_moving and not game.show_feedback:
                        if game.ore_rock_rect.collidepoint(game_mouse_pos):
                            game.add_ore()
                            game.pickaxe.swing()
                        elif game.ore_in_bucket > 0 and game.send_bucket_button.is_clicked(game_mouse_pos):
                            game.send_bucket()
                elif game.state == "results":
                    if game.play_again_button.is_clicked(game_mouse_pos):
                        game = MountainMinerGame()
                        game.state = "play"
                    elif game.quit_button.is_clicked(game_mouse_pos):
                        running = False
            if event.type == pygame.MOUSEBUTTONUP:
                if game.state == "menu":
                    game.play_button.release()
                elif game.state == "play":
                    game.send_bucket_button.release()
                elif game.state == "results":
                    game.play_again_button.release()
                    game.quit_button.release()

        if game.state == "menu":
            game.play_button.check_hover(game_mouse_pos)
        elif game.state == "play":
            if not game.bucket_moving and not game.show_feedback and game.ore_in_bucket > 0:
                game.send_bucket_button.check_hover(game_mouse_pos)
        elif game.state == "results":
            game.play_again_button.check_hover(game_mouse_pos)
            game.quit_button.check_hover(game_mouse_pos)

        game.update(game_mouse_pos)
        game_surface.fill(COLOR_SKY_GRADIENT_TOP)
        game.draw(game_surface)
        screen.fill(BLACK)
        screen.blit(scaled_surface, (pos_x, pos_y))
        pygame.display.flip()
        clock.tick(FPS)

    if game.logger.data and game.state != "results":
        print("Game exited. Saving data...")
        print(game.logger.save_csv())

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()