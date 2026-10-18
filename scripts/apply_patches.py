"""Apply reviewed local changes to the pinned upstream, without moving its revision."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PINNED = '46e47e8fabe852a9d6aab41d8a612ff5a78370c1'


def apply(source=ROOT/'upstream/qucs-s'):
    revision = subprocess.run(['git', '-C', str(source), 'rev-parse', 'HEAD'],
                              check=True, capture_output=True, text=True).stdout.strip()
    if revision != PINNED:
        raise RuntimeError('Upstream revision changed; review patches before building')
    for patch in sorted((ROOT/'patches').glob('*.patch')):
        command = ['git', '-C', str(source), 'apply']
        ready = subprocess.run(command + ['--check', str(patch)], capture_output=True, text=True)
        if ready.returncode == 0:
            subprocess.run(command + [str(patch)], check=True)
        else:
            already = subprocess.run(command + ['--reverse', '--check', str(patch)],
                                     capture_output=True, text=True)
            if already.returncode != 0:
                raise RuntimeError(f'Patch conflict: {patch.name}\n{ready.stderr}')
        print(f'Applied or already present: {patch.name}')


if __name__ == '__main__':
    apply()
