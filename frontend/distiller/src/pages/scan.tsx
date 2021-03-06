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
import { styled } from '@mui/material/styles';
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
import { IdType, JobType, Scan, ScanJob, Microscope } from '../types';
import JobStateComponent from '../components/job-state';
import TransferDialog from '../components/transfer-dialog';
import CountDialog from '../components/count-dialog';
import { createJob } from '../features/jobs/api';
import { RemoveScanFilesConfirmDialog } from '../components/scan-confirm-dialog';
import JobOutputDialog from '../components/job-output';
import { isNil } from '../utils';
import { SCANS } from '../routes';
import { canRunJobs } from '../utils/machine';
import MetadataComponent from '../components/metadata';
import {
  microscopesSelectors,
  microscopesState,
} from '../features/microscopes';
import { canonicalMicroscopeName } from '../utils/microscopes';

const TableHeaderCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 600,
}));

const ThumbnailImage = styled('img')(({ theme }) => ({
  width: '100%',
  height: '100%',
  objectFit: 'cover',
  cursor: 'pointer',
}));

const NoThumbnailImageIcon = styled(ImageIcon)(({ theme }) => ({
  width: '60%',
  height: '60%',
  objectFit: 'cover',
  color: pink.A400,
  cursor: 'pointer',
}));

const TableStateCell = styled(TableCell)(({ theme }) => ({
  width: '3rem',
}));

const StateContent = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'end',
}));

const Spacer = styled('div')(({ theme }) => ({
  flexGrow: 1,
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

  const microscopes = useAppSelector((state) =>
    microscopesSelectors.selectAll(microscopesState(state))
  );

  const microscopesByCanonicalName = microscopes.reduce(
    (obj: { [key: string]: Microscope }, microscope) => {
      obj[canonicalMicroscopeName(microscope.name)] = microscope;

      return obj;
    },
    {}
  );

  let microscope: Microscope | null = null;
  const microscopeParam = useUrlParams().microscope;
  if (microscopeParam !== undefined) {
    const canonicalName = canonicalMicroscopeName(microscopeParam as string);

    if (canonicalName in microscopesByCanonicalName) {
      microscope = microscopesByCanonicalName[canonicalName];
    }
  }

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
    if (microscope === null) {
      return;
    }
    const microscopeName = canonicalMicroscopeName(microscope.name);

    navigate(`/${microscopeName}/${SCANS}/${scan?.nextScanId}`);
  };

  const onNavigatePrev = () => {
    if (microscope === null) {
      return;
    }
    const microscopeName = canonicalMicroscopeName(microscope.name);

    navigate(`/${microscopeName}/${SCANS}/${scan?.prevScanId}`);
  };

  if (scan === undefined || microscope === null) {
    return null;
  }

  const actions = microscope.config['actions'];

  return (
    <React.Fragment>
      <Card sx={{ marginBottom: '2rem' }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={4} md={3}>
              {scan.image_path ? (
                <ThumbnailImage
                  src={`${staticURL}${scan.image_path}`}
                  alt="scan thumbnail"
                />
              ) : (
                <NoThumbnailImageIcon color="secondary" />
              )}
            </Grid>
            <Grid item xs={12} sm={8} md={9}>
              <Table>
                <TableBody>
                  {scan.scan_id && (
                    <TableRow>
                      <TableHeaderCell>Detector Scan ID</TableHeaderCell>
                      <TableCell align="right">{scan.scan_id}</TableCell>
                    </TableRow>
                  )}
                  <TableRow>
                    <TableHeaderCell>Location</TableHeaderCell>
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
                    <TableHeaderCell>Created</TableHeaderCell>
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
                  {scan.scan_id && (
                    <TableRow>
                      <TableHeaderCell>Progress</TableHeaderCell>
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
                  )}
                </TableBody>
              </Table>
            </Grid>
          </Grid>
          <MetadataComponent scan={scan} />
          <Table>
            <TableBody>
              <TableRow>
                <TableHeaderCell>Notes</TableHeaderCell>
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
          {actions.indexOf('transfer') !== -1 && (
            <Button
              onClick={onTransferClick}
              size="small"
              color="primary"
              variant="outlined"
              startIcon={<TransferIcon />}
            >
              Transfer
            </Button>
          )}
          {actions.indexOf('count') !== -1 && (
            <Button
              onClick={onCountClick}
              size="small"
              color="primary"
              variant="outlined"
              startIcon={<CountIcon />}
            >
              Count
            </Button>
          )}
          <Spacer />
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
      {actions.length !== 0 && (
        <Card>
          <CardHeader title="Jobs"></CardHeader>
          <CardContent>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>ID</TableHeaderCell>
                  <TableHeaderCell>Machine</TableHeaderCell>
                  <TableHeaderCell>Type</TableHeaderCell>
                  <TableHeaderCell>Slurm ID</TableHeaderCell>
                  <TableHeaderCell>Elapsed</TableHeaderCell>
                  <TableHeaderCell align="right">State</TableHeaderCell>
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
                        <TableStateCell align="right">
                          <StateContent>
                            <IconButton
                              disabled={!job.output}
                              onClick={() => onJobOutputClick(job)}
                            >
                              <OutputIcon />
                            </IconButton>
                            <JobStateComponent state={job.state} />
                          </StateContent>
                        </TableStateCell>
                      </TableRow>
                    );
                  })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

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
