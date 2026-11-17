import inspect
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

import job_worker
from faust_records import SubmitJobEvent


@pytest.mark.asyncio
async def test_perlmutter_submission_script(
    mocker,
    scan,
    job,
    perlmutter_machine,
    expected_perlmutter_submission_script,
    machine_names,
):
    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    dest_dir = "/tmp"

    perlmutter_submission_script = await job_worker.render_job_script(
        scan, job, perlmutter_machine, dest_dir, machine_names
    )

    assert perlmutter_submission_script == expected_perlmutter_submission_script


@pytest.mark.asyncio
async def test_perlmutter_reservation_submission_script(
    mocker,
    scan,
    job,
    perlmutter_reservation_machine,
    expected_perlmutter_reservation_submission_script,
    machine_names,
):
    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    dest_dir = "/tmp"

    perlmutter_submission_script = await job_worker.render_job_script(
        scan, job, perlmutter_reservation_machine, dest_dir, machine_names
    )

    assert (
        perlmutter_submission_script
        == expected_perlmutter_reservation_submission_script
    )


@pytest.mark.asyncio
async def test_machine_overrides(
    mocker,
    scan,
    job,
    perlmutter_reservation_machine,
    overrides_path,
    machine_names,
    expected_perlmutter_overridden,
):
    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    machines = {"perlmutter": perlmutter_reservation_machine}
    mocker.patch.object(job_worker, "get_machines", return_value=machines)
    mocker.patch.object(
        job_worker.settings, "JOB_MACHINE_OVERRIDES_PATH", overrides_path
    )

    perlmutter = await job_worker.get_machine(None, "perlmutter")

    assert perlmutter == expected_perlmutter_overridden


@pytest.mark.asyncio
async def test_render_file_transfer_script(mocker, perlmutter_machine):
    from job_worker import Job, JobType, render_file_transfer_script
    from schemas import Machine

    m_obj = Machine(**perlmutter_machine)
    job = Job(id=42, job_type=JobType.TRANSFER, params={}, machine="perlmutter")

    script = await render_file_transfer_script(
        job, m_obj, "/dest", "arina-linux", [("/mnt/data/file.h5", "file.h5")]
    )
    assert "#SBATCH --job-name=distiller-transfer-files-42" in script
    assert "#SBATCH --nodes=1" in script
    assert "#SBATCH --ntasks=1" in script
    assert "#SBATCH --cpus-per-task=1" in script
    assert "#SBATCH --time=02:00:00" in script
    assert f"#SBATCH --qos={m_obj.qos}" in script
    assert "@arina-linux:/mnt/data/file.h5" in script
    assert "-z -f -V -s" in script


