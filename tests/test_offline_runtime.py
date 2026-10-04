from pathlib import Path
from unittest.mock import patch
import json
import pytest
from offline_runtime import VERSION, tool, bundle_base_runtime
from verify_dist import verify_distribution


def test_corrupt_cached_tool_is_rejected(tmp_path: Path) -> None:
    asset = tmp_path / VERSION / "pixi-pack-x86_64-unknown-linux-musl"
    asset.parent.mkdir()
    asset.write_bytes(b"corrupted")
    with patch("offline_runtime.os.name", "posix"):
        with pytest.raises(ValueError, match="Checksum mismatch"):
            tool("pixi-pack", tmp_path)


def test_bundle_uses_declared_bootstrap_environment(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config/bootstrap.json").write_text(json.dumps({"environment": "launcher"}))
    binary = tmp_path / "tool"
    binary.write_bytes(b"binary")
    with patch("offline_runtime.tool", return_value=binary), patch("offline_runtime.subprocess.run") as run:
        bundle_base_runtime(tmp_path, cache=tmp_path / "cache")
    assert run.call_args.args[0][1:3] == ["-e", "launcher"]
    assert (tmp_path / "offline").is_dir()


def test_verifier_checks_second_launch_without_installing(tmp_path: Path) -> None:
    (tmp_path / ".runtime-location").write_text(str(tmp_path))
    with patch("verify_dist.subprocess.run") as run:
        verify_distribution(tmp_path)
    commands = [call.args[0] for call in run.call_args_list]
    assert len(commands) == 3
    assert commands[0] == commands[1]
    assert all("pixi" not in command and "install" not in command for command in commands)
    assert all("PYTHONPATH" not in call.kwargs["env"] for call in run.call_args_list)
