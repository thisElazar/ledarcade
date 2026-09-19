"""
Desktop emulators in the look of the marketing renders (tools/render_clip.py),
live in a window.

    python run_demo.py             # PanelDisplay: just the square, LED dots on black
    python run_arcade.py --paper   # PaperDisplay: the white page of the Reels and carousels

Every frame is composed by render_clip's own Composer / PaperComposer and
scaled to fit the screen, so the window and the posts stay one look. Only the
glow is done here: render_clip leaves that to ffmpeg.
"""

from types import SimpleNamespace

import numpy as np
import pygame

from arcade import Display, Colors, GRID_SIZE

SCREEN_MARGIN = 130   # menu bar + title bar + dock


class PanelDisplay(Display):
    """Just the square: round LED dots and glow on black (render_clip's square clip)."""

    def _composer(self, render_clip):
        return render_clip.Composer(vertical=False)

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Wonder Cabinet")
        desk_h = pygame.display.get_desktop_sizes()[0][1]

        # After pygame.init(): render_clip defaults SDL to the headless dummy
        # driver at import, which must not reach a real window.
        from tools import render_clip
        self.comp = self._composer(render_clip)

        # Largest whole-pixel LED whose frame fits this screen (render_clip LEDs are 16 px).
        cell = max(4, min(render_clip.CELL, (desk_h - SCREEN_MARGIN) * render_clip.CELL // self.comp.h))
        k = cell / render_clip.CELL
        self.screen = pygame.display.set_mode((round(self.comp.w * k), round(self.comp.h * k)))
        self.panel_rect = pygame.Rect(round(self.comp.px * k), round(self.comp.py * k),
                                      cell * GRID_SIZE, cell * GRID_SIZE)
        self.glow_gain = float(self.comp.mask.mean())   # lit share of each LED cell

        self.buffer = [[Colors.BLACK for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.font = pygame.font.Font(None, 24)
        self._color_lut = None
        self._epilepsy_guard = None

    def _panel_pixels(self):
        """The 64x64 buffer as uint8, after the same safety transforms as Display."""
        buf = np.asarray(self.buffer, dtype=np.uint8)
        if self._color_lut is None and self._epilepsy_guard is None:
            return buf
        from safety import apply_color_lut_buffer
        fb = bytearray(buf.tobytes())
        if self._color_lut is not None:
            apply_color_lut_buffer(fb, self._color_lut)
        if self._epilepsy_guard is not None:
            self._epilepsy_guard.process(fb, GRID_SIZE * GRID_SIZE)
        return np.frombuffer(fb, dtype=np.uint8).reshape(GRID_SIZE, GRID_SIZE, 3)

    def _glow(self, buf):
        """render_clip's ffmpeg glow (gblur sigma 10 px, screen-blended inside the
        panel): blur at LED resolution, upscale, screen = a + g * (1 - a)."""
        g = np.pad(buf * self.glow_gain, ((1, 1), (1, 1), (0, 0)), mode="edge")
        g = (g[:-2] + 4 * g[1:-1] + g[2:]) / 6
        g = (g[:, :-2] + 4 * g[:, 1:-1] + g[:, 2:]) / 6
        small = pygame.image.frombuffer(g.astype(np.uint8).tobytes(), (GRID_SIZE, GRID_SIZE), "RGB")
        glow = pygame.transform.smoothscale(small, self.panel_rect.size)
        inv = pygame.Surface(self.panel_rect.size)
        inv.fill((255, 255, 255))
        inv.blit(self.screen, (0, 0), self.panel_rect, special_flags=pygame.BLEND_RGB_SUB)
        glow.blit(inv, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        self.screen.blit(glow, self.panel_rect, special_flags=pygame.BLEND_RGB_ADD)

    def render(self):
        buf = self._panel_pixels()
        page = pygame.image.frombuffer(self.comp.frame(SimpleNamespace(buffer=buf)),
                                       (self.comp.w, self.comp.h), "RGB")
        self.screen.blit(pygame.transform.smoothscale(page, self.screen.get_size()), (0, 0))
        self._glow(buf)
        pygame.display.flip()


class PaperDisplay(PanelDisplay):
    """The white page: masthead, ruled mount, and the catalog line under the plate
    (render_clip's 4:5 slide layout)."""

    def _composer(self, render_clip):
        self._catalog_label = render_clip.catalog_label
        self.label_cls = None
        return render_clip.PaperComposer(slide=True)

    def set_label(self, item):
        """Name and catalog line under the plate for what is playing; None clears it."""
        cls = type(item) if item is not None else None
        if cls is not self.label_cls:
            self.label_cls = cls
            self.comp.set_title(self._catalog_label(cls) if cls else "")
