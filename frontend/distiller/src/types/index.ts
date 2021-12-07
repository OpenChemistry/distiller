export type IdType = number;

export type User = {
  username: string;
}

export type ScanLocation = {
  id: IdType;
  host: string;
  path: string;
}

export enum JobType {
  Transfer = 'transfer',
  Count = 'count',
}

export enum JobState {
  INITIALIZING = "INITIALIZING",
  BOOT_FAIL = "BOOT_FAIL",
  CANCELLED = "CANCELLED",
  COMPLETED = "COMPLETED",
  CONFIGURING = "CONFIGURING",
  COMPLETING = "COMPLETING",
  DEADLINE = "DEADLINE",
  FAILED = "FAILED",
  NODE_FAIL = "NODE_FAIL",
  OUT_OF_MEMORY = "OUT_OF_MEMORY",
  PENDING = "PENDING",
  PREEMPTED = "PREEMPTED",
  RUNNING = "RUNNING",
  RESV_DEL_HOLD = "RESV_DEL_HOLD",
  REQUEUE_FED = "REQUEUE_FED",
  REQUEUE_HOLD = "REQUEUE_HOLD",
  REQUEUED = "REQUEUED",
  RESIZING = "RESIZING",
  REVOKED = "REVOKED",
  SIGNALING = "SIGNALING",
  SPECIAL_EXIT = "SPECIAL_EXIT",
  STAGE_OUT = "STAGE_OUT",
  STOPPED = "STOPPED",
  SUSPENDED = "SUSPENDED",
  TIMEOUT = "TIMEOUT",
}

export const PendingJobStates = new Set<JobState>([
  JobState.INITIALIZING,
  JobState.PENDING,
]);

export const RunningJobStates = new Set<JobState>([

  JobState.CONFIGURING,
  JobState.COMPLETING,
  JobState.RUNNING,
  JobState.RESV_DEL_HOLD,
  JobState.REQUEUE_FED,
  JobState.REQUEUE_HOLD,
  JobState.REQUEUED,
  JobState.RESIZING,
  JobState.STAGE_OUT,
  JobState.SUSPENDED,
]);

export const CompleteJobStates = new Set<JobState>([
  JobState.COMPLETED,
]);

export const FailedJobStates = new Set<JobState>([
  JobState.BOOT_FAIL,
  JobState.NODE_FAIL,
  JobState.FAILED,
  JobState.DEADLINE,
  JobState.OUT_OF_MEMORY,
  JobState.PREEMPTED,
  JobState.REVOKED,
  JobState.STOPPED,
  JobState.TIMEOUT,
  JobState.CANCELLED,
]);

export type ScanJob = {
  id: IdType;
  job_type: JobType;
  scan_id: IdType;
  slurm_id: IdType;
  elapsed: number;
  state: JobState;
  params: any;
  output?: string;
}

export type Scan = {
  id: IdType;
  scan_id: IdType;
  log_files: number;
  created: string;
  locations: ScanLocation[];
  notes?: string;
  haadf_path?: string;
  jobs: ScanJob[];
}

export type ScansRequestResult = {
  scans: Scan[];
  // The unfiltered number of scans, needed for pagination
  totalCount: number;
}