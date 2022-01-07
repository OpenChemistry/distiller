import { IdType, JobState, JobType, Scan, ScanJob } from '../../types';
import { ScanCreatedEvent, ScanUpdatedEvent, ScanEventType } from './events';

function makeCreatedEvent(id: IdType): ScanCreatedEvent {
  return {
    event_type: ScanEventType.Created,
    id,
    scan_id: id,
    created: new Date().toISOString(),
    log_files: 0,
    locations: [
      {
        id: 0,
        host: 'edge',
        path: '/foo/bar',
      },
      {
        id: 1,
        host: 'edge',
        path: '/bar/baz',
      },
      {
        id: 2,
        host: 'picea',
        path: '/foo/bar',
      },
    ],
    jobs: [],
  };
}

function makeUpdatedEvent(
  id: IdType,
  updates: Partial<Scan>
): ScanUpdatedEvent {
  return {
    event_type: ScanEventType.Updated,
    id,
    ...updates,
  };
}

function sleep(t: number) {
  return new Promise((resolve) => {
    setTimeout(resolve, t);
  });
}

async function mockScanUpdates(ws: WebSocket, id: IdType) {
  {
    await sleep(0);
    const ev: any = new Event('message');
    ev.data = JSON.stringify(makeCreatedEvent(id));
    ws.dispatchEvent(ev);
  }

  for (let log_files of [10, 20, 30, 40, 50, 60, 72]) {
    await sleep(500);
    const ev: any = new Event('message');
    ev.data = JSON.stringify(makeUpdatedEvent(id, { log_files }));
    ws.dispatchEvent(ev);
  }

  const job: ScanJob = {
    id: 0,
    scan_id: id,
    job_type: JobType.Count,
    slurm_id: 123,
    elapsed: 213,
    state: JobState.PENDING,
    params: {},
  };

  for (let state of [
    JobState.PENDING,
    JobState.RUNNING,
    JobState.FAILED,
    JobState.COMPLETED,
  ]) {
    job.state = state;
    await sleep(2000);
    const ev: any = new Event('message');
    ev.data = JSON.stringify(makeUpdatedEvent(id, { jobs: [job] }));
    ws.dispatchEvent(ev);
  }
}

export async function startMockNotifications(ws: WebSocket) {
  const scans = [
    { id: -20, wait: 1000 },
    { id: -30, wait: 3000 },
    { id: -40, wait: 5000 },
  ];

  for (let { id, wait } of scans) {
    setTimeout(() => {
      mockScanUpdates(ws, id);
    }, wait);
  }
}
