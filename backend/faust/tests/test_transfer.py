import asyncio
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from schemas import Location

from transfer_config import (
    TransferConfig,
    prepare_transfer_files,
    resolve_destination_path,
)


def test_linux_file_selection():
    files = prepare_transfer_files(
        [
            Location(host="acquisition", path="/mnt/arina/scan_master.h5"),
            Location(host="acquisition", path="/mnt/arina/chunks/scan_data_001.h5"),
        ]
    )
    assert files == [
        ("/mnt/arina/scan_master.h5", "scan_master.h5"),
        ("/mnt/arina/chunks/scan_data_001.h5", "chunks/scan_data_001.h5"),
    ]


@pytest.mark.parametrize(
    "config",
    [
        {"transport": "sftp"},
        {"transport": "bbcp"},
        {"host": "windows"},
        {"sftp_root_mapping": {}},
        {"source_host": " "},
        {"username": " "},
        {"destination_subdir": "../escape"},
    ],
)
def test_invalid_config(config):
    with pytest.raises(ValidationError):
        TransferConfig(**{"source_host": "source", **config})


def test_destination_layout():
    assert (
        resolve_destination_path(
            "/raw", "f200/arina", datetime(2026, 11, 11, tzinfo=timezone.utc), 123
        )
        == "/raw/f200/arina/2026.11.11/123"
    )


@pytest.mark.parametrize(
    "paths",
    [
        [],
        ["relative.h5"],
        ["/mnt/data/../escape.h5"],
        ["/mnt/data/master.h5", "/other/chunk.h5"],
        ["/mnt/data/master.h5", "/mnt/data/master.h5"],
        ["/mnt/bad\nname.h5"],
    ],
)
def test_invalid_source_paths(paths):
    with pytest.raises(ValueError):
        prepare_transfer_files([Location(host="source", path=p) for p in paths])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username,failure",
    [
        (None, None),
        ("arina_operator", None),
        (None, "missing"),
        (None, "symlink"),
    ],
)
async def test_rendered_bbcp_job(
    tmp_path, monkeypatch, perlmutter_machine, username, failure
):
    """Execute the Slurm script with a local bbcp substitute to check copy arguments and failures."""
    import job_worker
    from schemas import Machine

    remote = tmp_path / "samba mount"
    names = ["scan_master.h5", "chunks/data [1] $literal.h5"]
    for name in names:
        source = remote / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(name.encode())
    destination = tmp_path / "raw destination"
    outside = tmp_path / "outside"
    outside.mkdir()
    if failure == "missing":
        (remote / names[1]).unlink()
    # This substitute implements only the argument contract under test.
    bbcp = tmp_path / "bbcp"
    bbcp.write_text("""#!/usr/bin/env python3
import shutil, sys
source, destination = sys.argv[-2:]
assert sys.argv[1:5] == ["-z", "-f", "-V", "-s"]
assert sys.argv[6:8] == ["-Z", "50000:51000"]
assert source.startswith("EXPECTED_USERNAME@acquisition:")
shutil.copyfile(source.split(":", 1)[1], destination)
""".replace("EXPECTED_USERNAME", username or "operator"))
    bbcp.chmod(0o755)
    monkeypatch.setattr(job_worker.settings, "JOB_BBCP_EXECUTABLE_PATH", str(bbcp))
    monkeypatch.setattr(job_worker.settings, "ACQUISITION_USER", "operator")
    monkeypatch.setattr(job_worker.settings, "JOB_SCRIPT_DIRECTORY", str(tmp_path))
    files = prepare_transfer_files(
        [Location(host="acquisition", path=str(remote / n)) for n in names]
    )
    if failure == "symlink":
        destination.mkdir()
        (destination / "chunks").symlink_to(outside)
    script = tmp_path / "transfer.sh"
    script.write_text(
        await job_worker.render_file_transfer_script(
            job_worker.Job(
                id=42,
                job_type=job_worker.JobType.TRANSFER,
                params={},
                machine="perlmutter",
            ),
            Machine(**perlmutter_machine),
            str(destination),
            "acquisition",
            files,
            username,
        )
    )
    proc = await asyncio.create_subprocess_exec(
        "bash",
        str(script),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
    if failure:
        assert proc.returncode != 0
        assert not list(outside.iterdir())
    else:
        assert proc.returncode == 0, stderr.decode()
        for name in names:
            assert (destination / name).read_bytes() == (remote / name).read_bytes()


@pytest.mark.parametrize("config", [{}, {"username": "arina"}])
def test_source_host_required(config):
    with pytest.raises(ValidationError, match="source_host"):
        TransferConfig(**config)
