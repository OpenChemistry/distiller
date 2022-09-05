import React, { useCallback, useEffect, useState } from 'react';

import { useNavigate, useParams } from 'react-router-dom';

import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableContainer,
  TablePagination,
  Paper,
  LinearProgress,
  IconButton,
  Checkbox,
} from '@mui/material';

import { styled } from '@mui/material/styles';
import CompleteIcon from '@mui/icons-material/CheckCircle';
import ImageIcon from '@mui/icons-material/Image';
import { pink } from '@mui/material/colors';
import Tooltip from '@mui/material/Tooltip';
import DeleteIcon from '@mui/icons-material/Delete';

import { DateTime } from 'luxon';

import { useAppDispatch, useAppSelector } from '../app/hooks';
import {
  getScans,
  patchScan,
  scansSelector,
  totalCount,
  removeScan,
} from '../features/scans';
import { MAX_LOG_FILES } from '../constants';
import EditableField from '../components/editable-field';
import { IdType, Microscope, Scan } from '../types';
import { staticURL } from '../client';
import ImageDialog from '../components/image-dialog';
import LocationComponent from '../components/location';
import { stopPropagation } from '../utils';
import {
  ScanDeleteConfirmDialog,
  RemoveScanFilesConfirmDialog,
} from '../components/scan-confirm-dialog';
import { machineSelectors, machineState } from '../features/machines';
import { ExportFormat, Metadata } from '../types';

import { isNil, isNull } from 'lodash';
import { ScansToolbar, FilterCriteria } from '../components/scans-toolbar';
import {
  microscopesSelectors,
  microscopesState,
} from '../features/microscopes';
import { canonicalMicroscopeName } from '../utils/microscopes';

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

const ThumbnailImage = styled('img')(({ theme }) => ({
  width: '100%',
  height: '100%',
  objectFit: 'cover',
  cursor: 'pointer',
}));

