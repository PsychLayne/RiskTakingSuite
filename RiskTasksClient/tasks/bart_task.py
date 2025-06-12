import pygame
import sys
import random
import time
import csv
from pathlib import Path
import math

# Initialize pygame
pygame.init()

# --- Constants ---
INFO = pygame.display.Info()
SCREEN_WIDTH = INFO.current_w
SCREEN_HEIGHT = INFO.current_h
FPS = 60
TOTAL_TRIALS = 30

# --- Colors ---
COLOR_BACKGROUND = (240, 248, 255)
COLOR_TEXT = (40, 42, 54)
COLOR_SCORE_BOX = (255, 255, 255)
COLOR_SCORE_BOX_BORDER = (200, 200, 220)
BALLOON_COLOR_BASE = (220, 20, 60)
BALLOON_COLOR_HIGHLIGHT = (255, 255, 255, 60)
AIR_TANK_COLOR = (119, 136, 153)
AIR_TANK_HIGHLIGHT = (176, 196, 222)
AIR_HOSE_COLOR = (47, 79, 79)
PUMP_BUTTON_COLOR = (0, 150, 136)
PUMP_BUTTON_HOVER = (0, 178, 161)
COLLECT_BUTTON_COLOR = (33, 150, 243)
COLLECT_BUTTON_HOVER = (66, 165, 245)
BUTTON_TEXT_COLOR = (255, 255, 255)
BUTTON_SHADOW_COLOR = (40, 40, 50, 150)
WHITE = (255, 255, 255)

# --- Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Balloon Analogue Risk Task")
clock = pygame.time.Clock()

# --- Fonts ---
try:
    FONT_FAMILY = "Arial"
    if "Calibri" in pygame.font.get_fonts(): FONT_FAMILY = "Calibri"
    font = pygame.font.SysFont(FONT_FAMILY, 36)
    small_font = pygame.font.SysFont(FONT_FAMILY, 24)
    large_font = pygame.font.SysFont(FONT_FAMILY, 48, bold=True)
except Exception as e:
    print(f"Font loading failed: {e}. Using default.")
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    large_font = pygame.font.SysFont(None, 48, bold=True)


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


class Logger:
    """Logs trial data to a CSV file."""

    def __init__(self):
        self.data = []
        self.start_time = time.time()

    def log_trial(self, trial_num, pumps, outcome, points):
        self.data.append({
            "Trial": trial_num,
            "Pumps": pumps,
            "Outcome": outcome,
            "Points": points,
            "Timestamp": time.time() - self.start_time
        })

    def save_csv(self):
        if not self.data: return "No data to save."
        data_dir = Path("./bart_data")
        try:
            data_dir.mkdir(exist_ok=True)
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            filename = data_dir / f"bart_results_{timestamp_str}.csv"
            with open(filename, 'w', newline='') as f:
                fieldnames = ["Trial", "Pumps", "Outcome", "Points", "Timestamp"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.data)
            return f"Data saved to {filename.resolve()}"
        except Exception as e:
            return f"Error saving data: {e}"


