import datetime
from pathlib import Path

import pytest

from faust_records import Location, Scan
from schemas import Machine


@pytest.fixture
def created():
    return datetime.datetime(2022, 1, 10, 14, 29, 59, 182918)


@pytest.fixture
def locations():
    return [
        Location(host="localhost", path="/mnt/nvmedata1"),
        Location(host="localhost", path="/mnt/nvmedata4"),
        Location(host="localhost", path="/mnt/nvmedata5"),
    ]


@pytest.fixture
def scan(locations, created):
    return Scan(id=0, scan_id=1, log_files=72, created=created, locations=locations)


@pytest.fixture
def job_params():
    return {"threshold": 4.0}


@pytest.fixture
def job(job_params, mocker):
    mocker.patch("job_worker.AsyncOAuth2Client", autospec=True)
    from job_worker import Job, JobType

    job = Job(id=0, job_type=JobType.COUNT, params=job_params, machine="cori")

    return job


@pytest.fixture
def cori_machine():
    return {
        "name": "cori",
        "account": "m3795",
        "qos": "realtime",
        "nodes": 20,
        "ntasks": 20,
        "constraint": "haswell",
        "cpus_per_task": 64,
        "bbcp_dest_dir": "${DW_JOB_STRIPED}",
        "balance_bridge": "ncem",
    }


@pytest.fixture
def perlmutter_machine():
    return {
        "name": "perlmutter",
        "account": "staff",
        "qos": "science",
        "nodes": 8,
        "constraint": "gpu",
        "cpus_per_task": 128,
        "ntasks_per_node": 1,
        "ntasks": 16,
        "bbcp_dest_dir": "$PSCRATCH/ncem",
    }


@pytest.fixture
def perlmutter_reservation_machine():
    params = {
        "name": "perlmutter",
        "account": "staff",
        "qos": "science",
        "nodes": 8,
        "constraint": "gpu",
        "cpus_per_task": 128,
        "ntasks_per_node": 1,
        "ntasks": 16,
        "bbcp_dest_dir": "$PSCRATCH/ncem",
        "reservation": "test",
    }

    return Machine(**params)


@pytest.fixture
def expected_cori_submission_script():
    excepted_cori_submission_script_path = (
        Path(__file__).parent / "fixtures" / "cori_submission_script"
    )
    with excepted_cori_submission_script_path.open() as fp:
        expected_cori_submission_script = fp.read()

    return expected_cori_submission_script


@pytest.fixture
def expected_perlmutter_submission_script():
    excepted_perlmutter_submission_script_path = (
        Path(__file__).parent / "fixtures" / "perlmutter_submission_script"
    )
    with excepted_perlmutter_submission_script_path.open() as fp:
        expected_perlmutter_submission_script = fp.read()

    return expected_perlmutter_submission_script


@pytest.fixture
def expected_perlmutter_reservation_submission_script():
    excepted_perlmutter_submission_script_path = (
        Path(__file__).parent / "fixtures" / "perlmutter_reservation_submission_script"
    )
    with excepted_perlmutter_submission_script_path.open() as fp:
        expected_perlmutter_submission_script = fp.read()

    return expected_perlmutter_submission_script


@pytest.fixture
def overrides_path():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def machine_names():
    return ["cori", "perlmutter"]


@pytest.fixture
def expected_perlmutter_overridden():
    params = {
        "name": "perlmutter",
        "account": "newaccount",
        "qos": "science",
        "nodes": 8,
        "constraint": "gpu",
        "cpus_per_task": 128,
        "ntasks_per_node": 1,
        "ntasks": 16,
        "bbcp_dest_dir": "$PSCRATCH/ncem",
        "reservation": "test2",
    }

    return Machine(**params)
