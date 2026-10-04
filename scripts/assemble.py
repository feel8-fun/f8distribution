"""Assemble the official combination of already published artifacts."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess

from artifacts import load_launcher_tools
from offline_runtime import bundle_base_runtime

ROOT = Path(__file__).resolve().parents[1]


def assemble(lock: Path, output: Path, cache: Path, *, offline: bool = True, archive: bool = True) -> Path:
    load_launcher_tools(lock, cache)
    from f8platform.release import assemble_release
    platform = 'windows-x86_64' if os.name == 'nt' else 'linux-x86_64'
    assemble_release(lock, output, cache=cache, platform=platform)
    subprocess.run(['pixi', 'lock', '--check', '--manifest-path', str(output / 'pixi.toml')], check=True)
    for name in ('f8studio.cmd', 'install_env.bat') if os.name == 'nt' else ('f8studio', 'install_env.sh'):
        destination = output / name
        shutil.copy2(ROOT / 'scripts/launchers' / name, destination)
        if os.name != 'nt':
            destination.chmod(0o755)
    if offline:
        bundle_base_runtime(output, cache=cache / 'offline')
    if archive:
        return Path(shutil.make_archive(str(output), 'zip' if os.name == 'nt' else 'gztar',
                                        root_dir=output.parent, base_dir=output.name))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release_lock', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--cache', type=Path, default=ROOT / 'build/cache')
    parser.add_argument('--no-offline', action='store_true', help='Skip bundling bootstrap interpreter')
    parser.add_argument('--no-archive', action='store_true')
    args = parser.parse_args()
    platform = 'windows-x86_64' if os.name == 'nt' else 'linux-x86_64'
    output = args.output or ROOT / f'build/dist/f8-{platform}'
    result = assemble(args.release_lock.resolve(), output.resolve(), args.cache.resolve(),
                      offline=not args.no_offline, archive=not args.no_archive)
    print(result)


if __name__ == '__main__':
    main()
