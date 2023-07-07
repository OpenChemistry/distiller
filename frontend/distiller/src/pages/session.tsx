import React, { useEffect } from 'react';
import { getJobScans } from '../features/scans';
import { useNavigate, useParams as useUrlParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { getJob, jobSelector } from '../features/jobs';
import SessionCard from '../components/session-card';
import { Button } from '@mui/material';
import { SESSIONS } from '../routes';
import LeftIcon from '@mui/icons-material/ArrowLeft';
import RightIcon from '@mui/icons-material/ArrowRight';
import { isNil } from '../utils';

const SessionPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const jobIdParam = useUrlParams().jobId;
  const jobId = parseInt(jobIdParam as string, 10);
  const job = useAppSelector(jobSelector(jobId));
  const microscopeName = useUrlParams().microscope;

  useEffect(() => {
    if (!job || (!job.nextJobId && !job.prevJobId)) {
      dispatch(getJob({ id: jobId }));
    }
    if (job) {
      dispatch(getJobScans({ jobId: job.id }));
    }
  }, [dispatch, job, jobId]);

  const onNavigateNext = () => {
    navigate(`/${microscopeName}/${SESSIONS}/${job?.nextJobId}`);
  };

  const onNavigatePrev = () => {
    navigate(`/${microscopeName}/${SESSIONS}/${job?.prevJobId}`);
  };

  return (
    <React.Fragment>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Button
          onClick={onNavigatePrev}
          size="small"
          color="primary"
          variant="outlined"
          startIcon={<LeftIcon />}
          disabled={isNil(job?.prevJobId)}
        >
          Prev Session
        </Button>
        <Button
          onClick={onNavigateNext}
          size="small"
          color="primary"
          variant="outlined"
          endIcon={<RightIcon />}
          disabled={isNil(job?.nextJobId)}
        >
          Next Session
        </Button>
      </div>
      {job && (
        <SessionCard jobId={job.id} isHoverable={false} compactMode={false} />
      )}
    </React.Fragment>
  );
};

export default SessionPage;
