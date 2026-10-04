"""Executed by the unpacked Python, never the checkout's interpreter."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
from importlib import metadata


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    prefix = Path(sys.prefix).resolve()
    assert prefix == root / 'env', prefix
    assert (root / "config/bootstrap.json").is_file()
    verify_platform_bootstrap(prefix)


def verify_platform_bootstrap(prefix: Path) -> None:
    from fastapi.testclient import TestClient
    from f8platform.api import access_token, create_app
    for name in ('f8platform', 'f8pysdk'):
        distribution = metadata.distribution(name)
        assert Path(distribution.locate_file('')).resolve().is_relative_to(prefix), name
        direct = json.loads(distribution.read_text('direct_url.json') or '{}')
        assert not direct.get('dir_info', {}).get('editable'), name
    installed = {distribution.metadata['Name'].lower().replace('_', '-') for distribution in metadata.distributions()}
    assert not {'f8studio-server', 'f8studio-core', 'f8media-gateway', 'aiortc'} & installed
    with tempfile.TemporaryDirectory() as temporary:
        data_dir = Path(temporary)
        with TestClient(create_app(data_dir)) as client:
            headers = {'Authorization': f'Bearer {access_token(data_dir)}'}
            assert client.get('/api/health', headers=headers).json()['service'] == 'f8platform'
            assert client.get('/api/applications', headers=headers).json() == []
    print('Offline bootstrap passed: independent platform API, no application wheels')


if __name__ == '__main__':
    main()
