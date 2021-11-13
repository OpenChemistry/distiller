import React from 'react';
import { CompleteJobStates, FailedJobStates, JobState, PendingJobStates, RunningJobStates } from '../types';

import AutoRenew from '@mui/icons-material/Autorenew';
import Done from '@mui/icons-material/CheckCircle';
import Help from '@mui/icons-material/Help';
import ReportProblem from '@mui/icons-material/ReportProblem';

import { blue } from '@mui/material/colors';
import { grey } from '@mui/material/colors';
import { lightGreen } from '@mui/material/colors';
import { red } from '@mui/material/colors';
import {orange } from '@mui/material/colors';

const blue500 = blue['500'];
const red500 = red['500'];
const lightGreenA700 = lightGreen['A700'];
const grey300 = grey['300'];
const yellow300 = orange['300'];

const stateToStyle = (state: JobState): {Icon: any; color: string; className?: string} => {
    if (PendingJobStates.has(state)) {
      return {
        Icon: Help,
        color: yellow300
      }
    } else if (RunningJobStates.has(state)) {
      return {
        Icon: AutoRenew,
        color: lightGreenA700,
        className: 'spinner',
      }
    } else if (CompleteJobStates.has(state)) {
      return {
        Icon: Done,
        color: blue500,
      }
    } else if (FailedJobStates.has(state)) {
      return {
        Icon: ReportProblem,
        color: red500,
      }
    } else {
      return {
        Icon: Help,
        color: grey300
      }
    }
}

type Props = {
    state: JobState;
}

const JobStateComponent: React.FC<Props> = ({state}) => {
  const {Icon, color, className} = stateToStyle(state);

  return (
    <div title={state}>
      <Icon className={className} style={{color: color}}/>
    </div>
  )
}

export default JobStateComponent;
