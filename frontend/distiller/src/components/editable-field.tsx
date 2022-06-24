import React, { useState } from 'react';

import { Typography, TextField, IconButton } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import { styled } from '@mui/material/styles';
import { stopPropagation } from '../utils';

type Props = {
  value: string;
  onSave: (value: string) => Promise<any>;
};

const Container = styled('div')(({ theme }) => ({
  display: 'flex',
  flexDirection: 'row',
  alignItems: 'center',
}));

const Field = styled(TextField)(({ theme }) => ({
  flexGrow: 1,
}));

const FieldTypography = styled(Typography)(({ theme }) => ({
  flexGrow: 1,
}));

const EditableField: React.FC<Props> = ({ value, onSave }) => {
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
    <Container>
      {editing ? (
        <React.Fragment>
          <Field
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
          <FieldTypography>{value}</FieldTypography>
          <IconButton onClick={stopPropagation(onEditClick)} size="large">
            <EditIcon />
          </IconButton>
        </React.Fragment>
      )}
    </Container>
  );
};

export default EditableField;
