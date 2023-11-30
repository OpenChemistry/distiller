import styled from '@emotion/styled';
import { Add } from '@mui/icons-material';
import {
  Box,
  Chip,
  Divider,
  Fab,
  List,
  ListItem,
  TablePagination,
} from '@mui/material';
import { groupBy, isNil } from 'lodash';
import { DateTime } from 'luxon';
import React, { useCallback, useEffect, useState } from 'react';
import useLocalStorageState from 'use-local-storage-state';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { ScansToolbar } from '../components/scans-toolbar';
import SessionCard from '../components/session-card';
import StreamingDialog from '../components/streaming-dialog';
import {
  allJobsSelector,
  getJobs,
  selectJobsByDateAndTypes,
  totalCount,
} from '../features/jobs';
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
import { getJobScans } from '../features/scans';
import { useUrlState } from '../routes/url-state';
import {
  IdType,
  Job,
  JobType,
  PendingJobStates,
  RunningJobStates,
} from '../types';
import { canRunJobs } from '../utils/machine';
import {
  dateTimeDeserializer,
  dateTimeSerializer,
  intDeserializer,
  intSerializer,
} from './scans';

const DateChip: React.FC<{ date: string }> = ({ date }) => (
  <Chip
    label={date}
    variant="filled"
    color="primary"
    sx={{
      height: 'auto',
      padding: '1%',
      fontSize: '1.2rem',
    }}
  />
);

const FabBox = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'right',
  '& button': { m: 2 },
}));

