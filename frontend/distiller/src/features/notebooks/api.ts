import { apiClient } from '../../client';
import { IdType, Notebook } from '../../types';
import { pickNil } from '../../utils';
import { DateTime } from 'luxon';

export function getNotebooks(): Promise<string[]> {
  return apiClient
    .get({
      url: `notebooks`,
    })
    .then((res) => res.json());
}

export function fetchOrCreateNotebook(
  name: string,
  scanId: number
): Promise<Notebook> {
  const payload = {
    name,
    scan_id: scanId,
  };

  return apiClient
    .post({
      url: 'notebooks',
      json: payload,
    })
    .then((res) => res.json());
}
