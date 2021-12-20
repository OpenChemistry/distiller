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
} from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import WarningIcon from '@mui/icons-material/Warning';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';

import {Scan, ScanLocation} from '../types'
import { COMPUTE_HOSTS } from '../constants';

const useStyles = makeStyles((theme) => ({
  warningText: {
    color: theme.palette.warning.light
  },
  dialogTitle: {
    display: "flex",
    alignItems: "right",
  }
}));

type BaseProps  = {
  scan: Scan|null;
  onConfirm: ((params: {[key: string]: any}) => void) | undefined;
}

interface ScanConfirmDialogProps extends BaseProps {
  title: string;
  contentText: string;
  children?: React.ReactNode;
}



const ScanConfirmDialog: React.FC<ScanConfirmDialogProps> = (props) => {
  const classes = useStyles();
  const { onConfirm, title, contentText, scan, children } = props;

  const [enteredScanID, setEnteredScanID]  = useState<number|null>(null);

  const onCancelClick = () =>  {
    if (onConfirm === undefined) {
      return
    }

    onConfirm({confirm: false})
    setEnteredScanID(null);
  }

  const onConfirmClick = () =>  {
    if (onConfirm === undefined) {
      return
    }

    onConfirm({confirm: true})
    setEnteredScanID(null);
  }

  if (scan === null) {
    return (null);
  }

  return (
    <Dialog
      open={scan !== null}
      onClose={onCancelClick}
      aria-labelledby="confirm-title"
    >
      <DialogTitle id="confirm-title" className={`${classes.warningText} ${classes.dialogTitle}`}>
        <WarningIcon/>
        <Typography ml={1}>{title}</Typography>
        </DialogTitle>

      <DialogContent>
        <DialogContentText mt={1} mb={1}>{contentText}</DialogContentText>
        {children}
        <DialogContentText mt={1} mb={1}>Please enter the scan ID to confirm action.</DialogContentText>
        <TextField label="scan ID" value={enteredScanID} onChange={(ev) => setEnteredScanID(parseInt(ev.target.value))} type="number" variant="standard"/>
      </DialogContent>
      <DialogActions>
        <Button onClick={onConfirmClick} disabled={scan.scan_id !== enteredScanID} color="warning">
          Confirm
        </Button>
        <Button onClick={onCancelClick}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export const ScanDeleteConfirmDialog: React.FC<BaseProps> = (props) => {
  const classes = useStyles();
  const { scan} = props;
  const [removeScanFiles, setRemoveScanFiles]  = useState<boolean>(false);

  if (scan === null) {
    return (null);
  }

  const title = "Remove scan";
  const contentText = `You are about to remove scan ${scan.scan_id}. This operation can not be undone.`

  const hasLocations = () => {
    const edgeLocations = scan.locations.filter((l: ScanLocation) => {
      return !COMPUTE_HOSTS.includes(l.host);
    });

    return edgeLocations.length !== 0;
  };

  const handleRemoveScanFilesChange = (event: React.ChangeEvent<HTMLInputElement>, checked: boolean) => {
    setRemoveScanFiles(checked);
  };

  const onConfirm = (params: {[key: string]: any}) => {
    if (props.onConfirm === undefined) {
      return
    }

    props.onConfirm({...params, removeScanFiles})
    setRemoveScanFiles(false);
  }

  return (
    <ScanConfirmDialog title={title} contentText={contentText} scan={scan} onConfirm={onConfirm}>
      { hasLocations() &&
      <React.Fragment>
        <DialogContentText mt={1} mb={1}>Warning: Scan files exist on the acquisition machine for this scan. To remove scan file check box below.</DialogContentText>
        <FormGroup>
          <FormControlLabel className={classes.warningText} control={<Checkbox  checked={removeScanFiles} onChange={handleRemoveScanFilesChange} />} label="Remove scan files (This operation can not be undone!)." />
        </FormGroup>
      </React.Fragment>
      }
    </ScanConfirmDialog>
  )
}

export const RemoveScanFilesConfirmDialog: React.FC<BaseProps> = (props) => {
  const { onConfirm, scan} = props;

  if (scan === null) {
    return (null);
  }

  const title = "Remove scan files";
  const contentText = `You are about to remove scan files from the acquisition machine for scan ${scan.scan_id}. This operation can not be undone.`;

  return (
    <ScanConfirmDialog title={title} contentText={contentText} scan={scan} onConfirm={onConfirm}  />
  )
}