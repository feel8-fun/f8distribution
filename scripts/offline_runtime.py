"""Build the offline base runtime from release wheels and the release lock."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request


VERSION = '0.7.11'
DIGESTS = {
    'pixi-pack-x86_64-pc-windows-msvc.exe': '12dde5b363fb7c5fb6215e0747638b0486a0bd3f47ef653b23ce020bc1936263',
    'pixi-unpack-x86_64-pc-windows-msvc.exe': '4b27cae647100dae4a321954461fe5863d25aa3eb9a919fb302f20509090bc72',
    'pixi-pack-x86_64-unknown-linux-musl': '4f2e6b70433c846974b9bd1356456335028afbe23f1fdf856ffa022ed691fc22',
    'pixi-unpack-x86_64-unknown-linux-musl': '8191f586b734e634e2f1644e553dcb8e07718d0bafbfefb65c5e6e22b4d484b7',
}


def tool(name: str, cache: Path) -> Path:
    suffix = 'x86_64-pc-windows-msvc.exe' if os.name == 'nt' else 'x86_64-unknown-linux-musl'
    asset = f'{name}-{suffix}'
    destination = cache / VERSION / asset
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.is_file():
        temporary = destination.with_suffix('.download')
        urllib.request.urlretrieve(f'https://github.com/Quantco/pixi-pack/releases/download/v{VERSION}/{asset}', temporary)
        temporary.replace(destination)
    with destination.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != DIGESTS[asset]:
        raise ValueError(f'Checksum mismatch for {destination}; remove it and retry')
    destination.chmod(0o755)
    return destination


def bundle_base_runtime(root: Path, *, cache: Path) -> None:
    pack = tool('pixi-pack', cache / 'tools')
    unpack = tool('pixi-unpack', cache / 'tools')
    destination = root / 'offline'
    destination.mkdir()
    bootstrap_path = root / 'config/bootstrap.json'
    bootstrap = json.loads(bootstrap_path.read_text())
    environment = bootstrap['environment']
    platform_name = 'win-64' if os.name == 'nt' else 'linux-64'
    subprocess.run([str(pack), '-e', environment, '-p', platform_name,
                    '-o', str(destination / 'base-runtime.tar'), '--use-cache', str(cache / 'packages'),
                    str(root / 'pixi.toml')], check=True)
    shutil.copy2(unpack, destination / ('pixi-unpack.exe' if os.name == 'nt' else 'pixi-unpack'))
