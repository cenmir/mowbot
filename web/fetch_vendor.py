"""Fetch the two things the page needs but git does not hold: Pyodide and the Monaco editor.

Both are served from our own origin, never a CDN, because the page runs cross-origin isolated
(it needs SharedArrayBuffer for the speed slider and the Stop button) and that blocks most
third-party resources anyway. Run once per checkout:

    python3 web/fetch_vendor.py
"""
import io
import pathlib
import tarfile
import urllib.request

PYODIDE = '314.0.7'            # the version the Python book serves too
MONACO = '0.52.2'
CORE = ['pyodide.js', 'pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm',
        'python_stdlib.zip', 'pyodide-lock.json']
HERE = pathlib.Path(__file__).resolve().parent


def get(url):
    return urllib.request.urlopen(url).read()


def fetch_pyodide():
    out = HERE / 'pyodide'
    out.mkdir(exist_ok=True)
    tgz = get(f'https://registry.npmjs.org/pyodide/-/pyodide-{PYODIDE}.tgz')
    with tarfile.open(fileobj=io.BytesIO(tgz)) as tar:
        for name in CORE:
            (out / name).write_bytes(tar.extractfile(f'package/{name}').read())
    print('Pyodide', PYODIDE, 'in', out)


def fetch_monaco():
    out = HERE / 'vendor' / 'monaco'
    out.mkdir(parents=True, exist_ok=True)
    tgz = get(f'https://registry.npmjs.org/monaco-editor/-/monaco-editor-{MONACO}.tgz')
    with tarfile.open(fileobj=io.BytesIO(tgz)) as tar:
        for member in tar.getmembers():
            if member.isfile() and member.name.startswith('package/min/vs/'):
                target = out / member.name[len('package/min/'):]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(tar.extractfile(member).read())
    print('Monaco', MONACO, 'in', out)


if __name__ == '__main__':
    fetch_pyodide()
    fetch_monaco()
