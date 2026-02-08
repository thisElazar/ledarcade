"""
Credits - Attribution and credits display
==========================================
Scrolling display of all sources, inspirations, and credits
used in the LED Arcade project.

Controls:
  Up/Down  - Slow down / speed up scroll
  Button   - Exit to menu
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
        self.base_speed = 12.0    # default pixels per second
        self.scroll_speed = 12.0  # current effective speed
        self.speed_mult = 1.0     # joystick multiplier

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
            ("", G),
            # --- Games ---
            ("- GAMES -", M),
            ("", G),
            ("NAMCO", C),
            ("PAC-MAN", W),
            ("GALAGA", W),
            ("DIG DUG", W),
            ("", G),
            ("GCC/MIDWAY", C),
            ("MS. PAC-MAN", W),
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
            ("", G),
            ("HUDSON SOFT", C),
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
            ("ASSEMBLY LINE", C),
            ("PIPE DREAM", W),
            ("", G),
            ("MICROSOFT", C),
            ("JEZZBALL", W),
            ("SKIFREE", W),
            ("", G),
            ("DATA EAST", C),
            ("BURGER TIME", W),
            ("", G),
            ("DAVIDSON", C),
            ("MATH BLASTER", G),
            ("SPACE CRUISE", W),
            ("TRASH BLASTER", W),
            ("", G),
            ("MALCOLM EVANS", C),
            ("3D MONSTER MAZE", W),
            ("", G),
            ("GREMLIN", C),
            ("BLOCKADE", W),
            ("", G),
            ("NOKIA", C),
            ("SNAKE", W),
            ("", G),
            ("MATTEL", C),
            ("DND", W),
            ("OTHELLO", W),
            ("", G),
            ("HASBRO", C),
            ("CONNECT 4", W),
            ("BOP IT  SIMON", W),
            ("", G),
            ("CINEMATRONICS", C),
            ("PINBALL", W),
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
            ("KETCHAPP", C),
            ("STACK", W),
            ("", G),
            ("WILLIAMS", C),
            ("DEFENDER", W),
            ("", G),
            ("NINJA KIWI", C),
            ("BLOONS", W),
            ("BLOONS TD", W),
            ("", G),
            ("VALVE", C),
            ("PORTAL", W),
            ("", G),
            ("N YOSHIGAHARA", C),
            ("RUSH HOUR", W),
            ("", G),
            ("M MEIROWITZ", C),
            ("MASTERMIND", W),
            ("", G),
            ("M VALADARES", C),
            ("AGAR.IO", W),
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
            ("TURING", C),
            ("A TURING 1952", W),
            ("", G),
            ("FLUID DYNAMICS", C),
            ("JOS STAM 1999", W),
            ("", G),
            ("EM FIELD", C),
            ("FARADAY +", W),
            ("MAXWELL", W),
            ("", G),
            ("ORBITS", C),
            ("KEPLER + NEWTON", W),
            ("", G),
            ("NEURONS", C),
            ("IZHIKEVICH 2003", W),
            ("", G),
            ("CHLADNI PLATES", C),
            ("E CHLADNI 1787", W),
            ("", G),
            ("OPTICS", C),
            ("NEWTON  SNELL", W),
            ("", G),
            ("CHESS AI", C),
            ("BERNSTEIN 1957", W),
            ("", G),
            ("CHECKERS AI", C),
            ("A SAMUEL 1959", W),
            ("", G),
            ("GRAY-SCOTT", C),
            ("PEARSON 1993", W),
            ("", G),
            ("", G),
            # --- Sprites ---
            ("- SPRITES -", M),
            ("", G),
            ("NINTENDO", C),
            ("MARIO  LINK", W),
            ("YOSHI  SAMUS", W),
            ("PIT", W),
            ("", G),
            ("HAL LABORATORY", C),
            ("KIRBY", W),
            ("", G),
            ("CAPCOM", C),
            ("MEGA MAN", W),
            ("", G),
            ("SEGA", C),
            ("SONIC", W),
            ("", G),
            ("MARVEL", C),
            ("SPIDER-MAN", W),
            ("", G),
            ("DC COMICS", C),
            ("BATMAN", W),
            ("GREEN LANTERN", W),
            ("", G),
            ("PIXEL ART", G),
            ("HUARD OLIVIER", W),
            ("", G),
            ("SPRITE RIPS", G),
            ("JERMUNGANDR", W),
            ("MISTERMIKE", W),
            ("SANICKING2", W),
            ("DOC VON", W),
            ("SCHMELTWICK", G),
            ("SUPERJUSTINBROS", W),
            ("125SCRATCH", W),
            ("FLEEPA", W),
            ("QUADFACTOR", W),
            ("ULTRAHYPE97", W),
            ("", G),
            ("NES MAPS", G),
            ("RICK BRUNS", W),
            ("NESMAPS.COM", G),
            ("", G),
            ("ADVENTURE TIME", G),
            ("V GOMINHO", W),
            ("JAKE DANCE", G),
            ("NANDOO.PX", W),
            ("JAKE MUSIC", G),
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
            ("MONDRIAN", C),
            ("PIET MONDRIAN", W),
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
            ("MATRIX", W),
            ("STARFIELD", W),
            ("", G),
            # --- Resources ---
            ("- RESOURCES -", M),
            ("", G),
            ("FOURMILAB.CH", W),
            ("SIZECODING.ORG", W),
            ("NATUREOFCODE", W),
            ("SHADERTOY.COM", W),
            ("BOOKOFSHADERS", W),
            ("CONWAYLIFE.COM", W),
            ("POUET.NET", W),
            ("NESMAPS.COM", W),
            ("SPRITERS", W),
            ("RESOURCE.COM", G),
            ("", G),
            ("", G),
            ("BUILT WITH", G),
            ("PYTHON", C),
            ("RGBMATRIX", C),
            ("RASPBERRY PI", C),
            ("", G),
            ("", G),
            # --- Team ---
            ("DESIGNED BY", G),
            ("THISELAZAR", Y),
            ("", G),
            ("PROGRAMMED BY", G),
            ("CLAUDE CODE", Y),
            ("", G),
            ("", G),
            ("", G),
        ]

        # Total height needed: each line is 7px (font height + spacing)
        self.line_height = 8
        self.total_height = len(self.lines) * self.line_height

    def handle_input(self, input_state) -> bool:
        if input_state.action_l or input_state.action_r:
            self.wants_exit = True
            return True
        # Joystick controls scroll speed (Smash Bros style)
        if input_state.down:
            self.speed_mult = 4.0   # fast forward
            return True
        elif input_state.up:
            self.speed_mult = -1.5  # rewind
            return True
        else:
            self.speed_mult = 1.0
        return False

    def update(self, dt: float):
        self.time += dt
        self.scroll_speed = self.base_speed * self.speed_mult
        self.scroll_y += self.scroll_speed * dt

        # Clamp: don't scroll above the start
        if self.scroll_y < 0.0:
            self.scroll_y = 0.0

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
