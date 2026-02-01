"""
Neurons - Spiking Neural Network
==================================
Izhikevich spiking neuron model with excitatory and inhibitory
connections. Membrane potential mapped to color: resting=dim blue,
depolarizing=cyan, spike=bright flash, recovering=purple.

Active synapses flash as bright lines between neurons.
Background noise triggers spontaneous firing; cascading waves emerge.

Controls:
  Up/Down    - Cycle color palette
  Left/Right - Adjust stimulation level
  Space      - Cycle neuron type (regular/chattering/bursting)
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# Izhikevich model parameters for different neuron types
NEURON_TYPES = [
    # (name, a, b, c, d) -- regular spiking
    ('regular',    0.02, 0.2, -65.0, 8.0),
    # chattering
    ('chattering', 0.02, 0.2, -50.0, 2.0),
    # bursting
    ('bursting',   0.02, 0.2, -55.0, 4.0),
]

# Spike threshold
V_THRESH = 30.0
# Reset after spike
V_RESET_BASE = -65.0

# Number of neurons
NUM_NEURONS = 120
# Connections per neuron
CONNECTIONS_PER = 4
# Fraction excitatory
EXCITATORY_FRAC = 0.8

# Synapse weight
EXCITATORY_WEIGHT = 8.0
INHIBITORY_WEIGHT = -5.0

# Synapse flash duration
SYNAPSE_FLASH_FRAMES = 3

PALETTES = [
    # Neural: blue resting -> cyan depol -> white spike -> purple recovery
    {'rest': (15, 20, 60), 'depol': (0, 180, 200), 'spike': (255, 255, 255),
     'recover': (120, 40, 160), 'excite': (0, 255, 150), 'inhibit': (255, 50, 50),
     'bg': (3, 3, 10)},
    # Warm
    {'rest': (40, 15, 10), 'depol': (200, 100, 30), 'spike': (255, 255, 200),
     'recover': (100, 30, 60), 'excite': (255, 200, 50), 'inhibit': (200, 50, 100),
     'bg': (5, 3, 3)},
    # Green
    {'rest': (10, 30, 15), 'depol': (50, 200, 80), 'spike': (200, 255, 200),
     'recover': (30, 80, 100), 'excite': (100, 255, 100), 'inhibit': (255, 80, 80),
     'bg': (2, 5, 3)},
    # Monochrome
    {'rest': (20, 20, 20), 'depol': (140, 140, 140), 'spike': (255, 255, 255),
     'recover': (60, 60, 60), 'excite': (200, 200, 200), 'inhibit': (100, 100, 100),
     'bg': (3, 3, 3)},
]


class Neuron:
    __slots__ = ('x', 'y', 'v', 'u', 'a', 'b', 'c', 'd',
                 'is_excitatory', 'connections', 'fired', 'flash_timer',
                 'input_current')

    def __init__(self, x, y, a, b, c, d, is_excitatory):
        self.x = x
        self.y = y
        self.v = -65.0  # Membrane potential
        self.u = b * (-65.0)  # Recovery variable
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.is_excitatory = is_excitatory
        self.connections = []  # List of (target_neuron, weight)
        self.fired = False
        self.flash_timer = 0
        self.input_current = 0.0


class Synapse:
    """Represents an active synapse flash for drawing."""
    __slots__ = ('x0', 'y0', 'x1', 'y1', 'timer', 'is_excitatory')

    def __init__(self, x0, y0, x1, y1, is_excitatory):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.timer = SYNAPSE_FLASH_FRAMES
        self.is_excitatory = is_excitatory


class Neurons(Visual):
    name = "NEURONS"
    description = "Spiking neural net"
    category = "science"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.type_idx = 0
        self.stim_level = 5.0  # Background noise amplitude
        self.active_synapses = []
        self._init_network()

    def _init_network(self):
        """Create neurons at random positions with local connections."""
        a, b, c, d = NEURON_TYPES[self.type_idx][1:]
        self.neurons = []
        margin = 3
        positions = set()

        for i in range(NUM_NEURONS):
            for _ in range(100):
                x = random.randint(margin, GRID_SIZE - margin - 1)
                y = random.randint(margin, GRID_SIZE - margin - 1)
                if (x, y) not in positions:
                    positions.add((x, y))
                    break
            is_exc = random.random() < EXCITATORY_FRAC
            n = Neuron(x, y, a, b, c, d, is_exc)
            self.neurons.append(n)

        # Connect each neuron to nearest neighbors
        for ni in self.neurons:
            # Find distances to all others
            dists = []
            for nj in self.neurons:
                if nj is ni:
                    continue
                dx = nj.x - ni.x
                dy = nj.y - ni.y
                dists.append((dx * dx + dy * dy, nj))
            dists.sort(key=lambda d: d[0])
            # Connect to closest CONNECTIONS_PER
            n_conn = min(CONNECTIONS_PER, len(dists))
            for k in range(n_conn):
                target = dists[k][1]
                weight = EXCITATORY_WEIGHT if ni.is_excitatory else INHIBITORY_WEIGHT
                ni.connections.append((target, weight))

        self.active_synapses = []

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left:
            self.stim_level = max(0.0, self.stim_level - 0.5)
            consumed = True
        if input_state.right:
            self.stim_level = min(15.0, self.stim_level + 0.5)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.type_idx = (self.type_idx + 1) % len(NEURON_TYPES)
            self._init_network()
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt
        stim = self.stim_level

        # Step 1: Apply background noise as input current
        for n in self.neurons:
            n.input_current = random.uniform(0, stim)

        # Step 2: Izhikevich dynamics (0.5ms steps, do 2 per frame at 30fps)
        for _ in range(2):
            for n in self.neurons:
                # Izhikevich equations
                v = n.v
                u = n.u
                I = n.input_current

                # Two 0.5ms substeps for numerical stability
                v += 0.5 * (0.04 * v * v + 5.0 * v + 140.0 - u + I)
                v += 0.5 * (0.04 * v * v + 5.0 * v + 140.0 - u + I)
                u += n.a * (n.b * v - u)

                n.fired = False
                if v >= V_THRESH:
                    n.fired = True
                    n.flash_timer = 3
                    v = n.c
                    u += n.d

                    # Propagate spike to connected neurons
                    for target, weight in n.connections:
                        target.input_current += weight
                        # Record synapse flash
                        self.active_synapses.append(
                            Synapse(n.x, n.y, target.x, target.y, n.is_excitatory))

                n.v = v
                n.u = u

        # Decay flash timers
        for n in self.neurons:
            if n.flash_timer > 0:
                n.flash_timer -= 1

        # Decay synapse flashes
        new_synapses = []
        for s in self.active_synapses:
            s.timer -= 1
            if s.timer > 0:
                new_synapses.append(s)
        self.active_synapses = new_synapses

    def _lerp_color(self, c0, c1, t):
        return (
            int(c0[0] + (c1[0] - c0[0]) * t),
            int(c0[1] + (c1[1] - c0[1]) * t),
            int(c0[2] + (c1[2] - c0[2]) * t),
        )

    def draw(self):
        pal = PALETTES[self.palette_idx]
        self.display.clear(pal['bg'])

        # Draw active synapses
        for s in self.active_synapses:
            t = s.timer / SYNAPSE_FLASH_FRAMES
            base = pal['excite'] if s.is_excitatory else pal['inhibit']
            color = (int(base[0] * t * 0.3), int(base[1] * t * 0.3), int(base[2] * t * 0.3))
            self.display.draw_line(s.x0, s.y0, s.x1, s.y1, color)

        # Draw neurons
        for n in self.neurons:
            v = n.v
            x, y = n.x, n.y

            if n.flash_timer > 0:
                # Spike flash
                t = n.flash_timer / 3.0
                color = self._lerp_color(pal['recover'], pal['spike'], t)
            elif v > -40:
                # Depolarizing
                t = min(1.0, (v + 65) / 25.0)
                color = self._lerp_color(pal['rest'], pal['depol'], t)
            elif v > -70:
                # Recovering
                t = min(1.0, (-40 - v) / 30.0)
                color = self._lerp_color(pal['rest'], pal['recover'], t * 0.5)
            else:
                color = pal['rest']

            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x, y, color)

                # Glow for spiking neurons
                if n.flash_timer > 0:
                    glow_t = n.flash_timer / 3.0
                    glow = (
                        int(color[0] * glow_t * 0.4),
                        int(color[1] * glow_t * 0.4),
                        int(color[2] * glow_t * 0.4),
                    )
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                            cur = self.display.get_pixel(nx, ny)
                            blended = (
                                min(255, cur[0] + glow[0]),
                                min(255, cur[1] + glow[1]),
                                min(255, cur[2] + glow[2]),
                            )
                            self.display.set_pixel(nx, ny, blended)