class BalloonTask:
    def __init__(self):
        self.trial = 1
        self.total_score = 0
        self.logger = Logger()

        self.max_pumps_for_trials = [random.randint(1, 64) for _ in range(TOTAL_TRIALS)]
        random.shuffle(self.max_pumps_for_trials)

        button_width = 250
        button_height = 80
        button_y = SCREEN_HEIGHT - 150
        self.pump_button = Button(SCREEN_WIDTH * 0.25 - button_width / 2, button_y, button_width, button_height, "Pump",
                                  PUMP_BUTTON_COLOR, PUMP_BUTTON_HOVER)
        self.collect_button = Button(SCREEN_WIDTH * 0.75 - button_width / 2, button_y, button_width, button_height,
                                     "Collect", COLLECT_BUTTON_COLOR, COLLECT_BUTTON_HOVER)

        self.particles = []
        self.state = "instructions"

        # Appearance parameters
        self.base_radius = 60
        self.growth_per_pump = 5

        # --- MODIFIED PLACEMENT ---
        # Balloon's anchor is moved higher up the screen.
        self.balloon_anchor = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50)

        # Trajectory-based animation parameters
        self.sway_angle = 0
        self.sway_speed = 0.02
        self.sway_amplitude = 12
        self.pump_velocity_boost = 0.0

        self.tank_width = 100
        self.tank_height = 200
        self.tank_x = SCREEN_WIDTH / 2 - self.tank_width / 2
        self.tank_y = SCREEN_HEIGHT - self.tank_height - 20

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
            print(self.logger.save_csv())
            return

        self.pumps = 0
        self.points_this_trial = 0
        self.max_pumps_this_trial = self.max_pumps_for_trials[self.trial - 1]
        self.state = "active"
        self.sway_angle = 0
        self.pump_velocity_boost = 0.0

    def handle_pump(self):
        if self.state != "active": return
        self.pumps += 1
        self.points_this_trial += 5

        boost_amount = 0.15
        self.pump_velocity_boost += boost_amount * random.choice([-1, 1])

        if self.pumps >= self.max_pumps_this_trial:
            self.pop_balloon()

    def handle_collect(self):
        if self.state != "active" or self.pumps == 0: return
        self.total_score += self.points_this_trial
        self.logger.log_trial(self.trial, self.pumps, "COLLECT", self.points_this_trial)
        self.state = "banked"
        self.trial += 1

    def pop_balloon(self):
        self.logger.log_trial(self.trial, self.pumps, "POP", 0)
        self.state = "popped"
        self.trial += 1
        # Use the modified shape for particle explosion
        radius_x = self.current_radius * 0.9
        radius_y = self.current_radius * 1.0
        for _ in range(80):
            angle = random.uniform(0, 2 * math.pi)
            x = self.balloon_center_x + radius_x * math.cos(angle)
            y = self.balloon_center_y + radius_y * math.sin(angle)
            self.particles.append(Particle(x, y, BALLOON_COLOR_BASE))

    def update(self, mouse_pos):
        self.pump_button.check_hover(mouse_pos)
        self.collect_button.check_hover(mouse_pos)

        self.sway_angle += self.sway_speed + self.pump_velocity_boost

        if abs(self.pump_velocity_boost) > 0:
            self.pump_velocity_boost *= 0.92
            if abs(self.pump_velocity_boost) < 0.001:
                self.pump_velocity_boost = 0

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
            "Click 'Pump' to inflate the balloon and earn 5 cents per pump.",
            "At any point, you can click 'Collect' to bank the money from that balloon.",
            "However, each balloon has a random popping point!",
            "If the balloon pops, you lose all the money from that balloon.",
            "Your goal is to earn as much money as possible.",
            "",
            "Press ENTER to begin."
        ]
        y_pos = 250
        for line in instructions:
            text = font.render(line, True, COLOR_TEXT)
            surface.blit(text, text.get_rect(center=(SCREEN_WIDTH / 2, y_pos)))
            y_pos += 50

    def draw_end_screen(self, surface):
        surface.fill(COLOR_BACKGROUND)
        title = large_font.render("Task Complete!", True, COLOR_TEXT)
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 200)))
        final_score = font.render(f"Your final score is: {self.total_score} cents", True, COLOR_TEXT)
        surface.blit(final_score, final_score.get_rect(center=(SCREEN_WIDTH / 2, 350)))
        save_msg = self.logger.save_csv()
        save_text = small_font.render(save_msg, True, COLOR_TEXT)
        surface.blit(save_text, save_text.get_rect(center=(SCREEN_WIDTH / 2, 450)))
        exit_text = font.render("Press ESC to exit.", True, COLOR_TEXT)
        surface.blit(exit_text, exit_text.get_rect(center=(SCREEN_WIDTH / 2, 600)))

    def draw_balloon(self, surface):
        # --- MODIFIED SHAPE ---
        # The y-radius is now smaller, making the balloon less tall.
        radius_x = self.current_radius * 0.9
        radius_y = self.current_radius * 1.0  # Changed from 1.2
        center_x, center_y = int(self.balloon_center_x), int(self.balloon_center_y)

        pygame.draw.ellipse(surface, BALLOON_COLOR_BASE,
                            (center_x - radius_x, center_y - radius_y, 2 * radius_x, 2 * radius_y))

        highlight_surf = pygame.Surface((radius_x * 2, radius_y * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(highlight_surf, BALLOON_COLOR_HIGHLIGHT,
                            (radius_x * 0.2, radius_y * 0.2, radius_x * 1.2, radius_y * 1.2))
        surface.blit(highlight_surf, (center_x - radius_x, center_y - radius_y))

        knot_radius = 10
        knot_y = center_y + radius_y
        pygame.draw.circle(surface, BALLOON_COLOR_BASE, (center_x, int(knot_y)), knot_radius)

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
        # --- MODIFIED HOSE CONNECTION POINT ---
        # Adjusted to match the new, shorter balloon shape.
        knot_y = int(self.balloon_center_y + self.current_radius * 1.0) + 10  # Changed from 1.2
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
            feedback = large_font.render("POP!", True, BALLOON_COLOR_BASE)
            surface.blit(feedback, feedback.get_rect(center=(self.balloon_anchor[0], self.balloon_anchor[1])))
        elif self.state == "banked":
            feedback = large_font.render("Collected!", True, COLLECT_BUTTON_COLOR)
            surface.blit(feedback, feedback.get_rect(center=(self.balloon_anchor[0], self.balloon_anchor[1])))

        if self.state == "active":
            self.pump_button.draw(surface)
            if self.pumps > 0: self.collect_button.draw(surface)
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
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == "active":
                    if game.pump_button.rect.collidepoint(mouse_pos): game.handle_pump()
                    if game.pumps > 0 and game.collect_button.rect.collidepoint(mouse_pos): game.handle_collect()

        game.update(mouse_pos)

        if game.state == "instructions":
            game.draw_instructions(screen)
        elif game.state == "end":
            game.draw_end_screen(screen)
        else:
            game.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    if game.logger.data and game.state != "end":
        print("Game exited prematurely. Saving data...")
        print(game.logger.save_csv())

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()