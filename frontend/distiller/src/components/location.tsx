import React from 'react';

import { Chip } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';

import { ScanLocation } from '../types';

const useStyles = makeStyles((_theme) => ({
  chip: {}
}));

type Props = {
    locations: ScanLocation[];
}

type UniqueLocation = {
    host: string;
    paths: string[];
}

const LocationComponent: React.FC<Props> = (props) => {
  const classes = useStyles();

  const { locations } = props;
  const uniqueLocations: UniqueLocation[] = Object.values(locations.reduce((locs, location) => {
    const {host, path} = location;
    if (locs[host] === undefined) {
      locs[host] = {host, paths: []}
    }
    locs[host].paths.push(path);

    return locs;
  }, {} as {[host: string]: UniqueLocation}));

  return (
    <React.Fragment>
      {uniqueLocations.map(location => {
        return (
          <div key={location.host} title={location.paths.join(', ')} className={classes.chip}>
            <Chip label={location.host}/>
          </div>
        )
      })}
    </React.Fragment>
  );
}

export default LocationComponent;
