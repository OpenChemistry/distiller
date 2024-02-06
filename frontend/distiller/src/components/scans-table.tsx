import React from 'react';

import CompleteIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import {
  Checkbox,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
} from '@mui/material';

import LinearProgress from '@mui/material/LinearProgress';
import Tooltip from '@mui/material/Tooltip';
import { styled } from '@mui/material/styles';
import { DateTime } from 'luxon';
import { isNil } from 'lodash';

import { stopPropagation } from '../utils';
import { Scan, IdType } from '../types';
import { staticURL } from '../client';

import { NoThumbnailImageIcon } from './no-thumbnail-image-icon';
import { ThumbnailImage } from './thumbnail-image';
import EditableField from './editable-field';
import LocationComponent from './location';
import { ProtectedImage } from '../components/protected-image';

type Props = {
  currentPage: number;
  scansPerPage: number;
  scansInCurrentPage: Scan[];
  totalNumberOfScans: number;
  displayIDs: boolean;
  selectedScanIDs: Set<IdType>;
  machineNames: string[];
  onScanClick: (scan: Scan) => void;
  onScanDelete: (scan: Scan) => void;
  onScanImageClick: (scan: Scan) => void;
  onScanFilesDelete: (scan: Scan) => Promise<boolean>;
  onSaveScanNotes: (scan: Scan, notes: string) => Promise<any>;
  onSelectAll: (checked: boolean) => void;
  onScanSelect: (scan: Scan) => void;
  onCurrentPageChange: (page: number) => void;
  onScansPerPageChange: (scansPerPage: number) => void;
};

const TableHeaderCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 600,
}));

const TableImageCell = styled(TableCell)(({ theme }) => ({
  width: '5rem',
  minWidth: '5rem',
  height: '5rem',
  minHeight: '5rem',
  padding: '0.2rem',
  textAlign: 'center',
  color: theme.palette.secondary.light,
}));

const TableNotesCell = styled(TableCell)(({ theme }) => ({
  width: '100%',
}));

const TableProgressCell = styled(TableCell)(({ theme }) => ({
  width: '5rem',
}));

const TableScanRow = styled(TableRow)(({ theme }) => ({
  cursor: 'pointer',
}));

export const ScansTable: React.FC<Props> = (props) => {
  const {
    currentPage,
    scansPerPage,
    scansInCurrentPage,
    totalNumberOfScans,
    displayIDs,
    selectedScanIDs,
    machineNames,
    onScanClick,
    onScanDelete,
    onScanImageClick,
    onScanFilesDelete,
    onSaveScanNotes,
    onSelectAll,
    onScanSelect,
    onCurrentPageChange,
    onScansPerPageChange,
  } = props;

  return (
    <React.Fragment>
      <TableContainer component={Paper}>
        <Table aria-label="scans table">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={
                    selectedScanIDs.size > 0 &&
                    selectedScanIDs.size < scansInCurrentPage.length
                  }
                  checked={selectedScanIDs.size === scansInCurrentPage.length}
                  onChange={(_ev, checked) => onSelectAll(checked)}
                />
              </TableCell>
              <TableImageCell></TableImageCell>
              <TableHeaderCell>ID</TableHeaderCell>
              {displayIDs && <TableHeaderCell>Scan ID</TableHeaderCell>}
              <TableHeaderCell>Notes</TableHeaderCell>
              <TableHeaderCell>Location</TableHeaderCell>
              <TableHeaderCell>Created</TableHeaderCell>
              <TableHeaderCell align="right">Progress</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {[...scansInCurrentPage].map((scan) => (
              <TableScanRow
                key={scan.id}
                hover
                onClick={(_ev) => onScanClick(scan)}
              >
                <TableCell className="selectCheckbox" padding="checkbox">
                  <Checkbox
                    onClick={stopPropagation(() => onScanSelect(scan))}
                    className="selectCheckbox"
                    checked={selectedScanIDs.has(scan.id)}
                  />
                </TableCell>
                <TableImageCell>
                  {scan.image_path ? (
                    <ProtectedImage
                      component={ThumbnailImage}
                      src={`${staticURL}${scan.image_path}`}
                      alt="scan thumbnail"
                      onClick={stopPropagation(() => onScanImageClick(scan))}
                    />
                  ) : (
                    <NoThumbnailImageIcon cursor="default" />
                  )}
                </TableImageCell>
                <TableCell>{scan.id}</TableCell>
                {!isNil(scan.scan_id) && <TableCell>{scan.scan_id}</TableCell>}
                <TableNotesCell>
                  <EditableField
                    value={scan.notes || ''}
                    onSave={(value) => onSaveScanNotes(scan, value)}
                  />
                </TableNotesCell>
                <TableCell>
                  <LocationComponent
                    confirmRemoval={onScanFilesDelete}
                    scan={scan}
                    locations={scan.locations}
                    machines={machineNames}
                  />
                </TableCell>
                <TableCell>
                  <Tooltip
                    title={DateTime.fromISO(scan.created).toISO()}
                    followCursor
                  >
                    <div>{DateTime.fromISO(scan.created).toLocaleString()}</div>
                  </Tooltip>
                </TableCell>
                <TableProgressCell align="right">
                  {scan.scan_id && scan.progress < 100 ? (
                    <LinearProgress
                      variant="determinate"
                      value={scan.progress}
                    />
                  ) : (
                    <CompleteIcon color="primary" />
                  )}
                </TableProgressCell>
                <TableCell align="right">
                  <IconButton
                    aria-label="delete"
                    onClick={stopPropagation(() => onScanDelete(scan))}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableScanRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 20, 100]}
        component="div"
        count={totalNumberOfScans}
        rowsPerPage={scansPerPage}
        page={currentPage}
        onPageChange={(_ev, page) => onCurrentPageChange(page)}
        onRowsPerPageChange={(ev) => onScansPerPageChange(+ev.target.value)}
        labelRowsPerPage="Scans per page"
      />
    </React.Fragment>
  );
};
