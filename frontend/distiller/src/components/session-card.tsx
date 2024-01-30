import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import styled from '@emotion/styled';
import { Cancel } from '@mui/icons-material';
import OutputIcon from '@mui/icons-material/Terminal';
import {
  Card,
  CardContent,
  CardProps,
  IconButton,
  Typography,
} from '@mui/material';
import humanizeDuration from 'humanize-duration';
import { DateTime } from 'luxon';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { cancelJob, jobSelector, patchJob } from '../features/jobs';
import { scansByJobIdSelector } from '../features/scans';
import { machineSelectors, machineState } from '../features/machines';
import { SCANS, SESSIONS } from '../routes';
import {
  useUrlState,
  intSerializer,
  intDeserializer,
} from '../routes/url-state';
import {
  IdType,
  Job,
  PendingJobStates,
  RunningJobStates,
  Scan,
} from '../types';
import EditableField from './editable-field';
import ImageGallery from './image-gallery';
import JobOutputDialog from './job-output';
import JobStateComponent from './job-state';
import { ScansTableContainer } from './scans-table-container';

interface HoverCardProps extends CardProps {
  isHoverable?: boolean;
}

const StateContent = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
}));

const HoverCard = styled(({ isHoverable, ...props }: HoverCardProps) => (
  <Card {...props} />
))<HoverCardProps>(
  {
    width: '100%',
    transition: 'transform 0.15s ease-in-out',
    boxShadow: '0 4px 6px 0 hsla(0, 0%, 0%, 0.2)',
  },
  ({ isHoverable }) =>
    isHoverable
      ? {
          '&:hover': {
            transform: 'scale3d(1.05, 1.05, 1)',
          },
        }
      : {},
);

interface SessionCardProps {
  jobId: IdType;
  setHoveredJobId?: React.Dispatch<React.SetStateAction<IdType | null>>;
  isHoverable?: boolean | undefined;
  compactMode?: boolean | undefined;
}

// SessionCard Component
const SessionCard = React.memo(
  ({ jobId, setHoveredJobId, isHoverable, compactMode }: SessionCardProps) => {
    const navigate = useNavigate();
    const dispatch = useAppDispatch();
    const job = useAppSelector(jobSelector(jobId)) as Job;
    const microscopeName = useParams().microscope;

    const machines = useAppSelector((state) =>
      machineSelectors.selectAll(machineState(state)),
    );
    const machineNames = useMemo(
      () => machines.map((machine) => machine.name),
      [machines],
    );

    const [page, setPage] = useUrlState(
      'page',
      0,
      intSerializer,
      intDeserializer,
    );

    const [rowsPerPage, setRowsPerPage] = useUrlState(
      'rowsPerPage',
      20,
      intSerializer,
      intDeserializer,
    );

    const [selectedScanIDs] = useState<Set<IdType>>(new Set<IdType>());

    const handleMouseEnter = (event: React.MouseEvent<HTMLElement>) => {
      if (setHoveredJobId) setHoveredJobId(jobId);
    };

    const handleMouseLeave = () => {
      if (setHoveredJobId) setHoveredJobId(null);
    };

    const onSaveNotes = (id: IdType, notes: string) => {
      return dispatch(patchJob({ id, updates: { notes } }));
    };

    const [canceling, setCanceling] = useState(false);

    const [jobOutputDialog, setJobOutputDialog] = useState<Job | undefined>();
    const onJobOutputClick = (event: React.MouseEvent, job: Job) => {
      event.stopPropagation();
      setJobOutputDialog(job);
    };

    const onJobOutputClose = () => {
      setJobOutputDialog(undefined);
    };

    const handleCancelJob = (event: React.MouseEvent) => {
      event.stopPropagation(); // Prevent triggering of other click events
      setCanceling(true);
      dispatch(cancelJob({ id: job.id }));
    };

    useEffect(() => {
      if (job.state === 'CANCELLED') {
        setCanceling(false);
      }
    }, [job.state]);

    const onScanClick = (scan: Scan) => {
      navigate(`/${microscopeName}/${SESSIONS}/${jobId}/${SCANS}/${scan.id}`);
    };

    // Scans
    const scans = useAppSelector(scansByJobIdSelector(job.id));

    const scansInCurrentPage = useMemo(() => {
      const start = page * rowsPerPage;
      const end = start + rowsPerPage;

      return scans
        .sort((a, b) => b.created.localeCompare(a.created))
        .slice(start, end);
    }, [scans, page, rowsPerPage]);

    const displayIDs = useMemo(() => {
      const ids = new Set(scansInCurrentPage.map((scan) => scan.scan_id));

      return ids.size > 1 || !ids.has(null);
    }, [scansInCurrentPage]);

    const noop = useCallback(() => {}, []);

    const onScansPerPageChange = useCallback(
      (scansPerPage: number) => {
        setRowsPerPage(scansPerPage);
        setPage(0);
      },
      [setRowsPerPage, setPage],
    );

    const scansTableProps = {
      currentPage: page,
      scansPerPage: rowsPerPage,
      scansInCurrentPage,
      totalNumberOfScans: scans.length,
      displayIDs,
      selectedScanIDs,
      machineNames,
      onScanClick,
      onSelectAll: noop,
      onScanSelect: noop,
      onCurrentPageChange: setPage,
      onScansPerPageChange: onScansPerPageChange,
    };

    const isJobRunning =
      job.state &&
      ((PendingJobStates.has(job.state) && job.slurm_id) ||
        RunningJobStates.has(job.state));

    return (
      <React.Fragment>
        <HoverCard
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onClick={() => {
            if (isHoverable) navigate(`${job.id}`);
          }}
          isHoverable={isHoverable}
          style={{ marginBottom: '2%' }}
        >
          <CardContent style={{ display: 'flex', flexDirection: 'column' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              {compactMode && (
                <Typography variant="h5" component="div">
                  {job.id}
                </Typography>
              )}
              <Typography variant="h5" component="div">
                {isJobRunning &&
                  humanizeDuration(job.elapsed ? job.elapsed * 1000 : 0)}
              </Typography>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <StateContent>
                  {isJobRunning && (
                    <IconButton
                      onClick={handleCancelJob}
                      color="error"
                      size="small"
                      disabled={canceling}
                      style={{ height: 'min-content', width: 'min-content' }}
                    >
                      <Cancel />
                    </IconButton>
                  )}
                  {job.output && (
                    <IconButton
                      disabled={!job.output}
                      onClick={(event) => onJobOutputClick(event, job)}
                      size="small"
                      style={{ height: 'min-content', width: 'min-content' }}
                    >
                      <OutputIcon />
                    </IconButton>
                  )}
                  {job.state && <JobStateComponent state={job.state} />}
                </StateContent>
              </div>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <Typography variant="h6" component="div">
                {job.submit
                  ? DateTime.fromISO(job.submit).toLocaleString(
                      DateTime.TIME_SIMPLE,
                    )
                  : ''}
              </Typography>
              <EditableField
                value={job!.notes || ''}
                onSave={(value) => onSaveNotes(job.id, value)}
              />
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            ></div>

            {scans.length > 0 ? (
              <div>
                {compactMode ? (
                  <ImageGallery scans={scans} />
                ) : (
                  <ScansTableContainer {...scansTableProps} />
                )}
              </div>
            ) : null}
          </CardContent>
        </HoverCard>
        <JobOutputDialog
          open={!!jobOutputDialog}
          onClose={onJobOutputClose}
          job={jobOutputDialog}
        />
      </React.Fragment>
    );
  },
);

export default SessionCard;
