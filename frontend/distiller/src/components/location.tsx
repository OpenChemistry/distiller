import React from 'react';

import {
  Chip,
  Grid,
  IconButton,
  Tooltip,
  TooltipProps,
  Typography,
  tooltipClasses,
} from '@mui/material';

import { ScanLocation, Scan } from '../types';

import { useAppDispatch } from '../app/hooks';
import { removeScanFiles } from '../features/scans';
import { isNil } from 'lodash';
import ContentCopy from '@mui/icons-material/ContentCopy';
import { styled } from '@mui/material/styles';
import { stopPropagation } from '../utils';

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

const LocationChip: React.FC<ChipProps> = React.forwardRef<
  HTMLDivElement,
  ChipProps
>((props, ref) => {
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
      {...props}
      ref={ref}
      label={host}
      onDelete={deletable && !machines.includes(host) ? onDelete : undefined}
    />
  );
});

type PathProps = {
  path: string;
};

const WhiteContentCopy = styled(ContentCopy)(({ theme }) => ({
  color: theme.palette.common.white,
}));

const PathComponent: React.FC<PathProps> = (props) => {
  const { path } = props;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(path);
  };

  return (
    <Grid container direction="row" alignItems="center">
      <Grid item>
        <Typography>{path}</Typography>
      </Grid>
      <Grid item>
        <IconButton
          aria-label="copy"
          onClick={stopPropagation(() => copyToClipboard())}
        >
          <WhiteContentCopy color="inherit" />
        </IconButton>
      </Grid>
    </Grid>
  );
};

const NoWrapTooltip = styled(({ className, ...props }: TooltipProps) => (
  <Tooltip {...props} classes={{ popper: className }} />
))({
  [`& .${tooltipClasses.tooltip}`]: {
    maxWidth: 'none',
  },
});

const LocationComponent: React.FC<Props> = (props, ref) => {
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
    <Grid
      container
      direction="row"
      alignItems="right"
      wrap="nowrap"
      spacing={1}
      m={0}
      justifyContent="flex-end"
    >
      {uniqueLocations.map((location) => {
        return (
          <Grid key={location.host} item>
            <NoWrapTooltip
              key={location.host}
              title={<PathComponent path={location.paths.join(', ')} />}
              leaveDelay={250}
              placement="bottom-start"
            >
              <LocationChip
                scan={props.scan}
                host={location.host}
                confirmRemoval={props.confirmRemoval}
                machines={machines}
              />
            </NoWrapTooltip>
          </Grid>
        );
      })}
    </Grid>
  );
};

export default LocationComponent;
