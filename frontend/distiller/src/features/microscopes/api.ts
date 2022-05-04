import { apiClient } from '../../client';
import { Microscope } from '../../types';

export function getMicroscopes(): Promise<Microscope[]> {
  return apiClient
    .get({
      url: `microscopes`,
    })
    .then((res) => res.json());
}