@pytest.mark.asyncio
@pytest.mark.parametrize("override_filter", ["science", "shared"])
async def test_file_transfer_machine_override_qos_filter_validation(
    mocker, tmp_path, perlmutter_machine, override_filter
):
    """Only the actual monitoring filter controls acceptance, not a submission override."""
    from faust_records import Scan as FaustScan
    from job_worker import (
        Job,
        JobState,
        JobType,
        SubmitJobEvent,
        process_submit_job_event,
    )
    from schemas import Location as RestLocation, Machine, Microscope, Scan as RestScan

    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    job_scripts_dir = tmp_path / "job_scripts"
    job_scripts_dir.mkdir()
    overrides_dir = tmp_path / "overrides"
    overrides_dir.mkdir()
    (overrides_dir / "perlmutter").write_text(
        f"qos=shared\nqos_filter={override_filter}\n"
    )

    mocker.patch.object(job_worker.settings, "JOB_SCRIPT_DIRECTORY", str(job_scripts_dir))
    mocker.patch.object(job_worker.settings, "JOB_NCEMHUB_RAW_DATA_PATH", str(tmp_path / "raw"))
    mocker.patch.object(job_worker.settings, "JOB_MACHINE_OVERRIDES_PATH", str(overrides_dir))

    created_dt = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
    rest_scan = RestScan(
        id=77,
        scan_id=1,
        progress=100,
        locations=[RestLocation(host="arina-linux", path='/mnt/data/yag_009_master.h5')],
        created=created_dt,
        microscope_id=5,
    )
    mocker.patch.object(job_worker, "get_scan", AsyncMock(return_value=rest_scan))

    microscope = Microscope(
        id=5,
        name="F200",
        config={
            "transfer": {
                "source_host": "arina-linux",
            }
        },
    )
    mocker.patch.object(job_worker, "get_microscope_by_id", AsyncMock(return_value=microscope))
    mock_submit_job = mocker.patch.object(job_worker, "submit_job", AsyncMock(return_value=987654))
    mock_update_job = mocker.patch.object(job_worker, "update_job", AsyncMock())
    mocker.patch.object(job_worker, "update_slurm_job_id", AsyncMock())

    # 1. Filtered monitor (qos_filter="science") rejects override qos=shared
    filtered_machine = Machine(**{**perlmutter_machine, "qos_filter": "science"})
    mocker.patch.object(
        job_worker,
        "get_machines",
        AsyncMock(return_value={"perlmutter": filtered_machine}),
    )

    job1 = Job(id=201, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[77])
    faust_scan = FaustScan(id=77, scan_id=1, created=created_dt, locations=[])
    session = AsyncMock()
    await process_submit_job_event(session, SubmitJobEvent(job=job1, scan=faust_scan))

    mock_submit_job.assert_not_awaited()
    mock_update_job.assert_awaited_once()
    assert mock_update_job.await_args.kwargs["state"] == JobState.FAILED
    assert "outside monitoring qos_filter" in mock_update_job.await_args.kwargs["output"]

    # 2. Unfiltered monitor (qos_filter=None) accepts override qos=shared
    mock_submit_job.reset_mock()
    mock_update_job.reset_mock()
    unfiltered_machine = Machine(**{**perlmutter_machine, "qos_filter": None})
    mocker.patch.object(
        job_worker,
        "get_machines",
        AsyncMock(return_value={"perlmutter": unfiltered_machine}),
    )

    job2 = Job(id=202, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[77])
    await process_submit_job_event(session, SubmitJobEvent(job=job2, scan=faust_scan))

    mock_submit_job.assert_awaited_once()
    mock_update_job.assert_not_awaited()
    script_text = (job_scripts_dir / "202" / "transfer-202.sh").read_text()
    assert "#SBATCH --qos=shared" in script_text


@pytest.mark.asyncio
async def test_process_submit_job_event_file_transfer(mocker, tmp_path, perlmutter_machine):
    from faust_records import Location as FaustLocation, Scan as FaustScan
    from job_worker import (
        Job,
        JobType,
        SubmitJobEvent,
        process_submit_job_event,
    )
    from schemas import Location as RestLocation, Machine, Microscope, Scan as RestScan

    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    job_scripts_dir = tmp_path / "job_scripts"
    job_scripts_dir.mkdir()
    mocker.patch.object(job_worker.settings, "JOB_SCRIPT_DIRECTORY", str(job_scripts_dir))
    mocker.patch.object(job_worker.settings, "JOB_NCEMHUB_RAW_DATA_PATH", str(tmp_path / "raw"))

    m_obj = Machine(**perlmutter_machine)
    mocker.patch.object(job_worker, "get_machine", AsyncMock(return_value=m_obj))
    mocker.patch.object(job_worker, "get_machines", AsyncMock(return_value={"perlmutter": m_obj}))

    created_dt = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
    rest_scan = RestScan(
        id=77,
        scan_id=1,
        progress=100,
        locations=[
            RestLocation(host="arina-linux", path='/mnt/data/yag_009_master.h5'),
            RestLocation(host="perlmutter", path="/already/staged/data"),
        ],
        created=created_dt,
        microscope_id=5,
    )
    mocker.patch.object(job_worker, "get_scan", AsyncMock(return_value=rest_scan))

    microscope = Microscope(
        id=5,
        name="F200",
        config={
            "transfer": {
                "source_host": "arina-linux",
                "destination_subdir": "f200/arina",
            }
        },
    )
    mocker.patch.object(job_worker, "get_microscope_by_id", AsyncMock(return_value=microscope))
    mocker.patch.object(job_worker, "submit_job", AsyncMock(return_value=987654))
    mocker.patch.object(job_worker, "update_slurm_job_id", AsyncMock())

    job = Job(id=10, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[77])
    faust_scan = FaustScan(id=77, scan_id=1, created=created_dt, locations=[])
    event = SubmitJobEvent(job=job, scan=faust_scan)

    session = AsyncMock()
    await process_submit_job_event(session, event)

    metadata = json.loads((job_scripts_dir / "10" / "transfer.json").read_text())
    assert metadata == {
        "job_id": 10, "scan_id": 77,
        "destination": f"{tmp_path / 'raw'}/f200/arina/2026.10.07/77",
    }

    script = (job_scripts_dir / "10" / "transfer-10.sh").read_text()
    assert "@arina-linux:/mnt/data/yag_009_master.h5" in script

    # Verify submit_job and update_slurm_job_id
    job_worker.submit_job.assert_awaited_once()
    job_worker.update_slurm_job_id.assert_awaited_once_with(session, 10, 987654)


