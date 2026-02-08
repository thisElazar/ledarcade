// =============================================================
// shared.js - Constants, Display, FONT, LEDRenderer
// Used by both showcase (index.html) and emulator (emulator.html)
// =============================================================

const GRID = 64;
const CELL = 10;
const DOT  = 8;
const GAP  = 1;

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

class LEDRenderer {
  constructor(ledCanvas, glowCanvas) {
    this.ledCanvas = ledCanvas;
    this.glowCanvas = glowCanvas;
    this.ledCtx = ledCanvas.getContext('2d');
    this.glowCtx = glowCanvas.getContext('2d');

    // Handle device pixel ratio for sharp rendering
    const dpr = window.devicePixelRatio || 1;
    const size = GRID * CELL;
    ledCanvas.width = size * dpr;
    ledCanvas.height = size * dpr;
    this.ledCtx.scale(dpr, dpr);

    // Pre-create glow ImageData
    this.glowImageData = this.glowCtx.createImageData(GRID, GRID);

    // Fill LED background once
    this.ledCtx.fillStyle = '#080808';
    this.ledCtx.fillRect(0, 0, size, size);
  }

  render(display) {
    const buf = display.buffer;
    const ctx = this.ledCtx;
    const size = GRID * CELL;
    const glowData = this.glowImageData.data;

    // Clear LED canvas to dark
    ctx.fillStyle = '#060606';
    ctx.fillRect(0, 0, size, size);

    // Draw each pixel as an LED dot
    for (let y = 0; y < GRID; y++) {
      for (let x = 0; x < GRID; x++) {
        const i = (y * GRID + x) * 3;
        const r = buf[i], g = buf[i+1], b = buf[i+2];

        // LED dot
        if (r > 3 || g > 3 || b > 3) {
          ctx.fillStyle = `rgb(${r},${g},${b})`;
          ctx.fillRect(x * CELL + GAP, y * CELL + GAP, DOT, DOT);
        } else {
          // Faint unlit LED
          ctx.fillStyle = '#0b0b0b';
          ctx.fillRect(x * CELL + GAP, y * CELL + GAP, DOT, DOT);
        }

        // Glow pixel
        const gi = (y * GRID + x) * 4;
        glowData[gi] = r; glowData[gi+1] = g; glowData[gi+2] = b; glowData[gi+3] = 255;
      }
    }

    this.glowCtx.putImageData(this.glowImageData, 0, 0);
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
