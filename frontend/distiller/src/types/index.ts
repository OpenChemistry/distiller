export type IdType = number;

export type User = {
  username: string;
};

export type ScanLocation = {
  id: IdType;
  host: string;
  path: string;
};

export enum JobType {
  Transfer = 'transfer',
  Count = 'count',
  Streaming = 'streaming',
}

export enum JobState {
  INITIALIZING = 'INITIALIZING',
  BOOT_FAIL = 'BOOT_FAIL',
  CANCELLED = 'CANCELLED',
  COMPLETED = 'COMPLETED',
  CONFIGURING = 'CONFIGURING',
  COMPLETING = 'COMPLETING',
  DEADLINE = 'DEADLINE',
  FAILED = 'FAILED',
  NODE_FAIL = 'NODE_FAIL',
  OUT_OF_MEMORY = 'OUT_OF_MEMORY',
  PENDING = 'PENDING',
  PREEMPTED = 'PREEMPTED',
  RUNNING = 'RUNNING',
  RESV_DEL_HOLD = 'RESV_DEL_HOLD',
  REQUEUE_FED = 'REQUEUE_FED',
  REQUEUE_HOLD = 'REQUEUE_HOLD',
  REQUEUED = 'REQUEUED',
  RESIZING = 'RESIZING',
  REVOKED = 'REVOKED',
  SIGNALING = 'SIGNALING',
  SPECIAL_EXIT = 'SPECIAL_EXIT',
  STAGE_OUT = 'STAGE_OUT',
  STOPPED = 'STOPPED',
  SUSPENDED = 'SUSPENDED',
  TIMEOUT = 'TIMEOUT',
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

export const CompleteJobStates = new Set<JobState>([JobState.COMPLETED]);

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

export type Job = {
  id: IdType;
  job_type: JobType;
  scan_ids: IdType[];
  slurm_id: IdType | null;
  elapsed: number | null;
  state: JobState | null;
  params: any;
  output?: string | null;
  machine?: string;
  submit?: string | null;
  notes?: string;
  prevJobId?: IdType;
  nextJobId?: IdType;
};

export type Metadata = { [name: string]: any };

export type Scan = {
  id: IdType;
  scan_id: IdType | null;
  progress: number;
  created: string;
  locations: ScanLocation[];
  notes?: string;
  image_path?: string;
  job_ids: IdType[];
  prevScanId?: IdType;
  nextScanId?: IdType;
  metadata?: Metadata;
  microscope_id: IdType;
};

export type ScansRequestResult = {
  scans: Scan[];
  // The unfiltered number of scans, needed for pagination
  totalCount: number;
};

export type JobsRequestResult = {
  jobs: Job[];
  // The unfiltered number of jobs
  totalCount: number;
};

export type Machine = {
  name: string;
  status: string;
  notes: string[];
  statusURL: string;
};

export type DarkfieldCorrection = {
  label: string;
  value: string;
};

export enum ExportFormat {
  JSON = 'json',
  CSV = 'csv',
  HTML = 'html',
}

export type Microscope = {
  id: number;
  name: string;
  config: { [name: string]: any };
  state?: { [name: string]: any };
};

export type Notebook = {
  name: string;
  path: string;
  scan_id: number;
};
