"""Exercise Save As only on the CI-owned application and a new artifact path."""
from pathlib import Path
import subprocess
import time


def save_copy(pid: int, window: str, destination: Path):
    destination = destination.resolve()
    if destination.exists():
        raise ValueError('Refusing to overwrite the roundtrip destination')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Qt WindowShortcut actions require an active top-level window, not X input focus alone.
    subprocess.run(['xdotool', 'windowactivate', '--sync', window], check=True, timeout=10)
    subprocess.run(['xdotool', 'windowfocus', '--sync', window], check=True, timeout=5)
    # Capture the real menu's labels/bindings before probing the shortcut.
    # This supplies diagnostic evidence without invoking an assumed menu index.
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'alt+f'], check=True, timeout=5)
    time.sleep(.3)
    subprocess.run(['import', '-window', 'root', str(destination.parent/'file-menu.png')],
                   check=True, timeout=10)
    subprocess.run(['xdotool', 'key', 'Escape'], check=True, timeout=5)
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+shift+s'], check=True, timeout=5)
    deadline = time.monotonic() + 10
    dialog = None
    while time.monotonic() < deadline:
        windows = subprocess.run(['xdotool', 'search', '--onlyvisible', '--pid', str(pid)],
                                 capture_output=True, text=True, timeout=5)
        for candidate in windows.stdout.split():
            name = subprocess.run(['xdotool', 'getwindowname', candidate], capture_output=True,
                                  text=True, timeout=5)
            if name.returncode == 0 and name.stdout.strip() == 'Enter a Document Name':
                dialog = candidate
                break
        if dialog:
            break
        time.sleep(.2)
    if dialog is None:
        subprocess.run(['import', '-window', 'root', str(destination.parent/'save-timeout.png')], timeout=10)
        raise RuntimeError('Save As did not open the expected document-name dialog')
    subprocess.run(['import', '-window', dialog, str(destination.parent/'save-dialog.png')], check=True, timeout=10)
    subprocess.run(['xdotool', 'windowactivate', '--sync', dialog], check=True, timeout=10)
    subprocess.run(['xdotool', 'windowfocus', '--sync', dialog], check=True, timeout=5)
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+a'], check=True, timeout=5)
    subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '1', '--', str(destination)],
                   check=True, timeout=10)
    subprocess.run(['import', '-window', dialog, str(destination.parent/'save-filled.png')],
                   check=True, timeout=10)
    # The filename completer can consume Return; use the visible Save button mnemonic.
    subprocess.run(['xdotool', 'key', '--clearmodifiers', 'alt+s'], check=True, timeout=5)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if destination.is_file() and destination.stat().st_size > 0:
            return {'saved_copy': str(destination), 'bytes': destination.stat().st_size,
                    'limits': 'GUI Save As only; validate saved topology separately'}
        time.sleep(.2)
    subprocess.run(['import', '-window', 'root', str(destination.parent/'save-file-timeout.png')],
                   check=True, timeout=10)
    raise RuntimeError('Save As did not produce a nonempty schematic')
