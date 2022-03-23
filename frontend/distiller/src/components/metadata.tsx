import React from 'react';

import {
  Grid,
  Table,
  TableRow,
  TableBody,
  TableCell,
  IconButton,
  Collapse,
  TableContainer,
  Paper,
} from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import Typography from '@mui/material/Typography';

import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

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
}));

type Props = {};

const AdvancedMetadata: React.FC<Props> = () => {
  const classes = useStyles();
  const [open, setOpen] = React.useState(false);

  const advancedMetadata = {
    foo: 'bar',
    bar: 'black',
    sheep: 'have',
    you: 'any',
    wool: 'yes',
  };

  return (
    <React.Fragment>
      <TableRow>
        <TableCell>
          <Grid container direction="row" alignItems="center">
            <Typography className={classes.nameCell}>Advanced</Typography>
            <IconButton
              aria-label="expand row"
              size="small"
              onClick={() => setOpen(!open)}
            >
              {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
            </IconButton>
          </Grid>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell className={classes.advancedTableCell} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Table>
              <TableBody>
                {Object.entries(advancedMetadata).map((key, value) => (
                  <TableRow>
                    <TableCell className={classes.advancedNameCell}>
                      {key}
                    </TableCell>
                    <TableCell
                      className={classes.advancedValueCell}
                      align="right"
                    >
                      {value}
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

const MetadataComponent: React.FC<Props> = () => {
  const classes = useStyles();

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableBody>
          <TableRow>
            <TableCell className={classes.nameCell}>
              Distiller Scan ID
            </TableCell>
            <TableCell align="right">999</TableCell>
          </TableRow>
          <TableRow>
            <TableCell className={classes.nameCell}>X size</TableCell>
            <TableCell align="right">999</TableCell>
          </TableRow>
          <TableRow>
            <TableCell className={classes.nameCell}>Y size</TableCell>
            <TableCell align="right">999</TableCell>
          </TableRow>
          <AdvancedMetadata />
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default MetadataComponent;
