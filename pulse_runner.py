import asyncio
import platform
import pygame
import random
import numpy as np
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pulse Runner")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# Player settings
player_size = 20
player_speed = 5
player_y = HEIGHT // 2
player_x = 100

# Track settings
track_points = []
track_offset = 0
track_speed = 3

# Energy settings
energy_size = 15
energies = []
energy_spawn_rate = 60
energy_spawn_counter = 0

# Shock settings
shock_size = 20
shock_speed = 4
shocks = []
shock_spawn_rate = 80
shock_spawn_counter = 0

# Score and font
score = 0
font = pygame.font.SysFont("arial", 24)

# Sound setup (NumPy for Pyodide compatibility)
sample_rate = 44100
duration = 0.12
t = np.linspace(0, duration, int(sample_rate * duration))
sound_array = np.sin(2 * np.pi * 770 * t) * 32767
sound_array = np.column_stack((sound_array, sound_array)).astype(np.int16)
collect_sound = pygame.sndarray.make_sound(sound_array)

# Game state
running = True
game_over = False
clock = pygame.time.Clock()
FPS = 60

def setup():
    global track_points, energies, shocks, score, player_y, running, game_over, track_offset
    track_points = []
    energies = []
    shocks = []
    score = 0
    player_y = HEIGHT // 2
    track_offset = 0
    running = True
    game_over = False
    # Initialize track
    for x in range(WIDTH + 1):
        y = HEIGHT // 2 + math.sin(x * 0.01) * 100
        track_points.append((x, y))
    # Spawn initial energies and shocks
    for _ in range(3):
        spawn_energy()
        spawn_shock()

def spawn_energy():
    x = WIDTH
    track_y = HEIGHT // 2 + math.sin((x + track_offset) * 0.01) * 100
    energies.append([x, track_y, random.uniform(0, 2 * math.pi)])

def spawn_shock():
    x = WIDTH
    track_y = HEIGHT // 2 + math.sin((x + track_offset) * 0.01) * 100
    shocks.append([x, track_y, random.uniform(-2, 2)])

def update_loop():
    global running, game_over, score, track_offset, energy_spawn_counter, shock_spawn_counter

    if not running:
        return

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_r:
                setup()

    if game_over:
        return

    # Player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        player_y -= player_speed
    if keys[pygame.K_DOWN]:
        player_y += player_speed
    player_y = max(player_size // 2, min(HEIGHT - player_size // 2, player_y))

    # Update track
    track_offset += track_speed
    track_points = []
    for x in range(WIDTH + 1):
        y = HEIGHT // 2 + math.sin((x + track_offset) * 0.01) * 100
        track_points.append((x, y))

    # Spawn energies and shocks
    energy_spawn_counter += 1
    if energy_spawn_counter >= energy_spawn_rate:
        spawn_energy()
        energy_spawn_counter = 0

    shock_spawn_counter += 1
    if shock_spawn_counter >= shock_spawn_rate:
        spawn_shock()
        shock_spawn_counter = 0

    # Update energies
    for energy in energies[:]:
        energy[0] -= track_speed
        energy[2] += 0.1  # Update phase for blinking
        energy[1] = HEIGHT // 2 + math.sin((energy[0] + track_offset) * 0.01) * 100
        if energy[0] < -energy_size:
            energies.remove(energy)

    # Update shocks
    for shock in shocks[:]:
        shock[0] -= track_speed
        shock[1] += shock[2]  # Random vertical drift
        if shock[0] < -shock_size:
            shocks.remove(shock)

    # Collision detection
    player_rect = pygame.Rect(player_x - player_size // 2, player_y - player_size // 2, player_size, player_size)
    for energy in energies[:]:
        energy_rect = pygame.Rect(energy[0] - energy_size // 2, energy[1] - energy_size // 2, energy_size, energy_size)
        if player_rect.colliderect(energy_rect):
            energies.remove(energy)
            score += 10
            collect_sound.play()
            spawn_energy()

    for shock in shocks:
        shock_rect = pygame.Rect(shock[0] - shock_size // 2, shock[1] - shock_size // 2, shock_size, shock_size)
        if player_rect.colliderect(shock_rect):
            game_over = True
            break

    # Increase score
    score += 0.1

    # Draw everything
    screen.fill(BLACK)
    # Draw track
    pygame.draw.lines(screen, BLUE, False, track_points, 5)
    # Draw player
    pygame.draw.circle(screen, WHITE, (int(player_x), int(player_y)), player_size // 2)
    # Draw energies with blinking effect
    for energy in energies:
        alpha = (math.sin(energy[2]) + 1) / 2 * 255
        color = (0, min(255, int(alpha)), 0)
        pygame.draw.circle(screen, color, (int(energy[0]), int(energy[1])), energy_size // 2)
    # Draw shocks
    for shock in shocks:
        pygame.draw.circle(screen, RED, (int(shock[0]), int(shock[1])), shock_size // 2)
    # Draw score
    score_text = font.render(f"Score: {int(score)}", True, WHITE)
    screen.blit(score_text, (10, 10))
    # Draw game over
    if game_over:
        game_over_text = font.render("Game Over! Press R to Restart", True, RED)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))

    pygame.display.flip()

async def main():
    setup()
    while running:
        update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
