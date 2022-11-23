import { IdType, Scan, ScanLocation, Microscope } from '../../types';

export enum ScanEventType {
  Created = 'scan.created',
  Updated = 'scan.updated',
}

export enum MicroscopeEventType {
  Updated = 'microscope.updated',
}

export interface ScanEvent<T extends ScanEventType> extends Partial<Scan> {
  id: IdType;
  event_type: T;
}

export interface ScanCreatedEvent extends ScanEvent<ScanEventType.Created> {
  scan_id: IdType;
  created: string;
  locations: ScanLocation[];
  log_files: number;
  microscope_id: IdType;
}

export interface ScanUpdatedEvent extends ScanEvent<ScanEventType.Updated> {}

export function isScanCreatedEvent(ev: any): ev is ScanCreatedEvent {
  return ev && ev.event_type === ScanEventType.Created;
}

export function isScanUpdatedEvent(ev: any): ev is ScanUpdatedEvent {
  return ev && ev.event_type === ScanEventType.Updated;
}

export interface MicroscopeUpdatedEvent extends Partial<Microscope> {}

export function isMicroscopeUpdatedEvent(ev: any): ev is MicroscopeUpdatedEvent {
  return ev && ev.event_type === MicroscopeEventType.Updated;
}

