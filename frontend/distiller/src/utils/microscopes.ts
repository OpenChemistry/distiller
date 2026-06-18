import { isNil } from 'lodash';
import { matchPath } from 'react-router';

import { Microscope } from '../types';

export const canonicalMicroscopeName = (name: string) =>
  name.toLowerCase().replace(' ', '');

export const getMicroscopeIdForPath = (
  microscopes: Microscope[],
  pathName: string,
) => {
  const microscopesByCanonicalName = microscopes.reduce(
    (obj: { [key: string]: Microscope }, microscope) => {
      obj[canonicalMicroscopeName(microscope.name)] = microscope;

      return obj;
    },
    {},
  );

  const pathMatch = matchPath({ path: '/:microscopeName/*' }, pathName);
  if (pathMatch === null) {
    return microscopes[0]?.id;
  }

  const { microscopeName } = pathMatch.params;
  if (isNil(microscopeName)) {
    throw new Error('Unable to extract microscope');
  }

  const canonicalName = canonicalMicroscopeName(microscopeName);
  if (!(canonicalName in microscopesByCanonicalName)) {
    throw new Error('Unable to find microscope ID');
  }

  return microscopesByCanonicalName[canonicalName].id;
};

export const getMicroscope = (
  microscopes: Microscope[],
  canonicalName: string,
) => {
  let microscope = null;

  const microscopesByCanonicalName = microscopes.reduce(
    (obj: { [key: string]: Microscope }, microscope) => {
      obj[canonicalMicroscopeName(microscope.name)] = microscope;

      return obj;
    },
    {},
  );

  if (canonicalName in microscopesByCanonicalName) {
    microscope = microscopesByCanonicalName[canonicalName];
  }

  return microscope;
};
