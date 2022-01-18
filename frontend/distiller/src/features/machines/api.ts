import { apiClient } from '../../client';

export function getMachines(): Promise<string[]> {
  return apiClient
    .get({
      url: `machines`,
    })
    .then((res) => res.json());
}
