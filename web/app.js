// The page: Monaco on the left, the lawn on the right, the Python worker behind both.
import { Renderer } from './render.js';

const $ = (id) => document.getElementById(id);
const BASE = new URL('.', import.meta.url).href;

// --- level table for the UI (names, prices and templates; the rules live in Python) ----------
const LEVELS = [
  { name: 'Sequence', price: 0, unlock: '' },
  { name: 'Repetition', price: 200, unlock: '`for` loops' },
  { name: 'State', price: 400, unlock: 'a 5×5 lawn, `while`, get_x/get_y/get_heading' },
  { name: 'Decisions', price: 800, unlock: 'grass_height, blade_on/off, `if`' },
  { name: 'Battery', price: 1200, unlock: 'the battery, get_battery, manual_recharge' },
  { name: 'Blade', price: 1500, unlock: 'blade wear, get_blade, manual_sharpen' },
  { name: 'Functions', price: 1800, unlock: 'the station, charge, sharpen, `def`' },
  { name: 'Lists', price: 2500, unlock: 'scan, get_growth, lists' },
  { name: 'Modules', price: 3000, unlock: '`import`' },
  { name: 'Flower beds', price: 6000, unlock: 'get_ground, and/or/not' },
  { name: 'Lawn shapes', price: 8000, unlock: 'is_clear' },
  { name: 'Cutting height', price: 12000, unlock: 'set_cut_height' },
  { name: 'Moving obstacles', price: 16000, unlock: 'the hedgehog and the person' },
  { name: 'Contracts', price: 20000, unlock: 'dicts' },
];
const TEMPLATES = {
  0: `# The mower starts at (0, 0) facing North and cuts every tile it drives into.
# Every call is one step. Mow the whole 3x3 lawn.
forward()
forward()
turn_right()
forward()
`,
  1: `# The grass grows back. Use a for loop to mow the lawn several times.
for lap in range(3):
    forward()
    forward()
    turn_right()
    forward()
    turn_right()
    forward()
    forward()
    turn_left()
    forward()
    turn_left()
    forward()
    forward()
    turn_right()
    turn_right()
    forward()
    forward()
    turn_right()
    turn_right()
`,
  2: `# The lawn is bigger now. forward() returns False at the fence, and the mower knows
# where it is. Write a program that does not depend on the size of the lawn.
while forward():
    pass
turn_right()
`,
  3: `# Short grass pays half and still costs cutting time. Look before you cut.
while True:
    if grass_height() >= 40:
        blade_on()
    else:
        blade_off()
    if not forward():
        turn_right()
`,
};

// --- state ---------------------------------------------------------------------------------
const save = JSON.parse(localStorage.getItem('mowbot') || '{}');
const progress = { tokens: save.tokens || 0, level: save.level || 0, code: save.code || {} };
let playing = progress.level;            // the level being replayed
let running = false;
let silent = false;                      // a run with empty code, only to draw the fresh lawn
let editor = null;

function persist() {
  progress.code[playing] = editor ? editor.getValue() : progress.code[playing];
  localStorage.setItem('mowbot', JSON.stringify(progress));
}

// --- worker ------------------------------------------------------------------------------------
const control = new SharedArrayBuffer(8);
const interrupt = new SharedArrayBuffer(1);
const controlView = new Int32Array(control);
const worker = new Worker(new URL('py-worker.js', import.meta.url), { type: 'module' });
worker.postMessage({ type: 'init', control, interrupt });

const renderer = new Renderer($('lawn'));
let pending = null;              // latest snapshot, drawn on the next frame

worker.onmessage = (ev) => {
  const msg = ev.data;
  if (msg.type === 'ready') { $('s-state').textContent = 'Python ready'; $('run').disabled = false; }
  else if (msg.type === 'failed') { $('s-state').textContent = 'Python failed'; log(msg.error, 'err'); }
  else if (msg.type === 'snapshot') { pending = msg.snapshot; }
  else if (msg.type === 'stdout') { log(msg.text); }
  else if (msg.type === 'done') finish(msg.result);
};