@pytest.mark.asyncio
async def test_process_submit_job_event_filters_only_configured_source_host(mocker, tmp_path, perlmutter_machine):
    """A scan with Linux, backup, and NERSC locations selects only configured source_host."""
    from faust_records import Scan as FaustScan
    from job_worker import Job, JobType, SubmitJobEvent, process_submit_job_event
    from schemas import Location as RestLocation, Machine, Microscope, Scan as RestScan

    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    job_scripts_dir = tmp_path / "job_scripts"
    job_scripts_dir.mkdir()
    mocker.patch.object(job_worker.settings, "JOB_SCRIPT_DIRECTORY", str(job_scripts_dir))
    mocker.patch.object(job_worker.settings, "JOB_NCEMHUB_RAW_DATA_PATH", str(tmp_path / "raw"))

    m_obj = Machine(**perlmutter_machine)
    mocker.patch.object(job_worker, "get_machine", AsyncMock(return_value=m_obj))
    mocker.patch.object(job_worker, "get_machines", AsyncMock(return_value={"perlmutter": m_obj}))

    created_dt = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
    rest_scan = RestScan(
        id=78,
        scan_id=2,
        progress=100,
        locations=[
            RestLocation(host="arina-linux", path='/mnt/data/target_file.h5'),
            RestLocation(host="backup-server", path="E:\\backup\\backup_file.h5"),
            RestLocation(host="perlmutter", path="/global/cfs/existing_file.h5"),
        ],
        created=created_dt,
        microscope_id=5,
    )
    mocker.patch.object(job_worker, "get_scan", AsyncMock(return_value=rest_scan))

    microscope = Microscope(
        id=5,
        name="F200",
        config={
            "transfer": {
                "source_host": "arina-linux",
            }
        },
    )
    mocker.patch.object(job_worker, "get_microscope_by_id", AsyncMock(return_value=microscope))
    mocker.patch.object(job_worker, "submit_job", AsyncMock(return_value=12345))
    mocker.patch.object(job_worker, "update_slurm_job_id", AsyncMock())

    job = Job(id=11, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[78])
    faust_scan = FaustScan(id=78, scan_id=2, created=created_dt, locations=[])
    event = SubmitJobEvent(job=job, scan=faust_scan)

    session = AsyncMock()
    await process_submit_job_event(session, event)

    script = (job_scripts_dir / "11" / "transfer-11.sh").read_text()
    assert "@arina-linux:/mnt/data/target_file.h5" in script
    assert "backup-server" not in script
    assert "/already/staged" not in script


