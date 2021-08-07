import { apiClient } from '../../client';
import { Scan } from '../../types';

export function getScans(skip?: number, limit?: number): Promise<Scan[]> {
  const params: any = {};
  if (skip !== undefined) {
    params['skip'] = skip;
  }
  if (limit !== undefined) {
    params['limit'] = limit;
  }

  return apiClient.get({
    url: 'scans',
    params,
  }).then(res => res.json());
}
