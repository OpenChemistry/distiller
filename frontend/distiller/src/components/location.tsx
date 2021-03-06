import React from 'react';

import { Chip } from '@mui/material';

import { ScanLocation, Scan } from '../types';

import { useAppDispatch } from '../app/hooks';
import { removeScanFiles } from '../features/scans';
import { isNil } from 'lodash';

type Props = {
  scan: Scan;
  locations: ScanLocation[];
  confirmRemoval: (scan: Scan) => Promise<boolean>;
  machines: string[];
};

type UniqueLocation = {
  host: string;
  paths: string[];
};

type ChipProps = {
  scan: Scan;
  host: string;
  machines: string[];

  confirmRemoval: (scan: Scan) => Promise<boolean>;
};

const LocationChip: React.FC<ChipProps> = (props) => {
  const dispatch = useAppDispatch();
  const { scan, host, confirmRemoval, machines } = props;
  const [deletable, setDeletable] = React.useState(!isNil(scan.scan_id));

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
      onDelete={deletable && !machines.includes(host) ? onDelete : undefined}
    />
  );
};

const LocationComponent: React.FC<Props> = (props) => {
  const { locations, machines } = props;
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
          <div key={location.host} title={location.paths.join(', ')}>
            <LocationChip
              scan={props.scan}
              host={location.host}
              confirmRemoval={props.confirmRemoval}
              machines={machines}
            />
          </div>
        );
      })}
    </React.Fragment>
  );
};

export default LocationComponent;
