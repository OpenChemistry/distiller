import React, {useEffect} from 'react';

import { Table, TableHead, TableBody, TableRow, TableCell, TableContainer, Paper, LinearProgress } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import CompleteIcon from '@material-ui/icons/CheckCircle';

import { useAppDispatch, useAppSelector } from '../app/hooks';
import { getScans, scansSelector } from '../features/scans';
import { MAX_LOG_FILES } from '../constants';


const useStyles = makeStyles((theme) => ({
  headCell: {
    fontWeight: 600
  },
}));

const ScansPage: React.FC = () => {
  const classes = useStyles();

  const dispatch = useAppDispatch();
  const scans = useAppSelector(scansSelector.selectAll);

  useEffect(() => {
    dispatch(getScans());
  }, [dispatch])

  return (
    <React.Fragment>
      <TableContainer component={Paper}>
        <Table aria-label='scans table'>
          <TableHead>
            <TableRow>
              <TableCell className={classes.headCell}>ID</TableCell>
              <TableCell className={classes.headCell}>Scan ID</TableCell>
              <TableCell className={classes.headCell}>Created</TableCell>
              <TableCell className={classes.headCell} align='right'>Progress</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {scans.map(scan => (
              <TableRow key={scan.id}>
                <TableCell>{scan.id}</TableCell>
                <TableCell>{scan.scan_id}</TableCell>
                <TableCell>{scan.created}</TableCell>
                <TableCell align='right'>
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
