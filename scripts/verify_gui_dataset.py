"""Validate only the DC-initialized RC GUI fixture's real Qucs dataset."""
import argparse
import json
import math
from pathlib import Path
import re


def validate(text):
    if not text.startswith('<Qucs Dataset '):
        raise ValueError('Missing Qucs dataset header')
    matches = re.findall(r'<indep time (\d+)>\s*(.*?)</indep>', text, re.S)
    if len(matches) != 1:
        raise ValueError('Expected one time vector')
    count, body = matches[0]
    times = [float(x) for x in body.split()]
    if len(times) != int(count) or len(times) < 100:
        raise ValueError('Incomplete time vector')
    if not all(math.isfinite(x) for x in times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Time must be finite and strictly increasing')
    if abs(times[0]) > 1e-12 or abs(times[-1] - .005) > 1e-12:
        raise ValueError('Expected full 0..5ms coverage')
    errors = {}
    for name in ('tran.v(in)', 'tran.v(out)'):
        vectors = re.findall(r'<dep ' + re.escape(name) + r' time>\s*(.*?)</dep>', text, re.S)
        if len(vectors) != 1:
            raise ValueError('Missing or duplicate voltage vector: ' + name)
        values = [float(x) for x in vectors[0].split()]
        if len(values) != len(times) or not all(math.isfinite(x) for x in values):
            raise ValueError('Incomplete or nonfinite voltage vector')
        errors[name] = max(abs(x - 5) for x in values)
        if errors[name] > 1e-6:
            raise ValueError('Expected DC-initialized 5V baseline: ' + name)
    return {'status': 'pass', 'samples': len(times), 'max_error_V': errors,
            'scope': 'DC-initialized RC only; no charging-transient or NI parity claim'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(args.dataset.read_text())
    except (OSError, ValueError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
