"""Load release tooling from the hash-pinned launcher artifact, never source repos."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import zipfile

LIMIT = 2 * 1024 * 1024 * 1024


def launcher_archive(lock_path: Path, cache: Path) -> Path:
    lock = json.loads(lock_path.read_text())
    if lock['schemaVersion'] != 'f8platformRelease/1':
        raise ValueError('Expected f8platformRelease/1 release lock')
    entries = [entry for entry in lock['artifacts']
               if entry['kind'] == 'runtime' and entry['artifactId'] == lock['baseRuntime']]
    if len(entries) != 1:
        raise ValueError('Release must select exactly one bootstrap artifact')
    entry = entries[0]
    digest = entry['sha256']
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('Bootstrap requires SHA-256')
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / f'{digest}.zip'
    if not archive.exists():
        temporary = archive.with_suffix('.download')
        location = entry['location']
        url = urllib.parse.urlsplit(location)
        try:
            if url.scheme and not Path(location).is_absolute():
                if url.scheme != 'https' or not url.hostname or url.username or url.password:
                    raise ValueError('Bootstrap URL requires HTTPS without credentials')
                with urllib.request.urlopen(location, timeout=30) as source, temporary.open('wb') as target:
                    if urllib.parse.urlsplit(str(source.geturl())).scheme != 'https':
                        raise ValueError('Bootstrap download redirected away from HTTPS')
                    total = 0
                    while chunk := source.read(1024 * 1024):
                        total += len(chunk)
                        if total > LIMIT:
                            raise ValueError('Bootstrap artifact exceeds size limit')
                        target.write(chunk)
            else:
                source_path = (lock_path.parent / location).resolve()
                if source_path.stat().st_size > LIMIT:
                    raise ValueError('Bootstrap artifact exceeds size limit')
                with source_path.open('rb') as source, temporary.open('wb') as target:
                    while chunk := source.read(1024 * 1024):
                        target.write(chunk)
            with temporary.open('rb') as source:
                if hashlib.file_digest(source, 'sha256').hexdigest() != digest:
                    raise ValueError('Bootstrap checksum mismatch')
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    with archive.open('rb') as source:
        if hashlib.file_digest(source, 'sha256').hexdigest() != digest:
            raise ValueError('Cached bootstrap checksum mismatch')
    return archive


def load_launcher_tools(lock_path: Path, cache: Path) -> None:
    archive = launcher_archive(lock_path, cache)
    lock = json.loads(lock_path.read_text())
    bootstrap = next(entry for entry in lock['artifacts'] if entry['kind'] == 'runtime' and entry['artifactId'] == lock['baseRuntime'])
    tools = cache / 'tools' / bootstrap['sha256']
    tools.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as package:
        descriptor = json.loads(package.read('config/artifact.json'))
        if (descriptor['kind'], descriptor['artifactId'], descriptor['version'], descriptor['platform']) != (
                'runtime', bootstrap['artifactId'], bootstrap['version'], lock['platform']):
            raise ValueError('Bootstrap identity/platform mismatch')
        for distribution in ('f8pysdk', 'f8platform'):
            candidates = [info for info in package.infolist()
                          if Path(info.filename).name.startswith(distribution + '-') and info.filename.endswith('.whl')]
            if len(candidates) != 1 or candidates[0].file_size > 128 * 1024 * 1024:
                raise ValueError(f'Bootstrap must carry exactly one {distribution} tooling wheel')
            info = candidates[0]
            path = tools / Path(info.filename).name
            with package.open(info) as source, path.open('wb') as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
            # Hash-pinned pure Python wheels are used as zip imports. No pip,
            # compiler, application source checkout or dependency solver runs here.
            sys.path.insert(0, str(path))
