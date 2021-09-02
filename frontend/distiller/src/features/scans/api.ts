import { apiClient } from '../../client';
import { IdType, Scan } from '../../types';

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

export function getScan(id: IdType): Promise<Scan> {
  return apiClient.get({
    url: `scans/${id}`
  }).then(res => res.json());
}

export function patchScan(id: IdType, updates: Partial<Scan>): Promise<Scan> {
  return apiClient.patch({
    url: `scans/${id}`,
    json: updates,
  }).then(res => res.json());
}
