import React, { useState } from 'react';

import { Typography, TextField, IconButton } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import makeStyles from '@mui/styles/makeStyles';
import { stopPropagation } from '../utils';

type Props = {
  value: string;
  onSave: (value: string) => Promise<any>;
};

const useStyles = makeStyles((theme) => ({
  container: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
  },
  field: {
    flexGrow: 1,
  },
}));

const EditableField: React.FC<Props> = ({ value, onSave }) => {
  const classes = useStyles();

  const [draftValue, setDraftValue] = useState('');
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(false);

  const onEditClick = () => {
    setDraftValue(value);
    setEditing(true);
    setSaving(false);
  };

  const onSaveClick = () => {
    setSaving(true);
    onSave(draftValue)
      .then(() => {
        setSaving(false);
        setEditing(false);
      })
      .catch(() => {
        setSaving(false);
        setError(true);
      });
  };

  const onKeyPress = (ev: React.KeyboardEvent<Element>) => {
    if (ev.key === 'Enter') {
      onSaveClick();
    }
  };

  return (
    <div className={classes.container}>
      {editing ? (
        <React.Fragment>
          <TextField
            className={classes.field}
            value={draftValue}
            onClick={stopPropagation(() => {})}
            onChange={(ev) => setDraftValue(ev.target.value)}
            disabled={saving}
            error={error}
            autoFocus={true}
            onKeyPress={onKeyPress}
          />
          <IconButton
            onClick={stopPropagation(onSaveClick)}
            disabled={saving}
            size="large"
          >
            <SaveIcon />
          </IconButton>
        </React.Fragment>
      ) : (
        <React.Fragment>
          <Typography className={classes.field}>{value}</Typography>
          <IconButton onClick={stopPropagation(onEditClick)} size="large">
            <EditIcon />
          </IconButton>
        </React.Fragment>
      )}
    </div>
  );
};

export default EditableField;
