"""
Credits - Attribution and credits display
==========================================
Scrolling display of all sources, inspirations, and credits
used in the LED Arcade project.

Controls:
  Any button - Exit to menu
"""

from . import Visual, Display, Colors, GRID_SIZE


class Credits(Visual):
    name = "CREDITS"
    description = "Project credits"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.scroll_y = 0.0
        self.scroll_speed = 12.0  # pixels per second

        # Build the credits content as (text, color) pairs
        # Each entry is one line; empty string = blank spacer line
        C = Colors.CYAN
        W = Colors.WHITE
        G = Colors.GRAY
        Y = Colors.YELLOW
        M = Colors.MAGENTA

        self.lines = [
            ("LED ARCADE", C),
            ("", G),
            # --- Team ---
            ("DESIGNED BY", G),
            ("THISELAZAR", Y),
            ("", G),
            ("PROGRAMMED BY", G),
            ("CLAUDE CODE", Y),
            ("", G),
            ("", G),
            # --- Games ---
            ("- GAMES -", M),
            ("", G),
            ("NAMCO", C),
            ("PAC-MAN", W),
            ("GALAGA", W),
            ("DIG DUG", W),
            ("", G),
            ("ATARI", C),
            ("PONG", W),
            ("BREAKOUT", W),
            ("ASTEROIDS", W),
            ("CENTIPEDE", W),
            ("LUNAR LANDER", W),
            ("NIGHT DRIVER", W),
            ("INDY 500", W),
            ("", G),
            ("T NISHIKADO", C),
            ("INVADERS", W),
            ("", G),
            ("A PAJITNOV", C),
            ("TETRIS", W),
            ("", G),
            ("KONAMI", C),
            ("FROGGER", W),
            ("BOMBERMAN", W),
            ("", G),
            ("TAITO", C),
            ("ARKANOID", W),
            ("", G),
            ("NINTENDO", C),
            ("DONKEY KONG", W),
            ("", G),
            ("GOTTLIEB", C),
            ("Q*BERT", W),
            ("", G),
            ("DOUG SMITH", C),
            ("LODE RUNNER", W),
            ("", G),
            ("LUCASARTS", C),
            ("PIPE DREAM", W),
            ("", G),
            ("MICROSOFT", C),
            ("JEZZBALL", W),
            ("SKIFREE", W),
            ("", G),
            ("D NGUYEN", C),
            ("FLAPPY BIRD", W),
            ("", G),
            ("G CIRULLI", C),
            ("2048", W),
            ("", G),
            ("TIGER ELEC", C),
            ("LIGHTS OUT", W),
            ("", G),
            ("ROBTOP", C),
            ("GEODASH", W),
            ("", G),
            ("", G),
            # --- Visuals ---
            ("- VISUALS -", M),
            ("", G),
            ("CELLAB", C),
            ("RUCKER + WALKER", W),
            ("FOURMILAB.CH", G),
            ("AURORA  FADERS", W),
            ("GYRE  RUG", W),
            ("QUARKS  RIPPLES", W),
            ("", G),
            ("HODGEPODGE", C),
            ("GERHARDT +", W),
            ("SCHUSTER", W),
            ("", G),
            ("GOSPER", C),
            ("GYRE RULE", W),
            ("", G),
            ("GAME OF LIFE", C),
            ("JOHN CONWAY", W),
            ("", G),
            ("BOIDS", C),
            ("CRAIG REYNOLDS", W),
            ("", G),
            ("CYCLIC CA", C),
            ("D GRIFFEATH", W),
            ("", G),
            ("STAR WARS CA", C),
            ("M WOJTOWICZ", W),
            ("345/2/4", G),
            ("", G),
            ("WOLFRAM CA", C),
            ("S WOLFRAM", W),
            ("", G),
            ("SANDPILE", C),
            ("BAK TANG", W),
            ("WIESENFELD", G),
            ("", G),
            ("PARTICLE LIFE", C),
            ("J VENTRELLA", W),
            ("T MOHR", W),
            ("", G),
            ("FIREFLIES", C),
            ("KURAMOTO MODEL", W),
            ("", G),
            ("CURL NOISE", C),
            ("R BRIDSON 2007", W),
            ("", G),
            ("TRUCHET TILES", C),
            ("S TRUCHET 1704", W),
            ("", G),
            ("SLIME MOLD", C),
            ("PHYSARUM", W),
            ("", G),
            ("ATTRACTORS", C),
            ("LORENZ ROSSLER", W),
            ("THOMAS", W),
            ("", G),
            # --- Art ---
            ("- ART -", M),
            ("", G),
            ("STARRY NIGHT", C),
            ("VAN GOGH", W),
            ("", G),
            ("WATER LILIES", C),
            ("MONET", W),
            ("", G),
            ("GREAT WAVE", C),
            ("HOKUSAI", W),
            ("", G),
            ("THE SCREAM", C),
            ("MUNCH 1893", W),
            ("", G),
            # --- Demoscene ---
            ("- DEMOSCENE -", M),
            ("", G),
            ("FIRE  PLASMA", W),
            ("ROTOZOOM", W),
            ("SINESCROLL", W),
            ("TWISTER", W),
            ("AMIGA BARS", W),
            ("LARSON SCAN", W),
            ("TRANCE", W),
            ("", G),
            ("", G),
            ("BUILT WITH", G),
            ("PYTHON", C),
            ("RGBMATRIX", C),
            ("RASPBERRY PI", C),
            ("", G),
            ("", G),
            ("", G),
        ]

        # Total height needed: each line is 7px (font height + spacing)
        self.line_height = 8
        self.total_height = len(self.lines) * self.line_height

    def handle_input(self, input_state) -> bool:
        if (input_state.action_l or input_state.action_r or
                input_state.up_pressed or input_state.down_pressed or
                input_state.left_pressed or input_state.right_pressed):
            self.wants_exit = True
            return True
        return False

    def update(self, dt: float):
        self.time += dt
        self.scroll_y += self.scroll_speed * dt

        # Loop when all credits have scrolled past
        if self.scroll_y > self.total_height + GRID_SIZE:
            self.scroll_y = 0.0

    def draw(self):
        self.display.clear(Colors.BLACK)

        for i, (text, color) in enumerate(self.lines):
            if not text:
                continue

            # Calculate screen y position
            y = int(GRID_SIZE - self.scroll_y + i * self.line_height)

            # Only draw if on screen
            if -8 < y < GRID_SIZE:
                self.display.draw_text_small(2, y, text, color)
