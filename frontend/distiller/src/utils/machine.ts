const STATUSES: { [key: string]: { canRun: boolean; color: any } } = {
  active: {
    canRun: true,
    color: 'success',
  },
  degraded: {
    canRun: true,
    color: 'warning',
  },
  down: {
    canRun: false,
    color: 'error',
  },
  unknown: {
    canRun: false,
    color: 'default',
  },
};

const OTHER_STATUS = {
  canRun: true,
  color: 'default',
};

export function canRunJobs(status: string) {
  const option = STATUSES[status] || OTHER_STATUS;
  return option.canRun;
}

export function statusColor(status: string) {
  const option = STATUSES[status] || OTHER_STATUS;
  return option.color;
}
