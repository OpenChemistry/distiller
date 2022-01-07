import React, { useState } from 'react';

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Typography,
} from '@mui/material';

type Props = {
  open: boolean;
  onClose: () => void;
  onSubmit: (params: any) => Promise<any>;
};

const TransferDialog: React.FC<Props> = (props) => {
  const { open, onClose, onSubmit } = props;
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);

  const submitClick = () => {
    setPending(true);
    onSubmit({})
      .then(() => {
        setPending(false);
        onClose();
      })
      .catch(() => {
        setPending(false);
        setError('Submission Failed');
      });
  };

  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="transfer-job-title">
      <DialogTitle id="transfer-job-title">Transfer Job</DialogTitle>
      <DialogContent>
        <DialogContentText>Create a new transfer job</DialogContentText>
        <Typography color="error" variant="caption">
          {error}
        </Typography>
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
  );
};

export default TransferDialog;
