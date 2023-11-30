import { isNil } from 'lodash';
import { DateTime } from 'luxon';
import { apiClient } from '../../client';
import { IdType, Job, Scan, ScansRequestResult } from '../../types';
import { pickNil } from '../../utils';

export function getScans(
  microscopeId: IdType,
  skip?: number,
  limit?: number,
  start?: DateTime,
  end?: DateTime,
): Promise<ScansRequestResult> {
  const params: any = { microscope_id: microscopeId };
  if (!isNil(skip)) {
    params['skip'] = skip;
  }
  if (!isNil(limit)) {
    params['limit'] = limit;
  }
  if (!isNil(start)) {
    params['start'] = start;
  }
  if (!isNil(end)) {
    params['end'] = end;
  }

  return apiClient
    .get({
      url: 'scans',
      params,
    })
    .then((res) => {
      return res.json().then((scans) => {
        let totalCount = -1;

        const totalScanCountHeader = res.headers.get('x-total-count');
        if (totalScanCountHeader != null) {
          totalCount = Number.parseInt(totalScanCountHeader);
        }

        const scansRequestResult = {
          scans,
          totalCount,
        };

        return new Promise<ScansRequestResult>((resolve) => {
          resolve(scansRequestResult);
        });
      });
    });
}

export function getScan(id: IdType): Promise<Scan> {
  return apiClient
    .get({
      url: `scans/${id}`,
    })
    .then((res) => {
      return res.json().then((scan: Scan) => {
        let prevScanId: any = pickNil(
          res.headers.get('x-previous-scan'),
          undefined,
        );
        let nextScanId: any = pickNil(
          res.headers.get('x-next-scan'),
          undefined,
        );
        return { ...scan, prevScanId, nextScanId };
      });
    });
}

export function getScanJobs(id: IdType): Promise<Job[]> {
  const params: any = {};
  params['scan_id'] = id;

  return apiClient
    .get({
      url: `jobs`,
      params,
    })
    .then((res) => res.json());
}

export function patchScan(id: IdType, updates: Partial<Scan>): Promise<Scan> {
  return apiClient
    .patch({
      url: `scans/${id}`,
      json: updates,
    })
    .then((res) => res.json());
}

export function removeScanFiles(id: IdType, host: string): Promise<void> {
  return apiClient
    .put({
      url: `scans/${id}/remove`,
      params: { host },
    })
    .then((_) => undefined);
}

export function removeScan(
  id: IdType,
  removeScanFiles: boolean,
): Promise<void> {
  return apiClient
    .delete({
      url: `scans/${id}`,
      params: { remove_scan_files: removeScanFiles },
    })
    .then((_) => undefined);
}
