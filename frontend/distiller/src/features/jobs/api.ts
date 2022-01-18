import { IdType, JobType, ScanJob } from '../../types';
import { apiClient } from '../../client';

export function createJob(
  type: JobType,
  scanId: IdType,
  machine: string,
  params: any
): Promise<ScanJob> {
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
