"""
Neurons - Spiking Neural Network
==================================
Izhikevich spiking neuron model with excitatory and inhibitory
connections. Membrane potential mapped to color: resting=dim blue,
depolarizing=cyan, spike=bright flash, recovering=purple.

Active synapses flash as bright lines between neurons.

Scenarios model different brain states and conditions, each tuning
the network parameters (stimulation, E/I ratio, connectivity, neuron
dynamics) to produce distinct firing patterns.

Controls:
  Up/Down    - Cycle color palette
  Left/Right - Adjust stimulation level
  Button     - Cycle brain state scenario
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

V_THRESH = 30.0

SCENARIOS = [
    {
        'name': 'CALM',
        'num_neurons': 100,
        'connections': 3,
        'exc_frac': 0.75,
        'exc_weight': 6.0,
        'inh_weight': -5.0,
        'stim': 3.0,
        'type': ('regular', 0.02, 0.2, -65.0, 8.0),
        'color': (100, 200, 255),
    },
    {
        'name': 'FOCUS',
        'num_neurons': 140,
        'connections': 6,
        'exc_frac': 0.85,
        'exc_weight': 7.0,
        'inh_weight': -4.0,
        'stim': 6.0,
        'type': ('regular', 0.02, 0.2, -65.0, 8.0),
        'color': (255, 255, 100),
    },
    {
        'name': 'SLEEP',
        'num_neurons': 100,
        'connections': 3,
        'exc_frac': 0.75,
        'exc_weight': 7.0,
        'inh_weight': -5.0,
        'stim': 1.5,
        'type': ('regular', 0.02, 0.2, -65.0, 8.0),
        'color': (80, 80, 200),
        'wave_period': 3.0,
    },
    {
        'name': 'DREAM',
        'num_neurons': 120,
        'connections': 6,
        'exc_frac': 0.85,
        'exc_weight': 10.0,
        'inh_weight': -3.0,
        'stim': 2.0,
        'type': ('bursting', 0.02, 0.2, -55.0, 4.0),
        'color': (200, 100, 255),
        'burst_chance': 0.02,
    },
    {
        'name': 'ALERT',
        'num_neurons': 130,
        'connections': 5,
        'exc_frac': 0.85,
        'exc_weight': 8.0,
        'inh_weight': -5.0,
        'stim': 10.0,
        'type': ('chattering', 0.02, 0.2, -50.0, 2.0),
        'color': (255, 200, 50),
    },
]

SYNAPSE_FLASH_FRAMES = 3

PALETTES = [
    {'rest': (15, 20, 60), 'depol': (0, 180, 200), 'spike': (255, 255, 255),
     'recover': (120, 40, 160), 'excite': (0, 255, 150), 'inhibit': (255, 50, 50),
     'bg': (3, 3, 10)},
    {'rest': (40, 15, 10), 'depol': (200, 100, 30), 'spike': (255, 255, 200),
     'recover': (100, 30, 60), 'excite': (255, 200, 50), 'inhibit': (200, 50, 100),
     'bg': (5, 3, 3)},
    {'rest': (10, 30, 15), 'depol': (50, 200, 80), 'spike': (200, 255, 200),
     'recover': (30, 80, 100), 'excite': (100, 255, 100), 'inhibit': (255, 80, 80),
     'bg': (2, 5, 3)},
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
        self.v = -65.0
        self.u = b * (-65.0)
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.is_excitatory = is_excitatory
        self.connections = []
        self.fired = False
        self.flash_timer = 0
        self.input_current = 0.0


class Synapse:
    __slots__ = ('x0', 'y0', 'x1', 'y1', 'timer', 'is_excitatory')

    def __init__(self, x0, y0, x1, y1, is_excitatory):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.timer = SYNAPSE_FLASH_FRAMES
        self.is_excitatory = is_excitatory


class Neurons(Visual):
    name = "BRAIN"
    description = "Spiking neural net"
    category = "science_micro"
    GUIDE = {
        'desc': 'A spiking neural network with excitatory and inhibitory neurons. Regular spiking, chattering, and bursting patterns. Membrane potential dynamics with real spike generation.',
        'credit': 'Izhikevich model',
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.palette_idx = 0
        self.scenario_idx = 0
        self.active_synapses = []
        self.overlay_timer = 2.5
        self.stim_offset = 0.0
        self.wave_phase = 0.0
        self._init_network()

    def _scenario(self):
        return SCENARIOS[self.scenario_idx]

    def _init_network(self):
        sc = self._scenario()
        _, a, b, c, d = sc['type']
        num = sc['num_neurons']
        exc_frac = sc['exc_frac']
        conn_per = sc['connections']

        self.neurons = []
        margin = 3
        positions = set()

        for i in range(num):
            for _ in range(100):
                x = random.randint(margin, GRID_SIZE - margin - 1)
                y = random.randint(margin, GRID_SIZE - margin - 1)
                if (x, y) not in positions:
                    positions.add((x, y))
                    break
            is_exc = random.random() < exc_frac
            n = Neuron(x, y, a, b, c, d, is_exc)
            self.neurons.append(n)

        for ni in self.neurons:
            dists = []
            for nj in self.neurons:
                if nj is ni:
                    continue
                dx = nj.x - ni.x
                dy = nj.y - ni.y
                dists.append((dx * dx + dy * dy, nj))
            dists.sort(key=lambda d: d[0])
            n_conn = min(conn_per, len(dists))
            for k in range(n_conn):
                target = dists[k][1]
                weight = sc['exc_weight'] if ni.is_excitatory else sc['inh_weight']
                ni.connections.append((target, weight))

        self.active_synapses = []
        self.wave_phase = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.left:
            self.stim_offset = max(-5.0, self.stim_offset - 0.3)
            consumed = True
        if input_state.right:
            self.stim_offset = min(10.0, self.stim_offset + 0.3)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.scenario_idx = (self.scenario_idx + 1) % len(SCENARIOS)
            self.stim_offset = 0.0
            self.overlay_timer = 2.5
            self._init_network()
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt
        sc = self._scenario()
        stim = max(0.0, sc['stim'] + self.stim_offset)

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Sleep: slow oscillating wave of stimulation
        if 'wave_period' in sc:
            self.wave_phase += dt
            wave = 0.5 + 0.5 * math.sin(2.0 * math.pi * self.wave_phase / sc['wave_period'])
            stim = stim * wave

        for n in self.neurons:
            n.input_current = random.uniform(0, stim)

            if sc.get('burst_chance') and random.random() < sc['burst_chance']:
                n.input_current += 20.0

        for _ in range(2):
            for n in self.neurons:
                v = n.v
                u = n.u
                I = n.input_current

                v += 0.5 * (0.04 * v * v + 5.0 * v + 140.0 - u + I)
                v += 0.5 * (0.04 * v * v + 5.0 * v + 140.0 - u + I)
                u += n.a * (n.b * v - u)

                n.fired = False
                if v >= V_THRESH:
                    n.fired = True
                    n.flash_timer = 3
                    v = n.c
                    u += n.d

                    for target, weight in n.connections:
                        target.input_current += weight
                        self.active_synapses.append(
                            Synapse(n.x, n.y, target.x, target.y, n.is_excitatory))

                n.v = v
                n.u = u

        for n in self.neurons:
            if n.flash_timer > 0:
                n.flash_timer -= 1

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
        sc = self._scenario()
        self.display.clear(pal['bg'])

        for s in self.active_synapses:
            t = s.timer / SYNAPSE_FLASH_FRAMES
            base = pal['excite'] if s.is_excitatory else pal['inhibit']
            color = (int(base[0] * t * 0.3), int(base[1] * t * 0.3), int(base[2] * t * 0.3))
            self.display.draw_line(s.x0, s.y0, s.x1, s.y1, color)

        for n in self.neurons:
            v = n.v
            x, y = n.x, n.y

            if n.flash_timer > 0:
                t = n.flash_timer / 3.0
                color = self._lerp_color(pal['recover'], pal['spike'], t)
            elif v > -40:
                t = min(1.0, (v + 65) / 25.0)
                color = self._lerp_color(pal['rest'], pal['depol'], t)
            elif v > -70:
                t = min(1.0, (-40 - v) / 30.0)
                color = self._lerp_color(pal['rest'], pal['recover'], t * 0.5)
            else:
                color = pal['rest']

            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x, y, color)

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

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            sc_color = sc['color']
            oc = (int(sc_color[0] * alpha), int(sc_color[1] * alpha),
                  int(sc_color[2] * alpha))
            self.display.draw_text_small(2, 2, sc['name'], oc)
