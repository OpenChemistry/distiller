import { IdType, JobState, JobType, Scan, Job } from '../../types';
import { ScanCreatedEvent, ScanUpdatedEvent, ScanEventType } from './events';

function makeCreatedEvent(id: IdType): ScanCreatedEvent {
  return {
    event_type: ScanEventType.Created,
    id,
    scan_id: id,
    created: new Date().toISOString(),
    progress: 0,
    microscope_id: 1,
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
    jobIds: [-20, -30, -40],
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

  for (let progress of [10, 20, 30, 40, 50, 70, 100]) {
    await sleep(500);
    const ev: any = new Event('message');
    ev.data = JSON.stringify(makeUpdatedEvent(id, { progress }));
    ws.dispatchEvent(ev);
  }

  const job: Job = {
    id: 0,
    scanIds: [],
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
    ev.data = JSON.stringify(makeUpdatedEvent(id, { jobIds: [id] }));
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
