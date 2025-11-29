# car_dodger_safe.py
# Lane dodger with obstacle-occupancy checks and forward/backward movement + on-screen buttons.
import pygame
import random
import os

# --------- Configuration ----------
WIDTH, HEIGHT = 480, 640
FPS = 60

LANE_COUNT = 3
ROAD_MARGIN = 20
LANE_WIDTH = (WIDTH - ROAD_MARGIN * 2) // LANE_COUNT  # account for road margins
LANE_X = [ROAD_MARGIN + i * LANE_WIDTH + LANE_WIDTH // 2 for i in range(LANE_COUNT)]  # center x of each lane

PLAYER_WIDTH, PLAYER_HEIGHT = 50, 90
OBSTACLE_BASE_WIDTH, OBSTACLE_BASE_HEIGHT = 52, 80

HIGH_SCORE_FILE = "highscore.txt"

# Colors
WHITE = (255, 255, 255)
BLACK = (12, 12, 12)
ROAD_GRAY = (40, 40, 40)
PLAYER_COLOR = (50, 200, 50)   # green player car
OBSTACLE_COLORS = [
    (200, 50, 50),   # red
    (20, 120, 220),  # blue
    (230, 180, 20),  # yellow
    (150, 50, 190),  # purple
]
WINDOW_COLOR = (180, 230, 255)
WHEEL_COLOR = (20, 20, 20)
SKY = (135, 206, 235)
DASH = (200, 200, 200)

# Movement
FORWARD_STEP = 60  # pixels the player moves forward (up)
BACKWARD_STEP = 60  # pixels the player moves backward (down)
PLAYER_MIN_Y = 80
PLAYER_MAX_Y = HEIGHT - PLAYER_HEIGHT - 20

# On-screen button sizes
BTN_W, BTN_H = 56, 36
BTN_PAD = 10

# --------- Helper functions ----------
def load_high_score():
    try:
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, "r") as f:
                return int(f.read().strip() or 0)
    except Exception:
        pass
    return 0

def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(int(score)))
    except Exception:
        pass

# --------- Game Objects ----------
class Player:
    def __init__(self):
        self.lane = 1  # start in middle lane
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        # start near bottom but allow moving forward/back
        self.y = PLAYER_MAX_Y
        self.rect = pygame.Rect(0, self.y, self.width, self.height)
        self.update_rect()

    def update_rect(self):
        center_x = LANE_X[self.lane]
        self.rect.x = center_x - self.width // 2
        self.rect.y = int(self.y)

    def can_move_to_lane(self, target_lane, obstacles):
        """
        Returns True if moving to target_lane would not overlap any current obstacle.
        Uses current self.y to check overlap zone.
        """
        # Build hypothetical rect at the target lane (same y)
        center_x = LANE_X[target_lane]
        target_rect = pygame.Rect(center_x - self.width // 2, int(self.y), self.width, self.height)
        for obs in obstacles:
            if target_rect.colliderect(obs.rect):
                return False
            # Also block if obstacle is just slightly overlapping vertically (close proximity)
            # e.g., obstacle near the player's area (within 12 px) to avoid clipping through.
            proximity_margin = 8
            expanded = obs.rect.inflate(0, proximity_margin)
            if target_rect.colliderect(expanded):
                return False
        return True

    def try_move_left(self, obstacles):
        if self.lane == 0:
            return False
        target_lane = self.lane - 1
        if self.can_move_to_lane(target_lane, obstacles):
            self.lane = target_lane
            self.update_rect()
            return True
        return False

    def try_move_right(self, obstacles):
        if self.lane == LANE_COUNT - 1:
            return False
        target_lane = self.lane + 1
        if self.can_move_to_lane(target_lane, obstacles):
            self.lane = target_lane
            self.update_rect()
            return True
        return False

    def move_forward(self):
        # moving "forward" = up (decrease y)
        self.y = max(PLAYER_MIN_Y, self.y - FORWARD_STEP)
        self.update_rect()

    def move_backward(self):
        # moving "backward" = down (increase y)
        self.y = min(PLAYER_MAX_Y, self.y + BACKWARD_STEP)
        self.update_rect()

    def draw(self, surface):
        # car body
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect, border_radius=8)
        # windows
        win = pygame.Rect(self.rect.x + 8, self.rect.y + 12, self.rect.width - 16, 24)
        pygame.draw.rect(surface, WINDOW_COLOR, win, border_radius=4)
        # wheels
        wheel_h = 10
        pygame.draw.rect(surface, WHEEL_COLOR, (self.rect.x + 6, self.rect.y + self.height - wheel_h, 18, wheel_h), border_radius=3)
        pygame.draw.rect(surface, WHEEL_COLOR, (self.rect.x + self.rect.width - 24, self.rect.y + self.height - wheel_h, 18, wheel_h), border_radius=3)

