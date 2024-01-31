from pathlib import Path

import pytest

from faust_records import Location, Scan
from schemas import Machine


# Change to match how faust record comes in... as str
@pytest.fixture
def created():
    return "2022-01-10T14:29:59+00:00"


@pytest.fixture
def locations():
    return [
        Location(host="localhost", path="/mnt/nvmedata1"),
        Location(host="localhost", path="/mnt/nvmedata4"),
        Location(host="localhost", path="/mnt/nvmedata5"),
    ]


@pytest.fixture
def scan(locations, created):
    return Scan(id=0, scan_id=1, created=created, locations=locations)


@pytest.fixture
def job_params():
    return {"threshold": 4.0, "darkfield": "none"}


@pytest.fixture
def job(job_params, mocker):
    mocker.patch("job_worker.AsyncOAuth2Client", autospec=True)
    from job_worker import Job, JobType

    job = Job(id=0, job_type=JobType.COUNT, params=job_params, machine="cori")

    return job


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
    return ["perlmutter"]


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
