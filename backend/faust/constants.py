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

SLURM_RUNNING_STATES = [
    "INITIALIZING",  # This is not a slurm state. This is the default start state
    "CONFIGURING",
    "COMPLETING",
    "PENDING",
    "RUNNING",
    "RESV_DEL_HOLD",
    "REQUEUE_FED",
    "REQUEUE_HOLD",
    "REQUEUED",
    "RESIZING",
    "STAGE_OUT",
    "SUSPENDED",
]
