"""Capture a real Qucs-S window under X11; this is startup evidence, not usability approval."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def capture(executable: Path, output: Path, timeout: float = 30):
    executable = executable.resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)
    for tool in ('xdotool', 'import'):
        if not shutil.which(tool):
            raise RuntimeError(f'Missing X11 capture dependency: {tool}')
    if not os.environ.get('DISPLAY'):
        raise RuntimeError('DISPLAY is required; run with xvfb-run -a')
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'startup.log').open('w') as log:
        process = subprocess.Popen([str(executable)], stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f'Application exited before capture: {process.returncode}')
                windows = subprocess.run(['xdotool', 'search', '--onlyvisible', '--pid', str(process.pid)],
                                         capture_output=True, text=True, timeout=5)
                for window in windows.stdout.split():
                    geometry = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', window],
                                              capture_output=True, text=True, check=True, timeout=5)
                    values = dict(line.split('=', 1) for line in geometry.stdout.splitlines() if '=' in line)
                    if int(values.get('WIDTH', 0)) < 640 or int(values.get('HEIGHT', 0)) < 400:
                        continue
                    title = subprocess.run(['xdotool', 'getwindowname', window], capture_output=True,
                                           text=True, check=True, timeout=5).stdout.strip()
                    # Allow the initial paint to finish, then fail if it crashed.
                    time.sleep(1)
                    if process.poll() is not None:
                        raise RuntimeError('Application crashed during initial paint')
                    subprocess.run(['import', '-window', window, str(output / 'startup.png')],
                                   check=True, timeout=10)
                    report = {'status': 'captured', 'title': title, 'geometry': values,
                              'limits': 'X11 startup only; first-run dialogs may be present. No wiring, saving, simulation or Windows claim.'}
                    (output / 'startup.json').write_text(json.dumps(report, indent=2) + '\n')
                    print(json.dumps(report))
                    return
                time.sleep(.25)
            raise RuntimeError('No visible window of at least 640x400 appeared before timeout')
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('reports/desktop'))
    args = parser.parse_args()
    try:
        capture(args.executable, args.output)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')


if __name__ == '__main__':
    main()
