import React, { useEffect, useState } from 'react';

import { useParams as useUrlParams, useNavigate } from 'react-router-dom';

import useLocalStorageState from 'use-local-storage-state';

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
  CardActions,
  Button,
  IconButton,
} from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import CompleteIcon from '@mui/icons-material/CheckCircle';
import ImageIcon from '@mui/icons-material/Image';
import TransferIcon from '@mui/icons-material/CompareArrows';
import CountIcon from '@mui/icons-material/BlurOn';
import OutputIcon from '@mui/icons-material/Terminal';
import LeftIcon from '@mui/icons-material/ArrowLeft';
import RightIcon from '@mui/icons-material/ArrowRight';
import { pink } from '@mui/material/colors';
import Tooltip from '@mui/material/Tooltip';
import humanizeDuration from 'humanize-duration';
import { DateTime } from 'luxon';

import { useAppDispatch, useAppSelector } from '../app/hooks';
import { staticURL } from '../client';
import { getScan, scansSelector, patchScan } from '../features/scans';
import {
  machineState,
  machineSelectors,
  getMachineState,
} from '../features/machines';
import LocationComponent from '../components/location';
import { MAX_LOG_FILES } from '../constants';
import EditableField from '../components/editable-field';
import { IdType, JobType, Scan, ScanJob } from '../types';
import JobStateComponent from '../components/job-state';
import TransferDialog from '../components/transfer-dialog';
import CountDialog from '../components/count-dialog';
import { createJob } from '../features/jobs/api';
import { RemoveScanFilesConfirmDialog } from '../components/scan-confirm-dialog';
import JobOutputDialog from '../components/job-output';
import { isNil } from '../utils';
import { SCANS_PATH } from '../routes';
import { canRunJobs } from '../utils/machine';

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
  noImage: {
    color: pink.A400,
  },
  stateCell: {
    width: '3rem',
  },
  stateContent: {
    display: 'flex',
    alignItems: 'end',
  },
  spacer: {
    flexGrow: 1,
  },
}));

type Props = {};

function jobTypeToIcon(type: JobType) {
  if (type === JobType.Count) {
    return CountIcon;
  } else if (type === JobType.Transfer) {
    return TransferIcon;
  } else {
    throw new Error('Unknown job type');
  }
}

