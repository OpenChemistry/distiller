import React from 'react';

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import { lime } from '@mui/material/colors';

import { ScanJob } from '../types';

type Props = {
  open: boolean;
  onClose: () => void;
  job?: ScanJob;
}

const useStyles = makeStyles((theme) => ({
  outputContainer: {
    backgroundColor: "#121858",
    color: lime['A400'],
    minHeight: '20rem',
    fontFamily: 'monospace',
    padding: '1rem'
  },
}));

const JobOutputDialog: React.FC<Props> = (props) => {
  const { open, onClose, job } = props;
  const classes = useStyles();

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
        <div className={classes.outputContainer}>
          {(job.output || '').split('\n').map(line => <p>{line}</p>)}
        </div>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default JobOutputDialog;
