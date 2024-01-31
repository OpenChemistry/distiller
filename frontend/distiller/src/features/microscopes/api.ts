import { apiClient } from '../../client';
import { Microscope } from '../../types';

export function getMicroscopes(): Promise<Microscope[]> {
  return apiClient
    .get({
      path: `microscopes`,
    })
    .then((res) => res.json());
}
