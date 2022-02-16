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
  Select,
  Typography,
} from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import { Machine } from '../types';
import MachineOptionComponent from './machine-option';

type Props = {
  open: boolean;
  machines: Machine[];
  machine: string;
  setMachine: (machine: string) => void;
  canRun: () => boolean;
  onClose: () => void;
  onSubmit: (params: any) => Promise<any>;
};

const useStyles = makeStyles((_theme) => ({
  form: {
    width: '100%',
  },
}));

const TransferDialog: React.FC<Props> = (props) => {
  const classes = useStyles();
  const { open, machines, machine, setMachine, onClose, onSubmit, canRun } =
    props;
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);

  const submitClick = () => {
    setPending(true);
    setError('');
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
    <Dialog
      fullWidth={true}
      maxWidth="xs"
      open={open}
      onClose={onClose}
      aria-labelledby="transfer-job-title"
    >
      <DialogTitle id="transfer-job-title">Transfer Job</DialogTitle>
      <DialogContent>
        <DialogContentText mt={1} mb={1}>
          Create a new transfer job
        </DialogContentText>
        <FormControl className={classes.form} variant="standard" fullWidth>
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
            {machines.map(MachineOptionComponent)}
          </Select>
        </FormControl>
        <Typography color="error" variant="caption">
          {error}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={submitClick} disabled={!canRun() || pending}>
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
