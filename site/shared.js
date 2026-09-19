// =============================================================
// shared.js - Constants, Display, FONT, LEDRenderer
// Used by both showcase (index.html) and emulator (emulator.html)
// =============================================================

const GRID = 64;
const CELL = 10;

// ----- Display (mirrors the Python Display class) -----

class Display {
  constructor() {
    this.buffer = new Uint8ClampedArray(GRID * GRID * 3);
  }

  clear(r, g, b) {
    for (let i = 0; i < this.buffer.length; i += 3) {
      this.buffer[i] = r; this.buffer[i+1] = g; this.buffer[i+2] = b;
    }
  }

  setPixel(x, y, color) {
    x = x | 0; y = y | 0;
    if (x >= 0 && x < GRID && y >= 0 && y < GRID) {
      const i = (y * GRID + x) * 3;
      this.buffer[i] = color[0];
      this.buffer[i+1] = color[1];
      this.buffer[i+2] = color[2];
    }
  }

  getPixel(x, y) {
    x = x | 0; y = y | 0;
    if (x >= 0 && x < GRID && y >= 0 && y < GRID) {
      const i = (y * GRID + x) * 3;
      return [this.buffer[i], this.buffer[i+1], this.buffer[i+2]];
    }
    return [0, 0, 0];
  }

  drawLine(x0, y0, x1, y1, color) {
    x0=x0|0; y0=y0|0; x1=x1|0; y1=y1|0;
    let dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
    let sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let err = dx - dy;
    while (true) {
      this.setPixel(x0, y0, color);
      if (x0 === x1 && y0 === y1) break;
      let e2 = 2 * err;
      if (e2 > -dy) { err -= dy; x0 += sx; }
      if (e2 < dx)  { err += dx; y0 += sy; }
    }
  }

  drawRect(x, y, w, h, color) {
    for (let dy = 0; dy < h; dy++)
      for (let dx = 0; dx < w; dx++)
        this.setPixel(x + dx, y + dy, color);
  }

  drawCircle(cx, cy, r, color, filled = false) {
    for (let y = -r; y <= r; y++) {
      for (let x = -r; x <= r; x++) {
        const d2 = x*x + y*y;
        if (filled ? d2 <= r*r : Math.abs(d2 - r*r) < r*2)
          this.setPixel(cx + x, cy + y, color);
      }
    }
  }

  drawTextSmall(x, y, text, color) {
    let cursor = x;
    for (const ch of text.toUpperCase()) {
      const glyph = FONT[ch];
      if (glyph) {
        for (let r = 0; r < 5; r++)
          for (let c = 0; c < 3; c++)
            if ((glyph[r] >> (2 - c)) & 1)
              this.setPixel(cursor + c, y + r, color);
      }
      cursor += 4;
    }
  }
}

const FONT = {
  'A':[2,5,7,5,5],'B':[6,5,6,5,6],'C':[3,4,4,4,3],'D':[6,5,5,5,6],
  'E':[7,4,6,4,7],'F':[7,4,6,4,4],'G':[3,4,5,5,3],'H':[5,5,7,5,5],
  'I':[7,2,2,2,7],'J':[1,1,1,5,2],'K':[5,6,4,6,5],'L':[4,4,4,4,7],
  'M':[5,7,7,5,5],'N':[5,7,7,7,5],'O':[2,5,5,5,2],'P':[6,5,6,4,4],
  'Q':[2,5,5,6,3],'R':[6,5,6,5,5],'S':[3,4,2,1,6],'T':[7,2,2,2,2],
  'U':[5,5,5,5,3],'V':[5,5,5,2,2],'W':[5,5,7,7,5],'X':[5,5,2,5,5],
  'Y':[5,5,2,2,2],'Z':[7,1,2,4,7],
  '0':[7,5,5,5,7],'1':[2,6,2,2,7],'2':[6,1,2,4,7],'3':[6,1,2,1,6],
  '4':[5,5,7,1,1],'5':[7,4,6,1,6],'6':[3,4,6,5,2],'7':[7,1,2,2,2],
  '8':[2,5,2,5,2],'9':[2,5,3,1,6],
  ' ':[0,0,0,0,0],':':[0,2,0,2,0],'-':[0,0,7,0,0],'.':[0,0,0,0,2],
  '!':[2,2,2,0,2],'?':[6,1,2,0,2],
};


