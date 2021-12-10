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

const useStyles = makeStyles((theme) => ({
  warningText: {
    color: theme.palette.warning.light
  },
  dialogTitle: {
    display: "flex",
    alignItems: "right",
  }
}));

type Props = {
    onConfirm: ((confirm: boolean) => void)|null;
    title: string;
    contentText: string;
    scanID: number|null;
}

const ScanConfirmDialog: React.FC<Props> = (props) => {
  const classes = useStyles();
  const { onConfirm, title, contentText, scanID } = props;

  const [enteredScanID, setEnteredScanID]  = useState<number|null>(null);

  const onCloseClick = () =>  {
    if (onConfirm != null) {
      onConfirm(false);
    }
    setEnteredScanID(null);
  }

  const onConfirmClick = () =>  {
    if (onConfirm != null) {
      onConfirm(true);
    }
    setEnteredScanID(null);
  }

  return (
    <Dialog
      open={scanID != null}
      onClose={onCloseClick}
      aria-labelledby="confirm-title"
    >
      <DialogTitle id="confirm-title" className={`${classes.warningText} ${classes.dialogTitle}`}>
        <WarningIcon/>
        <Typography ml={1}>{title}</Typography>
        </DialogTitle>

      <DialogContent>
        <DialogContentText mt={1} mb={1}>{contentText}</DialogContentText>
        <DialogContentText mt={1} mb={1}>Please enter the scan ID to confirm action.</DialogContentText>

        <TextField label="scan ID" value={enteredScanID} onChange={(ev) => setEnteredScanID(parseInt(ev.target.value))} type="number" variant="standard"/>
      </DialogContent>
      <DialogActions>
        <Button onClick={onConfirmClick} disabled={scanID !== enteredScanID} color="warning">
          Confirm
        </Button>
        <Button onClick={onCloseClick}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ScanConfirmDialog;