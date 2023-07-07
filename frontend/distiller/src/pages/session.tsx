import React, { useEffect } from 'react';
import { getJobScans } from '../features/scans';
import { useParams as useUrlParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { getJob, jobSelector } from '../features/jobs';
import SessionCard from '../components/session-card';

const SessionPage: React.FC = () => {
  const dispatch = useAppDispatch();

  const jobIdParam = useUrlParams().jobId;
  const jobId = parseInt(jobIdParam as string, 10);
  const job = useAppSelector(jobSelector(jobId));

  useEffect(() => {
    if (!job) {
      dispatch(getJob({ id: jobId }));
    }
    if (job) {
      dispatch(getJobScans({ jobId: job.id }));
    }
  }, [dispatch, job, jobId]);

  return (
    <React.Fragment>
      {job && (
        <SessionCard jobId={job.id} isHoverable={false} compactMode={false} />
      )}
    </React.Fragment>
  );
};

export default SessionPage;
