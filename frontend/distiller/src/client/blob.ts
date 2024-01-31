import { apiClient } from '.';

export function getBlob(url: string): Promise<Blob> {
  return apiClient
    .get({
      url,
    })
    .then((res) => res.blob());
}
