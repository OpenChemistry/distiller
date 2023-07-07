import { Chip, MenuItem } from '@mui/material';
import { styled } from '@mui/material/styles';
import { Machine } from '../types';
import { canRunJobs, statusColor } from '../utils/machine';

const MachineDiv = styled('div')(({ theme }) => ({
  justifyContent: 'space-between',
  display: 'flex',
  flexGrow: 1,
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
  return (
    <MenuItem
      value={machine.name}
      key={machine.name}
      disabled={!canRunJobs(machine.status)}
    >
      <MachineDiv>
        <div>{machine.name}</div> {statusIcon(machine)}
      </MachineDiv>
    </MenuItem>
  );
};

export default MachineOptionComponent;
