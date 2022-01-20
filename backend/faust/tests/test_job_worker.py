import pytest

import job_worker


@pytest.mark.asyncio
async def test_cori_submission_script(
    mocker, scan, job, cori_machine, expected_cori_submission_script, machine_names
):

    dest_dir = "/tmp"

    cori_submission_script = await job_worker.render_job_script(
        scan, job, cori_machine, dest_dir, machine_names
    )

    assert cori_submission_script == expected_cori_submission_script


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

    print(perlmutter_submission_script)

    assert perlmutter_submission_script == expected_perlmutter_reservation_submission_script