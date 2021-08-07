import React, {useEffect} from 'react';

import { Typography, Table, TableHead, TableBody, TableRow, TableCell, TableContainer, Paper } from '@material-ui/core';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { getScans, scansSelector } from '../features/scans';

const ScansPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const scans = useAppSelector(scansSelector.selectAll);

  useEffect(() => {
    dispatch(getScans());
  }, [dispatch])

  return (
    <React.Fragment>
      <Typography variant='h3'>Scans</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Scan ID</TableCell>
              <TableCell>Log Files</TableCell>
              <TableCell align='right'>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {scans.map(scan => (
              <TableRow key={scan.id}>
                <TableCell>{scan.id}</TableCell>
                <TableCell>{scan.scan_id}</TableCell>
                <TableCell>{scan.log_files}</TableCell>
                <TableCell align='right'>{scan.created}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </React.Fragment>
  )
}

export default ScansPage;
