import React from 'react';

import { Chip, MenuItem } from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';

import { Machine } from '../types';
import { canRunJobs, statusColor } from '../utils/machine';

const useStyles = makeStyles((_theme) => ({
  menu: {
    justifyContent: 'space-between',
    display: 'flex',
    flexGrow: 1,
  },
}));

function statusIcon(machine: Machine) {
  const { status, notes } = machine;
  let title: string | undefined = undefined;
  if (notes.length > 0) {
    title = notes[notes.length - 1];
  }
  return (
    <Chip
      label={status}
      color={statusColor(status)}
      size="small"
      title={title}
      variant="outlined"
    />
  );
}

const MachineOptionComponent = (machine: Machine) => {
  const classes = useStyles();

  return (
    <MenuItem
      value={machine.name}
      key={machine.name}
      disabled={!canRunJobs(machine.status)}
    >
      <div className={classes.menu}>
        <div>{machine.name}</div> {statusIcon(machine)}
      </div>
    </MenuItem>
  );
};

export default MachineOptionComponent;
