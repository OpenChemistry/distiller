import { useAppSelector } from '../app/hooks';
import {
  microscopesSelectors,
  microscopesState,
} from '../features/microscopes';
import { Microscope } from '../types';

export const canonicalMicroscopeName = (name: string) =>
  name.toLowerCase().replace(' ', '');

export const getMicroscope = (microscopes: Microscope[], canonicalName: string) => {
  let microscope = null;

  const microscopesByCanonicalName = microscopes.reduce(
    (obj: { [key: string]: Microscope }, microscope) => {
      obj[canonicalMicroscopeName(microscope.name)] = microscope;

      return obj;
    },
    {}
  );

  if (canonicalName in microscopesByCanonicalName) {
    microscope = microscopesByCanonicalName[canonicalName];
  }

  return microscope;
}