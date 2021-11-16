import React, {useEffect, useState} from 'react';

import { useNavigate } from 'react-router-dom';

import { Table, TableHead, TableBody, TableRow, TableCell,
         TableContainer, TablePagination, Paper,
         LinearProgress } from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import CompleteIcon from '@mui/icons-material/CheckCircle';
import ImageIcon from '@mui/icons-material/Image';
import {pink } from '@mui/material/colors';

import { useAppDispatch, useAppSelector } from '../app/hooks';
import { getScans, patchScan, scansSelector, totalCount } from '../features/scans';
import { MAX_LOG_FILES } from '../constants';
import EditableField from '../components/editable-field';
import { IdType, Scan } from '../types';
import { staticURL } from '../client';
import ImageDialog from '../components/image-dialog';
import LocationComponent from '../components/location';
import { SCANS_PATH } from '../routes';
import { stopPropagation } from '../utils';


const useStyles = makeStyles((theme) => ({
  headCell: {
    fontWeight: 600,
  },
  scanRow: {
    cursor: 'pointer',
  },
  imgCell: {
    width: '5rem',
    minWidth: '5rem',
    height: '5rem',
    minHeight: '5rem',
    padding: '0.2rem',
    textAlign: 'center',
    color: theme.palette.secondary.light
  },
  thumbnail: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    cursor: 'pointer',
  },
  noThumbnail: {
    width: '60%',
    height: '60%',
    objectFit: 'cover',
    color: pink.A400,
  },
  notesCell: {
    width: '100%',
  },
  location: {
  },
  progressCell: {
    width: '5rem',
  }
}));




const ScansPage: React.FC = () => {
  const classes = useStyles();

  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const scans = useAppSelector(scansSelector.selectAll);
  const totalScans = useAppSelector(totalCount);

  const [maximizeImg, setMaximizeImg] = useState(false);
  const [activeImg, setActiveImg] = useState('');
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(20);

  useEffect(() => {
    dispatch(getScans({skip: page*rowsPerPage, limit: rowsPerPage}));
  }, [dispatch, page, rowsPerPage])

  const onSaveNotes = (id: IdType, notes: string) => {
    return dispatch(patchScan({id, updates: {notes}}));
  }

  const onImgClick = (scan: Scan) => {
    setActiveImg(`${staticURL}${scan.haadf_path!}`);
    setMaximizeImg(true);
  }

  const onCloseDialog = () => {
    setMaximizeImg(false);
  }

  const onScanClick = (scan: Scan) => {
    navigate(`${SCANS_PATH}/${scan.id}`);
  }
  const onChangePage = (event: React.MouseEvent<HTMLButtonElement> | null, page: number) => {
    setPage(page);
    dispatch(getScans({skip: page*rowsPerPage, limit: rowsPerPage}));
  };

  const onChangeRowsPerPage = (event: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    const scansPerPage = +event.target.value
    setRowsPerPage(scansPerPage);
    setPage(0);
    dispatch(getScans({skip: 0, limit: scansPerPage}));
  };

  return (
    <React.Fragment>
      <TableContainer component={Paper}>
        <Table aria-label='scans table'>
          <TableHead>
            <TableRow>
              <TableCell className={classes.imgCell}></TableCell>
              <TableCell className={classes.headCell}>ID</TableCell>
              <TableCell className={classes.headCell}>Scan ID</TableCell>
              <TableCell className={classes.headCell}>Notes</TableCell>
              <TableCell className={classes.headCell}>Location</TableCell>
              <TableCell className={classes.headCell}>Created</TableCell>
              <TableCell className={classes.headCell} align='right'>Progress</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {[...scans].sort((a, b) => b.created.localeCompare(a.created)).slice(0, rowsPerPage).map(scan => (
              <TableRow key={scan.id} className={classes.scanRow} hover onClick={() => onScanClick(scan)}>
                <TableCell className={classes.imgCell}>
                  {scan.haadf_path
                    ? <img
                        src={`${staticURL}${scan.haadf_path}`}
                        alt='scan thumbnail'
                        className={classes.thumbnail}
                        onClick={stopPropagation(() => onImgClick(scan))}
                      />
                    : <ImageIcon className={classes.noThumbnail}/>
                  }
                </TableCell>
                <TableCell>{scan.id}</TableCell>
                <TableCell>{scan.scan_id}</TableCell>
                <TableCell className={classes.notesCell}>
                  <EditableField
                    value={scan.notes || ''}
                    onSave={(value) => onSaveNotes(scan.id, value)}
                  />
                </TableCell>
                <TableCell className={classes.location}>
                  <LocationComponent locations={scan.locations}/>
                </TableCell>
                <TableCell>{scan.created}</TableCell>
                <TableCell align='right' className={classes.progressCell}>
                  {scan.log_files < MAX_LOG_FILES
                    ? <LinearProgress variant='determinate' value={100 * scan.log_files / MAX_LOG_FILES}/>
                    : <CompleteIcon color='primary'/>
                  }
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 20, 100]}
        component="div"
        count={totalScans}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={onChangePage}
        onRowsPerPageChange={onChangeRowsPerPage}
        labelRowsPerPage="Scans per page"
      />
      <ImageDialog open={maximizeImg} src={activeImg} alt='scan image' handleClose={onCloseDialog}/>
    </React.Fragment>
  )
}

export default ScansPage;
