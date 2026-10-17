"""Build the pinned desktop upstream. Python 3.10+, CMake, Qt6 required."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    source = ROOT / 'upstream' / 'qucs-s'
    if not (source / 'CMakeLists.txt').is_file():
        parser.error('Initialize source: git submodule update --init --recursive')
    commands = [
        ['cmake', '-S', str(source), '-B', str(ROOT / 'build'), '-DCMAKE_BUILD_TYPE=Release', f'-DCMAKE_INSTALL_PREFIX={ROOT / "install"}'],
        ['cmake', '--build', str(ROOT / 'build'), '--parallel', str(args.jobs)],
        ['cmake', '--install', str(ROOT / 'build')],
    ]
    for command in commands:
        subprocess.run(command, check=True)

if __name__ == '__main__':
    main()
