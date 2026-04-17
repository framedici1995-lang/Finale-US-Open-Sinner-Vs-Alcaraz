import pygame
import sys
import random
import array
import math
import os

# --- LOGICA PER I PERCORSI ---
# Trova la cartella dove si trova fisicamente questo file .py
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def get_path(relative_path):
    """Converte un percorso relativo in uno assoluto"""
    return os.path.join(BASE_PATH, relative_path)

# --- Inizializzazione ---
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

# Dimensioni finestra 2026
WIDTH, HEIGHT = 800, 750 
GAME_AREA_OFFSET = 150  
COURT_HEIGHT = HEIGHT - GAME_AREA_OFFSET

BALL_SIZE = 15
PADDLE_WIDTH, PADDLE_HEIGHT = 60, 90 
FPS = 60

# --- COLORI ---
US_OPEN_BLUE_OUTSIDE = (0, 38, 120)
US_OPEN_GREEN_INSIDE = (0, 110, 80)
WHITE = (240, 240, 240)
GOLD = (255, 215, 0)
BLACK_BOARD = (10, 10, 10) 
NEON_GREEN = (57, 255, 20)
RED_PADDLE = (255, 0, 0)
ORANGE_PADDLE = (255, 100, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sinner vs Alcaraz: Grand Slam US Open 2026")
clock = pygame.time.Clock()

font_main = pygame.font.Font(None, 80)
font_menu = pygame.font.Font(None, 45)
font_score = pygame.font.SysFont("monospace", 35, bold=True) 

# --- FUNZIONI AUDIO (Generate via codice, non servono file esterni) ---
def create_8bit_sound(kind="hit", duration=0.1, volume=0.3):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = i / sample_rate
        freq = 440
        if kind == "bounce": freq = 150
        elif kind == "score": freq = 440 + (i / n_samples) * 440
        elif kind == "fail": freq = 600 - (i / n_samples) * 500
        val = 1 if math.sin(2 * math.pi * freq * t) > 0 else -1
        buf[i] = int(val * volume * 32767 * (1 - i / n_samples))
    return pygame.mixer.Sound(buf)

sound_hit = create_8bit_sound("hit", 0.1)
sound_bounce = create_8bit_sound("bounce", 0.15)
sound_score = create_8bit_sound("score", 0.4)
sound_fail = create_8bit_sound("fail", 0.5)

# --- CLASSE PUNTEGGIO ---
class TennisScoreSystem:
    def __init__(self):
        self.points = [0, 0] # [0: Alcaraz, 1: Sinner]
        self.games = [0, 0]
        self.sets = [0, 0]
        self.score_labels = {0: "00", 1: "15", 2: "30", 3: "40"}
        self.game_in_progress = True

    def add_point(self, player_index):
        if not self.game_in_progress: return
        other = 1 if player_index == 0 else 0
        self.points[player_index] += 1
        if self.points[player_index] >= 4 and self.points[player_index] >= self.points[other] + 2:
            self._win_game(player_index)
        elif self.points[other] >= 4 and self.points[other] >= self.points[player_index]:
            self.points[player_index] = min(self.points[player_index], 3)
            self.points[other] = min(self.points[other], 3)

    def _win_game(self, player_index):
        self.games[player_index] += 1
        self.points = [0, 0]
        other = 1 if player_index == 0 else 0
        if self.games[player_index] >= 6 and self.games[player_index] >= self.games[other] + 2:
            self._win_set(player_index)
        
    def _win_set(self, player_index):
        self.sets[player_index] += 1
        self.games = [0, 0]
        if self.sets[player_index] == 2: self.game_in_progress = False

    def get_current_pts(self, idx):
        p0, p1 = self.points[0], self.points[1]
        if p0 >= 3 and p1 >= 3:
            if p0 == p1: return "40"
            if idx == 0: return "AD" if p0 > p1 else "--"
            if idx == 1: return "AD" if p1 > p0 else "--"
        return self.score_labels.get(self.points[idx], "40")

# --- CARICAMENTO IMMAGINI CORRETTO ---
def load_img(path, size):
    full_path = get_path(path) # Forza la ricerca nella cartella corretta
    if os.path.exists(full_path):
        return pygame.transform.scale(pygame.image.load(full_path).convert_alpha(), size)
    else:
        print(f"Attenzione: Immagine non trovata in {full_path}")
    return None

img_sinner = load_img("sinner.png", (PADDLE_WIDTH, PADDLE_HEIGHT))
img_alcaraz = load_img("alcaraz.png", (PADDLE_WIDTH, PADDLE_HEIGHT))
img_sinner_big = load_img("sinner.png", (220, 320))
img_alcaraz_big = load_img("alcaraz.png", (220, 320))

# --- STATO GIOCO ---
MENU, CHAR_SELECT, PLAYING, WINNER = 0, 1, 2, 3
game_state, difficulty = MENU, 1
selected_player = "SINNER" 
ball = pygame.Rect(WIDTH // 2, GAME_AREA_OFFSET + COURT_HEIGHT // 2, BALL_SIZE, BALL_SIZE)
player = pygame.Rect(WIDTH - 70, GAME_AREA_OFFSET + COURT_HEIGHT // 2 - 45, PADDLE_WIDTH, PADDLE_HEIGHT)
opponent = pygame.Rect(10, GAME_AREA_OFFSET + COURT_HEIGHT // 2 - 45, PADDLE_WIDTH, PADDLE_HEIGHT)
ball_speed_x, ball_speed_y, player_speed = 7, 7, 0
score_system = TennisScoreSystem()

def reset_ball():
    global ball_speed_x, ball_speed_y
    ball.center = (WIDTH // 2, GAME_AREA_OFFSET + COURT_HEIGHT // 2)
    ball_speed_x = 7 * random.choice((-1, 1))
    ball_speed_y = 7 * random.uniform(-0.8, 0.8)

# --- LOOP PRINCIPALE ---
while True:
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        
        if game_state == MENU:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    difficulty = int(event.unicode); game_state = CHAR_SELECT
        
        elif game_state == CHAR_SELECT:
            alc_rect = pygame.Rect(100, 250, 220, 320)
            sin_rect = pygame.Rect(480, 250, 220, 320)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if alc_rect.collidepoint(mouse_pos): selected_player = "ALCARAZ"; game_state = PLAYING; reset_ball()
                if sin_rect.collidepoint(mouse_pos): selected_player = "SINNER"; game_state = PLAYING; reset_ball()

        elif game_state == PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: player_speed = -9
                if event.key == pygame.K_DOWN: player_speed = 9
            if event.type == pygame.KEYUP: player_speed = 0
            
        elif game_state == WINNER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                score_system = TennisScoreSystem(); game_state = MENU

    if game_state == PLAYING:
        ball.x += ball_speed_x; ball.y += ball_speed_y
        player.y += player_speed; player.clamp_ip(pygame.Rect(0, GAME_AREA_OFFSET, WIDTH, COURT_HEIGHT))
        speed_ia = 4 + (difficulty * 2)
        if opponent.centery < ball.centery: opponent.y += speed_ia
        else: opponent.y -= speed_ia
        opponent.clamp_ip(pygame.Rect(0, GAME_AREA_OFFSET, WIDTH, COURT_HEIGHT))
        if ball.top <= GAME_AREA_OFFSET or ball.bottom >= HEIGHT: ball_speed_y *= -1; sound_bounce.play()
        if (ball.colliderect(player) and ball_speed_x > 0) or (ball.colliderect(opponent) and ball_speed_x < 0): ball_speed_x *= -1.05; sound_hit.play()
        if ball.right >= WIDTH:
            score_system.add_point(0); sound_fail.play(); reset_ball()
            if not score_system.game_in_progress: game_state = WINNER
        elif ball.left <= 0:
            score_system.add_point(1); sound_score.play(); reset_ball()
            if not score_system.game_in_progress: game_state = WINNER

    # --- RENDERING ---
    screen.fill(US_OPEN_BLUE_OUTSIDE)

    # Tabellone
    pygame.draw.rect(screen, BLACK_BOARD, (0, 0, WIDTH, GAME_AREA_OFFSET))
    pygame.draw.line(screen, GOLD, (0, GAME_AREA_OFFSET), (WIDTH, GAME_AREA_OFFSET), 4)
    screen.blit(font_score.render(f"C. ALCARAZ", True, RED_PADDLE), (40, 30))
    screen.blit(font_score.render(f"SETS:{score_system.sets[0]} GAMES:{score_system.games[0]}", True, WHITE), (300, 30))
    screen.blit(font_score.render(f"{score_system.get_current_pts(0)}", True, NEON_GREEN), (WIDTH - 100, 30))
    screen.blit(font_score.render(f"J. SINNER", True, ORANGE_PADDLE), (40, 85))
    screen.blit(font_score.render(f"SETS:{score_system.sets[1]} GAMES:{score_system.games[1]}", True, WHITE), (300, 85))
    screen.blit(font_score.render(f"{score_system.get_current_pts(1)}", True, NEON_GREEN), (WIDTH - 100, 85))

    # Campo
    court_rect = pygame.Rect(50, GAME_AREA_OFFSET + 30, WIDTH - 100, COURT_HEIGHT - 60)
    pygame.draw.rect(screen, US_OPEN_GREEN_INSIDE, court_rect)
    pygame.draw.rect(screen, WHITE, court_rect, 3) 
    alley_h = int(court_rect.height * (1.37 / 10.97))
    pygame.draw.line(screen, WHITE, (court_rect.left, court_rect.top + alley_h), (court_rect.right, court_rect.top + alley_h), 2)
    pygame.draw.line(screen, WHITE, (court_rect.left, court_rect.bottom - alley_h), (court_rect.right, court_rect.bottom - alley_h), 2)
    pygame.draw.line(screen, WHITE, (court_rect.centerx, court_rect.top), (court_rect.centerx, court_rect.bottom), 5)
    service_dist_x = int((court_rect.width / 2) * (6.40 / (23.77/2)))
    pygame.draw.line(screen, WHITE, (court_rect.centerx - service_dist_x, court_rect.top + alley_h), (court_rect.centerx - service_dist_x, court_rect.bottom - alley_h), 2)
    pygame.draw.line(screen, WHITE, (court_rect.centerx + service_dist_x, court_rect.top + alley_h), (court_rect.centerx + service_dist_x, court_rect.bottom - alley_h), 2)
    pygame.draw.line(screen, WHITE, (court_rect.centerx - service_dist_x, court_rect.centery), (court_rect.centerx + service_dist_x, court_rect.centery), 2)
    pygame.draw.line(screen, WHITE, (court_rect.left, court_rect.centery - 10), (court_rect.left, court_rect.centery + 10), 2)
    pygame.draw.line(screen, WHITE, (court_rect.right, court_rect.centery - 10), (court_rect.right, court_rect.centery + 10), 2)

    if game_state == MENU:
        title = font_main.render("US OPEN 2026", True, NEON_GREEN)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2))
        msg = font_menu.render("1 Facile | 2 Normale | 3 Leggendario", True, WHITE)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 + 80))

    elif game_state == CHAR_SELECT:
        alc_rect = pygame.Rect(100, 250, 220, 320)
        sin_rect = pygame.Rect(480, 250, 220, 320)
        titolo_selezione = font_main.render("SCEGLI IL TUO CAMPIONE", True, GOLD)
        screen.blit(titolo_selezione, (WIDTH // 2 - titolo_selezione.get_width() // 2, 180))
        
        # Alcaraz
        col_a = GOLD if alc_rect.collidepoint(mouse_pos) else RED_PADDLE
        pygame.draw.rect(screen, col_a, alc_rect, 5, border_radius=10)
        if img_alcaraz_big: screen.blit(img_alcaraz_big, alc_rect.topleft)
        txt_a = font_menu.render("ALCARAZ", True, col_a)
        screen.blit(txt_a, (alc_rect.centerx - txt_a.get_width() // 2, 580))

        # Sinner
        col_s = GOLD if sin_rect.collidepoint(mouse_pos) else ORANGE_PADDLE
        pygame.draw.rect(screen, col_s, sin_rect, 5, border_radius=10)
        if img_sinner_big: screen.blit(img_sinner_big, sin_rect.topleft)
        txt_s = font_menu.render("SINNER", True, col_s)
        screen.blit(txt_s, (sin_rect.centerx - txt_s.get_width() // 2, 580))

    elif game_state == PLAYING:
        if selected_player == "SINNER": p_img, o_img = img_sinner, img_alcaraz
        else: p_img, o_img = img_alcaraz, img_sinner
        if o_img: screen.blit(o_img, opponent)
        else: pygame.draw.rect(screen, RED_PADDLE, opponent)
        if p_img: screen.blit(p_img, player)
        else: pygame.draw.rect(screen, ORANGE_PADDLE, player)
        pygame.draw.ellipse(screen, NEON_GREEN, ball)

    elif game_state == WINNER:
        winner_name = "SINNER" if score_system.sets[1] > score_system.sets[0] else "ALCARAZ"
        txt_vittoria = font_main.render(f"CAMPIONE: {winner_name}!", True, GOLD)
        screen.blit(txt_vittoria, (WIDTH // 2 - txt_vittoria.get_width() // 2, HEIGHT // 2))
        msg_restart = font_menu.render("SPAZIO per rigiocare", True, WHITE)
        screen.blit(msg_restart, (WIDTH // 2 - msg_restart.get_width() // 2, HEIGHT // 2 + 80))

    pygame.display.flip()
    clock.tick(FPS)