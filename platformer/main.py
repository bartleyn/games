import pygame
import random
import numpy as np
from sklearn.linear_model import LinearRegression

from platform_ml import PlatformRegressor
# Example import, you can extend this with ML models later

# Initialize Pygame
pygame.init()

# Define game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
LEVEL_WIDTH = 15000
FPS = 60

# Setup display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Adaptive Stick Figure Platformer")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

camera_x = 0

background_image = pygame.image.load('backdrop.png')
background_image.set_alpha(85)
background_image = pygame.transform.scale(background_image, (LEVEL_WIDTH, SCREEN_HEIGHT))  # Scale to fit the screen

platform_regressor = PlatformRegressor()

def fade_to_black(screen, duration=1, text=None):
    """Fades the screen to black over a specified duration."""
    overlay = pygame.Surface(screen.get_size())
    overlay.fill((0, 0, 0))  # Fill the overlay with black
    font = pygame.font.Font(None, 74)
    text_surface = font.render(text, True, (255, 255, 255))  # Render the text (white color)
    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//4, SCREEN_HEIGHT // 2))  # Center the text

    for alpha in range(0, 255, 5):  # Increase alpha from 0 to 255
        overlay.set_alpha(alpha)  # Set the alpha value
        screen.blit(overlay, (0, 0))  # Draw the overlay
        if text:
            screen.blit(text_surface, text_rect)
        pygame.display.flip()  # Update the display
        pygame.time.delay(int(duration * 1000 / 51))  # Delay to control speed

def fade_from_black(screen, duration=1):
    """Fades the screen from black over a specified duration."""
    overlay = pygame.Surface(screen.get_size())
    overlay.fill((0, 0, 0))  # Fill the overlay with black
    for alpha in range(255, 0, -5):  # Decrease alpha from 255 to 0
        overlay.set_alpha(alpha)  # Set the alpha value
        screen.blit(overlay, (0, 0))  # Draw the overlay
        pygame.display.flip()  # Update the display
        pygame.time.delay(int(duration * 1000 / 51))  # Delay to control speed

avg_jump_dist = 0.0
# Define player object (stick figure)
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 60))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.center = (100, SCREEN_HEIGHT - 100)
        self.velocity = 0
        self.v_x = 0
        self.jump_timer = 0
        self.jumping = False
        self.jump_start_x = None
        self.total_jumps = 0
        self.total_dist = 0.0


    def update(self, keys, platforms, e_type):
        # Basic movement logic (jumping, falling)
        #print("current rect ", self.rect.x, self.rect.y, self.velocity)
        keys2 = pygame.key.get_pressed()
        if keys2[pygame.K_SPACE]:#== pygame.K_SPACE:#keys[pygame.K_SPACE]:
            self.velocity = -25  # jump
            self.jump_timer += 1
            self.jumping = True
            if self.jump_start_x is None:
                self.jump_start_x = self.rect.x
            #print("jump")
        if keys2[pygame.K_RIGHT]:# == pygame.K_RIGHT:
            self.v_x = 10
        elif keys2[pygame.K_LEFT]:# == pygame.K_LEFT:
            self.v_x = -10
        else:
        #    self.v_x = 0
            if self.jumping and not keys2[pygame.K_SPACE]:
                #print("yo", keys2[pygame.K_SPACE])
                self.velocity = -min(25, self.jump_timer)
                self.jump_timer = 0
                self.jumping = False
            
                #if keys == pygame.K_SPACE:


      

        # Simulate gravity
        self.velocity += 1  # gravity pull


        # Simple ground check
        if self.rect.y > SCREEN_HEIGHT - 60:
            #print("am i here")
            self.rect.y = SCREEN_HEIGHT - 60
            self.velocity = 0

        
        plt_ctr = 0
        if any([self.rect.colliderect(x.rect) for x in platforms.sprites()]):
            for platform in platforms.sprites():
                if self.rect.colliderect(platform.rect) and self.velocity >= 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity = 0

                    if self.jump_start_x is not None:
                        jump_dist = abs(self.rect.x - self.jump_start_x)
                        self.total_dist += jump_dist
                        self.total_jumps += 1
                        avg_jump_dist = self.total_dist / self.total_jumps
                        gap = jump_dist
                        platform_regressor.record_jump(gap, [avg_jump_dist, plt_ctr, level_difficulty, 1])
                        self.jump_start_x = None
                    break
                plt_ctr += 1
        
        if self.velocity == 0 and self.jump_start_x is not None:
            jump_dist = abs(self.rect.x - self.jump_start_x)
            self.total_dist += jump_dist
            self.total_jumps += 1
            avg_jump_dist = self.total_dist / self.total_jumps
            gap = jump_dist
            platform_regressor.record_jump(gap, [avg_jump_dist, plt_ctr, level_difficulty, -1])
            self.jump_start_x = None

        friction = 0.25
        if self.velocity == 0:
            self.v_x *= (1 - friction)
        else:
            self.v_x *= (0.98)

        
        
        self.rect.y += self.velocity
        self.rect.x += self.v_x

        global camera_x
        if self.rect.centerx > SCREEN_WIDTH // 4 and self.rect.centerx < LEVEL_WIDTH - (SCREEN_WIDTH//4):
            camera_x = self.rect.centerx - SCREEN_WIDTH // 4

        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x > LEVEL_WIDTH:
            self.rect.x = LEVEL_WIDTH
            

