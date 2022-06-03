import React from 'react';

import {
  Grid,
  Table,
  TableRow,
  TableBody,
  TableCell,
  Collapse,
  Button,
} from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';

import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

import { Metadata, Scan } from '../types';

// Search for patterns of the form <prefix><number><suffix> or <prefix><X or Y><suffix>
const groupingPatterns = [
  /^(Calibrations.Dimension)\.(\d{1})\.(.*)$/,
  /^(.+)([XY]{1})(.+)$/,
];

// Move the value to the end so we get the common prefix/suffix sorted together
const rearrange = (prefix: string, suffix: string, value: string | number) => {
  return `${prefix}${suffix}${value}`;
};

const processKey = (key: string) => {
  for (let i = 0; i < groupingPatterns.length; i++) {
    let m = key.match(groupingPatterns[i]);
    if (m !== null) {
      key = rearrange(m[1], m[3], m[2]);
      break;
    }
  }
  return key;
};

// Sort the key but group by common suffix and prefix
const sortWithGrouping = (keys: string[]) => {
  const sort = (a: string, b: string) => {
    a = processKey(a);
    b = processKey(b);

    return a.localeCompare(b);
  };

  return keys.sort(sort);
};

const useStyles = makeStyles((theme) => ({
  nameCell: {
    fontWeight: 600,
  },
  advancedNameCell: {
    fontWeight: 600,
    paddingLeft: 0,
  },
  advancedValueCell: {
    paddingRight: 0,
  },
  advancedTableCell: {
    paddingBottom: 0,
    paddingTop: 0,
  },
  advancedTableHeader: {
    borderBottom: 'unset',
    paddingLeft: 0,
  },
}));

type AdvancedMetadataProps = {
  metadata: Metadata;
};

const AdvancedMetadata: React.FC<AdvancedMetadataProps> = (props) => {
  const classes = useStyles();
  const [open, setOpen] = React.useState(false);
  const { metadata } = props;

  return (
    <React.Fragment>
      <TableRow>
        <TableCell className={classes.advancedTableHeader}>
          <Grid container direction="row" alignItems="center">
            <Button
              endIcon={
                open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />
              }
              onClick={() => setOpen(!open)}
            >
              Advanced
            </Button>
          </Grid>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell className={classes.advancedTableCell} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Table>
              <TableBody>
                {sortWithGrouping(Object.keys(metadata)).map((key) => (
                  <TableRow key={key}>
                    <TableCell className={classes.advancedNameCell}>
                      {key}
                    </TableCell>
                    <TableCell
                      className={classes.advancedValueCell}
                      align="right"
                    >
                      {
                        JSON.stringify(metadata[key]).replace(
                          /^"(.*)"$/,
                          '$1'
                        ) /* strip outer quotes */
                      }
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
};

type MetadataComponentProps = {
  scan: Scan;
};

const MetadataComponent: React.FC<MetadataComponentProps> = (props) => {
  const classes = useStyles();
  const { scan } = props;

  return (
    <Table>
      <TableBody>
        <TableRow>
          <TableCell className={classes.nameCell}>Distiller Scan ID</TableCell>
          <TableCell align="right">{scan.id}</TableCell>
        </TableRow>
        {scan.metadata && (
          <React.Fragment>
            <TableRow>
              <TableCell className={classes.nameCell}>Size</TableCell>
              <TableCell align="right">{`${scan.metadata['Dimensions.1']} x ${scan.metadata['Dimensions.2']}`}</TableCell>
            </TableRow>
          </React.Fragment>
        )}
        {scan.metadata && <AdvancedMetadata metadata={scan.metadata} />}
      </TableBody>
    </Table>
  );
};

export default MetadataComponent;
