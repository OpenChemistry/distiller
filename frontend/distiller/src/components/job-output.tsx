import React from 'react';

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { lime } from '@mui/material/colors';

import { Job } from '../types';

type Props = {
  open: boolean;
  onClose: () => void;
  job?: Job;
};

const OutputContainer = styled('div')(({ theme }) => ({
  backgroundColor: '#121858',
  color: lime['A400'],
  minHeight: '20rem',
  fontFamily: 'monospace',
  padding: '1rem',
}));

const JobOutputDialog: React.FC<Props> = (props) => {
  const { open, onClose, job } = props;

  if (!job) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="job-output-title"
      fullWidth={true}
      maxWidth={'xl'}
    >
      <DialogTitle id="job-output-title">{`Job ${job.id}`}</DialogTitle>
      <DialogContent>
        <OutputContainer>
          {(job.output || '').split('\n').map((line) => (
            <p>{line}</p>
          ))}
        </OutputContainer>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default JobOutputDialog;
