import React, { useEffect } from 'react';
import { getJobScans } from '../features/scans';
import { useParams as useUrlParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import {
  addFetchedJobId,
  fetchedJobIdsSelector,
  getJob,
  jobSelector,
} from '../features/jobs';
import SessionCard from '../components/session-card';

const SessionPage: React.FC = () => {
  const dispatch = useAppDispatch();

  const jobIdParam = useUrlParams().jobId;
  const jobId = parseInt(jobIdParam as string, 10);
  const job = useAppSelector(jobSelector(jobId));
  const fetchedJobIds = useAppSelector(fetchedJobIdsSelector);

  useEffect(() => {
    if (!job) {
      dispatch(getJob({ id: jobId }));
    }
    if (job && !fetchedJobIds.includes(job.id)) {
      dispatch(getJobScans({ jobId: job.id }));
      dispatch(addFetchedJobId(job.id));
    }
  }, [dispatch, fetchedJobIds, job, jobId]);

  return (
    <React.Fragment>
      {job && <SessionCard job={job} isHoverable={false} compactMode={false} />}
    </React.Fragment>
  );
};

export default SessionPage;
