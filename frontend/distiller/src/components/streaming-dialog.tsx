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
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material';
import { LocalizationProvider, TimeField } from '@mui/x-date-pickers';
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon';
import { DateTime, Duration } from 'luxon';

import { Machine } from '../types';
import {
  DARKFIELD_CORRECTIONS,
  DEFAULT_DARKFIELD_CORRECTION,
} from '../utils/darkfield';
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

  const [darkfieldCorrection, setDarkfieldCorrection] = useLocalStorageState(
    'darkfieldCorrection',
    {
      defaultValue: DEFAULT_DARKFIELD_CORRECTION.value,
    },
  );
  const [threshold, setThreshold] = useLocalStorageState('threshold', {
    defaultValue: 4,
  });
  const [time, setTime] = useState<DateTime>(defaultTime);
  const [duration, setDuration] = useState<Duration>(
    Duration.fromObject({
      hours: time.hour,
      minutes: time.minute,
    }),
  );

  const [error, setError] = useState('');
  const [disableSubmit, setDisableSubmit] = useState<boolean>(false);
  const [pending, setPending] = useState(false);
  const submitClick = () => {
    setPending(true);
    setError('');
    onSubmit({
      threshold,
      darkfield: darkfieldCorrection,
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
      Duration.fromObject({ hours: time.hour, minutes: time.minute }),
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
            onChange={(ev) => setMachine(ev.target.value)}
            placeholder="Machine"
          >
            {machines.map(MachineOptionComponent)}
          </Select>
        </FormControl>
        <FormControl sx={{ width: '100%' }} variant="standard" margin="normal">
          <InputLabel id="darkfield-select-label">
            Darkfield Correction
          </InputLabel>
          <Select
            fullWidth
            label="Darkfield Correction"
            labelId="darkfield-select-label"
            value={darkfieldCorrection}
            onChange={(ev) => setDarkfieldCorrection(ev.target.value)}
            placeholder="Darkfield Correction"
          >
            {DARKFIELD_CORRECTIONS.map((correction) => (
              <MenuItem value={correction.value} key={correction.value}>
                {correction.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
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
            fullWidth
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