@pytest.mark.asyncio
async def test_process_submit_job_event_file_transfer_failure_records_failed_state(mocker, tmp_path, perlmutter_machine):
    """Submit invalid File transfer config followed by valid job. First marks FAILED, second succeeds."""
    from faust_records import Scan as FaustScan
    from job_worker import Job, JobState, JobType, SubmitJobEvent, process_submit_job_event
    from schemas import Location as RestLocation, Machine, Microscope, Scan as RestScan

    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    job_scripts_dir = tmp_path / "job_scripts"
    job_scripts_dir.mkdir()
    mocker.patch.object(job_worker.settings, "JOB_SCRIPT_DIRECTORY", str(job_scripts_dir))
    mocker.patch.object(job_worker.settings, "JOB_NCEMHUB_RAW_DATA_PATH", str(tmp_path / "raw"))

    m_obj = Machine(**perlmutter_machine)
    mocker.patch.object(job_worker, "get_machine", AsyncMock(return_value=m_obj))
    mocker.patch.object(job_worker, "get_machines", AsyncMock(return_value={"perlmutter": m_obj}))

    mock_update_job = mocker.patch.object(job_worker, "update_job", AsyncMock())
    mock_submit_job = mocker.patch.object(job_worker, "submit_job", AsyncMock(return_value=99999))
    mock_update_slurm_id = mocker.patch.object(job_worker, "update_slurm_job_id", AsyncMock())

    # Job 1: Invalid File transfer config (blank source_host)
    created_dt = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
    scan_1 = RestScan(
        id=101,
        scan_id=1,
        progress=100,
        locations=[RestLocation(host="arina-linux", path='/mnt/data/scan1.h5')],
        created=created_dt,
        microscope_id=5,
    )
    mocker.patch.object(job_worker, "get_scan", AsyncMock(return_value=scan_1))

    # Invalid microscope config: blank source_host
    invalid_scope = Microscope(
        id=5, name="F200", config={"transfer": {"source_host": ""}}
    )
    mocker.patch.object(job_worker, "get_microscope_by_id", AsyncMock(return_value=invalid_scope))

    job1 = Job(id=501, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[101])
    faust_scan1 = FaustScan(id=101, scan_id=1, created=created_dt, locations=[])
    event1 = SubmitJobEvent(job=job1, scan=faust_scan1)

    session = AsyncMock()
    # Processing job 1 must not crash consumer and must record FAILED
    await process_submit_job_event(session, event1)

    mock_update_job.assert_awaited_once()
    kwargs = mock_update_job.await_args.kwargs
    assert kwargs["job_id"] == 501
    assert kwargs["state"] == JobState.FAILED
    assert "source_host must not be blank" in kwargs["output"]

    # Job 2: Valid File transfer config immediately processed subsequently
    valid_scope = Microscope(
        id=5,
        name="F200",
        config={
            "transfer": {
                "source_host": "arina-linux",
            }
        },
    )
    mocker.patch.object(job_worker, "get_microscope_by_id", AsyncMock(return_value=valid_scope))

    job2 = Job(id=502, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[101])
    event2 = SubmitJobEvent(job=job2, scan=faust_scan1)

    await process_submit_job_event(session, event2)

    mock_submit_job.assert_awaited_once()
    mock_update_slurm_id.assert_awaited_once_with(session, 502, 99999)


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["COMPLETED", "FAILED", "TIMEOUT", "CANCELLED"])
async def test_monitor_file_transfer_state(mocker, tmp_path, perlmutter_machine, state):
    from job_worker import JobState, completed_jobs
    from schemas import Job as SchemasJob, Machine, Scan as SchemasScan

    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    job_workdir = tmp_path / "123"
    job_workdir.mkdir()
    manifest_path = job_workdir / "transfer.json"
    with open(manifest_path, "w") as fp:
        json.dump(
            {
                "job_id": 123,
                "scan_id": 777,
                "destination": '/global/cfs/f200/arina/2026.10.07/777',
            },
            fp,
        )


    m_obj = Machine(**perlmutter_machine)
    mocker.patch.object(job_worker, "get_machines", AsyncMock(return_value={"perlmutter": m_obj}))

    status_resp = mocker.patch("httpx.Response")
    status_resp.status_code = 200
    status_resp.json.return_value = {"status": "ok"}

    jobs_resp = mocker.patch("httpx.Response")
    jobs_resp.status_code = 200
    jobs_resp.json.return_value = {
        "status": "ok",
        "output": [
            {
                "workdir": str(job_workdir),
                "state": state,
                "jobname": "distiller-transfer-files-123",
                "jobid": "55555",
                "elapsed": "00:01:00",
                "submit": "2026-10-07T12:00:00",
            }
        ],
    }

    async def fake_sfapi_get(url, params=None):
        if "status" in url:
            return status_resp
        return jobs_resp

    mocker.patch.object(job_worker, "sfapi_get", side_effect=fake_sfapi_get)
    mocker.patch.object(job_worker, "update_job", AsyncMock())
    mocker.patch.object(job_worker, "read_slurm_out", AsyncMock(return_value="done"))

    job_model = SchemasJob(
        id=123,
        job_type="transfer",
        scan_ids=[777],
        state="COMPLETED",
        machine="perlmutter",
    )
    mocker.patch.object(job_worker, "get_job", AsyncMock(return_value=job_model))

    scan_model = SchemasScan(
        id=777,
        scan_id=1,
        progress=100,
        locations=[],
        created=datetime.now(timezone.utc),
        microscope_id=1,
    )
    mocker.patch.object(job_worker, "get_scan", AsyncMock(return_value=scan_model))
    mock_update_scan = mocker.patch.object(job_worker, "update_scan", AsyncMock())

    completed_jobs.clear()
    await inspect.unwrap(job_worker.monitor_jobs)()

    if state == "COMPLETED":
        mock_update_scan.assert_awaited_once()
        update_arg = mock_update_scan.await_args[0][1]
        assert update_arg.id == 777
        assert update_arg.locations[0].path == "/global/cfs/f200/arina/2026.10.07/777"
        assert update_arg.locations[0].host == "perlmutter"
    else:
        mock_update_scan.assert_not_awaited()
    assert 123 in completed_jobs


