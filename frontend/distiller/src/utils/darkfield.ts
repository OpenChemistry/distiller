import { DarkfieldCorrection } from '../types';

const NoneCorrection: DarkfieldCorrection = {
  label: 'None',
  value: 'none',
};

const RDMeanCorrection: DarkfieldCorrection = {
  label: 'Row-Dark Mean',
  value: 'row-dark-mean',
};

const RDMedianCorrection: DarkfieldCorrection = {
  label: 'Row-Dark Median',
  value: 'row-dark-median',
};

export const DARKFIELD_CORRECTIONS: DarkfieldCorrection[] = [
  NoneCorrection,
  RDMeanCorrection,
  RDMedianCorrection,
];

export const DEFAULT_DARKFIELD_CORRECTION = NoneCorrection;
