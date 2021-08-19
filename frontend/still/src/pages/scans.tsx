import React, {useEffect} from 'react';

import { Table, TableHead, TableBody, TableRow, TableCell, TableContainer, Paper, LinearProgress } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import CompleteIcon from '@material-ui/icons/CheckCircle';

import { useAppDispatch, useAppSelector } from '../app/hooks';
import { getScans, patchScan, scansSelector } from '../features/scans';
import { MAX_LOG_FILES } from '../constants';
import EditableField from '../components/editable-field';
import { IdType } from '../types';


const useStyles = makeStyles((theme) => ({
  headCell: {
    fontWeight: 600,
  },
  notesCell: {
    width: '100%',
  },
  progressCell: {
    width: '5rem',
  }
}));

const ScansPage: React.FC = () => {
  const classes = useStyles();

  const dispatch = useAppDispatch();
  const scans = useAppSelector(scansSelector.selectAll);

  useEffect(() => {
    dispatch(getScans());
  }, [dispatch])

  const onSaveNotes = (id: IdType, notes: string) => {
    return dispatch(patchScan({id, updates: {notes}}));
  }

  return (
    <React.Fragment>
      <TableContainer component={Paper}>
        <Table aria-label='scans table'>
          <TableHead>
            <TableRow>
              <TableCell className={classes.headCell}>ID</TableCell>
              <TableCell className={classes.headCell}>Scan ID</TableCell>
              <TableCell className={classes.headCell}>Notes</TableCell>
              <TableCell className={classes.headCell}>Created</TableCell>
              <TableCell className={classes.headCell} align='right'>Progress</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {scans.map(scan => (
              <TableRow key={scan.id}>
                <TableCell>{scan.id}</TableCell>
                <TableCell>{scan.scan_id}</TableCell>
                <TableCell className={classes.notesCell}>
                  <EditableField
                    value={scan.notes || ''}
                    onSave={(value) => onSaveNotes(scan.id, value)}
                  />
                </TableCell>
                <TableCell>{scan.created}</TableCell>
                <TableCell align='right' className={classes.progressCell}>
                  {scan.log_files < MAX_LOG_FILES
                    ? <LinearProgress variant='determinate' value={100 * scan.log_files / MAX_LOG_FILES}/>
                    : <CompleteIcon color='primary'/>
                  }
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </React.Fragment>
  )
}

export default ScansPage;
