from pathlib import Path
import hashlib
import json
import zipfile

import pytest

from artifacts import launcher_archive, load_launcher_tools


def release(tmp_path: Path, *, corrupt: bool = False, platform: str = 'linux-x86_64') -> tuple[Path, Path]:
    artifact = tmp_path / 'bootstrap.zip'
    with zipfile.ZipFile(artifact, 'w') as package:
        package.writestr('config/artifact.json', json.dumps({
            'artifactId': 'platform-runtime', 'version': '1.0', 'kind': 'runtime', 'platform': platform,
        }))
        package.writestr('wheels/f8platform-1.0-py3-none-any.whl', b'launcher')
        package.writestr('wheels/f8pysdk-1.0-py3-none-any.whl', b'sdk')
    digest = 'a' * 64 if corrupt else hashlib.sha256(artifact.read_bytes()).hexdigest()
    lock = tmp_path / 'release.json'
    lock.write_text(json.dumps({
        'schemaVersion': 'f8platformRelease/1', 'platform': 'linux-x86_64',
        'baseRuntime': 'platform-runtime', 'artifacts': [{
            'artifactId': 'platform-runtime', 'version': '1.0', 'kind': 'runtime',
            'location': artifact.name, 'sha256': digest,
        }],
    }))
    return lock, artifact


def test_source_checksum_failure_leaves_no_cached_artifact(tmp_path: Path) -> None:
    lock, _ = release(tmp_path, corrupt=True)
    cache = tmp_path / 'cache'
    with pytest.raises(ValueError, match='checksum mismatch'):
        launcher_archive(lock, cache)
    assert not list(cache.iterdir())


def test_cached_artifact_is_reverified(tmp_path: Path) -> None:
    lock, _ = release(tmp_path)
    cached = launcher_archive(lock, tmp_path / 'cache')
    cached.write_bytes(b'changed')
    with pytest.raises(ValueError, match='Cached bootstrap checksum'):
        launcher_archive(lock, tmp_path / 'cache')


def test_bootstrap_platform_is_checked_before_wheel_loading(tmp_path: Path) -> None:
    lock, _ = release(tmp_path, platform='windows-x86_64')
    with pytest.raises(ValueError, match='identity/platform mismatch'):
        load_launcher_tools(lock, tmp_path / 'cache')