@pytest.mark.asyncio
async def test_monitor_jobs_retries_when_update_scan_fails(mocker, tmp_path, perlmutter_machine):
    from job_worker import completed_jobs
    from schemas import Job as SchemasJob, Machine, Scan as SchemasScan

    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    job_workdir = tmp_path / "124"
    job_workdir.mkdir()
    manifest_path = job_workdir / "transfer.json"
    with open(manifest_path, "w") as fp:
        json.dump(
            {
                "job_id": 124,
                "scan_id": 778,
                "destination": '/global/cfs/f200/arina/2026.10.07/778',
            },
            fp,
        )


    m_obj = Machine(**perlmutter_machine)
    mocker.patch.object(job_worker, "get_machines", AsyncMock(return_value={"perlmutter": m_obj}))

    status_resp = mocker.patch("httpx.Response")
    status_resp.status_code = 200
    status_resp.json.return_value = {"status": "ok"}

    jobs_resp = mocker.patch("httpx.Response")
    jobs_resp.status_code = 200
    jobs_resp.json.return_value = {
        "status": "ok",
        "output": [
            {
                "workdir": str(job_workdir),
                "state": "COMPLETED",
                "jobname": "distiller-transfer-files-124",
                "jobid": "55556",
                "elapsed": "00:01:00",
                "submit": "2026-10-07T12:00:00",
            }
        ],
    }

    async def fake_sfapi_get(url, params=None):
        if "status" in url:
            return status_resp
        return jobs_resp

    mocker.patch.object(job_worker, "sfapi_get", side_effect=fake_sfapi_get)
    mocker.patch.object(job_worker, "update_job", AsyncMock())
    mocker.patch.object(job_worker, "read_slurm_out", AsyncMock(return_value="done"))

    job_model = SchemasJob(
        id=124,
        job_type="transfer",
        scan_ids=[778],
        state="COMPLETED",
        machine="perlmutter",
    )
    mocker.patch.object(job_worker, "get_job", AsyncMock(return_value=job_model))

    scan_model = SchemasScan(
        id=778,
        scan_id=2,
        progress=100,
        locations=[],
        created=datetime.now(timezone.utc),
        microscope_id=1,
    )
    mocker.patch.object(job_worker, "get_scan", AsyncMock(return_value=scan_model))
    # Simulate network error updating scan
    mocker.patch.object(job_worker, "update_scan", AsyncMock(side_effect=RuntimeError("API failure")))

    completed_jobs.clear()
    await inspect.unwrap(job_worker.monitor_jobs)()

    # Job must NOT be marked completed so that subsequent poll can retry!
    assert 124 not in completed_jobs


