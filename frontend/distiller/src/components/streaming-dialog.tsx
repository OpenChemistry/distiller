import React, { useEffect, useState } from 'react';
import useLocalStorageState from 'use-local-storage-state';

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
  TextField,
  Typography,
} from '@mui/material';
import { LocalizationProvider, TimeField } from '@mui/x-date-pickers';
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon';
import { DateTime, Duration } from 'luxon';

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

const maxTime = DateTime.fromObject({
  hour: 2,
  minute: 0,
});
const minTime = DateTime.fromObject({
  hour: 0,
  minute: 0,
});
const defaultTime = DateTime.fromObject({
  hour: 2,
  minute: 0,
});

const StreamingDialog: React.FC<Props> = (props) => {
  const { open, machines, machine, setMachine, onClose, onSubmit, canRun } =
    props;
  const [threshold, setThreshold] = useLocalStorageState('threshold', {
    defaultValue: 4,
  });
  const [time, setTime] = useState<DateTime>(defaultTime);
  const [duration, setDuration] = useState<Duration>(
    Duration.fromObject({
      hours: time.hour,
      minutes: time.minute,
    })
  );

  const [error, setError] = useState('');
  const [disableSubmit, setDisableSubmit] = useState<boolean>(false);
  const [pending, setPending] = useState(false);
  const submitClick = () => {
    setPending(true);
    setError('');
    onSubmit({
      threshold,
      duration: duration.toISOTime({ suppressSeconds: true }),
    })
      .then(() => {
        setPending(false);
        onClose();
      })
      .catch(() => {
        setPending(false);
        setError('Submission Failed');
      });
  };

  useEffect(() => {
    setDuration(
      Duration.fromObject({ hours: time.hour, minutes: time.minute })
    );
    if (time > maxTime) {
      setError('Sessions longer than 2 hours not allowed.');
      setDisableSubmit(true);
    } else {
      setError('');
      setDisableSubmit(false);
    }
  }, [time]);

  return (
    <Dialog
      fullWidth={true}
      maxWidth="xs"
      open={open}
      onClose={onClose}
      aria-labelledby="streaming-job-title"
    >
      <DialogTitle id="streaming-job-title">Streaming Session</DialogTitle>
      <DialogContent>
        <DialogContentText mt={1} mb={1}>
          Start a new streaming session
        </DialogContentText>
        <FormControl sx={{ width: '100%' }} variant="standard">
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
          <TextField
            label="threshold"
            fullWidth
            value={threshold}
            onChange={(ev) => setThreshold(parseFloat(ev.target.value))}
            type="number"
            variant="standard"
            margin="normal"
          />
          <LocalizationProvider dateAdapter={AdapterLuxon}>
            <TimeField
              label="Session time (HH:MM)"
              value={time}
              onChange={(newTime) =>
                newTime ? setTime(newTime) : setTime(defaultTime)
              }
              format="HH:mm"
              minTime={minTime}
              maxTime={maxTime}
              formatDensity="spacious"
              variant="standard"
            />
          </LocalizationProvider>
          <Typography color="error" variant="caption">
            {error}
          </Typography>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button
          onClick={submitClick}
          disabled={!canRun() || pending || disableSubmit}
        >
          Submit
        </Button>
        <Button onClick={onClose} disabled={pending}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default StreamingDialog;
