import React, { useEffect, useState } from 'react';
import { useNavigate, useParams as useUrlParams } from 'react-router-dom';

import LeftIcon from '@mui/icons-material/ArrowLeft';
import RightIcon from '@mui/icons-material/ArrowRight';
import CountIcon from '@mui/icons-material/BlurOn';
import CompleteIcon from '@mui/icons-material/CheckCircle';
import TransferIcon from '@mui/icons-material/CompareArrows';
import OutputIcon from '@mui/icons-material/Terminal';
import TextSnippetOutlined from '@mui/icons-material/TextSnippetOutlined';
import {
  Button,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  Grid,
  IconButton,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';
import CircularProgress from '@mui/material/CircularProgress';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Tooltip from '@mui/material/Tooltip';
import { styled } from '@mui/material/styles';
import { Box } from '@mui/system';
import humanizeDuration from 'humanize-duration';
import { DateTime } from 'luxon';
import useLocalStorageState from 'use-local-storage-state';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { staticURL } from '../client';
import CountDialog from '../components/count-dialog';
import EditableField from '../components/editable-field';
import ImageDialog from '../components/image-dialog';
import JobOutputDialog from '../components/job-output';
import JobStateComponent from '../components/job-state';
import LocationComponent from '../components/location';
import MetadataComponent from '../components/metadata';
import { NoThumbnailImageIcon } from '../components/no-thumbnail-image-icon';
import { RemoveScanFilesConfirmDialog } from '../components/scan-confirm-dialog';
import { ThumbnailImage } from '../components/thumbnail-image';
import TransferDialog from '../components/transfer-dialog';
import { JUPYTER_USER_REDIRECT_URL } from '../constants';
import { getScanJobs, jobsByScanIdAndTypes } from '../features/jobs';
import { createJob } from '../features/jobs/api';
import {
  getMachineState,
  machineSelectors,
  machineState,
} from '../features/machines';
import {
  microscopesSelectors,
  microscopesState,
} from '../features/microscopes';
import { getNotebooks, selectNotebooks } from '../features/notebooks';
import { fetchOrCreateNotebook } from '../features/notebooks/api';
import { getScan, patchScan, scansSelector } from '../features/scans';
import { SCANS, SESSIONS } from '../routes';
import { IdType, Job, JobType, Microscope, Scan } from '../types';
import { isNil, stopPropagation } from '../utils';
import { canRunJobs } from '../utils/machine';
import { canonicalMicroscopeName } from '../utils/microscopes';

const TableHeaderCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 600,
}));

const TableStateCell = styled(TableCell)(({ theme }) => ({
  width: '3rem',
}));