class ObstacleCar:
    def __init__(self, lane, speed):
        # slight random size variation to make traffic feel varied
        w_variation = random.randint(-6, 8)
        h_variation = random.randint(-8, 10)
        self.width = max(36, OBSTACLE_BASE_WIDTH + w_variation)
        self.height = max(48, OBSTACLE_BASE_HEIGHT + h_variation)
        self.lane = lane
        self.x = LANE_X[lane] - self.width // 2
        # spawn slightly above screen
        self.y = -self.height - random.randint(0, 120)
        self.speed = speed
        self.color = random.choice(OBSTACLE_COLORS)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, dt):
        self.y += self.speed * dt
        self.rect.y = int(self.y)

    def draw(self, surface):
        # car body
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        # window (smaller than player windows, tinted)
        win = pygame.Rect(self.rect.x + int(self.width*0.12), self.rect.y + int(self.height*0.12),
                          int(self.width*0.76), int(self.height*0.22))
        pygame.draw.rect(surface, WINDOW_COLOR, win, border_radius=3)
        # small decoration (headlight-ish)
        head_w = max(4, self.width // 10)
        pygame.draw.rect(surface, (255, 255, 200), (self.rect.x + 6, self.rect.y + self.height - int(self.height*0.75), head_w, head_w))
        pygame.draw.rect(surface, (255, 255, 200), (self.rect.x + self.width - 6 - head_w, self.rect.y + self.height - int(self.height*0.75), head_w, head_w))
        # wheels - front and back
        wheel_h = max(8, self.height // 8)
        pygame.draw.rect(surface, WHEEL_COLOR, (self.rect.x + 6, self.rect.y + self.height - wheel_h, int(self.width*0.28), wheel_h), border_radius=3)
        pygame.draw.rect(surface, WHEEL_COLOR, (self.rect.x + self.width - int(self.width*0.28) - 6, self.rect.y + self.height - wheel_h, int(self.width*0.28), wheel_h), border_radius=3)

# --------- Main Game ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Car Lane Dodger - Safe Moves")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 26)
    big_font = pygame.font.SysFont(None, 56)
    small_font = pygame.font.SysFont(None, 20)

    high_score = load_high_score()

    def new_game():
        player = Player()
        obstacles = []
        score = 0
        spawn_timer = 0.0
        spawn_interval = 1.25
        game_over = False
        return player, obstacles, score, spawn_timer, spawn_interval, game_over

    player, obstacles, score, spawn_timer, spawn_interval, game_over = new_game()
    running = True

    # button rects (bottom-right)
    btn_x = WIDTH - ROAD_MARGIN - BTN_W
    btn_y_up = HEIGHT - ROAD_MARGIN - BTN_H*2 - BTN_PAD
    btn_y_down = HEIGHT - ROAD_MARGIN - BTN_H
    btn_up_rect = pygame.Rect(btn_x, btn_y_up, BTN_W, BTN_H)
    btn_down_rect = pygame.Rect(btn_x, btn_y_down, BTN_W, BTN_H)

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if not game_over:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        player.try_move_left(obstacles)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        player.try_move_right(obstacles)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        player.move_forward()
                        # after moving forward, ensure we didn't clip into an obstacle in same lane
                        # if clipping, revert move
                        player.update_rect()
                        for obs in obstacles:
                            if player.rect.colliderect(obs.rect):
                                player.move_backward()
                                break
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        player.move_backward()
                        # check clipping and revert
                        player.update_rect()
                        for obs in obstacles:
                            if player.rect.colliderect(obs.rect):
                                player.move_forward()
                                break
                else:
                    if event.key == pygame.K_r:
                        player, obstacles, score, spawn_timer, spawn_interval, game_over = new_game()
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if not game_over:
                    if btn_up_rect.collidepoint(mx, my):
                        player.move_forward()
                        player.update_rect()
                        # revert if overlapped
                        for obs in obstacles:
                            if player.rect.colliderect(obs.rect):
                                player.move_backward()
                                break
                    elif btn_down_rect.collidepoint(mx, my):
                        player.move_backward()
                        player.update_rect()
                        for obs in obstacles:
                            if player.rect.colliderect(obs.rect):
                                player.move_forward()
                                break
                else:
                    # clicking anywhere when game over -> ignore (or could restart)
                    pass

        if not game_over:
            # scale difficulty by score
            base_speed = 150 + (score * 6)
            spawn_interval = max(0.45, 1.2 - score * 0.025)

            spawn_timer += dt
            if spawn_timer >= spawn_interval:
                spawn_timer = 0.0
                # spawn across all lanes (including middle)
                lane = random.choice([0, 1, 2])
                speed = base_speed * (0.9 + random.random() * 0.5)
                obstacles.append(ObstacleCar(lane, speed))

            # update obstacles
            for obs in obstacles:
                obs.update(dt)

            # remove off-screen and increment score for passed obstacles
            survived = []
            for obs in obstacles:
                if obs.rect.top > HEIGHT:
                    score += 1
                else:
                    survived.append(obs)
            obstacles = survived

            # collision detection
            player.update_rect()
            for obs in obstacles:
                if player.rect.colliderect(obs.rect):
                    game_over = True
                    if score > high_score:
                        high_score = score
                        save_high_score(high_score)
                    break

        # ----- draw -----
        screen.fill(SKY)

        # draw road
        road_rect = pygame.Rect(ROAD_MARGIN, 0, WIDTH - ROAD_MARGIN * 2, HEIGHT)
        pygame.draw.rect(screen, ROAD_GRAY, road_rect)

        # lane lines (solid separators at edges)
        pygame.draw.line(screen, WHITE, (ROAD_MARGIN, 0), (ROAD_MARGIN, HEIGHT), 4)
        pygame.draw.line(screen, WHITE, (WIDTH - ROAD_MARGIN, 0), (WIDTH - ROAD_MARGIN, HEIGHT), 4)

        # dashed separators between lanes
        for i in range(1, LANE_COUNT):
            x = ROAD_MARGIN + i * LANE_WIDTH
            for y in range(0, HEIGHT, 36):
                pygame.draw.rect(screen, DASH, (x - 2, y + 6, 4, 20))

        # draw player and obstacles
        player.draw(screen)
        for obs in obstacles:
            obs.draw(screen)

        # HUD
        score_surf = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_surf, (8, 8))
        hs_surf = font.render(f"High: {high_score}", True, WHITE)
        screen.blit(hs_surf, (WIDTH - hs_surf.get_width() - 8, 8))
        tip = small_font.render("← → or A D to change lanes (blocked if occupied). ↑ ↓ or W S to move forward/back.", True, WHITE)
        screen.blit(tip, (8, HEIGHT - 60))

        # draw on-screen buttons
        pygame.draw.rect(screen, (220, 220, 220), btn_up_rect, border_radius=6)
        pygame.draw.rect(screen, (220, 220, 220), btn_down_rect, border_radius=6)
        up_text = small_font.render("UP", True, BLACK)
        down_text = small_font.render("DOWN", True, BLACK)
        screen.blit(up_text, (btn_up_rect.centerx - up_text.get_width()//2, btn_up_rect.centery - up_text.get_height()//2))
        screen.blit(down_text, (btn_down_rect.centerx - down_text.get_width()//2, btn_down_rect.centery - down_text.get_height()//2))

        if game_over:
            # overlay
            over_surf = big_font.render("GAME OVER", True, BLACK)
            sub_surf = font.render("Press R to restart  •  Q or ESC to quit", True, BLACK)
            final_surf = font.render(f"Final Score: {score}", True, BLACK)
            screen.blit(over_surf, (WIDTH // 2 - over_surf.get_width() // 2, HEIGHT // 2 - 70))
            screen.blit(final_surf, (WIDTH // 2 - final_surf.get_width() // 2, HEIGHT // 2 - 10))
            screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