const SessionsPage: React.FC = () => {
  // Job type to display (always streaming)
  let jobType = JobType.Streaming;

  // Redux Hooks
  const dispatch = useAppDispatch();

  // URL state management for page and rowsPerPage
  const [page, setPage] = useUrlState(
    'page',
    0,
    intSerializer,
    intDeserializer,
  );
  const [rowsPerPage, setRowsPerPage] = useUrlState(
    'rowsPerPage',
    10,
    intSerializer,
    intDeserializer,
  );

  // URL state management for date filters
  const [startDateFilter, setStartDateFilter] = useUrlState<DateTime | null>(
    'startDate',
    null,
    dateTimeSerializer,
    dateTimeDeserializer,
  );

  const [endDateFilter, setEndDateFilter] = useUrlState<DateTime | null>(
    'endDate',
    null,
    dateTimeSerializer,
    dateTimeDeserializer,
  );

  // Selectors
  const totalJobs = useAppSelector(totalCount);
  const allJobs = useAppSelector(allJobsSelector);
  const microscopes = useAppSelector((state) =>
    microscopesSelectors.selectAll(microscopesState(state)),
  );
  const machines = useAppSelector((state) =>
    machineSelectors.selectAll(machineState(state)),
  );
  const jobs = useAppSelector(
    selectJobsByDateAndTypes(startDateFilter, endDateFilter, [jobType]),
  ).sort((a, b) => b.id - a.id);

  const start = page * rowsPerPage;
  const end = start + rowsPerPage;

  const jobsOnThisPage = jobs.slice(start, end);

  const anyStreamingJobs = allJobs.some((job) => {
    if (job && job.state) {
      if (job.job_type === JobType.Streaming) {
        // Check if job is in pending and has slurm id, or is in running state
        if (
          (PendingJobStates.has(job.state) && job.slurm_id) ||
          RunningJobStates.has(job.state)
        ) {
          return true;
        }
      }
    }
    return false;
  });

  // Jobs
  const [hoveredJobId, setHoveredJobId] = useState<IdType | null>(null);
  const jobsGroupedByDate = groupBy(jobsOnThisPage, (job) =>
    // @ts-ignore: Object is possibly 'null'.
    job.submit
      ? DateTime.fromISO(job.submit)?.toISO()?.split('T')[0]
      : 'Queued',
  );

  // Machine
  const [machine, setMachine] = useLocalStorageState<string>('machine', {
    defaultValue: machines.length > 0 ? machines[0].name : '',
  });

  // Microscope
  let microscopeId: IdType | undefined =
    microscopes.length > 0 ? microscopes[0].id : undefined;

  // Start job dialog
  const [jobDialog, setJobDialog] = useState<JobType | undefined>();

  // Event Handlers
  const onChangePage = (
    event: React.MouseEvent<HTMLButtonElement> | null,
    page: number,
  ) => setPage(page);
  const onChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>,
  ) => {
    const jobsPerPage = +event.target.value;
    setRowsPerPage(jobsPerPage);
    setPage(0);
  };
  const onStartStreamingClick = () => {
    fetchMachineStates();
    setJobDialog(JobType.Streaming);
  };
  const onJobClose = () => setJobDialog(undefined);
  const onJobSubmit = async (type: JobType, machine: string, params: any) => {
    const returnedJob: Job = await createJob(type, null, machine, params);
    return returnedJob;
  };
  const onStartDate = useCallback(
    (date: DateTime | null) => {
      setPage(0);
      setStartDateFilter(date);
    },
    [setPage, setStartDateFilter],
  );
  const onEndDate = useCallback(
    (date: DateTime | null) => {
      setPage(0);
      setEndDateFilter(date);
    },
    [setPage, setEndDateFilter],
  );

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
  const fetchMachineStates = () =>
    machines.forEach((machine) => dispatch(getMachineState(machine)));

  // Effects
  useEffect(() => {
    if (hoveredJobId !== null) {
      dispatch(getJobScans({ jobId: hoveredJobId }));
    }
  }, [dispatch, hoveredJobId]);

  useEffect(() => {
    if (microscopeId === undefined) return;
    dispatch(
      getJobs({
        skip: page * rowsPerPage,
        limit: rowsPerPage,
        jobType: jobType,
        start: startDateFilter || undefined,
        end: endDateFilter || undefined,
      }),
    );
  }, [
    dispatch,
    page,
    rowsPerPage,
    startDateFilter,
    endDateFilter,
    jobType,
    microscopeId,
  ]);

  useEffect(() => {
    if (microscopeId === undefined) return;
    const result = microscopes.filter((m) => m.id === microscopeId);
    if (result.length === 1) document.title = `distiller - ${result[0].name}`;
  }, [microscopes, microscopeId]);

  return (
    <React.Fragment>
      <FabBox>
        <Fab
          color="primary"
          aria-label="start"
          disabled={anyStreamingJobs}
          onClick={onStartStreamingClick}
        >
          <Add />
        </Fab>
      </FabBox>
      {Object.entries(jobsGroupedByDate)
        .sort(
          ([dateA], [dateB]) =>
            new Date(dateB).getTime() - new Date(dateA).getTime(),
        )
        .map(([date, jobs], index, arr) => (
          <Box key={date} mb={3}>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <DateChip date={date} />
              {index === 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <ScansToolbar
                    startDate={startDateFilter}
                    endDate={endDateFilter}
                    onStartDate={onStartDate}
                    onEndDate={onEndDate}
                    showFilterBadge={
                      !isNil(startDateFilter) || !isNil(endDateFilter)
                    }
                    showExportButton={false}
                  />
                </Box>
              )}
            </Box>
            <List>
              {jobs.map((job) => (
                <ListItem key={job.id}>
                  <SessionCard
                    key={job.id}
                    jobId={job.id}
                    setHoveredJobId={setHoveredJobId}
                    isHoverable={true}
                    compactMode={true}
                  />
                </ListItem>
              ))}
            </List>
            {index < arr.length - 1 && <Divider variant="middle" />}
          </Box>
        ))}
      {Object.keys(jobsGroupedByDate).length === 0 && (
        <ScansToolbar
          startDate={startDateFilter}
          endDate={endDateFilter}
          onStartDate={onStartDate}
          onEndDate={onEndDate}
          showFilterBadge={!isNil(startDateFilter) || !isNil(endDateFilter)}
          showExportButton={false}
        />
      )}
      <TablePagination
        rowsPerPageOptions={[10, 20, 100]}
        component="div"
        count={totalJobs}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={onChangePage}
        onRowsPerPageChange={onChangeRowsPerPage}
        labelRowsPerPage="Sessions per page"
      />
      <StreamingDialog
        open={jobDialog === JobType.Streaming}
        machines={machines}
        machine={machine}
        setMachine={setMachine}
        onClose={onJobClose}
        onSubmit={(params) => onJobSubmit(JobType.Streaming, machine, params)}
        canRun={allowRunningJobs}
      />
    </React.Fragment>
  );
};

export default SessionsPage;