# Level generation
def generate_level(difficulty):
    platforms = pygame.sprite.Group()
    # Modify platform generation based on difficulty
    num_platforms = difficulty * 5
    last_x = 0.0
    offset = 50
    for i in range(num_platforms):
        platform_width = random.randint(50, 150)
        if difficulty == 1:
            predicted_gap = offset
        else:
            predicted_gap = platform_regressor.predict_gap([avg_jump_dist, i, difficulty, 1])

        platform_x = random.randint(last_x + abs(predicted_gap), last_x + abs(predicted_gap) + platform_width) if last_x + abs(predicted_gap) < LEVEL_WIDTH - platform_width else LEVEL_WIDTH - platform_width
        platform_y = random.randint(SCREEN_HEIGHT - 200, SCREEN_HEIGHT - 100)
        platform = pygame.sprite.Sprite()
        platform.image = pygame.Surface((platform_width, 20))
        platform.image.fill(BLACK)
        platform.rect = platform.image.get_rect()
        platform.rect.topleft = (platform_x, platform_y)
        platforms.add(platform)
        last_x = platform_x + platform_width
    return platforms

# Main game loop
def game_loop():

    num_success, num_fail = pygame.init()
    print('Number modules loaded: {}\tNumber failed: {}'.format(num_success, num_fail))
    screen = pygame.display.set_mode((468, 600))
    pygame.display.set_caption('Monkey Fever')
    pygame.mouse.set_visible(0)
    
    clock = pygame.time.Clock()
    running = True
    player = Player()
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)

    global level_difficulty
    level_difficulty = 1  # Start with easy difficulty
    platforms = generate_level(level_difficulty)
    
    while running:
        screen.fill(WHITE)
        screen.blit(background_image, (-2*camera_x, 0))  # Draw at the top-left corner

        events_processed = False
        keys = None
        e_type = None
        

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = event.key#event.pygame.key.get_pressed()
                e_type = 'down'
            if event.type == pygame.KEYUP:
                e_type = 'up'
                #break
            events_processed = True
            player.update(keys, platforms, e_type)
            
        if not events_processed:
            player.update(keys, platforms, None)

        screen.blit(player.image, (player.rect.x - camera_x, player.rect.y))
        #all_sprites.draw(screen)
        #platforms.draw(screen)

        for platform in platforms:
            screen.blit(platform.image, (platform.rect.x - camera_x, platform.rect.y))



        # Check if player reached end of level or died, then train ML model and adjust difficulty
        if player.rect.colliderect(platforms.sprites()[-1].rect):  # Simple end condition
            fade_to_black(screen, text="NEXT LEVEL")

            platform_regressor.train()
            level_difficulty += 1
            platforms = generate_level(level_difficulty)
            player.rect.x = 100
            player.rect.y = SCREEN_HEIGHT - 100
            player.update(keys, platforms, None)
            fade_from_black(screen)


        pygame.display.flip()
        clock.tick(FPS)

game_loop()
pygame.quit()
