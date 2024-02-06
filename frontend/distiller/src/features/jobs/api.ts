import { isNil } from 'lodash';
import { DateTime } from 'luxon';

import { apiClient } from '../../client';
import { IdType, Job, JobType, JobsRequestResult, Scan } from '../../types';
import { pickNil } from '../../utils';

export function createJob(
  type: JobType,
  scanId: IdType | null,
  machine: string,
  params: any,
): Promise<Job> {
  const payload = {
    job_type: type,
    scan_id: scanId,
    machine,
    params,
  };

  return apiClient
    .post({
      path: 'jobs',
      json: payload,
    })
    .then((res) => res.json());
}

export function getJobs(
  skip?: number,
  limit?: number,
  jobType?: JobType,
  start?: DateTime,
  end?: DateTime,
): Promise<JobsRequestResult> {
  const params: any = {};
  if (!isNil(skip)) {
    params['skip'] = skip;
  }
  if (!isNil(limit)) {
    params['limit'] = limit;
  }
  if (!isNil(jobType)) {
    params['job_type'] = jobType;
  }
  if (!isNil(start)) {
    params['start'] = start;
  }
  if (!isNil(end)) {
    params['end'] = end;
  }

  return apiClient
    .get({
      path: 'jobs',
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

export function getJob(id: IdType): Promise<Job> {
  return apiClient
    .get({
      path: `jobs/${id}`,
    })
    .then((res) => {
      return res.json().then((job: Job) => {
        let prevJobId: any = pickNil(
          res.headers.get('x-previous-job'),
          undefined,
        );
        let nextJobId: any = pickNil(res.headers.get('x-next-job'), undefined);
        return { ...job, prevJobId, nextJobId };
      });
    });
}

export function getJobScans(id: IdType): Promise<Scan[]> {
  const params: any = {};
  params['job_id'] = id;

  return apiClient
    .get({
      path: `scans`,
      params,
    })
    .then((res) => res.json());
}

export function patchJob(id: IdType, updates: Partial<Job>): Promise<Job> {
  return apiClient
    .patch({
      path: `jobs/${id}`,
      json: updates,
    })
    .then((res) => res.json());
}

export function cancelJob(id: IdType): Promise<Job> {
  return apiClient
    .put({
      path: `jobs/${id}/cancel`,
    })
    .then((res) => res.json());
}
