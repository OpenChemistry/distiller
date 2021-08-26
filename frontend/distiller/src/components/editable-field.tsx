import React, {useState} from 'react';

import {
  Typography,
  TextField,
  IconButton,
} from '@material-ui/core';
import EditIcon from '@material-ui/icons/Edit';
import SaveIcon from '@material-ui/icons/Save';
import { makeStyles } from '@material-ui/core/styles';

type Props = {
  value: string;
  onSave: (value: string) => Promise<any>;
}

const useStyles = makeStyles((theme) => ({
  container: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
  },
  field: {
    flexGrow: 1
  }
}));

const EditableField: React.FC<Props> = ({value, onSave}) => {
  const classes = useStyles();

  const [draftValue, setDraftValue] = useState('');
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(false);

  const onEditClick = () => {
    setDraftValue(value);
    setEditing(true);
    setSaving(false);
  }

  const onSaveClick = () => {
    setSaving(true);
    onSave(draftValue)
      .then(() => {
        setSaving(false);
        setEditing(false);
      }).catch(() => {
        setSaving(false);
        setError(true);
      });
  }
  return (
    <div className={classes.container}>
      {editing
        ? <React.Fragment>
          <TextField
            className={classes.field}
            value={draftValue}
            onChange={(ev) => setDraftValue(ev.target.value)}
            disabled={saving}
            error={error}
          />
          <IconButton onClick={onSaveClick} disabled={saving}><SaveIcon/></IconButton>
        </React.Fragment>
        : <React.Fragment>
          <Typography className={classes.field}>{value}</Typography>
          <IconButton onClick={onEditClick}><EditIcon/></IconButton>
        </React.Fragment>
      }
    </div>
  );
}

export default EditableField;
