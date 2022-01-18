import React, { useState } from 'react';

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from '@mui/material';

type Props = {
  open: boolean;
  machines: string[];
  machine: string;
  setMachine: (machine: string) => void;
  onClose: () => void;
  onSubmit: (params: any) => Promise<any>;
};

const TransferDialog: React.FC<Props> = (props) => {
  const { open, machines, machine, setMachine, onClose, onSubmit } = props;
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
        <DialogContentText mt={1} mb={1}>
          Create a new transfer job
        </DialogContentText>
        <FormControl variant="standard" fullWidth>
          <InputLabel id="machine-select-label">Machine</InputLabel>
          <Select
            fullWidth
            label="Machine"
            labelId="machine-select-label"
            value={machine}
            size="small"
            onChange={(ev) => setMachine(ev.target.value)}
            placeholder="Machine"
          >
            {machines.map((machine) => (
              <MenuItem key={machine} value={machine}>
                {machine}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
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
