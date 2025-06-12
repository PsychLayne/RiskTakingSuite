import pygame
import sys
import math
import random
import csv
from datetime import datetime
import numpy as np

# Initialize pygame
pygame.init()

# --- Pygame Feature Check for Anti-aliasing ---
SUPPORTS_AAPOLYGON = hasattr(pygame.draw, 'aapolygon')
SUPPORTS_AALINES = hasattr(pygame.draw, 'aalines')
SUPPORTS_AALINE = hasattr(pygame.draw, 'aaline')

if not (SUPPORTS_AAPOLYGON and SUPPORTS_AALINES and SUPPORTS_AALINE):
    print(
        f"Warning: Your Pygame installation (version {pygame.version.ver}) appears to be missing some anti-aliasing draw functions (aapolygon, aalines, or aaline).")
    print("Falling back to non-anti-aliased drawing for some shapes.")
    if pygame.version.vernum[0] < 2:
        print("For sharper visuals, consider upgrading Pygame: pip install --upgrade pygame")
# --- End Pygame Feature Check ---

# Constants
WHEEL_RADIUS = 480
BOTTLE_LENGTH = 420
BOTTLE_NECK_WIDTH = 27
BOTTLE_BODY_WIDTH = 74
BOTTLE_TIP_DOT_RADIUS = 5
SEGMENTS = 16
FPS = 60
TOTAL_TRIALS = 30
POINTS_PER_ADD = 5  # New constant for points earned per "Add" click

# --- UI Element Sizes ---
FONT_SIZE = 48
SMALL_FONT_SIZE = 32
LARGE_FONT_SIZE = 80

DANGER_BAR_X = 20
DANGER_BAR_Y = 120
DANGER_BAR_WIDTH = 40
DANGER_BAR_HEIGHT = 250

BUTTON_WIDTH = 180
BUTTON_HEIGHT = 60
BUTTON_SPACING = 20

# --- New Enhanced Color Palette ---
BACKGROUND_COLOR = (40, 42, 54)
UI_TEXT_COLOR = (248, 248, 242)
WHEEL_GREEN = (80, 250, 123)
WHEEL_RED = (255, 85, 85)
WHEEL_SEGMENT_BORDER_COLOR = (248, 248, 242)

BOTTLE_GLASS_COLOR = (100, 180, 110)
BOTTLE_HIGHLIGHT_COLOR = (150, 220, 160)
BOTTLE_LABEL_BG_COLOR = (248, 248, 242)
BOTTLE_INNER_LABEL_COLOR = (220, 220, 210)
BOTTLE_LABEL_LINE_COLOR = (180, 170, 130)

DANGER_BAR_BORDER_COLOR = (200, 200, 200)
DANGER_BAR_EMPTY_COLOR = (68, 71, 90)
GRADIENT_YELLOW = (255, 220, 50)

STATS_OVERLAY_COLOR = (40, 42, 54, 230)
STATS_CHART_BG_COLOR = (68, 71, 90)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Button Colors
BUTTON_ADD_ACTIVE_COLOR = (0, 180, 0)
BUTTON_SPIN_ACTIVE_COLOR = (0, 120, 220)
BUTTON_INACTIVE_COLOR = (100, 100, 100)
BUTTON_TEXT_COLOR = UI_TEXT_COLOR