const NoThumbnailImageIcon = styled(ImageIcon)(({ theme }) => ({
  width: '60%',
  height: '60%',
  objectFit: 'cover',
  color: pink.A400,
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

const ScansPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const scans = useAppSelector(scansSelector.selectAll);
  const totalScans = useAppSelector(totalCount);
  const machines = useAppSelector((state) =>
    machineSelectors.selectAll(machineState(state))
  );
  const machineNames = machines.map((machine) => machine.name);

  const [maximizeImg, setMaximizeImg] = useState(false);
  const [activeImg, setActiveImg] = useState('');
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(20);
  const [scanToDelete, setScanToDelete] = React.useState<Scan | null>(null);
  const [scanFilesToRemove, setScanFilesToRemove] = React.useState<Scan | null>(
    null
  );
  const [onScanFilesRemovalConfirm, setOnScanFilesRemovalConfirm] =
    React.useState<(params: { [key: string]: any }) => void | undefined>();
  const [filterCriteria, setFilterCriteria] = useState<FilterCriteria | null>(
    null
  );
  const [selectedScanIDs, setSelectedScanIDs] = useState<Set<IdType>>(
    new Set<IdType>()
  );

  const microscopes = useAppSelector((state) =>
    microscopesSelectors.selectAll(microscopesState(state))
  );

  const microscopesByCanonicalName = microscopes.reduce(
    (obj: { [key: string]: Microscope }, microscope) => {
      obj[canonicalMicroscopeName(microscope.name)] = microscope;

      return obj;
    },
    {}
  );

  // Default to 4D Camera
  let microscopeId: IdType | undefined;

  if (microscopes.length > 0) {
    microscopeId = microscopes[0].id;
  }

  const microscope = useParams().microscope;
  if (microscope !== undefined) {
    const canonicalName = canonicalMicroscopeName(microscope as string);

    if (canonicalName in microscopesByCanonicalName) {
      microscopeId = microscopesByCanonicalName[canonicalName].id;
    }
  }

  useEffect(() => {
    if (microscopeId === undefined) {
      return;
    }

    dispatch(
      getScans({
        skip: page * rowsPerPage,
        limit: rowsPerPage,
        start: filterCriteria?.start,
        end: filterCriteria?.end,
        microscopeId: microscopeId,
      })
    );
  }, [dispatch, page, rowsPerPage, filterCriteria, microscopeId]);

  useEffect(() => {
    setSelectedScanIDs(new Set<IdType>());
  }, [scans]);

  useEffect(() => {
    if (microscopeId === undefined) {
      return;
    }

    const result = microscopes.filter((m) => m.id === microscopeId);
    if (result.length === 1) {
      const microscopeName = result[0].name;
      document.title = `distiller - ${microscopeName}`;
    }
  }, [microscopes, microscopeId]);

  const onSaveNotes = (id: IdType, notes: string) => {
    return dispatch(patchScan({ id, updates: { notes } }));
  };

  const onImgClick = (scan: Scan) => {
    setActiveImg(`${staticURL}${scan.image_path!}`);
    setMaximizeImg(true);
  };

  const onCloseDialog = () => {
    setMaximizeImg(false);
  };

  const onScanClick = (scan: Scan) => {
    navigate(`scans/${scan.id}`);
  };
  const onChangePage = (
    event: React.MouseEvent<HTMLButtonElement> | null,
    page: number
  ) => {
    setPage(page);
  };

  const onChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const scansPerPage = +event.target.value;
    setRowsPerPage(scansPerPage);
    setPage(0);
  };

  const confirmScanFilesRemoval = (scan: Scan) => {
    return new Promise<boolean>((resolve) => {
      setScanFilesToRemove(scan);
      setOnScanFilesRemovalConfirm(() => (params: { [key: string]: any }) => {
        const { confirm } = params;
        resolve(confirm);
        setScanFilesToRemove(null);
      });
    });
  };

  const onDelete = (scan: Scan) => {
    setScanToDelete(scan);
  };

  const onScanDeleteConfirm = (params: { [key: string]: any }) => {
    const { confirm, removeScanFiles } = params;

    if (confirm && scanToDelete !== null) {
      const id = scanToDelete.id;
      dispatch(removeScan({ id, removeScanFiles }));
    }

    setScanToDelete(null);
  };

  const onFilter = useCallback((criteria: FilterCriteria | null) => {
    setPage(0);
    setFilterCriteria(criteria);
  }, []);

  const selectedScans = () => {
    if (selectedScanIDs.size > 0) {
      return scans.filter((scan: Scan) => selectedScanIDs.has(scan.id));
    }

    return scans;
  };

  const hasScanIDs = () => {
    const ids = new Set(scans.map((scan) => scan.scan_id));

    return ids.size > 1 || !ids.has(null);
  };

  const exportScans = async (data: string, mimetype: string) => {
    const blob = new Blob([data], { type: mimetype });
    const href = await URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = href;
    const fileSuffix = mimetype.split('/')[1];
    link.download = `scans.${fileSuffix}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const onExportJSON = async () => {
    const filteredScans = selectedScans().map((scan: Scan) => {
      let scanJSON: { [key: string]: string | number | Metadata | undefined } =
        {
          distiller_scan_id: scan.id,
        };

      // Only add if non null
      if (!isNil(scan.scan_id)) {
        scanJSON['detector_scan_id'] = scan.scan_id;
      }

      scanJSON = {
        ...scanJSON,
        created: scan.created,
        notes: scan.notes,
        metadata: scan.metadata,
      };

      return scanJSON;
    });
    const json = JSON.stringify(filteredScans, null, 2);

    exportScans(json, 'application/json');
  };

  const onExportCSV = async () => {
    const headers: string[] = [];

    if (hasScanIDs()) {
      headers.push('distiller_scan_id', 'detector_scan_id');
    } else {
      headers.push('distiller_scan_id');
    }
    headers.push('created', 'notes');

    // Generate metadata headers
    const metadataHeaders = new Set<string>();
    for (let scan of selectedScans()) {
      if (!isNil(scan.metadata)) {
        const keys = Object.keys(scan.metadata);
        keys.forEach((key) => metadataHeaders.add(key));
      }
    }
    headers.push(...Array.from(metadataHeaders));

    const filteredScans = selectedScans().map((scan: Scan) => {
      const exportScan: { [key: string]: string | number } = {
        distiller_scan_id: scan.id,
        created: scan.created,
        notes: scan.notes ? scan.notes : '',
      };

      if (!isNil(scan.scan_id)) {
        exportScan['detector_scan_id'] = scan.scan_id;
      }

      Array.from(metadataHeaders).forEach((header: string) => {
        if (!isNil(scan.metadata) && !isNil(scan.metadata[header])) {
          exportScan[header] = scan.metadata[header];
        } else {
          exportScan[header] = '';
        }
      });

      return exportScan;
    });

    const csvHeaders = headers.map((header: string) =>
      metadataHeaders.has(header)
        ? `METADATA.${header.toUpperCase()}`
        : header.toUpperCase()
    );
    const csvContent =
      csvHeaders.join(',') +
      '\n' +
      filteredScans
        .map((scan) => {
          let columns: any[] = [];
          headers.forEach((header: string) => {
            if (header in scan) {
              let key = header as keyof typeof scan;
              if (!isNil(scan[key])) {
                columns.push(scan[key]);
              } else {
                columns.push('');
              }
            }
          });

          return columns.join(',');
        })
        .join('\n');

    exportScans(csvContent, 'text/csv');
  };

  const onExport = async (format: ExportFormat) => {
    if (format === ExportFormat.JSON) {
      onExportJSON();
    } else if (format === ExportFormat.CSV) {
      onExportCSV();
    }
  };

  const onSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedScanIDs(new Set<IdType>(scans.map((s) => s.id)));
    } else {
      setSelectedScanIDs(new Set<IdType>());
    }
  };

  const onSelectRowClick = (
    event: React.MouseEvent<HTMLButtonElement>,
    id: IdType
  ) => {
    event.stopPropagation();

    if (!selectedScanIDs.has(id)) {
      setSelectedScanIDs(new Set<IdType>(selectedScanIDs).add(id));
    } else {
      setSelectedScanIDs(
        new Set<IdType>(
          Array.from(selectedScanIDs).filter(
            (selectedId: IdType) => selectedId !== id
          )
        )
      );
    }
  };

  return (
    <React.Fragment>
      <ScansToolbar
        onFilter={onFilter}
        onExport={onExport}
        showFilterBadge={!isNull(filterCriteria)}
      />
      <TableContainer component={Paper}>
        <Table aria-label="scans table">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={
                    selectedScanIDs.size > 0 &&
                    selectedScanIDs.size < scans.length
                  }
                  checked={selectedScanIDs.size === scans.length}
                  onChange={onSelectAllClick}
                />
              </TableCell>
              <TableImageCell></TableImageCell>
              <TableHeaderCell>ID</TableHeaderCell>
              {hasScanIDs() && <TableHeaderCell>Scan ID</TableHeaderCell>}
              <TableHeaderCell>Notes</TableHeaderCell>
              <TableHeaderCell>Location</TableHeaderCell>
              <TableHeaderCell>Created</TableHeaderCell>
              <TableHeaderCell align="right">Progress</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {[...scans]
              .sort((a, b) => b.created.localeCompare(a.created))
              .slice(0, rowsPerPage)
              .map((scan) => (
                <TableScanRow
                  key={scan.id}
                  hover
                  onClick={() => onScanClick(scan)}
                >
                  <TableCell className="selectCheckbox" padding="checkbox">
                    <Checkbox
                      onClick={(event) => onSelectRowClick(event, scan.id)}
                      className="selectCheckbox"
                      checked={selectedScanIDs.has(scan.id)}
                    />
                  </TableCell>
                  <TableImageCell>
                    {scan.image_path ? (
                      <ThumbnailImage
                        src={`${staticURL}${scan.image_path}`}
                        alt="scan thumbnail"
                        onClick={stopPropagation(() => onImgClick(scan))}
                      />
                    ) : (
                      <NoThumbnailImageIcon />
                    )}
                  </TableImageCell>
                  <TableCell>{scan.id}</TableCell>
                  {!isNil(scan.scan_id) && (
                    <TableCell>{scan.scan_id}</TableCell>
                  )}
                  <TableNotesCell>
                    <EditableField
                      value={scan.notes || ''}
                      onSave={(value) => onSaveNotes(scan.id, value)}
                    />
                  </TableNotesCell>
                  <TableCell>
                    <LocationComponent
                      confirmRemoval={confirmScanFilesRemoval}
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
                      <div>
                        {DateTime.fromISO(scan.created).toLocaleString()}
                      </div>
                    </Tooltip>
                  </TableCell>
                  <TableProgressCell align="right">
                    {scan.scan_id && scan.progress < 1000 ? (
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
                      onClick={stopPropagation(() => onDelete(scan))}
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
        count={totalScans}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={onChangePage}
        onRowsPerPageChange={onChangeRowsPerPage}
        labelRowsPerPage="Scans per page"
      />
      <ImageDialog
        open={maximizeImg}
        src={activeImg}
        alt="scan image"
        handleClose={onCloseDialog}
      />
      <RemoveScanFilesConfirmDialog
        onConfirm={onScanFilesRemovalConfirm}
        scan={scanFilesToRemove}
        machines={machineNames}
      />
      <ScanDeleteConfirmDialog
        onConfirm={onScanDeleteConfirm}
        scan={scanToDelete}
        machines={machineNames}
      />
    </React.Fragment>
  );
};

export default ScansPage;
