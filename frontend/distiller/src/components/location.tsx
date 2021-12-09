import React from 'react';

import { Chip } from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';

import { ScanLocation, IdType } from '../types';

import {  } from '../features/scans';

import { useAppDispatch } from '../app/hooks';
import { removeScanFiles } from '../features/scans';

import { COMPUTE_HOSTS } from '../constants';

const useStyles = makeStyles((_theme) => ({
  chip: {}
}));

type Props = {
    scanID: IdType,
    locations: ScanLocation[];
}

type UniqueLocation = {
    host: string;
    paths: string[];
}

type ChipProps = {
  scanID: number,
  host: string;
}


const LocationChip: React.FC<ChipProps> = (props) => {

  const dispatch = useAppDispatch();
  const [deletable, setDeletable] = React.useState(true);
  const {scanID, host} = props;

  const onDelete = () => {
    dispatch(removeScanFiles({id: scanID, host}));
    setDeletable(false);
  };

  return (
    <Chip label={host} onDelete={(deletable && !(COMPUTE_HOSTS.includes(host))) ? onDelete : undefined} />
  );
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
            <LocationChip scanID={props.scanID} host={location.host}/>
          </div>
        )
      })}
    </React.Fragment>
  );
}

export default LocationComponent;
