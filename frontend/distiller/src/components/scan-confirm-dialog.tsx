import React, { useState } from 'react';

import WarningIcon from '@mui/icons-material/Warning';
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
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import { styled } from '@mui/material/styles';
import { isNil } from 'lodash';
import { Scan, ScanLocation } from '../types';

const DialogTitleWarningText = styled(DialogTitle)(({ theme }) => ({
  color: theme.palette.warning.light,
  display: 'flex',
  alignItems: 'right',
}));

const FormControlLabelWarningText = styled(FormControlLabel)(({ theme }) => ({
  color: theme.palette.warning.light,
}));

type BaseProps = {
  scan: Scan | null;
  machines: string[];
  onConfirm: ((params: { [key: string]: any }) => void) | undefined;
};

interface ScanConfirmDialogProps extends BaseProps {
  title: string;
  contentText: string;
  children?: React.ReactNode;
}

const ScanConfirmDialog: React.FC<ScanConfirmDialogProps> = (props) => {
  const { onConfirm, title, contentText, scan, children } = props;

  const [enteredScanID, setEnteredScanID] = useState<number | null>(null);

  const onCancelClick = () => {
    if (onConfirm === undefined) {
      return;
    }

    onConfirm({ confirm: false });
    setEnteredScanID(null);
  };

  const onConfirmClick = () => {
    if (onConfirm === undefined) {
      return;
    }

    onConfirm({ confirm: true });
    setEnteredScanID(null);
  };

  if (scan === null) {
    return null;
  }

  // We use the scan ID in the case of 4D and ID otherwise
  const idLabel = !isNil(scan.scan_id) ? 'scan ID' : 'ID';

  // The id to use for confirmation
  const id = !isNil(scan.scan_id) ? scan.scan_id : scan.id;

  const onKeyDown = (ev: React.KeyboardEvent<HTMLDivElement>) => {
    if (ev.key !== 'Enter') {
      return;
    }

    if (id !== enteredScanID) {
      return;
    }

    onConfirmClick();
  };

  return (
    <Dialog
      open={scan !== null}
      onClose={onCancelClick}
      aria-labelledby="confirm-title"
      // disableRestoreFocus ensures the autofocus on the text
      // field works: https://github.com/mui/material-ui/issues/33004
      disableRestoreFocus
    >
      <DialogTitleWarningText id="confirm-title">
        <WarningIcon />
        <Typography ml={1}>{title}</Typography>
      </DialogTitleWarningText>

      <DialogContent>
        <DialogContentText mt={1} mb={1}>
          {contentText}
        </DialogContentText>
        {children}
        <DialogContentText mt={1} mb={1}>
          Please enter the {idLabel} to confirm action.
        </DialogContentText>
        <TextField
          label={idLabel}
          value={enteredScanID}
          onChange={(ev) => setEnteredScanID(parseInt(ev.target.value))}
          onKeyDown={onKeyDown}
          type="number"
          variant="standard"
          autoFocus
        />
      </DialogContent>
      <DialogActions>
        <Button
          onClick={onConfirmClick}
          disabled={id !== enteredScanID}
          color="warning"
        >
          Confirm
        </Button>
        <Button onClick={onCancelClick}>Cancel</Button>
      </DialogActions>
    </Dialog>
  );
};

export const ScanDeleteConfirmDialog: React.FC<BaseProps> = (props) => {
  const { scan, machines } = props;
  const [removeScanFiles, setRemoveScanFiles] = useState<boolean>(false);

  if (scan === null) {
    return null;
  }

  const title = 'Remove scan';
  const contentText = `You are about to remove scan ${
    !isNil(scan.scan_id) ? scan.scan_id : scan.id
  }. This operation can not be undone.`;

  const hasLocations = () => {
    const edgeLocations = scan.locations.filter((l: ScanLocation) => {
      return !machines.includes(l.host);
    });

    return edgeLocations.length !== 0;
  };

  const handleRemoveScanFilesChange = (
    event: React.ChangeEvent<HTMLInputElement>,
    checked: boolean,
  ) => {
    setRemoveScanFiles(checked);
  };

  const onConfirm = (params: { [key: string]: any }) => {
    if (props.onConfirm === undefined) {
      return;
    }

    props.onConfirm({ ...params, removeScanFiles });
    setRemoveScanFiles(false);
  };

  return (
    <ScanConfirmDialog
      title={title}
      contentText={contentText}
      scan={scan}
      onConfirm={onConfirm}
      machines={machines}
    >
      {hasLocations() && !isNil(scan.scan_id) && (
        <React.Fragment>
          <DialogContentText mt={1} mb={1}>
            Warning: Scan files exist on the acquisition machine for this scan.
            To remove scan file check box below.
          </DialogContentText>
          <FormGroup>
            <FormControlLabelWarningText
              control={
                <Checkbox
                  checked={removeScanFiles}
                  onChange={handleRemoveScanFilesChange}
                />
              }
              label="Remove scan files (This operation can not be undone!)."
            />
          </FormGroup>
        </React.Fragment>
      )}
    </ScanConfirmDialog>
  );
};

export const RemoveScanFilesConfirmDialog: React.FC<BaseProps> = (props) => {
  const { onConfirm, scan, machines } = props;

  if (scan === null) {
    return null;
  }

  const title = 'Remove scan files';
  const contentText = `You are about to remove scan files from the acquisition machine for scan ${scan.scan_id}. This operation can not be undone.`;

  return (
    <ScanConfirmDialog
      title={title}
      contentText={contentText}
      scan={scan}
      onConfirm={onConfirm}
      machines={machines}
    />
  );
};
