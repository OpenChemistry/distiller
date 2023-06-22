import { IdType, JobType, Job, JobsRequestResult, Scan } from '../../types';
import { apiClient } from '../../client';
import { DateTime } from 'luxon';

export function createJob(
  type: JobType,
  scanId: IdType | null,
  machine: string,
  params: any
): Promise<Job> {
  const payload = {
    job_type: type,
    scan_id: scanId,
    machine,
    params,
  };

  return apiClient
    .post({
      url: 'jobs',
      json: payload,
    })
    .then((res) => res.json());
}

export function getJobs(
  skip?: number,
  limit?: number,
  jobType?: JobType,
  start?: DateTime,
  end?: DateTime
): Promise<JobsRequestResult> {
  const params: any = {};
  if (skip !== undefined) {
    params['skip'] = skip;
  }
  if (limit !== undefined) {
    params['limit'] = limit;
  }
  if (jobType !== undefined) {
    params['job_type'] = jobType;
  }
  if (start !== undefined) {
    params['start'] = start;
  }
  if (end !== undefined) {
    params['end'] = end;
  }

  return apiClient
    .get({
      url: 'jobs',
      params,
    })
    .then((res) => {
      return res.json().then((jobs) => {
        let totalCount = -1;

        const totalJobCountHeader = res.headers.get('x-total-count');
        if (totalJobCountHeader != null) {
          totalCount = Number.parseInt(totalJobCountHeader);
        }

        const jobsRequestResult = {
          jobs,
          totalCount,
        };

        return new Promise<JobsRequestResult>((resolve) => {
          resolve(jobsRequestResult);
        });
      });
    });
}

export function getJob(id: IdType, withScans?: boolean): Promise<Job> {
  const params: any = {};
  if (withScans !== undefined) {
    params['with_scans'] = withScans;
  }
  return apiClient
    .get({
      url: `jobs/${id}`,
      params,
    })
    .then((res) => res.json());
}

export function getJobScans(id: IdType): Promise<Scan[]> {
  return apiClient
    .get({
      url: `jobs/${id}/scans`,
    })
    .then((res) => res.json());
}

export function patchJob(id: IdType, updates: Partial<Job>): Promise<Job> {
  return apiClient
    .patch({
      url: `jobs/${id}`,
      json: updates,
    })
    .then((res) => res.json());
}

export function cancelJob(id: IdType): Promise<Job> {
  return apiClient
    .delete({
      url: `jobs/${id}`,
    })
    .then((res) => res.json());
}
