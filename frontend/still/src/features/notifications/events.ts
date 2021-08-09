import { IdType } from '../../types';

export enum ScanEventType {
  Created = 'scan.created',
  Updated = 'scan.updated',
}

export interface ScanEvent<T extends ScanEventType> {
  id: IdType;
  log_files: number;
  event_type: T;
}

export interface ScanCreatedEvent extends ScanEvent<ScanEventType.Created> {
  scan_id: IdType;
  created: string;
}

export interface ScanUpdatedEvent extends ScanEvent<ScanEventType.Updated> {
}

export function isCreatedEvent(ev: any): ev is ScanCreatedEvent {
  return ev.event_type === ScanEventType.Created;
}

export function isUpdatedEvent(ev: any): ev is ScanUpdatedEvent {
  return ev.event_type === ScanEventType.Updated;
}
