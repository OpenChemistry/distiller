import React from 'react';

import { Chip, MenuItem } from '@mui/material';

import { Machine } from '../types';
import { canRunJobs, statusColor } from '../utils/machine';

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
  return (
    <MenuItem
      value={machine.name}
      key={machine.name}
      disabled={!canRunJobs(machine.status)}
    >
      {machine.name} <span style={{ flexGrow: 1 }}></span> {statusIcon(machine)}
    </MenuItem>
  );
};

export default MachineOptionComponent;
