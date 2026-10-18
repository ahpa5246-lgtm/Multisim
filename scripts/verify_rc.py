"""Run real ngspice and compare an RC charge with its analytic solution."""
import argparse
import json
import math
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def validate(rows):
    if len(rows) < 100:
        raise ValueError('Insufficient samples')
    previous = -1.0
    errors = []
    for t, voltage in rows:
        if not math.isfinite(t) or not math.isfinite(voltage) or t < 0 or t <= previous:
            raise ValueError('Invalid or non-monotonic simulation data')
        previous = t
        errors.append(abs(voltage - 5 * (1 - math.exp(-t / .001))))
    if rows[0][0] > .00001 or rows[-1][0] < .005 - 1e-9:
        raise ValueError('Capture must cover startup through five time constants')
    at_tau = min(rows, key=lambda row: abs(row[0] - .001))
    if abs(at_tau[0] - .001) > .000011:
        raise ValueError('Missing sample near one time constant')
    if max(errors) > .020:
        raise ValueError(f'RC error exceeds 20 mV: {max(errors):.6g} V')
    return {'samples': len(rows), 'max_error_v': max(errors),
            'tau_s': .001, 'sample_near_tau': at_tau,
            'expected_at_tau_v': 5*(1-math.exp(-1)), 'status': 'pass'}

def measurement_deck(exported: str) -> str:
    pattern = r'(?im)^\s*\.control\s*$[\s\S]*?^\s*\.endc\s*$'
    if len(re.findall(pattern, exported)) != 1:
        raise ValueError('Expected exactly one exported control block')
    commands = ".control\nset noaskquit\nset wr_singlescale\nset wr_vecnames\ntran 10u 5m uic\nwrdata rc.dat v(out)\nquit\n.endc"
    return re.sub(pattern, lambda _: commands, exported)


def run(netlist=None):
    executable = shutil.which('ngspice')
    if executable is None:
        raise RuntimeError('ngspice is required; no synthetic fallback is allowed')
    with tempfile.TemporaryDirectory(prefix='circuit regression ') as directory:
        path = Path(directory)
        if netlist is None:
            shutil.copyfile(ROOT/'examples/rc.cir', path/'rc.cir')
        else:
            (path/'rc.cir').write_text(measurement_deck(netlist.read_text()))
        result = subprocess.run([executable, '-b', 'rc.cir'], cwd=path,
                                capture_output=True, text=True, timeout=30, check=True)
        data = path/'rc.dat'
        if not data.is_file():
            raise RuntimeError('Solver produced no output: ' + result.stdout + result.stderr)
        rows = []
        for line in data.read_text().splitlines():
            parts = line.split()
            if not parts or parts[0].lower() == 'time':
                continue
            if len(parts) != 2:
                raise ValueError('Unexpected ngspice output columns')
            rows.append(tuple(map(float, parts)))
        report = validate(rows)
        report['solver_version'] = subprocess.run([executable, '--version'], capture_output=True,
                                                  text=True, timeout=10, check=True).stdout.strip()
        return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--netlist', type=Path, help='Measure actual exported RC devices with fixed zero-charge test conditions')
    args = parser.parse_args()
    try:
        report = run(args.netlist)
    except (ValueError, RuntimeError, subprocess.SubprocessError, OSError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')
    content = json.dumps(report, indent=2)
    print(content)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content+'\n')

if __name__ == '__main__':
    main()
