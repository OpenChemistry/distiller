import { IdType } from '../../types';
import { ScanCreatedEvent, ScanUpdatedEvent, ScanEventType } from './events';

function makeCreatedEvent(id: IdType): ScanCreatedEvent {
  return {
    event_type: ScanEventType.Created,
    id,
    scan_id: id,
    created: (new Date()).toISOString(),
    log_files: 0,
  }
}

function makeUpdatedEvent(id: IdType, log_files: number): ScanUpdatedEvent {
  return {
    event_type: ScanEventType.Updated,
    id,
    log_files,
  }
}

function sleep(t: number) {
  return new Promise((resolve) => {
    setTimeout(resolve, t);
  })
}

async function mockScanUpdates(ws: WebSocket, id: IdType) {
  {
    await sleep(0);
    const ev: any = new Event('message');
    ev.data = makeCreatedEvent(id);
    ws.dispatchEvent(ev);
  }

  for (let log_files of [10, 20, 30, 40, 50, 60, 72]) {
    await sleep(500);
    const ev: any = new Event('message');
    ev.data = makeUpdatedEvent(id, log_files);
    ws.dispatchEvent(ev);
  }
}

export async function startMockNotifications(ws: WebSocket) {
  const scans = [
    {id: '20', wait: 1000},
    {id: '30', wait: 3000},
    {id: '40', wait: 5000},
  ];

  for (let {id, wait} of scans) {
    setTimeout(() => {
      mockScanUpdates(ws, id);
    }, wait);
  }
}
