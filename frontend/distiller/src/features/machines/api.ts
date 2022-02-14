import { apiClient } from '../../client';
import { Machine } from '../../types';

export function getMachines(): Promise<Machine[]> {
  return apiClient
    .get({
      url: `machines`,
    })
    .then((res) => res.json());
}
