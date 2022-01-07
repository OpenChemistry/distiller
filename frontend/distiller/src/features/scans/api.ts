import { apiClient } from '../../client';
import { IdType, Scan, ScansRequestResult } from '../../types';

export function getScans(
  skip?: number,
  limit?: number
): Promise<ScansRequestResult> {
  const params: any = {};
  if (skip !== undefined) {
    params['skip'] = skip;
  }
  if (limit !== undefined) {
    params['limit'] = limit;
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
  removeScanFiles: boolean
): Promise<void> {
  return apiClient
    .delete({
      url: `scans/${id}`,
      params: { remove_scan_files: removeScanFiles },
    })
    .then((_) => undefined);
}
