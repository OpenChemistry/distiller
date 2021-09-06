from enum import Enum

TOPIC_LOG_FILE_EVENTS = "log_file_events"
TOPIC_SCAN_EVENTS = "scan_events"
TOPIC_LOG_FILE_SYNC_EVENTS = "log_file_sync_events"
TOPIC_HAADF_FILE_EVENTS = "haadf_file_events"
TOPIC_JOB_SUBMIT_EVENTS = "job_events"

FILE_EVENT_TYPE_DELETED = "deleted"
FILE_EVENT_TYPE_CREATED = "created"
FILE_EVENT_TYPE_CLOSED = "closed"
FILE_EVENT_TYPE_MODIFIED = "modified"

PRIMARY_LOG_FILE_REGEX = r".*module0to1_dst0.*"

LOG_PREFIX = "log_scan"
SFAPI_TOKEN_URL = "https://oidc.nersc.gov/c2id/token"
SFAPI_BASE_URL = "https://api.nersc.gov/api/v1.2"

TRANSFER_JOB_SCRIPT_TEMPLATE = "transfer.sh.j2"
COUNT_JOB_SCRIPT_TEMPLATE = "count.sh.j2"
DW_JOB_STRIPED_VAR = "${DW_JOB_STRIPED}"

class JobState(str, Enum):
    INITIALIZING = (
        "INITIALIZING"  # This is not a slurm state. This is the default start state
    )
    BOOT_FAIL = "BOOT_FAIL"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    CONFIGURING = "CONFIGURING"
    COMPLETING = "COMPLETING"
    DEADLINE = "DEADLINE"
    FAILED = "FAILED"
    NODE_FAIL = "NODE_FAIL"
    OUT_OF_MEMORY = "OUT_OF_MEMORY"
    PENDING = "PENDING"
    PREEMPTED = "PREEMPTED"
    RUNNING = "RUNNING"
    RESV_DEL_HOLD = "RESV_DEL_HOLD"
    REQUEUE_FED = "REQUEUE_FED"
    REQUEUE_HOLD = "REQUEUE_HOLD"
    REQUEUED = "REQUEUED"
    RESIZING = "RESIZING"
    REVOKED = "REVOKED"
    SIGNALING = "SIGNALING"
    SPECIAL_EXIT = "SPECIAL_EXIT"
    STAGE_OUT = "STAGE_OUT"
    STOPPED = "STOPPED"
    SUSPENDED = "SUSPENDED"
    TIMEOUT = "TIMEOUT"

    def __str__(self) -> str:
        return self.name


SLURM_RUNNING_STATES = [
    JobState.INITIALIZING,
    JobState.CONFIGURING,
    JobState.COMPLETING,
    JobState.PENDING,
    JobState.RUNNING,
    JobState.RESV_DEL_HOLD,
    JobState.REQUEUE_FED,
    JobState.REQUEUE_HOLD,
    JobState.REQUEUED,
    JobState.RESIZING,
    JobState.STAGE_OUT,
    JobState.SUSPENDED,
]

class JobType(str, Enum):
    TRANSFER = "transfer"
    COUNT = "count"

    def __str__(self) -> str:
        return self.value
