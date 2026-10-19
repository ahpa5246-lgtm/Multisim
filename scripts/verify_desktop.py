"""Capture a real Qucs-S window under X11; this is startup evidence, not usability approval."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def is_known_setup_notice(title: str) -> bool:
    # Upstream qucs.cpp shows this informational notice before QucsMain->show().
    # Do not send keys to unknown dialogs or weaken the main-window size gate.
    return title == 'Set simulator'


def acknowledge_setup_notice(window: str):
    command = ['xdotool', 'key', '--window', window, 'Return']
    result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        return
    # Qt may destroy the modal on key-down, before xdotool sends key-up.
    # Accept only that specific race, and only when the window is now gone.
    if 'BadWindow' in result.stderr:
        probe = subprocess.run(['xdotool', 'getwindowname', window], capture_output=True,
                               text=True, timeout=5)
        if probe.returncode != 0 and 'BadWindow' in probe.stderr:
            return
    raise subprocess.CalledProcessError(result.returncode, command,
                                        output=result.stdout, stderr=result.stderr)


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
            acknowledged = []
            observed = {}
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
                    title = subprocess.run(['xdotool', 'getwindowname', window], capture_output=True,
                                           text=True, check=True, timeout=5).stdout.strip()
                    observed[window] = {'title': title, 'geometry': values}
                    if is_known_setup_notice(title) and not acknowledged:
                        subprocess.run(['import', '-window', window, str(output / 'setup-notice.png')],
                                       check=True, timeout=10)
                        acknowledge_setup_notice(window)
                        acknowledged.append(title)
                        continue
                    if int(values.get('WIDTH', 0)) < 640 or int(values.get('HEIGHT', 0)) < 400:
                        continue
                    # Allow the initial paint to finish, then fail if it crashed.
                    time.sleep(1)
                    if process.poll() is not None:
                        raise RuntimeError('Application crashed during initial paint')
                    subprocess.run(['import', '-window', window, str(output / 'startup.png')],
                                   check=True, timeout=10)
                    report = {'status': 'captured', 'title': title, 'geometry': values, 'acknowledged_notices': acknowledged,
                              'limits': 'X11 startup only; first-run dialogs may be present. No wiring, saving, simulation or Windows claim.'}
                    (output / 'startup.json').write_text(json.dumps(report, indent=2) + '\n')
                    print(json.dumps(report))
                    return
                time.sleep(.25)
            (output / 'observed-windows.json').write_text(json.dumps(observed, indent=2) + '\n')
            subprocess.run(['import', '-window', 'root', str(output / 'timeout-screen.png')], timeout=10)
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