function frame() {
  if (pending) { renderer.draw(pending); renderer.fit($('lawn-pane')); status(pending); pending = null; }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// --- run and stop --------------------------------------------------------------------------------
function run() {
  if (running) return;
  running = true;
  persist();
  $('run').disabled = true; $('stop').disabled = false;
  $('s-state').textContent = 'running';
  log(`▶ level ${playing}, ${LEVELS[playing].name}`, 'note');
  new Uint8Array(interrupt)[0] = 0;
  worker.postMessage({ type: 'run', code: editor.getValue(), level: playing, easy: $('easy').checked });
}

function stop() {
  new Uint8Array(interrupt)[0] = 2;      // SIGINT for Pyodide
  Atomics.store(controlView, 1, 1);      // wake the sleeping worker
  Atomics.notify(controlView, 1);
  Atomics.store(controlView, 1, 0);
}

function showLawn(level) {
  silent = true;
  worker.postMessage({ type: 'run', code: '', level, easy: $('easy').checked });
}

function finish(result) {
  if (silent) { silent = false; if (result.snapshot) pending = result.snapshot; return; }
  running = false;
  $('run').disabled = false; $('stop').disabled = true;
  $('s-state').textContent = 'Python ready';
  if (result.snapshot) pending = result.snapshot;
  if (result.error) log(result.error, result.ok === false && !result.gate && !result.stopped ? 'err' : 'note');
  if (result.ticks !== undefined) {
    log(`■ ${result.tokens} tokens in ${result.ticks} ticks, score ${result.score} per 1000 ticks`, 'ok');
    // tokens count only on the current level; replaying an old level is practice
    if (playing === progress.level && !result.gate) {
      progress.tokens = Math.round((progress.tokens + result.tokens) * 10) / 10;
      persist();
      showProgress();
    }
  }
}

$('run').onclick = run;
$('stop').onclick = stop;
$('clear').onclick = () => { $('output').textContent = ''; };
$('speed').oninput = setSpeed;
function setSpeed() {
  const perSecond = Number($('speed').value);
  $('speed-val').textContent = perSecond;
  Atomics.store(controlView, 0, Math.round(1000 / perSecond));
}
setSpeed();

// --- progress ------------------------------------------------------------------------------------
function showProgress() {
  $('p-level').textContent = progress.level;
  $('p-name').textContent = LEVELS[progress.level].name;
  $('p-tokens').textContent = progress.tokens;
  const next = LEVELS[progress.level + 1];
  $('p-next').textContent = next ? `${next.unlock} for ${next.price}` : 'everything unlocked';
  $('unlock').disabled = !(next && progress.tokens >= next.price);
  const sel = $('level');
  sel.innerHTML = '';
  for (let i = 0; i <= progress.level; i++) {
    const o = document.createElement('option');
    o.value = i; o.textContent = `${i}: ${LEVELS[i].name}`;
    sel.appendChild(o);
  }
  sel.value = playing;
}
$('unlock').onclick = () => {
  const next = LEVELS[progress.level + 1];
  if (!next || progress.tokens < next.price) return;
  progress.tokens = Math.round((progress.tokens - next.price) * 10) / 10;
  progress.level += 1;
  log(`★ Level ${progress.level}, ${next.name}: unlocked ${next.unlock}.`, 'ok');
  switchLevel(progress.level);
};
$('level').onchange = () => switchLevel(Number($('level').value));

function switchLevel(n) {
  if (running) return;
  persist();
  playing = n;
  editor.setValue(progress.code[n] ?? TEMPLATES[n] ?? `# Level ${n}: ${LEVELS[n].name}\n`);
  showProgress();
  showLawn(n);
}
$('easy').onchange = () => { if (!running) showLawn(playing); };
$('act-help').onclick = () => {
  log(`Unlocked up to level ${playing}:`, 'note');
  log('  forward(), backward(), turn_left(), turn_right(); North, East, South, West');
  for (let i = 1; i <= playing; i++) log(`  level ${i}: ${LEVELS[i].unlock}`);
};

// --- output and status ---------------------------------------------------------------------------
function log(text, cls) {
  const out = $('output');
  const span = document.createElement('span');
  if (cls) span.className = cls;
  span.textContent = text + '\n';
  out.appendChild(span);
  out.scrollTop = out.scrollHeight;
}

function status(s) {
  $('s-level').textContent = `level ${s.level} ${s.name}`;
  $('s-ticks').textContent = `ticks ${s.ticks}`;
  $('s-tokens').textContent = `tokens ${s.tokens}`;
  $('s-score').textContent = `score ${s.score} /1000`;
  $('s-battery').hidden = !s.rules.battery;
  $('s-battery').textContent = `battery ${s.battery} %`;
  $('s-blade').hidden = !s.rules.blade;
  $('s-blade').textContent = `blade ${s.sharpness} %`;
}

// --- editor --------------------------------------------------------------------------------------
require.config({ paths: { vs: BASE + 'vendor/monaco/vs' } });
require(['vs/editor/editor.main'], async () => {
  editor = monaco.editor.create($('editor'), {
    value: progress.code[playing] ?? TEMPLATES[playing] ?? '',
    language: 'python', theme: 'vs-dark', fontSize: 14, minimap: { enabled: false },
    automaticLayout: true, tabSize: 4, insertSpaces: true, scrollBeyondLastLine: false,
  });
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, run);
  editor.onDidChangeModelContent(() => persist());
  await renderer.load(BASE);
  showProgress();
  $('run').disabled = true;                         // until Python is ready
  showLawn(playing);
});
window.addEventListener('resize', () => renderer.fit($('lawn-pane')));
