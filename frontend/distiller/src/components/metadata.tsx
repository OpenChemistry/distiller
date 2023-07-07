import React from 'react';

import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import {
  Button,
  Collapse,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from '@mui/material';
import { styled } from '@mui/material/styles';
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

const TableNameCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 600,
}));

const TableAdvancedNameCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 600,
  paddingLeft: 0,
}));

const TableAdvancedValueCell = styled(TableCell)(({ theme }) => ({
  paddingRight: 0,
}));

const TableAdvancedCell = styled(TableCell)(({ theme }) => ({
  paddingBottom: 0,
  paddingTop: 0,
}));

const TableAdvancedHeaderCell = styled(TableCell)(({ theme }) => ({
  borderBottom: 'unset',
  paddingLeft: 0,
}));

type AdvancedMetadataProps = {
  metadata: Metadata;
};

const AdvancedMetadata: React.FC<AdvancedMetadataProps> = (props) => {
  const [open, setOpen] = React.useState(false);
  const { metadata } = props;

  return (
    <React.Fragment>
      <TableRow>
        <TableAdvancedHeaderCell>
          <Grid container direction="row" alignItems="center">
            <Button
              endIcon={
                open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />
              }
              onClick={() => setOpen(!open)}
            >
              Metadata
            </Button>
          </Grid>
        </TableAdvancedHeaderCell>
      </TableRow>
      <TableRow>
        <TableAdvancedCell colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Table>
              <TableBody>
                {sortWithGrouping(Object.keys(metadata)).map((key) => (
                  <TableRow key={key}>
                    <TableAdvancedNameCell>{key}</TableAdvancedNameCell>
                    <TableAdvancedValueCell align="right">
                      {
                        JSON.stringify(metadata[key]).replace(
                          /^"(.*)"$/,
                          '$1'
                        ) /* strip outer quotes */
                      }
                    </TableAdvancedValueCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Collapse>
        </TableAdvancedCell>
      </TableRow>
    </React.Fragment>
  );
};

type MetadataComponentProps = {
  scan: Scan;
};

const MetadataComponent: React.FC<MetadataComponentProps> = (props) => {
  const { scan } = props;

  return (
    <Table>
      <TableBody>
        {scan.metadata && (
          <React.Fragment>
            <TableRow>
              <TableNameCell>Size</TableNameCell>
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
