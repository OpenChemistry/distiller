import React from 'react';
import { CompleteJobStates, FailedJobStates, JobState, PendingJobStates, RunningJobStates } from '../types';

import AutoRenew from '@material-ui/icons/Autorenew';
import Done from '@material-ui/icons/CheckCircle';
import Help from '@material-ui/icons/Help';
import ReportProblem from '@material-ui/icons/ReportProblem';

import blue from '@material-ui/core/colors/blue';
import grey from '@material-ui/core/colors/grey';
import lightGreen from '@material-ui/core/colors/lightGreen';
import red from '@material-ui/core/colors/red';
import orange from '@material-ui/core/colors/orange';

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
