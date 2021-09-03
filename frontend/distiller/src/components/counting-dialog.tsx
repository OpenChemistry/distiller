import React, { useState } from 'react';

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField,
  Typography,
} from '@material-ui/core';

type Props = {
    open: boolean;
    onClose: () => void;
    onSubmit: (params: any) => Promise<any>;
}

const CountingDialog: React.FC<Props> = (props) => {
  const { open, onClose, onSubmit } = props;
  const [threshold, setThreshold] = useState(4);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);

  const submitClick = () => {
    setPending(true);
    onSubmit({threshold})
      .then(() => {
        setPending(false);
        onClose();
      })
      .catch(() => {
        setPending(false);
        setError('Submission Failed');
      });
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="counting-job-title"
    >
      <DialogTitle id="counting-job-title">Counting Job</DialogTitle>
      <DialogContent>
        <DialogContentText>Create a new counting job</DialogContentText>
        <TextField label='threshold' fullWidth value={threshold} onChange={(ev) => setThreshold(parseFloat(ev.target.value))} type='number'/>
        <Typography color='error' variant='caption'>{error}</Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={submitClick} disabled={pending}>
          Submit
        </Button>
        <Button onClick={onClose} disabled={pending}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default CountingDialog;