# Setup display for fullscreen
infoObject = pygame.display.Info()
WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SRCALPHA)
CENTER = (WIDTH // 2, HEIGHT // 2)

pygame.display.set_caption("Risk Wheel Experiment - Add/Spin Version")
clock = pygame.time.Clock()

# Fonts
FONT_NAME_PLACEHOLDER = "arial.ttf"
try:
    font = pygame.font.Font(FONT_NAME_PLACEHOLDER, FONT_SIZE)
    small_font = pygame.font.Font(FONT_NAME_PLACEHOLDER, SMALL_FONT_SIZE)
    large_font = pygame.font.Font(FONT_NAME_PLACEHOLDER, LARGE_FONT_SIZE)
    print(f"Successfully loaded font: {FONT_NAME_PLACEHOLDER}")
except pygame.error as e:
    print(f"Warning: Font '{FONT_NAME_PLACEHOLDER}' not found ({e}). Falling back to system default font.")
    font = pygame.font.SysFont(None, FONT_SIZE)
    small_font = pygame.font.SysFont(None, SMALL_FONT_SIZE)
    large_font = pygame.font.SysFont(None, LARGE_FONT_SIZE)


class RiskTracker:
    def __init__(self):
        self.trials = []
        self.current_trial = 0
        self.total_score = 0
        self.won_trials = 0
        self.lost_trials = 0

    def record_trial(self, risk_level, points_earned, result):
        trial_data = {
            'trial_number': self.current_trial + 1,
            'risk_level': risk_level,
            'points_earned': points_earned,
            'result': result
        }
        self.trials.append(trial_data)
        self.current_trial += 1
        self.total_score += points_earned
        if result == 'win':
            self.won_trials += 1
        else:
            self.lost_trials += 1

    def get_trial_count(self):
        return self.current_trial

    def is_experiment_complete(self):
        return self.current_trial >= TOTAL_TRIALS


class RiskWheel:
    def __init__(self, risk_tracker):
        self.segments = SEGMENTS
        self.segment_angle = 360 / self.segments
        self.red_segments = []
        self.bottle_angle = 0.0
        self.spin_speed = 0.0
        self.max_spin_speed = random.uniform(12.0, 18.0)
        self.deceleration = random.uniform(0.05, 0.15)
        self.points = 0
        self.potential_points_current_trial = 0
        self.game_over = False
        self.result_message = ""
        self.risk_tracker = risk_tracker
        self.game_phase = "decision"
        buttons_y = CENTER[1] + WHEEL_RADIUS + 50
        self.add_button_rect = pygame.Rect(CENTER[0] - BUTTON_WIDTH - BUTTON_SPACING // 2, buttons_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.spin_button_rect = pygame.Rect(CENTER[0] + BUTTON_SPACING // 2, buttons_y, BUTTON_WIDTH, BUTTON_HEIGHT)

    def update(self):
        if self.game_phase == "spinning":
            if self.spin_speed > 0:
                self.spin_speed -= self.deceleration
                if self.spin_speed < 0:
                    self.spin_speed = 0
                if self.spin_speed == 0 and not self.game_over:
                    self.check_result()
                    self.game_phase = "result"
            self.bottle_angle = (self.bottle_angle + self.spin_speed) % 360

    def turn_segment_red(self):
        if len(self.red_segments) >= self.segments:
            return
        available_segments = [i for i in range(self.segments) if i not in self.red_segments]
        if available_segments:
            new_red = random.choice(available_segments)
            self.red_segments.append(new_red)

    def check_result(self):
        if self.game_over:
            return
        normalized_angle = self.bottle_angle % 360
        landed_segment_index = int(normalized_angle // self.segment_angle)
        risk_level = len(self.red_segments) / self.segments if self.segments > 0 else 0.0
        earned_points_for_trial = 0
        if landed_segment_index in self.red_segments:
            self.result_message = f"Landed on RED! Lost {self.potential_points_current_trial} cents."
            result_type = 'loss'
            earned_points_for_trial = 0
        else:
            earned_points_for_trial = self.potential_points_current_trial
            self.points += earned_points_for_trial
            self.result_message = f"Landed on GREEN! Won {earned_points_for_trial} cents!"
            result_type = 'win'
        self.risk_tracker.record_trial(risk_level, earned_points_for_trial, result_type)
        self.game_over = True

    def reset(self):
        self.red_segments = []
        self.spin_speed = 0
        self.potential_points_current_trial = 0
        self.game_over = False
        self.result_message = ""
        self.game_phase = "decision"
        self.max_spin_speed = random.uniform(12.0, 18.0)
        self.deceleration = random.uniform(0.05, 0.15)

    def handle_click(self, pos):
        if self.game_phase == "decision":
            if self.add_button_rect.collidepoint(pos):
                self.action_add()
            elif self.spin_button_rect.collidepoint(pos):
                self.action_spin()

    def action_add(self):
        if len(self.red_segments) < self.segments:
            self.potential_points_current_trial += POINTS_PER_ADD
            self.turn_segment_red()
        else:
            print("All segments are already red. Cannot add more points/risk.")

    def action_spin(self):
        if self.potential_points_current_trial >= 0:
            self.game_phase = "spinning"
            self.spin_speed = self.max_spin_speed
            self.game_over = False

    def draw_wheel(self, surface):
        for i in range(self.segments):
            start_angle_rad = math.radians(i * self.segment_angle - 90)
            end_angle_rad = math.radians((i + 1) * self.segment_angle - 90)
            color = WHEEL_RED if i in self.red_segments else WHEEL_GREEN
            points_list = [CENTER]
            arc_steps = max(5, int(self.segment_angle / 1.5))
            for step in range(arc_steps + 1):
                angle = start_angle_rad + (end_angle_rad - start_angle_rad) * step / arc_steps
                x = CENTER[0] + WHEEL_RADIUS * math.cos(angle)
                y = CENTER[1] + WHEEL_RADIUS * math.sin(angle)
                points_list.append((x, y))
            if SUPPORTS_AAPOLYGON:
                pygame.draw.aapolygon(surface, color, points_list)
            else:
                pygame.draw.polygon(surface, color, points_list)
        line_color = WHEEL_SEGMENT_BORDER_COLOR
        for i in range(self.segments):
            angle_rad = math.radians(i * self.segment_angle - 90)
            end_x = CENTER[0] + WHEEL_RADIUS * math.cos(angle_rad)
            end_y = CENTER[1] + WHEEL_RADIUS * math.sin(angle_rad)
            if SUPPORTS_AALINE:
                pygame.draw.aaline(surface, line_color, CENTER, (end_x, end_y))
            else:
                pygame.draw.line(surface, line_color, CENTER, (end_x, end_y), 2)

    def draw_bottle(self, surface):
        bottle_color_local = BOTTLE_GLASS_COLOR
        bottle_highlight_local = BOTTLE_HIGHLIGHT_COLOR
        label_bg_color = BOTTLE_LABEL_BG_COLOR
        inner_label_color = BOTTLE_INNER_LABEL_COLOR
        label_line_color = BOTTLE_LABEL_LINE_COLOR
        bottle_length_current = BOTTLE_LENGTH
        neck_width_current = BOTTLE_NECK_WIDTH
        body_width_current = BOTTLE_BODY_WIDTH
        bottle_neck_length = bottle_length_current * 0.3
        bottle_body_length = bottle_length_current - bottle_neck_length
        bottle_angle_rad = math.radians(self.bottle_angle - 90)
        dir_x = math.cos(bottle_angle_rad)
        dir_y = math.sin(bottle_angle_rad)
        perp_x = -dir_y
        perp_y = dir_x
        bottle_pivot_x = CENTER[0]
        bottle_pivot_y = CENTER[1]
        base_x = bottle_pivot_x - (bottle_length_current / 2.0) * dir_x
        base_y = bottle_pivot_y - (bottle_length_current / 2.0) * dir_y
        body_start = (base_x, base_y)
        body_end_main = (base_x + (bottle_body_length - 30 * (bottle_length_current / 200.0)) * dir_x, base_y + (bottle_body_length - 30 * (bottle_length_current / 200.0)) * dir_y)
        body_points = [(body_start[0] - body_width_current / 2 * perp_x, body_start[1] - body_width_current / 2 * perp_y), (body_start[0] + body_width_current / 2 * perp_x, body_start[1] + body_width_current / 2 * perp_y), (body_end_main[0] + body_width_current / 2 * perp_x, body_end_main[1] + body_width_current / 2 * perp_y), (body_end_main[0] - body_width_current / 2 * perp_x, body_end_main[1] - body_width_current / 2 * perp_y)]
        if SUPPORTS_AAPOLYGON: pygame.draw.aapolygon(surface, bottle_color_local, body_points)
        else: pygame.draw.polygon(surface, bottle_color_local, body_points)
        highlight_width = body_width_current * 0.2
        highlight_points = [(body_start[0] + (body_width_current / 4) * perp_x, body_start[1] + (body_width_current / 4) * perp_y), (body_start[0] + (body_width_current / 4 + highlight_width) * perp_x, body_start[1] + (body_width_current / 4 + highlight_width) * perp_y), (body_end_main[0] + (body_width_current / 4 + highlight_width) * perp_x, body_end_main[1] + (body_width_current / 4 + highlight_width) * perp_y), (body_end_main[0] + (body_width_current / 4) * perp_x, body_end_main[1] + (body_width_current / 4) * perp_y)]
        if SUPPORTS_AAPOLYGON: pygame.draw.aapolygon(surface, bottle_highlight_local, highlight_points)
        else: pygame.draw.polygon(surface, bottle_highlight_local, highlight_points)
        shoulder_start_point = body_end_main
        neck_start_point = (base_x + bottle_body_length * dir_x, base_y + bottle_body_length * dir_y)
        trans1_width = body_width_current * 0.8; trans2_width = body_width_current * 0.6; trans3_width = body_width_current * 0.4
        offset1 = 10 * (bottle_length_current / 200.0); offset2 = 20 * (bottle_length_current / 200.0); offset3 = 25 * (bottle_length_current / 200.0)
        trans1 = (shoulder_start_point[0] + offset1 * dir_x, shoulder_start_point[1] + offset1 * dir_y)
        trans2 = (shoulder_start_point[0] + offset2 * dir_x, shoulder_start_point[1] + offset2 * dir_y)
        trans3 = (shoulder_start_point[0] + offset3 * dir_x, shoulder_start_point[1] + offset3 * dir_y)
        trans4 = neck_start_point
        shoulder_points = [(shoulder_start_point[0] - body_width_current / 2 * perp_x, shoulder_start_point[1] - body_width_current / 2 * perp_y), (trans1[0] - trans1_width / 2 * perp_x, trans1[1] - trans1_width / 2 * perp_y), (trans2[0] - trans2_width / 2 * perp_x, trans2[1] - trans2_width / 2 * perp_y), (trans3[0] - trans3_width / 2 * perp_x, trans3[1] - trans3_width / 2 * perp_y), (trans4[0] - neck_width_current / 2 * perp_x, trans4[1] - neck_width_current / 2 * perp_y), (trans4[0] + neck_width_current / 2 * perp_x, trans4[1] + neck_width_current / 2 * perp_y), (trans3[0] + trans3_width / 2 * perp_x, trans3[1] + trans3_width / 2 * perp_y), (trans2[0] + trans2_width / 2 * perp_x, trans2[1] + trans2_width / 2 * perp_y), (trans1[0] + trans1_width / 2 * perp_x, trans1[1] + trans1_width / 2 * perp_y), (shoulder_start_point[0] + body_width_current / 2 * perp_x, shoulder_start_point[1] + body_width_current / 2 * perp_y)]
        if SUPPORTS_AAPOLYGON: pygame.draw.aapolygon(surface, bottle_color_local, shoulder_points)
        else: pygame.draw.polygon(surface, bottle_color_local, shoulder_points)
        neck_end_point = (base_x + bottle_length_current * dir_x, base_y + bottle_length_current * dir_y)
        neck_points = [(neck_start_point[0] - neck_width_current / 2 * perp_x, neck_start_point[1] - neck_width_current / 2 * perp_y), (neck_start_point[0] + neck_width_current / 2 * perp_x, neck_start_point[1] + neck_width_current / 2 * perp_y), (neck_end_point[0] + neck_width_current / 2 * perp_x, neck_end_point[1] + neck_width_current / 2 * perp_y), (neck_end_point[0] - neck_width_current / 2 * perp_x, neck_end_point[1] - neck_width_current / 2 * perp_y)]
        if SUPPORTS_AAPOLYGON: pygame.draw.aapolygon(surface, bottle_color_local, neck_points)
        else: pygame.draw.polygon(surface, bottle_color_local, neck_points)
        label_center_offset_from_new_base = bottle_body_length * 0.35
        label_length_on_bottle = bottle_body_length * 0.5
        label_width_on_bottle = body_width_current * 0.9
        label_center_x = base_x + label_center_offset_from_new_base * dir_x
        label_center_y = base_y + label_center_offset_from_new_base * dir_y
        half_label_len_vec_x = (label_length_on_bottle / 2) * dir_x; half_label_len_vec_y = (label_length_on_bottle / 2) * dir_y
        half_label_width_vec_x = (label_width_on_bottle / 2) * perp_x; half_label_width_vec_y = (label_width_on_bottle / 2) * perp_y
        label_points = [(label_center_x - half_label_len_vec_x - half_label_width_vec_x, label_center_y - half_label_len_vec_y - half_label_width_vec_y), (label_center_x - half_label_len_vec_x + half_label_width_vec_x, label_center_y - half_label_len_vec_y + half_label_width_vec_y), (label_center_x + half_label_len_vec_x + half_label_width_vec_x, label_center_y + half_label_len_vec_y + half_label_width_vec_y), (label_center_x + half_label_len_vec_x - half_label_width_vec_x, label_center_y + half_label_len_vec_y - half_label_width_vec_y)]
        if SUPPORTS_AAPOLYGON: pygame.draw.aapolygon(surface, label_bg_color, label_points)
        else: pygame.draw.polygon(surface, label_bg_color, label_points)
        inner_label_scale_len = 0.7; inner_label_scale_width = 0.7
        half_inner_label_len_vec_x = (label_length_on_bottle * inner_label_scale_len / 2) * dir_x
        half_inner_label_len_vec_y = (label_length_on_bottle * inner_label_scale_len / 2) * dir_y
        half_inner_label_width_vec_x = (label_width_on_bottle * inner_label_scale_width / 2) * perp_x
        half_inner_label_width_vec_y = (label_width_on_bottle * inner_label_scale_width / 2) * perp_y
        inner_label_points = [(label_center_x - half_inner_label_len_vec_x - half_inner_label_width_vec_x, label_center_y - half_inner_label_len_vec_y - half_inner_label_width_vec_y), (label_center_x - half_inner_label_len_vec_x + half_inner_label_width_vec_x, label_center_y - half_inner_label_len_vec_y + half_inner_label_width_vec_y), (label_center_x + half_inner_label_len_vec_x + half_inner_label_width_vec_x, label_center_y + half_inner_label_len_vec_y + half_inner_label_width_vec_y), (label_center_x + half_inner_label_len_vec_x - half_inner_label_width_vec_x, label_center_y + half_inner_label_len_vec_y - half_inner_label_width_vec_y)]
        if SUPPORTS_AAPOLYGON: pygame.draw.aapolygon(surface, inner_label_color, inner_label_points)
        else: pygame.draw.polygon(surface, inner_label_color, inner_label_points)
        line_offset_from_label_center1 = -label_length_on_bottle * 0.15; line_offset_from_label_center2 = label_length_on_bottle * 0.15
        line_visual_width = label_width_on_bottle * 0.6
        line1_center_x = label_center_x + line_offset_from_label_center1 * dir_x; line1_center_y = label_center_y + line_offset_from_label_center1 * dir_y
        line2_center_x = label_center_x + line_offset_from_label_center2 * dir_x; line2_center_y = label_center_y + line_offset_from_label_center2 * dir_y
        half_line_visual_width_vec_x = (line_visual_width / 2) * perp_x; half_line_visual_width_vec_y = (line_visual_width / 2) * perp_y
        line1_start = (line1_center_x - half_line_visual_width_vec_x, line1_center_y - half_line_visual_width_vec_y)
        line1_end = (line1_center_x + half_line_visual_width_vec_x, line1_center_y + half_line_visual_width_vec_y)
        line2_start = (line2_center_x - half_line_visual_width_vec_x, line2_center_y - half_line_visual_width_vec_y)
        line2_end = (line2_center_x + half_line_visual_width_vec_x, line2_center_y + half_line_visual_width_vec_y)
        if SUPPORTS_AALINE: pygame.draw.aaline(surface, label_line_color, line1_start, line1_end); pygame.draw.aaline(surface, label_line_color, line2_start, line2_end)
        else: pygame.draw.line(surface, label_line_color, line1_start, line1_end, 2); pygame.draw.line(surface, label_line_color, line2_start, line2_end, 2)
        pygame.draw.circle(surface, BLACK, (int(neck_end_point[0]), int(neck_end_point[1])), BOTTLE_TIP_DOT_RADIUS)

    def draw_ui(self, surface):
        score_text_img = font.render(f"Total Score: {self.points} cents", True, UI_TEXT_COLOR)
        surface.blit(score_text_img, (20, 20))
        current_earned_value = self.potential_points_current_trial
        current_earned_text_img = large_font.render(f"{current_earned_value} cents", True, UI_TEXT_COLOR)
        current_earned_text_rect = current_earned_text_img.get_rect(centerx=WIDTH // 2, bottom=CENTER[1] - WHEEL_RADIUS - 30)
        surface.blit(current_earned_text_img, current_earned_text_rect)
        trial_display_count = self.risk_tracker.get_trial_count()
        if self.game_phase != "result":
            trial_display_count += 1
        if trial_display_count > TOTAL_TRIALS: trial_display_count = TOTAL_TRIALS
        trial_text_img = font.render(f"Trial: {trial_display_count}/{TOTAL_TRIALS}", True, UI_TEXT_COLOR)
        trial_text_rect = trial_text_img.get_rect(topright=(WIDTH - 20, 20))
        surface.blit(trial_text_img, trial_text_rect)
        pygame.draw.rect(surface, DANGER_BAR_EMPTY_COLOR, (DANGER_BAR_X, DANGER_BAR_Y, DANGER_BAR_WIDTH, DANGER_BAR_HEIGHT))
        pygame.draw.rect(surface, DANGER_BAR_BORDER_COLOR, (DANGER_BAR_X, DANGER_BAR_Y, DANGER_BAR_WIDTH, DANGER_BAR_HEIGHT), 3)
        danger_level = len(self.red_segments) / self.segments if self.segments > 0 else 0.0
        filled_height = int(DANGER_BAR_HEIGHT * danger_level)
        if filled_height > 0:
            bar_color = WHEEL_RED
            if danger_level <= 0.5:
                ratio = danger_level * 2
                r = int(WHEEL_GREEN[0] * (1 - ratio) + GRADIENT_YELLOW[0] * ratio)
                g = int(WHEEL_GREEN[1] * (1 - ratio) + GRADIENT_YELLOW[1] * ratio)
                b = int(WHEEL_GREEN[2] * (1 - ratio) + GRADIENT_YELLOW[2] * ratio)
                bar_color = (max(0, min(r, 255)), max(0, min(g, 255)), max(0, min(b, 255)))
            else:
                ratio = (danger_level - 0.5) * 2
                r = int(GRADIENT_YELLOW[0] * (1 - ratio) + WHEEL_RED[0] * ratio)
                g = int(GRADIENT_YELLOW[1] * (1 - ratio) + WHEEL_RED[1] * ratio)
                b = int(GRADIENT_YELLOW[2] * (1 - ratio) + WHEEL_RED[2] * ratio)
                bar_color = (max(0, min(r, 255)), max(0, min(g, 255)), max(0, min(b, 255)))
            pygame.draw.rect(surface, bar_color, (DANGER_BAR_X + 3, DANGER_BAR_Y + DANGER_BAR_HEIGHT - filled_height + 3, DANGER_BAR_WIDTH - 6, filled_height - 6))
        add_btn_color = BUTTON_INACTIVE_COLOR
        if self.game_phase == "decision" and len(self.red_segments) < self.segments:
            add_btn_color = BUTTON_ADD_ACTIVE_COLOR
        spin_btn_color = BUTTON_INACTIVE_COLOR
        if self.game_phase == "decision":
            spin_btn_color = BUTTON_SPIN_ACTIVE_COLOR
        pygame.draw.rect(surface, add_btn_color, self.add_button_rect, border_radius=10)
        pygame.draw.rect(surface, spin_btn_color, self.spin_button_rect, border_radius=10)
        add_text_img = small_font.render(f"Add ({POINTS_PER_ADD}c)", True, BUTTON_TEXT_COLOR)
        spin_text_img = small_font.render("Spin!", True, BUTTON_TEXT_COLOR)
        add_text_rect = add_text_img.get_rect(center=self.add_button_rect.center)
        spin_text_rect = spin_text_img.get_rect(center=self.spin_button_rect.center)
        surface.blit(add_text_img, add_text_rect)
        surface.blit(spin_text_img, spin_text_rect)
        if self.game_phase == "result":
            result_text_img = font.render(self.result_message, True, UI_TEXT_COLOR)
            text_rect = result_text_img.get_rect(center=(WIDTH // 2, HEIGHT - 100))
            surface.blit(result_text_img, text_rect)
            if not self.risk_tracker.is_experiment_complete():
                instruction_text_img = font.render("Press ENTER for next trial", True, UI_TEXT_COLOR)
                instruction_rect = instruction_text_img.get_rect(center=(WIDTH // 2, HEIGHT - 50))
                surface.blit(instruction_text_img, instruction_rect)
            else:
                instruction_text_img = font.render("Experiment finished. Press ENTER to save and exit.", True, UI_TEXT_COLOR)
                instruction_rect = instruction_text_img.get_rect(center=(WIDTH // 2, HEIGHT - 50))
                surface.blit(instruction_text_img, instruction_rect)

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)
        self.draw_wheel(surface)
        self.draw_bottle(surface)
        self.draw_ui(surface)


def display_instructions(surface, title_font, body_font):
    surface.fill(BACKGROUND_COLOR)
    title_text_img = title_font.render("Instructions", True, UI_TEXT_COLOR)
    title_rect = title_text_img.get_rect(center=(WIDTH // 2, HEIGHT // 6))
    surface.blit(title_text_img, title_rect)
    instructions = [
        f"Score as many cents as possible in {TOTAL_TRIALS} trials.",
        "",
        "How to Play:",
        f" - Click the 'Add ({POINTS_PER_ADD}c)' button to increase your potential winnings for this trial by {POINTS_PER_ADD} cents.",
        " - Each time you click 'Add', one GREEN segment on the wheel will turn RED.",
        " - More RED segments mean a higher risk, but your potential reward is also higher.",
        " - The 'Danger Bar' on the left shows the current risk level.",
        " - When you are ready, click the 'Spin!' button.",
        "",
        " - The bottle will spin and land on a segment.",
        " - Landing on GREEN wins the accumulated cents for that trial.",
        " - Landing on RED means no cents are earned for that trial.",
        "",
        "Press ENTER to start."
    ]
    line_spacing = int(FONT_SIZE * 1.15)
    current_y = title_rect.bottom + line_spacing * 1.5
    for line in instructions:
        line_text_img = body_font.render(line, True, UI_TEXT_COLOR)
        if line.strip().startswith("-") or line.strip() == "":
            line_rect = line_text_img.get_rect(left=WIDTH // 2 - 350, top=current_y)
        else:
            line_rect = line_text_img.get_rect(centerx=WIDTH // 2, top=current_y)
        surface.blit(line_text_img, line_rect)
        current_y += line_spacing
    pygame.display.flip()
    waiting_for_start = True
    while waiting_for_start:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting_for_start = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        clock.tick(FPS)

def save_data_to_csv(risk_tracker):
    """Saves the recorded trial data to a CSV file with a unique timestamped name."""
    if not risk_tracker.trials:
        print("No data to save.")
        return

    # Generate a unique filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"risk_task_data_{timestamp}.csv"

    # Define the CSV header, which matches the keys in the trial_data dictionary
    fieldnames = ['trial_number', 'risk_level', 'points_earned', 'result']

    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(risk_tracker.trials)
        print(f"Data successfully saved to {filename}")
    except IOError as e:
        print(f"Error saving data to CSV: {e}")

def main():
    global screen, WIDTH, HEIGHT, CENTER, font, small_font, large_font
    risk_tracker = RiskTracker()
    current_wheel = RiskWheel(risk_tracker)
    display_instructions(screen, large_font, font)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif current_wheel.game_phase == "result":
                    if event.key == pygame.K_RETURN:
                        if not current_wheel.risk_tracker.is_experiment_complete():
                            current_wheel.reset()
                        else:
                            save_data_to_csv(risk_tracker)
                            running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    current_wheel.handle_click(event.pos)

        current_wheel.update()
        current_wheel.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
