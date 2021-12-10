import React from 'react';

import { Chip } from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';

import { ScanLocation, IdType } from '../types';

import {  } from '../features/scans';

import { useAppDispatch, useAppSelector } from '../app/hooks';
import { removeScanFiles, scanSelector } from '../features/scans';

import { COMPUTE_HOSTS } from '../constants';

const useStyles = makeStyles((_theme) => ({
  chip: {}
}));

type Props = {
    scanID: IdType;
    locations: ScanLocation[];
    confirmRemoval: (scanID: number, title: string, message: string) => Promise<boolean>;
}

type UniqueLocation = {
    host: string;
    paths: string[];
}

type ChipProps = {
  scanID: number;
  host: string;
  confirmRemoval: (scanID: number, title: string, message: string) => Promise<boolean>;
}

const LocationChip: React.FC<ChipProps> = (props) => {
  const dispatch = useAppDispatch();
  const [deletable, setDeletable] = React.useState(true);
  const {scanID, host, confirmRemoval} = props;
  const scan = useAppSelector(scanSelector(scanID));

  const onDelete =  async () => {
    if (scan === undefined) {
      return;
    }

    const confirmed = await confirmRemoval(scanID, "Remove scan files", `You are about to remove scan files from the acquisition machine for scan ${scan.scan_id}. This operation can not be undone.`);

    if (confirmed) {
      dispatch(removeScanFiles({id: scanID, host}));
      setDeletable(false);
    }
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
            <LocationChip scanID={props.scanID} host={location.host} confirmRemoval={props.confirmRemoval}/>
          </div>
        )
      })}
    </React.Fragment>
  );
}

export default LocationComponent;
