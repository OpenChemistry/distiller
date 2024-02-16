import { isNil } from 'lodash';
import { apiClient } from '../../client';
import { IdType, Notebook, NotebookSpecification } from '../../types';

export function getNotebooks(): Promise<NotebookSpecification[]> {
  return apiClient
    .get({
      path: `notebooks`,
    })
    .then((res) => res.json());
}

export function fetchOrCreateNotebook(
  name: string,
  scanId: number,
): Promise<Notebook> {
  const payload = {
    name,
    scan_id: scanId,
  };

  return apiClient
    .post({
      path: 'notebooks',
      json: payload,
    })
    .then((res) => res.json());
}