@pytest.mark.asyncio
async def test_process_submit_job_event_transfer_config_dispatch_and_validation(
    mocker, tmp_path, perlmutter_machine
):
    """Absent transfer config uses legacy bbcp. Supplied config requires a source host."""
    from faust_records import Location as FaustLocation, Scan as FaustScan
    from job_worker import Job, JobState, JobType, SubmitJobEvent, process_submit_job_event
    from schemas import Location as RestLocation, Machine, Microscope, Scan as RestScan

    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    job_scripts_dir = tmp_path / "job_scripts"
    job_scripts_dir.mkdir()
    mocker.patch.object(job_worker.settings, "JOB_SCRIPT_DIRECTORY", str(job_scripts_dir))
    mocker.patch.object(job_worker.settings, "JOB_NCEMHUB_RAW_DATA_PATH", str(tmp_path / "raw"))

    m_obj = Machine(**perlmutter_machine)
    mocker.patch.object(job_worker, "get_machine", AsyncMock(return_value=m_obj))
    mocker.patch.object(job_worker, "get_machines", AsyncMock(return_value={"perlmutter": m_obj}))

    mock_update_job = mocker.patch.object(job_worker, "update_job", AsyncMock())
    mock_submit_job = mocker.patch.object(job_worker, "submit_job", AsyncMock(return_value=77700))
    mock_update_slurm_id = mocker.patch.object(job_worker, "update_slurm_job_id", AsyncMock())

    created_dt = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
    rest_scan = RestScan(
        id=901,
        scan_id=1,
        progress=100,
        locations=[RestLocation(host="ncemhub", path="/data/scan_01.dm4")],
        created=created_dt,
        microscope_id=5,
    )
    mocker.patch.object(job_worker, "get_scan", AsyncMock(return_value=rest_scan))

    faust_scan = FaustScan(
        id=901,
        scan_id=1,
        created=created_dt,
        locations=[FaustLocation(host="ncemhub", path="/data/scan_01.dm4")],
    )
    session = AsyncMock()

    # 1. Absent configuration (config=None and config={}) -> dispatches to legacy bbcp
    for idx, cfg in enumerate([None, {}], start=1):
        mock_submit_job.reset_mock()
        mock_update_job.reset_mock()
        mock_update_slurm_id.reset_mock()

        mocker.patch.object(
            job_worker,
            "get_microscope_by_id",
            AsyncMock(return_value=Microscope(id=5, name="F200", config=cfg)),
        )
        job = Job(id=600 + idx, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[901])
        await process_submit_job_event(session, SubmitJobEvent(job=job, scan=faust_scan))

        mock_submit_job.assert_awaited_once()
        mock_update_slurm_id.assert_awaited_once_with(session, 600 + idx, 77700)
        mock_update_job.assert_not_awaited()
        assert (job_scripts_dir / str(600 + idx) / f"transfer-{600 + idx}.sh").exists()

    # Supplied transfer configurations must be valid and name a source host.
    malformed_cases = [
        (603, {"transfer": {}}),
        (609, {"transfer": {"username": "arina"}}),
        (604, {"transfer": {"host": "192.168.1.50", "username": "arina"}}),
        (605, {"transfer": {"transport": "rsync"}}),
        (606, {"transfer": "file_transfer"}),
        (607, {"transfer": ["file_transfer"]}),
        (608, {"transfer": 123}),
    ]
    for job_id, bad_cfg in malformed_cases:
        mock_submit_job.reset_mock()
        mock_update_job.reset_mock()
        mock_update_slurm_id.reset_mock()

        mocker.patch.object(
            job_worker,
            "get_microscope_by_id",
            AsyncMock(return_value=Microscope(id=5, name="F200", config=bad_cfg)),
        )
        bad_job = Job(id=job_id, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[901])
        await process_submit_job_event(session, SubmitJobEvent(job=bad_job, scan=faust_scan))

        mock_submit_job.assert_not_awaited()
        mock_update_slurm_id.assert_not_awaited()
        mock_update_job.assert_awaited_once()
        args, kwargs = mock_update_job.await_args
        assert kwargs.get("job_id") == job_id
        assert kwargs.get("state") == JobState.FAILED
        assert "File transfer submission error" in kwargs.get("output", "")


