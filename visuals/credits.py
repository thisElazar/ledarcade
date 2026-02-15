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
            ("INSPIRED BY THE", G),
            ("GOLDEN AGE OF", G),
            ("ARCADE GAMES", G),
            ("", G),
            ("30+ CLASSIC", W),
            ("ARCADE GAMES", W),
            ("REIMAGINED", W),
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
            ("LENIA", C),
            ("BERT CHAN 2018", W),
            ("", G),
            ("POTTS MODEL", C),
            ("R B POTTS 1952", W),
            ("CRYSTALLIZE", G),
            ("", G),
            ("FRACTALS", C),
            ("MANDELBROT", W),
            ("JULIA  SIERPINSKI", W),
            ("KOCH  BARNSLEY", W),
            ("", G),
            ("COMANCHE", C),
            ("VOXEL TERRAIN", W),
            ("NOVALOGIC 1992", G),
            ("", G),
            ("CONSTELLATIONS", C),
            ("HIPPARCOS CATALOG", W),
            ("STELLARIUM", W),
            ("", G),
            ("FLAGS", C),
            ("FLAGCDN.COM", W),
            ("", G),
            ("", G),
            ("", G),
            # --- Art ---
            ("- ART -", M),
            ("", G),
            ("SALON GALLERY", C),
            ("116 PAINTINGS", W),
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
            ("WONDER CABINET", W),
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
            ("FLAGCDN.COM", W),
            ("STELLARIUM.ORG", W),
            ("TOMBATOSSALS", W),
            ("CHORDS-DB", G),
            ("RCSB.ORG", W),
            ("PROTEIN DATA BANK", G),
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
