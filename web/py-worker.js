// Runs the student's Python in the background with Pyodide, so the page never freezes.
//
// The rules engine (../mowbot/*.py) is fetched from the repo and written into Pyodide's file
// system, so the browser runs exactly the code the tests run. After every game action the
// engine calls back into `step`, which posts a snapshot for drawing and then sleeps on a
// shared buffer for the speed slider's delay. Stop sets Pyodide's interrupt buffer, which
// raises KeyboardInterrupt inside the student's code, and wakes the sleep early.
import { loadPyodide } from './pyodide/pyodide.mjs';

const FILES = ['__init__.py', 'lawn.py', 'game.py', 'levels.py', 'gate.py', 'api.py'];

let py = null;
let control = null;      // Int32Array over a SharedArrayBuffer: [0] delay in ms, [1] wake word
let interrupt = null;    // Uint8Array over a SharedArrayBuffer: 2 means "stop"

function step(json) {
  self.postMessage({ type: 'snapshot', snapshot: JSON.parse(json) });
  const delay = Atomics.load(control, 0);
  if (delay > 0) Atomics.wait(control, 1, 0, delay);
}

// The runner lives in Python so that the student's code, the gate and the game share one
// interpreter and one traceback format.
const RUNNER = `
import json, traceback
import mowbot_host
from mowbot import Game, LEVELS, GameOver, check_syntax
from mowbot import api

def short(tb):
    lines = tb.rstrip().split("\\n")
    at = next((i for i, l in enumerate(lines) if 'File "main.py"' in l), None)
    return "\\n".join(lines[at:] if at is not None else lines[-3:])

def run(code, level, easy):
    lvl = LEVELS[level]
    msg = check_syntax(code, lvl.allowed_syntax)
    if msg:
        return json.dumps({"ok": False, "error": msg, "gate": True})
    game = Game(lvl, easy=easy)
    game.listeners.append(lambda g: mowbot_host.step(json.dumps(g.snapshot())))
    api.bind(game)
    mowbot_host.step(json.dumps(game.snapshot()))
    ns = {"__name__": "__main__"}
    exec("from mowbot.api import *", ns)
    outcome = {"ok": True}
    try:
        exec(compile(code, "main.py", "exec"), ns)
    except GameOver as e:
        outcome = {"ok": False, "error": str(e), "gameover": True}
    except KeyboardInterrupt:
        outcome = {"ok": False, "error": "Stopped.", "stopped": True}
    except Exception:
        outcome = {"ok": False, "error": short(traceback.format_exc())}
    outcome.update(tokens=round(game.tokens, 1), ticks=game.ticks, score=round(game.score(), 1),
                   snapshot=game.snapshot())
    return json.dumps(outcome)
`;

const ready = (async () => {
  py = await loadPyodide({ indexURL: new URL('pyodide/', import.meta.url).href });
  py.FS.mkdirTree('/mowbot');
  for (const name of FILES) {
    const url = new URL('../mowbot/' + name, import.meta.url);
    const src = await (await fetch(url)).text();
    py.FS.writeFile('/mowbot/' + name, src);
  }
  py.registerJsModule('mowbot_host', { step });
  py.runPython("import sys; sys.path.insert(0, '/')");
  py.FS.writeFile('/host_runner.py', RUNNER);
  py.runPython('import host_runner');
  return py;
})();

ready.then(() => self.postMessage({ type: 'ready' }),
           (e) => self.postMessage({ type: 'failed', error: String(e) }));

self.onmessage = async (ev) => {
  const msg = ev.data;
  if (msg.type === 'init') {
    control = new Int32Array(msg.control);
    interrupt = new Uint8Array(msg.interrupt);
    return;
  }
  if (msg.type === 'run') {
    try {
      await ready;
      py.setInterruptBuffer(interrupt);
      interrupt[0] = 0;
      py.setStdout({ batched: (s) => self.postMessage({ type: 'stdout', text: s }) });
      const runner = py.globals.get('host_runner');
      const result = JSON.parse(runner.run(msg.code, msg.level, msg.easy));
      runner.destroy();
      self.postMessage({ type: 'done', result });
    } catch (e) {
      self.postMessage({ type: 'done', result: { ok: false, error: String(e) } });
    }
  }
};