@pytest.mark.asyncio
async def test_monitor_missing_metadata(
    mocker, tmp_path, perlmutter_machine
):
    """Missing File transfer metadata fails registration. Legacy bbcp still uses its usual path."""
    from job_worker import JobState, completed_jobs
    from schemas import Job as SchemasJob, Machine, Scan as SchemasScan

    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)
    mocker.patch.object(job_worker.settings, "JOB_NCEMHUB_RAW_DATA_PATH", str(tmp_path / "raw"))

    # Neither workdir contains transfer metadata.
    files_workdir = tmp_path / "127"
    files_workdir.mkdir()
    bbcp_workdir = tmp_path / "128"
    bbcp_workdir.mkdir()

    m_obj = Machine(**perlmutter_machine)
    mocker.patch.object(job_worker, "get_machines", AsyncMock(return_value={"perlmutter": m_obj}))

    status_resp = mocker.patch("httpx.Response")
    status_resp.status_code = 200
    status_resp.json.return_value = {"status": "ok"}

    jobs_resp = mocker.patch("httpx.Response")
    jobs_resp.status_code = 200
    jobs_resp.json.return_value = {
        "status": "ok",
        "output": [
            {
                "workdir": str(files_workdir),
                "state": "COMPLETED",
                "jobname": "distiller-transfer-files-127",
                "jobid": "55559",
                "elapsed": "00:01:00",
                "submit": "2026-10-07T12:00:00",
            },
            {
                "workdir": str(bbcp_workdir),
                "state": "COMPLETED",
                "jobname": "distiller-transfer-128",
                "jobid": "55560",
                "elapsed": "00:01:00",
                "submit": "2026-10-07T12:00:00",
            },
        ],
    }

    async def fake_sfapi_get(url, params=None):
        if "status" in url:
            return status_resp
        return jobs_resp

    mocker.patch.object(job_worker, "sfapi_get", side_effect=fake_sfapi_get)
    mock_update_job = mocker.patch.object(job_worker, "update_job", AsyncMock())
    mocker.patch.object(job_worker, "read_slurm_out", AsyncMock(return_value="done"))

    jobs_by_id = {
        127: SchemasJob(id=127, job_type="transfer", scan_ids=[781], state="COMPLETED", machine="perlmutter"),
        128: SchemasJob(id=128, job_type="transfer", scan_ids=[782], state="COMPLETED", machine="perlmutter"),
    }
    mocker.patch.object(job_worker, "get_job", AsyncMock(side_effect=lambda s, jid: jobs_by_id[jid]))

    created_dt = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
    scans_by_id = {
        781: SchemasScan(id=781, scan_id=5, progress=100, locations=[], created=created_dt, microscope_id=1),
        782: SchemasScan(id=782, scan_id=6, progress=100, locations=[], created=created_dt, microscope_id=1),
    }
    mocker.patch.object(job_worker, "get_scan", AsyncMock(side_effect=lambda s, sid: scans_by_id[sid]))
    mock_update_scan = mocker.patch.object(job_worker, "update_scan", AsyncMock())

    completed_jobs.clear()
    await inspect.unwrap(job_worker.monitor_jobs)()

    # File transfer job 127 must be marked FAILED and its scan (781) must NOT be updated
    failed_calls = [
        call
        for call in mock_update_job.await_args_list
        if call.args[1] == 127 and call.kwargs.get("state") == JobState.FAILED
    ]
    assert len(failed_calls) == 1
    assert "missing transfer.json" in failed_calls[0].kwargs.get("output", "").lower()
    assert 127 in completed_jobs

    # Legacy bbcp job 128 must still register its scan (782) via _scan_path()
    mock_update_scan.assert_awaited_once()
    scan_call_args, scan_call_kwargs = mock_update_scan.await_args
    assert scan_call_args[1].id == 782
    assert 128 in completed_jobs


@pytest.mark.asyncio
async def test_process_submit_job_event_lookup_failures_mark_job_failed(
    mocker, tmp_path, perlmutter_machine
):
    """Failures in get_scan() or get_microscope_by_id() record JobState.FAILED instead of leaving job INITIALIZING."""
    from faust_records import Location as FaustLocation, Scan as FaustScan
    from job_worker import Job, JobState, JobType, SubmitJobEvent, process_submit_job_event
    from schemas import Location as RestLocation, Machine, Scan as RestScan

    mocker.patch("authlib.integrations.httpx_client.AsyncOAuth2Client", autospec=True)

    m_obj = Machine(**perlmutter_machine)
    mocker.patch.object(job_worker, "get_machine", AsyncMock(return_value=m_obj))
    mocker.patch.object(job_worker, "get_machines", AsyncMock(return_value={"perlmutter": m_obj}))

    mock_update_job = mocker.patch.object(job_worker, "update_job", AsyncMock())
    mock_submit_job = mocker.patch.object(job_worker, "submit_job", AsyncMock())

    created_dt = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
    faust_scan = FaustScan(
        id=920,
        scan_id=20,
        created=created_dt,
        locations=[FaustLocation(host="ncemhub", path="/data/scan_20.dm4")],
    )
    session = AsyncMock()

    # 1. get_scan() fails
    mocker.patch.object(
        job_worker,
        "get_scan",
        AsyncMock(side_effect=RuntimeError("Backend scan lookup failed")),
    )
    job_scan_fail = Job(id=801, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[920])
    await process_submit_job_event(session, SubmitJobEvent(job=job_scan_fail, scan=faust_scan))

    mock_submit_job.assert_not_awaited()
    mock_update_job.assert_awaited_once()
    kwargs = mock_update_job.await_args.kwargs
    assert kwargs["job_id"] == 801
    assert kwargs["state"] == JobState.FAILED
    assert "Backend scan lookup failed" in kwargs["output"]

    # 2. get_scan() succeeds, get_microscope_by_id() fails
    mock_update_job.reset_mock()
    rest_scan = RestScan(
        id=920,
        scan_id=20,
        progress=100,
        locations=[RestLocation(host="ncemhub", path="/data/scan_20.dm4")],
        created=created_dt,
        microscope_id=5,
    )
    mocker.patch.object(job_worker, "get_scan", AsyncMock(return_value=rest_scan))
    mocker.patch.object(
        job_worker,
        "get_microscope_by_id",
        AsyncMock(side_effect=RuntimeError("Microscope lookup failed")),
    )

    job_scope_fail = Job(id=802, job_type=JobType.TRANSFER, machine="perlmutter", params={}, scan_ids=[920])
    await process_submit_job_event(session, SubmitJobEvent(job=job_scope_fail, scan=faust_scan))

    mock_submit_job.assert_not_awaited()
    mock_update_job.assert_awaited_once()
    kwargs = mock_update_job.await_args.kwargs
    assert kwargs["job_id"] == 802
    assert kwargs["state"] == JobState.FAILED
    assert "Microscope lookup failed" in kwargs["output"]


