import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import {
  Card,
  CardContent,
  CardProps,
  IconButton,
  Typography,
} from '@mui/material';
import EditableField from './editable-field';
import OutputIcon from '@mui/icons-material/Terminal';

import ScansPage from '../pages/scans';
import styled from '@emotion/styled';
import { IdType, Job, PendingJobStates, RunningJobStates, Scan } from '../types';
import { DateTime } from 'luxon';
import { jobSelector, patchJob } from '../features/jobs';
import { scansByJobIdSelector } from '../features/scans';
import JobOutputDialog from './job-output';
import JobStateComponent from './job-state';
import ImageGallery from './image-gallery';
import { cancelJob } from '../features/jobs';
import { Cancel } from '@mui/icons-material';
import { SCANS, SESSIONS } from '../routes';

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
      : {}
);

interface SessionCardProps {
  jobId: IdType;
  setHoveredJobId?: React.Dispatch<React.SetStateAction<IdType | null>>;
  isHoverable?: boolean | undefined;
  compactMode?: boolean | undefined | null;
}

// SessionCard Component
const SessionCard = React.memo(
  ({ jobId, setHoveredJobId, isHoverable, compactMode }: SessionCardProps) => {
    const navigate = useNavigate();
    const dispatch = useAppDispatch();
    const job = useAppSelector(jobSelector(jobId)) as Job;
    const microscopeName = useParams().microscope;

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

    const onScanClick = (event: React.MouseEvent, scan: Scan) => {
      event.stopPropagation();
      navigate(`/${microscopeName}/${SESSIONS}/${jobId}/${SCANS}/${scan.id}`);
    };

    // Scans
    const scans = useAppSelector(scansByJobIdSelector(job.id));

    const scansPageProps = {
      selector: scansByJobIdSelector(job.id),
      showScansToolbar: false,
      showTablePagination: false,
      showDiskUsage: false,
      shouldFetchScans: false,
      onScanClick: onScanClick
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
        >
          <CardContent style={{ display: 'flex', flexDirection: 'column' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <Typography variant="h5" component="div">
                {job.id}
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
                      DateTime.TIME_SIMPLE
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
                  <ScansPage {...scansPageProps} />
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
  }
);

export default SessionCard;