const ScanPage: React.FC<Props> = () => {
  const classes = useStyles();

  const scanIdParam = useUrlParams().scanId;

  const scanId = parseInt(scanIdParam as string);

  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const [jobDialog, setJobDialog] = useState<JobType | undefined>();
  const [jobOutputDialog, setJobOutputDialog] = useState<ScanJob | undefined>();
  const [scanFilesToRemove, setScanFilesToRemove] = React.useState<Scan | null>(
    null
  );
  const [onScanFilesRemovalConfirm, setOnScanFilesRemovalConfirm] =
    React.useState<(params: { [key: string]: any } | undefined) => void>();

  const machines = useAppSelector((state) =>
    machineSelectors.selectAll(machineState(state))
  );
  const machineNames = machines.map((machine) => machine.name);
  const [machine, setMachine] = useLocalStorageState<string>('machine', {
    defaultValue: machines.length > 0 ? machines[0].name : '',
  });

  useEffect(() => {
    dispatch(getScan({ id: scanId }));
  }, [dispatch, scanId]);

  const onSaveNotes = (id: IdType, notes: string) => {
    return dispatch(patchScan({ id, updates: { notes } }));
  };

  const fetchMachineStates = () => {
    machines.forEach((machine) => {
      dispatch(getMachineState(machine));
    });
  };

  const onTransferClick = () => {
    fetchMachineStates();
    setJobDialog(JobType.Transfer);
  };

  const onCountClick = () => {
    fetchMachineStates();
    setJobDialog(JobType.Count);
  };

  const onJobClose = () => {
    setJobDialog(undefined);
  };

  const onJobSubmit = (type: JobType, machine: string, params: any) => {
    return createJob(type, scanId, machine, params);
  };

  const onJobOutputClick = (job: ScanJob) => {
    setJobOutputDialog(job);
  };

  const onJobOutputClose = () => {
    setJobOutputDialog(undefined);
  };

  const allowRunningJobs = () => {
    let canRun = false;

    for (let m of machines) {
      if (m.name === machine) {
        canRun = canRunJobs(m.status);
        break;
      }
    }

    return canRun;
  };

  const confirmScanRemoval = (scan: Scan) => {
    return new Promise<boolean>((resolve) => {
      setScanFilesToRemove(scan);

      setOnScanFilesRemovalConfirm(() => (params: { [key: string]: any }) => {
        const { confirm } = params;
        resolve(confirm);
        setScanFilesToRemove(null);
      });
    });
  };

  const scan = useAppSelector((state) =>
    scansSelector.selectById(state, scanId)
  );

  const onNavigateNext = () => {
    navigate(`${SCANS_PATH}/${scan?.nextScanId}`);
  };

  const onNavigatePrev = () => {
    navigate(`${SCANS_PATH}/${scan?.prevScanId}`);
  };

  if (scan === undefined) {
    return null;
  }

  return (
    <React.Fragment>
      <Card className={classes.card}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={4} md={3}>
              {scan.haadf_path ? (
                <img
                  src={`${staticURL}${scan.haadf_path}`}
                  alt="scan thumbnail"
                  className={classes.image}
                />
              ) : (
                <ImageIcon
                  className={`${classes.image} ${classes.noImage}`}
                  color="secondary"
                />
              )}
            </Grid>
            <Grid item xs={12} sm={8} md={9}>
              <Table>
                <TableBody>
                  <TableRow>
                    <TableCell className={classes.headCell}>Scan ID</TableCell>
                    <TableCell align="right">{scan.scan_id}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className={classes.headCell}>Location</TableCell>
                    <TableCell align="right">
                      <LocationComponent
                        confirmRemoval={confirmScanRemoval}
                        scan={scan}
                        locations={scan.locations}
                        machines={machineNames}
                      />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className={classes.headCell}>Created</TableCell>
                    <TableCell align="right">
                      <Tooltip title={scan.created} followCursor>
                        <div>
                          {DateTime.fromISO(scan.created).toLocaleString(
                            DateTime.DATETIME_FULL
                          )}
                        </div>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className={classes.headCell}>Progress</TableCell>
                    <TableCell align="right">
                      {scan.log_files < MAX_LOG_FILES ? (
                        <LinearProgress
                          variant="determinate"
                          value={(100 * scan.log_files) / MAX_LOG_FILES}
                        />
                      ) : (
                        <CompleteIcon color="primary" />
                      )}
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
                <TableCell align="right">
                  <EditableField
                    value={scan.notes || ''}
                    onSave={(value) => onSaveNotes(scan.id, value)}
                  />
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
        <CardActions>
          <Button
            onClick={onTransferClick}
            size="small"
            color="primary"
            variant="outlined"
            startIcon={<TransferIcon />}
          >
            Transfer
          </Button>
          <Button
            onClick={onCountClick}
            size="small"
            color="primary"
            variant="outlined"
            startIcon={<CountIcon />}
          >
            Count
          </Button>
          <div className={classes.spacer}></div>
          <Button
            onClick={onNavigatePrev}
            size="small"
            color="primary"
            variant="outlined"
            startIcon={<LeftIcon />}
            disabled={isNil(scan.prevScanId)}
          >
            Prev Scan
          </Button>
          <Button
            onClick={onNavigateNext}
            size="small"
            color="primary"
            variant="outlined"
            endIcon={<RightIcon />}
            disabled={isNil(scan.nextScanId)}
          >
            Next Scan
          </Button>
        </CardActions>
      </Card>

      <Card>
        <CardHeader title="Jobs"></CardHeader>
        <CardContent>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell className={classes.headCell}>ID</TableCell>
                <TableCell className={classes.headCell}>Machine</TableCell>
                <TableCell className={classes.headCell}>Type</TableCell>
                <TableCell className={classes.headCell}>Slurm ID</TableCell>
                <TableCell className={classes.headCell}>Elapsed</TableCell>
                <TableCell className={classes.headCell} align="right">
                  State
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {[...scan.jobs]
                .sort((a, b) => b.id - a.id)
                .map((job) => {
                  const Icon = jobTypeToIcon(job.job_type);
                  return (
                    <TableRow key={job.id}>
                      <TableCell>{job.id}</TableCell>
                      <TableCell>{job.machine}</TableCell>
                      <TableCell title={job.job_type}>
                        <Icon />
                      </TableCell>
                      <TableCell>{job.slurm_id}</TableCell>
                      <TableCell>
                        {humanizeDuration(job.elapsed * 1000)}
                      </TableCell>
                      <TableCell className={classes.stateCell} align="right">
                        <div className={classes.stateContent}>
                          <IconButton
                            disabled={!job.output}
                            onClick={() => onJobOutputClick(job)}
                          >
                            <OutputIcon />
                          </IconButton>
                          <JobStateComponent state={job.state} />
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <TransferDialog
        open={jobDialog === JobType.Transfer}
        machines={machines}
        machine={machine}
        setMachine={setMachine}
        onClose={onJobClose}
        onSubmit={(params) => onJobSubmit(JobType.Transfer, machine, params)}
        canRun={allowRunningJobs}
      />

      <CountDialog
        open={jobDialog === JobType.Count}
        machines={machines}
        machine={machine}
        setMachine={setMachine}
        onClose={onJobClose}
        onSubmit={(params: any) => onJobSubmit(JobType.Count, machine, params)}
        canRun={allowRunningJobs}
      />

      <RemoveScanFilesConfirmDialog
        onConfirm={onScanFilesRemovalConfirm}
        scan={scanFilesToRemove}
        machines={machineNames}
      />

      <JobOutputDialog
        open={!!jobOutputDialog}
        onClose={onJobOutputClose}
        job={jobOutputDialog}
      />
    </React.Fragment>
  );
};

export default ScanPage;
