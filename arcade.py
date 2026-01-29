#!/usr/bin/env python3
"""
LED Arcade - 64x64 Pixel Game Framework
========================================
A prototype framework for classic arcade games on a 64x64 LED matrix.
Runs on desktop with PyGame, designed to port easily to hardware.

Controls:
  Arrow Keys  - Joystick (4-way or 8-way depending on game)
  Space       - Left action button
  Z           - Right action button
  Hold both   - Back to menu (games need both buttons held)
  
Author: LED Arcade Project
"""

import pygame
import sys
import random
import math
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

# =============================================================================
# CONFIGURATION
# =============================================================================

GRID_SIZE = 64          # 64x64 pixel display
SCALE = 10              # Scale up for desktop (640x640 window)
FPS = 30                # Frame rate

# Colors (RGB) - Classic arcade palette
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 128, 0)
    PINK = (255, 128, 128)
    LIME = (128, 255, 0)
    PURPLE = (128, 0, 255)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    
    # Named game colors
    SNAKE = GREEN
    FOOD = RED
    WALL = GRAY
    PADDLE = WHITE
    BALL = WHITE
    BRICK = ORANGE
    PLAYER = CYAN
    ENEMY = RED
    BULLET = YELLOW

# =============================================================================
# INPUT SYSTEM
# =============================================================================