// ----- LED Renderer -----
// The look of the marketing renders (tools/render_clip.py, paper_display.py):
// round LED dots on black, plus a soft glow that is the frame blurred at LED
// resolution, scaled up and screen-blended over the dots.

const DOT_RADIUS = 6.5 / 16;   // of one LED cell, as in render_clip
const GLOW_GAIN = 0.52;        // lit share of each LED cell (mean of render_clip's dot mask)

class LEDRenderer {
  constructor(ledCanvas) {
    this.canvas = ledCanvas;
    this.ctx = ledCanvas.getContext('2d');

    // The frame and its glow, one canvas pixel per LED
    this.frame = this._grid();
    this.glow = this._grid();
    this.glowBuf = new Float32Array(GRID * GRID * 3);
    this.mask = document.createElement('canvas');

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  _grid() {
    const c = document.createElement('canvas');
    c.width = c.height = GRID;
    const ctx = c.getContext('2d');
    const img = ctx.createImageData(GRID, GRID);
    img.data.fill(255);
    return { canvas: c, ctx, img };
  }

  // Backing store = displayed size in device pixels, snapped to whole-pixel LEDs.
  // The mask is black with a round hole over every LED.
  resize() {
    const dpr = window.devicePixelRatio || 1;
    const shown = this.canvas.clientWidth || GRID * CELL;
    const cell = Math.max(3, Math.round(shown * dpr / GRID));
    if (cell === this.cell) return;
    this.cell = cell;
    const size = this.canvas.width = this.canvas.height = this.mask.width = this.mask.height = GRID * cell;
    const m = this.mask.getContext('2d');
    m.fillStyle = '#000';
    m.fillRect(0, 0, size, size);
    m.globalCompositeOperation = 'destination-out';
    m.beginPath();
    for (let y = 0; y < GRID; y++) {
      for (let x = 0; x < GRID; x++) {
        const cx = (x + 0.5) * cell, cy = (y + 0.5) * cell;
        m.moveTo(cx + DOT_RADIUS * cell, cy);
        m.arc(cx, cy, DOT_RADIUS * cell, 0, Math.PI * 2);
      }
    }
    m.fill();
  }

  render(display) {
    const buf = display.buffer;
    const px = this.frame.img.data, gpx = this.glow.img.data, g = this.glowBuf;
    const row = GRID * 3;

    // Frame as-is; glow = frame * gain, blurred [1 4 1]/6 across then down (edges clamped)
    for (let i = 0, j = 0; i < buf.length; i += 3, j += 4) {
      px[j] = buf[i]; px[j+1] = buf[i+1]; px[j+2] = buf[i+2];
      const x = (i / 3) % GRID;
      const l = x > 0 ? i - 3 : i, r = x < GRID - 1 ? i + 3 : i;
      for (let c = 0; c < 3; c++) g[i+c] = (buf[l+c] + 4 * buf[i+c] + buf[r+c]) * (GLOW_GAIN / 6);
    }
    for (let i = 0, j = 0; i < g.length; i += 3, j += 4) {
      const u = i >= row ? i - row : i, d = i < g.length - row ? i + row : i;
      for (let c = 0; c < 3; c++) gpx[j+c] = (g[u+c] + 4 * g[i+c] + g[d+c]) / 6;
    }
    this.frame.ctx.putImageData(this.frame.img, 0, 0);
    this.glow.ctx.putImageData(this.glow.img, 0, 0);

    const ctx = this.ctx, size = this.canvas.width;
    ctx.globalCompositeOperation = 'source-over';
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(this.frame.canvas, 0, 0, size, size);   // square colour cells
    ctx.drawImage(this.mask, 0, 0);                       // cut to round dots on black
    ctx.globalCompositeOperation = 'screen';
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(this.glow.canvas, 0, 0, size, size);
  }

  getAverageColor(display) {
    const buf = display.buffer;
    let tr = 0, tg = 0, tb = 0;
    for (let i = 0; i < buf.length; i += 3) {
      tr += buf[i]; tg += buf[i+1]; tb += buf[i+2];
    }
    const n = GRID * GRID;
    return [tr/n|0, tg/n|0, tb/n|0];
  }
}
