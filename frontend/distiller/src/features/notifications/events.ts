import { IdType, Job, Microscope, Scan, ScanLocation } from '../../types';

export enum ScanEventType {
  Created = 'scan.created',
  Updated = 'scan.updated',
}

export enum JobEventType {
  Submit = 'job.submit',
  Updated = 'job.updated',
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
  progress: number;
  microscope_id: IdType;
}

export interface ScanUpdatedEvent extends ScanEvent<ScanEventType.Updated> {}

export function isScanCreatedEvent(ev: any): ev is ScanCreatedEvent {
  return ev && ev.event_type === ScanEventType.Created;
}

export function isScanUpdatedEvent(ev: any): ev is ScanUpdatedEvent {
  return ev && ev.event_type === ScanEventType.Updated;
}

export interface JobEvent<T extends JobEventType> extends Partial<Job> {
  id: IdType;
  event_type: T;
}

export interface JobSubmitEvent {
  job: Job;
  scan: Scan;
  event_type: JobEventType.Submit;
}

export interface JobUpdatedEvent extends JobEvent<JobEventType.Updated> {}

export function isJobSubmitEvent(ev: any): ev is JobSubmitEvent {
  return ev && ev.event_type === JobEventType.Submit;
}

export function isJobUpdatedEvent(ev: any): ev is JobUpdatedEvent {
  return ev && ev.event_type === JobEventType.Updated;
}

export interface MicroscopeUpdatedEvent extends Partial<Microscope> {}

export function isMicroscopeUpdatedEvent(
  ev: any,
): ev is MicroscopeUpdatedEvent {
  return ev && ev.event_type === MicroscopeEventType.Updated;
}
