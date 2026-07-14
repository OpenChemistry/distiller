import json
from datetime import datetime

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


def test_submit_job_event_coerces_scan_created_to_datetime():
    event = SubmitJobEvent.loads(
        json.dumps(
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
    )

    assert isinstance(event.scan.created, datetime)
    assert event.scan.created.isoformat() == "2026-07-14T17:54:08+00:00"
