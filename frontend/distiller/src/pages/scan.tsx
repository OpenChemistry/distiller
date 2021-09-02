import React, { useEffect } from 'react';

import { useParams as useUrlParams } from 'react-router-dom';

import {
  Card,
  Grid,
  Table,
  TableRow,
  TableBody,
  TableCell,
  LinearProgress,
  CardContent,
  TableHead,
  CardHeader,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import CompleteIcon from '@material-ui/icons/CheckCircle';
import ImageIcon from '@material-ui/icons/Image';

import { useAppDispatch, useAppSelector } from '../app/hooks';
import { staticURL } from '../client';
import { getScan, scansSelector, patchScan } from '../features/scans';
import LocationComponent from '../components/location';
import { MAX_LOG_FILES } from '../constants';
import EditableField from '../components/editable-field';
import { IdType } from '../types';
import JobStateComponent from '../components/job-state';

const useStyles = makeStyles((theme) => ({
  card: {
    marginBottom: '2rem',
  },
  headCell: {
    fontWeight: 600,
  },
  image: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
}));

type Props = {}
type UrlProps = {
    scanId: string;
}

const ScanPage: React.FC<Props> = () => {
  const classes = useStyles();

  const { scanId } = useUrlParams<UrlProps>();

  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(getScan({id: scanId}));
  }, [dispatch, scanId]);

  const onSaveNotes = (id: IdType, notes: string) => {
    return dispatch(patchScan({id, updates: {notes}}));
  }

  const scan = useAppSelector((state) => scansSelector.selectById(state, scanId));

  if (scan === undefined) {
    return null;
  }

  return <React.Fragment>
    <Card className={classes.card}>
      <CardContent>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={4} md={3}>
            {scan.haadf_path
              ? <img
                  src={`${staticURL}${scan.haadf_path}`}
                  alt='scan thumbnail'
                  className={classes.image}
                />
              : <ImageIcon className={classes.image} color='secondary'/>
            }
          </Grid>
          <Grid item xs={12} sm={8} md={9}>
            <Table>
              <TableBody>
                {/* <TableRow>
                  <TableCell className={classes.headCell}>ID</TableCell>
                  <TableCell align='right'>{scan.id}</TableCell>
                </TableRow> */}
                <TableRow>
                  <TableCell className={classes.headCell}>Scan ID</TableCell>
                  <TableCell align='right'>{scan.scan_id}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className={classes.headCell}>Location</TableCell>
                  <TableCell align='right'>
                    <LocationComponent locations={scan.locations}/>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className={classes.headCell}>Created</TableCell>
                  <TableCell align='right'>{scan.created}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className={classes.headCell}>Progress</TableCell>
                  <TableCell align='right'>
                    {scan.log_files < MAX_LOG_FILES
                      ? <LinearProgress variant='determinate' value={100 * scan.log_files / MAX_LOG_FILES}/>
                      : <CompleteIcon color='primary'/>
                    }
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Grid>
        </Grid>
        <Table>
          <TableBody>
            <TableRow>
              <TableCell className={classes.headCell}>Notes</TableCell>
              <TableCell align='right'>
                <EditableField
                  value={scan.notes || ''}
                  onSave={(value) => onSaveNotes(scan.id, value)}
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>

    <Card>
      <CardHeader title="Jobs">
      </CardHeader>
      <CardContent>
      <Table>
      <TableHead>
        <TableRow>
          <TableCell className={classes.headCell}>ID</TableCell>
          <TableCell className={classes.headCell}>Type</TableCell>
          <TableCell className={classes.headCell}>Slurm ID</TableCell>
          <TableCell className={classes.headCell} align='right'>State</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {scan.jobs.map((job) => {
          return (
            <TableRow key={job.id}>
              <TableCell>{job.id}</TableCell>
              <TableCell>{job.job_type}</TableCell>
              <TableCell>{job.slurm_id}</TableCell>
              <TableCell align='right'><JobStateComponent state={job.state}/></TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
      </CardContent>

    </Card>
  </React.Fragment>
}

export default ScanPage;
