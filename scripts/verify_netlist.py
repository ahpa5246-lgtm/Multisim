"""Verify the pinned editor exports the RC fixture without changing topology or values."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def spice_value(token):
    match = re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)(meg|[kmunpf]?)', token.lower())
    if not match:
        raise ValueError(f'Unsupported fixture value: {token}')
    scales = {'': 1, 'meg': 1e6, 'k': 1e3, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15}
    return float(match[1]) * scales[match[2]]


def validate_rc_netlist(content):
    expected = {'r1': ({'in', 'out'}, 1000), 'c1': ({'out', '0'}, 1e-6), 'v1': ({'in', '0'}, 5)}
    found = {}
    for line in content.splitlines():
        tokens = line.lower().split()
        if not tokens or tokens[0] not in expected:
            continue
        name = tokens[0]
        if name in found or len(tokens) < 4:
            raise ValueError(f'Duplicate or incomplete component: {name}')
        nodes, value = expected[name]
        if set(tokens[1:3]) != nodes:
            raise ValueError(f'Incorrect connectivity for {name}: {tokens[1:3]}')
        if name == 'v1' and tokens[1:3] != ['in', '0']:
            raise ValueError('Source polarity changed')
        index = 4 if name == 'v1' and tokens[3] == 'dc' else 3
        if index >= len(tokens) or not math.isclose(spice_value(tokens[index]), value, rel_tol=1e-9):
            raise ValueError(f'Incorrect value for {name}')
        found[name] = True
    if set(found) != set(expected):
        raise ValueError(f'Missing fixture components: {set(expected)-set(found)}')
    return {'status': 'pass', 'components': len(found), 'scope': 'RC schematic export only; not simulation or NI parity'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--schematic', type=Path, default=ROOT/'examples/rc.sch')
    parser.add_argument('--output', type=Path, default=Path('reports/netlist'))
    args = parser.parse_args()
    try:
        args.output.mkdir(parents=True, exist_ok=True)
        netlist = args.output.resolve() / 'rc-export.cir'
        # A failed export must not accidentally validate stale output.
        netlist.unlink(missing_ok=True)
        result = subprocess.run([str(args.executable.resolve()), '--netlist', '--ngspice',
            '-i', str(args.schematic.resolve()), '-o', str(netlist)],
            capture_output=True, text=True, check=True, timeout=30)
        (args.output/'export.log').write_text(result.stdout + result.stderr)
        report = validate_rc_netlist(netlist.read_text())
        (args.output/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')


if __name__ == '__main__':
    main()