@pytest.mark.asyncio
@pytest.mark.parametrize("metadata", [
    {"job_id": 999, "scan_id": 2, "destination": "/dest"},
    {"job_id": 1, "scan_id": 999, "destination": "/dest"},
    {"job_id": 1, "scan_id": 2, "destination": "relative"},
    [],
    "malformed JSON",
])
async def test_invalid_transfer_metadata(tmp_path, metadata):
    from aiopath import AsyncPath

    path = tmp_path / "transfer.json"
    path.write_text(metadata if isinstance(metadata, str) else json.dumps(metadata))
    with pytest.raises(ValueError):
        await job_worker._resolve_transfer_destination(1, 2, AsyncPath(path))


@pytest.mark.asyncio
@pytest.mark.parametrize("job_type", ["transfer", "count"])
async def test_legacy_completion_skips_metadata(mocker, tmp_path, job_type):
    from datetime import timedelta
    from schemas import Job as RestJob, Scan as RestScan, SfapiJob

    scan = RestScan(
        id=100, scan_id=1, progress=100, locations=[],
        created=datetime(2026, 11, 11, tzinfo=timezone.utc), microscope_id=5,
    )
    job = RestJob(id=10, job_type=job_type, scan_ids=[100], state="COMPLETED", machine="perlmutter")
    slurm_job = SfapiJob(
        slurm_id=123, name=f"distiller-{job_type}-10", workdir=str(tmp_path),
        state="COMPLETED", elapsed=timedelta(seconds=60), submit=scan.created,
    )
    mocker.patch.object(job_worker, "get_job", AsyncMock(return_value=job))
    mocker.patch.object(job_worker, "get_scan", AsyncMock(return_value=scan))
    exists = mocker.patch.object(job_worker.AsyncPath, "exists", AsyncMock(
        side_effect=AssertionError("Legacy completion must not look up transfer metadata")
    ))
    update = mocker.patch.object(job_worker, "update_scan", AsyncMock())

    job_worker.completed_jobs.clear()
    await job_worker._process_completed_job(AsyncMock(), 10, slurm_job)

    exists.assert_not_awaited()
    update.assert_awaited_once()
    assert update.await_args.args[1].locations[0].path == str(job_worker._scan_path(job_type, scan))
    assert 10 in job_worker.completed_jobs


def test_submit_job_event_coerces_scan_created_to_datetime():
    event = SubmitJobEvent.from_data(
        {
            "job": {
                "id": 1,
                "job_type": "count",
                "machine": "perlmutter",
                "params": {},
                "scan_ids": [1],
            },
            "scan": {
                "id": 1,
                "locations": [],
                "created": "2026-07-14T17:54:08Z",
                "scan_id": 1,
            },
            "event_type": "job.submit",
        }
    )

    assert isinstance(event.scan.created, datetime)
    assert event.scan.created.isoformat() == "2026-07-14T17:54:08+00:00"