class InputState:
    """Tracks the state of all inputs for the current frame."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        # Directions (held — True while key is held)
        self.up = False
        self.down = False
        self.left = False
        self.right = False
        # Directions (pressed — True only on first frame)
        self.up_pressed = False
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False

        # Buttons (pressed this frame)
        self.action_l = False    # Space - left action
        self.action_r = False    # Z - right action

        # Buttons (held)
        self.action_l_held = False
        self.action_r_held = False
    
    @property
    def dx(self) -> int:
        """Horizontal direction: -1, 0, or 1"""
        return (1 if self.right else 0) - (1 if self.left else 0)
    
    @property
    def dy(self) -> int:
        """Vertical direction: -1, 0, or 1"""
        return (1 if self.down else 0) - (1 if self.up else 0)
    
    @property
    def any_direction(self) -> bool:
        return self.up or self.down or self.left or self.right


class InputHandler:
    """Handles keyboard input, designed to be swapped for hardware later."""
    
    def __init__(self):
        self.state = InputState()
        self._prev_keys = set()
    
    def update(self) -> InputState:
        """Update input state. Call once per frame."""
        keys = pygame.key.get_pressed()

        # Directions (held state)
        self.state.up = keys[pygame.K_UP]
        self.state.down = keys[pygame.K_DOWN]
        self.state.left = keys[pygame.K_LEFT]
        self.state.right = keys[pygame.K_RIGHT]

        # Buttons (held state)
        self.state.action_l_held = keys[pygame.K_SPACE]
        self.state.action_r_held = keys[pygame.K_z]

        # Detect fresh presses (not held from last frame)
        current_keys = set()
        if keys[pygame.K_UP]: current_keys.add(pygame.K_UP)
        if keys[pygame.K_DOWN]: current_keys.add(pygame.K_DOWN)
        if keys[pygame.K_LEFT]: current_keys.add(pygame.K_LEFT)
        if keys[pygame.K_RIGHT]: current_keys.add(pygame.K_RIGHT)
        if keys[pygame.K_SPACE]: current_keys.add(pygame.K_SPACE)
        if keys[pygame.K_z]: current_keys.add(pygame.K_z)

        self.state.up_pressed = pygame.K_UP in current_keys and pygame.K_UP not in self._prev_keys
        self.state.down_pressed = pygame.K_DOWN in current_keys and pygame.K_DOWN not in self._prev_keys
        self.state.left_pressed = pygame.K_LEFT in current_keys and pygame.K_LEFT not in self._prev_keys
        self.state.right_pressed = pygame.K_RIGHT in current_keys and pygame.K_RIGHT not in self._prev_keys
        self.state.action_l = pygame.K_SPACE in current_keys and pygame.K_SPACE not in self._prev_keys
        self.state.action_r = pygame.K_z in current_keys and pygame.K_z not in self._prev_keys

        self._prev_keys = current_keys
        return self.state


# =============================================================================
# DISPLAY SYSTEM
# =============================================================================

class Display:
    """
    Abstracted 64x64 pixel display.
    On desktop: renders via PyGame with scaling.
    On hardware: would render to LED matrix.
    """
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("LED Arcade - 64x64")
        
        self.window_size = GRID_SIZE * SCALE
        self.screen = pygame.display.set_mode((self.window_size, self.window_size))
        
        # Virtual framebuffer (64x64)
        self.buffer = [[Colors.BLACK for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Font for HUD (small pixel font simulation)
        self.font = pygame.font.Font(None, 24)
    
    def clear(self, color=Colors.BLACK):
        """Clear the display to a solid color."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.buffer[y][x] = color
    
    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """Set a single pixel. Coordinates are 0-63."""
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            self.buffer[y][x] = color
    
    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get color of a pixel."""
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            return self.buffer[y][x]
        return Colors.BLACK
    
    def draw_rect(self, x: int, y: int, w: int, h: int, color: Tuple[int, int, int], filled: bool = True):
        """Draw a rectangle."""
        for dy in range(h):
            for dx in range(w):
                if filled or dx == 0 or dx == w-1 or dy == 0 or dy == h-1:
                    self.set_pixel(x + dx, y + dy, color)
    
    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: Tuple[int, int, int]):
        """Draw a line using Bresenham's algorithm."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
    
    def draw_circle(self, cx: int, cy: int, r: int, color: Tuple[int, int, int], filled: bool = False):
        """Draw a circle."""
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                dist = x*x + y*y
                if filled:
                    if dist <= r*r:
                        self.set_pixel(cx + x, cy + y, color)
                else:
                    if abs(dist - r*r) < r * 2:
                        self.set_pixel(cx + x, cy + y, color)
    
    def draw_text_small(self, x: int, y: int, text: str, color: Tuple[int, int, int]):
        """
        Draw tiny 3x5 pixel text. Each character is 3 wide + 1 space.
        Only supports uppercase, numbers, and basic punctuation.
        """
        FONT_3X5 = {
            'A': ['010', '101', '111', '101', '101'],
            'B': ['110', '101', '110', '101', '110'],
            'C': ['011', '100', '100', '100', '011'],
            'D': ['110', '101', '101', '101', '110'],
            'E': ['111', '100', '110', '100', '111'],
            'F': ['111', '100', '110', '100', '100'],
            'G': ['011', '100', '101', '101', '011'],
            'H': ['101', '101', '111', '101', '101'],
            'I': ['111', '010', '010', '010', '111'],
            'J': ['001', '001', '001', '101', '010'],
            'K': ['101', '110', '100', '110', '101'],
            'L': ['100', '100', '100', '100', '111'],
            'M': ['101', '111', '111', '101', '101'],
            'N': ['101', '111', '111', '111', '101'],
            'O': ['010', '101', '101', '101', '010'],
            'P': ['110', '101', '110', '100', '100'],
            'Q': ['010', '101', '101', '110', '011'],
            'R': ['110', '101', '110', '101', '101'],
            'S': ['011', '100', '010', '001', '110'],
            'T': ['111', '010', '010', '010', '010'],
            'U': ['101', '101', '101', '101', '011'],
            'V': ['101', '101', '101', '010', '010'],
            'W': ['101', '101', '111', '111', '101'],
            'X': ['101', '101', '010', '101', '101'],
            'Y': ['101', '101', '010', '010', '010'],
            'Z': ['111', '001', '010', '100', '111'],
            '0': ['111', '101', '101', '101', '111'],
            '1': ['010', '110', '010', '010', '111'],
            '2': ['110', '001', '010', '100', '111'],
            '3': ['110', '001', '010', '001', '110'],
            '4': ['101', '101', '111', '001', '001'],
            '5': ['111', '100', '110', '001', '110'],
            '6': ['011', '100', '110', '101', '010'],
            '7': ['111', '001', '010', '010', '010'],
            '8': ['010', '101', '010', '101', '010'],
            '9': ['010', '101', '011', '001', '110'],
            ' ': ['000', '000', '000', '000', '000'],
            ':': ['000', '010', '000', '010', '000'],
            '-': ['000', '000', '111', '000', '000'],
            '.': ['000', '000', '000', '000', '010'],
            '!': ['010', '010', '010', '000', '010'],
            '?': ['110', '001', '010', '000', '010'],
        }
        
        cursor = x
        for char in text.upper():
            if char in FONT_3X5:
                glyph = FONT_3X5[char]
                for row_idx, row in enumerate(glyph):
                    for col_idx, pixel in enumerate(row):
                        if pixel == '1':
                            self.set_pixel(cursor + col_idx, y + row_idx, color)
            cursor += 4  # 3 pixels + 1 space
    
    def render(self):
        """Render the buffer to the screen."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                color = self.buffer[y][x]
                rect = (x * SCALE, y * SCALE, SCALE, SCALE)
                pygame.draw.rect(self.screen, color, rect)
        
        # Optional: draw grid lines for debugging
        # for i in range(GRID_SIZE + 1):
        #     pygame.draw.line(self.screen, Colors.DARK_GRAY, (i*SCALE, 0), (i*SCALE, self.window_size))
        #     pygame.draw.line(self.screen, Colors.DARK_GRAY, (0, i*SCALE), (self.window_size, i*SCALE))
        
        pygame.display.flip()


# =============================================================================
# GAME BASE CLASS
# =============================================================================

class GameState(Enum):
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    WIN = auto()


class Game(ABC):
    """Base class for all arcade games."""
    
    name: str = "Unnamed Game"
    description: str = ""
    
    def __init__(self, display: Display):
        self.display = display
        self.state = GameState.PLAYING
        self.score = 0
        self.high_score = 0
    
    @abstractmethod
    def reset(self):
        """Reset the game to initial state."""
        pass
    
    @abstractmethod
    def update(self, input_state: InputState, dt: float):
        """Update game logic. dt is delta time in seconds."""
        pass
    
    @abstractmethod
    def draw(self):
        """Draw the game to the display."""
        pass
    
    def draw_score(self, y: int = 1):
        """Draw score at top of screen."""
        self.display.draw_text_small(1, y, f"{self.score}", Colors.WHITE)
    
    def draw_game_over(self, selection: int = 0):
        """Draw game over screen with menu options.

        Args:
            selection: 0 = PLAY AGAIN, 1 = MENU
        """
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(12, 30, f"SCORE:{self.score}", Colors.WHITE)

        # Draw selection options
        if selection == 0:
            self.display.draw_text_small(4, 44, ">PLAY AGAIN", Colors.YELLOW)
            self.display.draw_text_small(4, 54, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(4, 44, " PLAY AGAIN", Colors.GRAY)
            self.display.draw_text_small(4, 54, ">MENU", Colors.YELLOW)


# =============================================================================
# MAIN ARCADE SYSTEM
# =============================================================================

class Arcade:
    """Main arcade system - handles menu and game switching."""
    
    def __init__(self):
        self.display = Display()
        self.input = InputHandler()
        self.clock = pygame.time.Clock()
        
        self.games: List[type] = []  # Game classes
        self.current_game: Optional[Game] = None
        self.menu_selection = 0
        self.game_over_selection = 0  # 0 = PLAY AGAIN, 1 = MENU
        self.in_menu = True
    
    def register_game(self, game_class: type):
        """Register a game class with the arcade."""
        self.games.append(game_class)
    
    def draw_menu(self):
        """Draw the game selection menu."""
        self.display.clear(Colors.BLACK)
        
        # Title
        self.display.draw_text_small(4, 2, "LED ARCADE", Colors.CYAN)
        self.display.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)
        
        # Game list
        visible_games = 6
        start_idx = max(0, self.menu_selection - visible_games // 2)
        
        for i, game_class in enumerate(self.games[start_idx:start_idx + visible_games]):
            actual_idx = start_idx + i
            y = 14 + i * 8
            
            if actual_idx == self.menu_selection:
                # Selected item
                self.display.draw_rect(0, y - 1, 64, 7, Colors.DARK_GRAY)
                self.display.draw_text_small(2, y, f">{game_class.name}", Colors.YELLOW)
            else:
                self.display.draw_text_small(2, y, f" {game_class.name}", Colors.WHITE)
        
        # Instructions
        self.display.draw_line(0, 56, 63, 56, Colors.DARK_GRAY)
        self.display.draw_text_small(2, 58, "SPACE:SELECT", Colors.GRAY)
    
    def run(self):
        """Main game loop."""
        running = True
        exit_hold = 0.0  # Hold-to-exit timer

        while running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Update input
            input_state = self.input.update()

            if self.in_menu:
                # Hold either button 2 sec to quit
                if input_state.action_l_held or input_state.action_r_held:
                    exit_hold += dt
                    if exit_hold >= 2.0:
                        running = False
                else:
                    exit_hold = 0.0

                # Menu navigation
                if input_state.up_pressed and self.menu_selection > 0:
                    self.menu_selection -= 1
                elif input_state.down_pressed and self.menu_selection < len(self.games) - 1:
                    self.menu_selection += 1
                elif (input_state.action_l or input_state.action_r) and self.games:
                    # Start selected game
                    self.current_game = self.games[self.menu_selection](self.display)
                    self.current_game.reset()
                    self.in_menu = False
                    exit_hold = 0.0

                self.draw_menu()

            else:
                # In game — hold BOTH buttons 2 sec to return to menu
                if input_state.action_l_held and input_state.action_r_held:
                    exit_hold += dt
                    if exit_hold >= 2.0:
                        self.in_menu = True
                        self.current_game = None
                        exit_hold = 0.0
                else:
                    exit_hold = 0.0

                if self.current_game:
                    if self.current_game.state == GameState.GAME_OVER:
                        # Handle game over menu selection
                        if input_state.up_pressed or input_state.down_pressed:
                            self.game_over_selection = 1 - self.game_over_selection
                        elif input_state.action_l or input_state.action_r:
                            if self.game_over_selection == 0:
                                # Play again
                                self.current_game.reset()
                            else:
                                # Return to menu
                                self.in_menu = True
                                self.current_game = None
                            self.game_over_selection = 0
                        self.current_game.draw_game_over(self.game_over_selection)
                    else:
                        self.current_game.update(input_state, dt)
                        self.current_game.draw()

            self.display.render()

        pygame.quit()


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    print("LED Arcade Framework")
    print("====================")
    print("This is the base framework. Run 'python main.py' to play games!")