const StateContent = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'end',
  justifyContent: 'center',
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
  const [maximizeImg, setMaximizeImg] = useState(false);
  const [notebookLoading, setNotebookLoading] = React.useState(false);
  const [notebookMenuAnchorEl, setNotebookMenuAnchorEl] =
    React.useState<null | HTMLElement>(null);
  const showNotebookMenu = Boolean(notebookMenuAnchorEl);
  const scanIdParam = useUrlParams().scanId;

  const scanId = parseInt(scanIdParam as string);
  const scan = useAppSelector((state) =>
    scansSelector.selectById(state, scanId),
  );
  const jobs = useAppSelector(
    jobsByScanIdAndTypes(scanId, [JobType.Count, JobType.Transfer]),
  );

  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const [jobDialog, setJobDialog] = useState<JobType | undefined>();
  const [jobOutputDialog, setJobOutputDialog] = useState<Job | undefined>();
  const [scanFilesToRemove, setScanFilesToRemove] = React.useState<Scan | null>(
    null,
  );
  const [onScanFilesRemovalConfirm, setOnScanFilesRemovalConfirm] =
    React.useState<(params: { [key: string]: any } | undefined) => void>();

  const machines = useAppSelector((state) =>
    machineSelectors.selectAll(machineState(state)),
  );
  const machineNames = machines.map((machine) => machine.name);
  const [machine, setMachine] = useLocalStorageState<string>('machine', {
    defaultValue: machines.length > 0 ? machines[0].name : '',
  });

  const microscopes = useAppSelector((state) =>
    microscopesSelectors.selectAll(microscopesState(state)),
  );

  const microscopesByCanonicalName = microscopes.reduce(
    (obj: { [key: string]: Microscope }, microscope) => {
      obj[canonicalMicroscopeName(microscope.name)] = microscope;

      return obj;
    },
    {},
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

  // This effect handles fetching jobs related to the scan
  useEffect(() => {
    if (scanId) {
      dispatch(getScanJobs({ scanId: scanId }));
    }
  }, [dispatch, scanId]);

  useEffect(() => {
    dispatch(getNotebooks());
  }, [dispatch]);

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

  const onJobOutputClick = (job: Job) => {
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

  const notebooks = useAppSelector((state) => selectNotebooks(state));

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

  const jobId = useUrlParams().jobId;
  const onNavigateBack = () => {
    if (microscope === null) {
      return;
    }
    const microscopeName = canonicalMicroscopeName(microscope.name);
    if (jobId) {
      navigate(`/${microscopeName}/${SESSIONS}/${jobId}`);
    } else {
      navigate(`/${microscopeName}/${SCANS}`);
    }
  };

  if (scan === undefined || microscope === null) {
    return null;
  }

  const actions = microscope.config['actions'];

  const onImgClick = (scan: Scan) => {
    setMaximizeImg(true);
  };

  const onCloseDialog = () => {
    setMaximizeImg(false);
  };

  const onLaunchNotebook = (name: string) => {
    setNotebookLoading(true);
    setNotebookMenuAnchorEl(null);
    fetchOrCreateNotebook(name, scan.id)
      .then((notebook) => {
        window.open(`${JUPYTER_USER_REDIRECT_URL}${notebook.path}`, '_blank');
      })
      .catch((error) => {
        // Should display to user
        console.error('Notebook creation failed');
      })
      .finally(() => setNotebookLoading(false));
  };

  return (
    <React.Fragment>
      <Button
        onClick={onNavigateBack}
        size="small"
        color="primary"
        sx={{ mb: 2 }}
        variant="outlined"
      >
        {jobId ? `Session ${jobId}` : 'Scans'}
      </Button>
      <Card sx={{ marginBottom: '2rem' }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={4} md={3}>
              {scan.image_path ? (
                <ThumbnailImage
                  src={`${staticURL}${scan.image_path}`}
                  alt="scan thumbnail"
                  onClick={stopPropagation(() => onImgClick(scan))}
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
                    <TableHeaderCell>Distiller Scan ID</TableHeaderCell>
                    <TableCell align="right">{scan.id}</TableCell>
                  </TableRow>
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
                            DateTime.DATETIME_FULL,
                          )}
                        </div>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                  {scan.scan_id && (
                    <TableRow>
                      <TableHeaderCell>Progress</TableHeaderCell>
                      <TableCell align="right">
                        {scan.progress < 100 ? (
                          <LinearProgress
                            variant="determinate"
                            value={scan.progress}
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
          {notebooks && (
            <Box sx={{ m: 1, position: 'relative' }}>
              <Button
                onClick={(event: React.MouseEvent<HTMLButtonElement>) => {
                  setNotebookMenuAnchorEl(event.currentTarget);
                }}
                size="small"
                color="primary"
                variant="outlined"
                startIcon={<TextSnippetOutlined />}
              >
                Launch notebook
              </Button>
              {notebookLoading && (
                <CircularProgress
                  size={24}
                  sx={{
                    color: 'primary',
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    marginTop: '-12px',
                    marginLeft: '-12px',
                  }}
                />
              )}
              <Menu
                anchorEl={notebookMenuAnchorEl}
                open={showNotebookMenu}
                onClose={() => {
                  setNotebookMenuAnchorEl(null);
                }}
                MenuListProps={{
                  'aria-labelledby': 'basic-button',
                }}
              >
                {notebooks.map((name: string) => {
                  return (
                    <MenuItem
                      onClick={() => {
                        onLaunchNotebook(name);
                      }}
                    >
                      {name.toUpperCase()}
                    </MenuItem>
                  );
                })}
              </Menu>
            </Box>
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
                {[...jobs]
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
                          {humanizeDuration(
                            job.elapsed ? job.elapsed * 1000 : 0,
                          )}
                        </TableCell>
                        <TableStateCell align="right">
                          <StateContent>
                            <IconButton
                              disabled={!job.output}
                              onClick={() => onJobOutputClick(job)}
                            >
                              <OutputIcon />
                            </IconButton>
                            {job.state && (
                              <JobStateComponent state={job.state} />
                            )}
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
      <ImageDialog
        open={maximizeImg}
        src={`${staticURL}${scan.image_path!}`}
        alt="scan image"
        handleClose={onCloseDialog}
      />
    </React.Fragment>
  );
};

export default ScanPage;
