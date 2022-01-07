import React from 'react';

import { Chip } from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';

import { ScanLocation, Scan } from '../types';

import { useAppDispatch } from '../app/hooks';
import { removeScanFiles } from '../features/scans';

import { COMPUTE_HOSTS } from '../constants';

const useStyles = makeStyles((_theme) => ({
  chip: {},
}));

type Props = {
  scan: Scan;
  locations: ScanLocation[];
  confirmRemoval: (scan: Scan) => Promise<boolean>;
};

type UniqueLocation = {
  host: string;
  paths: string[];
};

type ChipProps = {
  scan: Scan;
  host: string;
  confirmRemoval: (scan: Scan) => Promise<boolean>;
};

const LocationChip: React.FC<ChipProps> = (props) => {
  const dispatch = useAppDispatch();
  const [deletable, setDeletable] = React.useState(true);
  const { scan, host, confirmRemoval } = props;

  const onDelete = async () => {
    if (scan === undefined) {
      return;
    }

    const confirmed = await confirmRemoval(scan);

    if (confirmed) {
      dispatch(removeScanFiles({ id: scan.id, host }));
      setDeletable(false);
    }
  };

  return (
    <Chip
      label={host}
      onDelete={
        deletable && !COMPUTE_HOSTS.includes(host) ? onDelete : undefined
      }
    />
  );
};

const LocationComponent: React.FC<Props> = (props) => {
  const classes = useStyles();

  const { locations } = props;
  const uniqueLocations: UniqueLocation[] = Object.values(
    locations.reduce((locs, location) => {
      const { host, path } = location;
      if (locs[host] === undefined) {
        locs[host] = { host, paths: [] };
      }
      locs[host].paths.push(path);

      return locs;
    }, {} as { [host: string]: UniqueLocation })
  );

  return (
    <React.Fragment>
      {uniqueLocations.map((location) => {
        return (
          <div
            key={location.host}
            title={location.paths.join(', ')}
            className={classes.chip}
          >
            <LocationChip
              scan={props.scan}
              host={location.host}
              confirmRemoval={props.confirmRemoval}
            />
          </div>
        );
      })}
    </React.Fragment>
  );
};

export default LocationComponent;
