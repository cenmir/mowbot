// Draws a snapshot of the game on a canvas from the sprite sheet, pixel for pixel like the mock.
const TILE = 32;
const BORDER = 2;             // one ring of garden, one ring of fence, like the mock lawn

export class Renderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.sheet = null;
    this.index = null;
    this.snapshot = null;
    this.scale = 1;
  }

  async load(base) {
    const [img, json] = await Promise.all([
      new Promise((ok, fail) => {
        const im = new Image();
        im.onload = () => ok(im);
        im.onerror = fail;
        im.src = base + 'assets/sheet.png';
      }),
      fetch(base + 'assets/sheet.json').then((r) => r.json()),
    ]);
    this.sheet = img;
    this.index = json;
  }

  blit(name, x, y) {
    const r = this.index[name];
    if (!r) throw new Error('no sprite ' + name);
    this.ctx.drawImage(this.sheet, r[0], r[1], r[2], r[3], x, y, r[2], r[3]);
  }

  // integer scale so that the pixels stay crisp, chosen to fit the pane
  fit(container) {
    if (!this.snapshot) return;
    const W = (this.snapshot.width + 2 * BORDER) * TILE;
    const H = (this.snapshot.height + 2 * BORDER) * TILE;
    const scale = Math.max(1, Math.floor(Math.min(container.clientWidth / W, container.clientHeight / H)));
    if (this.canvas.width !== W || this.canvas.height !== H) {
      this.canvas.width = W;
      this.canvas.height = H;
    }
    this.scale = scale;
    this.canvas.style.width = W * scale + 'px';
    this.canvas.style.height = H * scale + 'px';
  }

  draw(snapshot) {
    this.snapshot = snapshot;
    const { width: w, height: h } = snapshot;
    const ctx = this.ctx;
    ctx.imageSmoothingEnabled = false;
    const cols = w + 2 * BORDER, rows = h + 2 * BORDER;
    // garden all around
    for (let i = 0; i < cols; i++)
      for (let j = 0; j < rows; j++)
        this.blit(`grass_1_0_${(i * 7 + j) % 4}`, i * TILE, j * TILE);
    // the fence ring on the inner border tile
    for (let i = 1; i <= w + 2; i++) {
      this.blit('fence_h', i * TILE, 1 * TILE);
      this.blit('fence_h', i * TILE, (h + 2) * TILE);
    }
    for (let j = 2; j <= h + 1; j++) {
      this.blit('fence_v', 1 * TILE, j * TILE);
      this.blit('fence_v', (w + 2) * TILE, j * TILE);
    }
    const at = (x, y) => [(x + BORDER) * TILE, (h - 1 - y + BORDER) * TILE];
    // the lawn
    for (const t of snapshot.tiles) {
      const [px, py] = at(t.x, t.y);
      const v = (t.x * 7 + t.y * 3) % 4;
      if (t.ground === 'Grass') {
        const tier = t.h < 30 ? 0 : t.h < 40 ? 1 : t.h <= 70 ? 2 : 3;
        const stripe = t.stripe === 'East' || t.stripe === 'North' ? 'p'
                     : t.stripe === 'West' || t.stripe === 'South' ? 'm' : '0';
        this.blit(`grass_${tier}_${stripe}_${v}`, px, py);
      } else if (t.ground === 'Path') {
        this.blit(`path_${v % 2}`, px, py);
      } else if (t.ground === 'Flowerbed') {
        this.blit(`flower_${v % 2}`, px, py);
      } else if (t.ground === 'Stone') {
        this.blit(`grass_1_0_${v}`, px, py);
        this.blit('rock', px, py);
      }
    }
    if (snapshot.station) {
      const [px, py] = at(snapshot.station[0], snapshot.station[1]);
      this.blit('station', px, py);
    }
    for (const ob of snapshot.obstacles) {
      const [px, py] = at(ob.x, ob.y);
      this.blit(ob.kind === 'hedgehog' ? 'hedgehog_S' : 'person', px, py);
    }
    const m = snapshot.mower;
    const [mx, my] = at(m.x, m.y);
    this.blit('mower_' + m.heading[0], mx, my);
    // two trees outside the fence, as in the mock
    this.blit('tree', 0, 0);
    this.blit('tree', (w + 3) * TILE, (h + 2) * TILE);
    this.blit('rock', (w + 3) * TILE, 3 * TILE);
  }
}
