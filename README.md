# LED Arcade 🕹️

A collection of classic arcade games designed for a **64×64 RGB LED matrix**, with a desktop emulator for prototyping.

![64x64 resolution](https://img.shields.io/badge/resolution-64×64-blue)
![Python 3.7+](https://img.shields.io/badge/python-3.7+-green)
![PyGame](https://img.shields.io/badge/pygame-2.0+-orange)

## 🎮 Games Included

| Game | Description | Controls |
|------|-------------|----------|
| **Snake** | Eat food, grow longer, don't hit yourself! | Arrows to move |
| **Pong** | Beat the AI opponent (first to 7 wins) | Up/Down to move paddle |
| **Breakout** | Break all the bricks with your ball | Left/Right to move, Space to launch |
| **Invaders** | Defend Earth from alien invasion | Left/Right to move, Space to fire |
| **Tetris** | Stack blocks and clear lines | Left/Right/Down to move, Up to rotate, Space for hard drop |
| **Asteroids** | Destroy asteroids before they destroy you! | Left/Right to rotate, Up to thrust, Space to fire |

## 🚀 Quick Start

### Desktop Emulator (Prototyping)

```bash
# Clone or download the project
cd led-arcade

# Install dependencies
pip install -r requirements.txt

# Run the arcade!
python main.py
```

A 640×640 window will open (10× scale of the 64×64 display).

### Controls

| Key | Action |
|-----|--------|
| **Arrow Keys** | Move / Navigate menu |
| **Space** | Action (fire, select, hard drop, launch ball) |
| **Z** | Secondary action (rarely used) |
| **Escape** | Return to menu |

## 📁 Project Structure

```
led-arcade/
├── main.py              # Entry point
├── arcade.py            # Core framework (display, input, game base class)
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── games/
    ├── __init__.py      # Game registry
    ├── snake.py         # Snake game
    ├── pong.py          # Pong game
    ├── breakout.py      # Breakout game
    ├── invaders.py      # Space Invaders game
    ├── tetris.py        # Tetris game
    └── asteroids.py     # Asteroids game
```

## 🎨 Architecture

The framework is designed for easy porting to hardware:

### Display Abstraction
```python
from arcade import Display, Colors

display = Display()
display.clear(Colors.BLACK)
display.set_pixel(32, 32, Colors.RED)
display.draw_rect(10, 10, 20, 20, Colors.BLUE)
display.draw_text_small(1, 1, "SCORE:100", Colors.WHITE)
display.render()
```

### Input Abstraction
```python
from arcade import InputHandler

input_handler = InputHandler()
state = input_handler.update()

if state.up:
    player.move_up()
if state.action:  # Space pressed this frame
    player.fire()
```

### Creating New Games
```python
from arcade import Game, GameState, Display, Colors

class MyGame(Game):
    name = "MY GAME"
    description = "A cool game!"
    
    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        # Initialize game state...
    
    def update(self, input_state, dt):
        # Game logic here
        # dt = delta time in seconds
        pass
    
    def draw(self):
        self.display.clear(Colors.BLACK)
        # Draw game elements...
```

## 🔧 Hardware Porting

When you're ready to move to actual hardware, you'll need:

### Hardware Components
- **64×64 RGB LED Matrix** (HUB75 connector) - ~$40
- **Controller board** - one of:
  - Pimoroni Interstate 75 (RP2040) - ~$20
  - Adafruit RGB Matrix Bonnet + Raspberry Pi - ~$15 + Pi
- **5V Power Supply** - 4A minimum for one panel
- **Arcade controls** - joystick + buttons

### Porting Steps

1. **Replace Display class** - Swap PyGame rendering for LED matrix library:
   ```python
   # For Raspberry Pi with rpi-rgb-led-matrix:
   from rgbmatrix import RGBMatrix, RGBMatrixOptions
   
   # For RP2040 with Pimoroni:
   from interstate75 import Interstate75
   ```

2. **Replace InputHandler** - Read from GPIO or arcade controller:
   ```python
   # Example for GPIO buttons
   import RPi.GPIO as GPIO
   
   class HardwareInput:
       def update(self):
           state.up = GPIO.input(PIN_UP) == GPIO.LOW
           # etc...
   ```

3. **Adjust timing** - Hardware may need different FPS or timing tweaks

### Recommended Libraries
- **rpi-rgb-led-matrix** (hzeller) - Best for Raspberry Pi
- **Pimoroni Interstate 75** - Great for RP2040-based builds
- **Adafruit RGB Matrix** - Good documentation, works with CircuitPython

## 🎯 Design Principles

### 64×64 Constraints
- **Resolution**: Each pixel matters! Design with bold, readable shapes
- **Colors**: Bright, high-contrast palette works best on LED
- **HUD**: Reserve top 6-8 rows for score/status
- **Sprites**: 4×4 to 8×8 pixel characters work well
- **Text**: 3×5 pixel font included (uppercase, numbers, basic punctuation)

### Frame Rate
- Target **30 FPS** for smooth gameplay
- LED matrices can handle 60+ FPS but 30 is plenty for retro games
- Use delta time (`dt`) for consistent speed across different hardware

## 📝 Adding Your Own Games

1. Create a new file in `games/` folder
2. Subclass `Game` and implement `reset()`, `update()`, `draw()`
3. Register in `games/__init__.py`

```python
# games/my_game.py
from arcade import Game, GameState, Colors

class MyGame(Game):
    name = "MYGAME"  # Keep it short for menu
    
    def reset(self):
        self.state = GameState.PLAYING
        # ...
    
    def update(self, input_state, dt):
        if input_state.action:
            # Do something
            pass
    
    def draw(self):
        self.display.clear()
        self.display.draw_text_small(10, 30, "HELLO!", Colors.GREEN)
```

```python
# games/__init__.py
from .my_game import MyGame
ALL_GAMES.append(MyGame)
```

## 🤝 Contributing

Feel free to:
- Add new games
- Improve existing games
- Add features (high scores, sound, etc.)
- Create hardware integration examples

## 📜 License

MIT License - do whatever you want with it!

## 🎉 Have Fun!

This project is all about having fun with low-resolution gaming. The constraints of 64×64 pixels force creative design decisions that hearken back to the golden age of arcade games.

Questions? Ideas? Build something cool? Let's see it! 🕹️
