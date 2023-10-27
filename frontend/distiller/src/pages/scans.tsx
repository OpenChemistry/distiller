import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { useNavigate, useParams } from 'react-router-dom';

import CompleteIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import {
  Box,
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
  Typography,
} from '@mui/material';
import LinearProgress, {
  linearProgressClasses,
} from '@mui/material/LinearProgress';
import Tooltip from '@mui/material/Tooltip';
import { styled } from '@mui/material/styles';
import { DateTime } from 'luxon';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { staticURL } from '../client';
import EditableField from '../components/editable-field';
import ImageDialog from '../components/image-dialog';
import LocationComponent from '../components/location';
import {
  RemoveScanFilesConfirmDialog,
  ScanDeleteConfirmDialog,
} from '../components/scan-confirm-dialog';
import { machineSelectors, machineState } from '../features/machines';
import {
  getScans,
  patchScan,
  removeScan,
  scansByDateSelector,
  totalCount,
} from '../features/scans';
import { ExportFormat, IdType, Metadata, Microscope, Scan } from '../types';
import { stopPropagation } from '../utils';

import { isNil } from 'lodash';
import { ScansToolbar } from '../components/scans-toolbar';
import {
  microscopesSelectors,
  microscopesState,
} from '../features/microscopes';
import { canonicalMicroscopeName } from '../utils/microscopes';

import { RootState } from '../app/store';
import { NoThumbnailImageIcon } from '../components/no-thumbnail-image-icon';
import { ThumbnailImage } from '../components/thumbnail-image';
import { SCANS } from '../routes';
import { Deserializer, Serializer, useUrlState } from '../routes/url-state';

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

const bytesToSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return 'n/a';
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    sizes.length - 1
  );
  if (i === 0) return `${bytes} ${sizes[i]}`;
  return `${(bytes / 1024 ** i).toFixed(1)} ${sizes[i]}`;
};

export const dateTimeSerializer: Serializer<DateTime | null> = (dt) => {
  if (!isNil(dt)) {
    return dt.toString();
  } else {
    return '';
  }
};

export const dateTimeDeserializer: Deserializer<DateTime | null> = (dtStr) => {
  const dt = DateTime.fromISO(dtStr);
  if (dt.isValid) {
    return dt;
  } else {
    return null;
  }
};

export const intSerializer: Serializer<number> = (n) => {
  if (isNil(n)) {
    return '';
  } else {
    return n.toString();
  }
};

export const intDeserializer: Deserializer<number> = (nStr) => {
  const n = parseInt(nStr);

  if (!Number.isFinite(n)) {
    return undefined;
  }

  return n;
};

export interface ScansPageProps {
  selector?: (state: RootState) => Scan[];
  showScansToolbar?: boolean;
  showTablePagination?: boolean;
  totalScans?: number;
  showDiskUsage?: boolean;
  shouldFetchScans?: boolean;
  onScanClick?: (event: React.MouseEvent, scan: Scan) => void;
}

const ScansPage: React.FC<ScansPageProps> = ({
  selector,
  showScansToolbar = true,
  showTablePagination = true,
  totalScans: totalScansProp,
  showDiskUsage = true,
  shouldFetchScans = true,
  onScanClick,
}) => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const totalScans = useAppSelector(totalCount);
  const machines = useAppSelector((state) =>
    machineSelectors.selectAll(machineState(state))
  );
  const machineNames = machines.map((machine) => machine.name);

  const [maximizeImg, setMaximizeImg] = useState(false);
  const [activeImg, setActiveImg] = useState('');
  const [page, setPage] = useUrlState(
    'page',
    0,
    intSerializer,
    intDeserializer
  );

  const [rowsPerPage, setRowsPerPage] = useUrlState(
    'rowsPerPage',
    20,
    intSerializer,
    intDeserializer
  );
  const [scanToDelete, setScanToDelete] = React.useState<Scan | null>(null);
  const [scanFilesToRemove, setScanFilesToRemove] = React.useState<Scan | null>(
    null
  );
  const [onScanFilesRemovalConfirm, setOnScanFilesRemovalConfirm] =
    React.useState<(params: { [key: string]: any }) => void | undefined>();

  const [startDateFilter, setStartDateFilter] = useUrlState<DateTime | null>(
    'startDate',
    null,
    dateTimeSerializer,
    dateTimeDeserializer
  );

  const [endDateFilter, setEndDateFilter] = useUrlState<DateTime | null>(
    'endDate',
    null,
    dateTimeSerializer,
    dateTimeDeserializer
  );

  const defaultSelector = useMemo(
    () => scansByDateSelector(startDateFilter, endDateFilter),
    [startDateFilter, endDateFilter]
  );

  const scans = useAppSelector(selector || defaultSelector).sort((a, b) =>
    b.created.localeCompare(a.created)
  );

  const start = page * rowsPerPage;
  const end = start + rowsPerPage;

  const scansOnThisPage = useMemo(() => {
    return scans.slice(start, end);
  }, [scans, start, end]);

  const [selectedScanIDs, setSelectedScanIDs] = useState<Set<IdType>>(
    new Set<IdType>()
  );

  let microscope: Microscope | null = null;
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

  const microscopeName = useParams().microscope;
  if (microscope !== undefined) {
    const canonicalName = canonicalMicroscopeName(microscopeName as string);

    if (canonicalName in microscopesByCanonicalName) {
      microscope = microscopesByCanonicalName[canonicalName];
      microscopeId = microscope.id;
    }
  }

  useEffect(() => {
    if (!shouldFetchScans || microscopeId === undefined) {
      return;
    }

    dispatch(
      getScans({
        skip: page * rowsPerPage,
        limit: rowsPerPage,
        start: startDateFilter || undefined,
        end: endDateFilter || undefined,
        microscopeId: microscopeId,
      })
    );
  }, [
    dispatch,
    page,
    rowsPerPage,
    startDateFilter,
    endDateFilter,
    microscopeId,
    shouldFetchScans,
  ]);

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

  const defaultOnScanClick = (event: React.MouseEvent, scan: Scan) => {
    if (microscope === null) {
      return;
    }
    const canonicalName = canonicalMicroscopeName(microscopeName as string);
    navigate(`/${canonicalName}/${SCANS}/${scan.id}`);
  };

  const handleScanClick = onScanClick || defaultOnScanClick;

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

  const onStartDate = useCallback(
    (date: DateTime | null) => {
      setPage(0);
      setStartDateFilter(date);
    },
    [setPage, setStartDateFilter]
  );

  const onEndDate = useCallback(
    (date: DateTime | null) => {
      setPage(0);
      setEndDateFilter(date);
    },
    [setPage, setEndDateFilter]
  );

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
      setSelectedScanIDs(new Set<IdType>(scansOnThisPage.map((s) => s.id)));
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

  const disk_usage = microscope?.state?.disk_usage;
  const percentageDiskUsed = disk_usage
    ? (disk_usage.used / disk_usage.total) * 100
    : 0;

  const DiskUsage = styled(LinearProgress)(({ theme }) => {
    let barColor = theme.palette.success.light;

    if (percentageDiskUsed > 75) {
      barColor = theme.palette.error.light;
    } else if (percentageDiskUsed > 50) {
      barColor = theme.palette.warning.light;
    }

    return {
      height: 15,
      borderRadius: 5,
      [`&.${linearProgressClasses.colorPrimary}`]: {
        backgroundColor:
          theme.palette.grey[theme.palette.mode === 'light' ? 300 : 800],
      },
      [`& .${linearProgressClasses.bar}`]: {
        borderRadius: 5,
        backgroundColor: barColor,
      },
    };
  });

  return (
    <React.Fragment>
      {showDiskUsage && disk_usage && (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box sx={{ minWidth: 105 }}>
            <Typography variant="body2" color="text.secondary">
              Storage Usage
            </Typography>
          </Box>
          <Box sx={{ width: '100%', mr: 1 }}>
            <DiskUsage
              variant="determinate"
              value={percentageDiskUsed}
            ></DiskUsage>
          </Box>
          <Box sx={{ minWidth: 105 }}>
            <Typography variant="body2" color="text.secondary">
              {bytesToSize(disk_usage.free)} Free
            </Typography>
          </Box>
        </Box>
      )}
      {showScansToolbar && (
        <ScansToolbar
          startDate={startDateFilter}
          endDate={endDateFilter}
          onStartDate={onStartDate}
          onEndDate={onEndDate}
          onExport={onExport}
          showFilterBadge={!isNil(startDateFilter) || !isNil(endDateFilter)}
        />
      )}
      <TableContainer component={Paper}>
        <Table aria-label="scans table">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={
                    selectedScanIDs.size > 0 &&
                    selectedScanIDs.size < scansOnThisPage.length
                  }
                  checked={selectedScanIDs.size === scansOnThisPage.length}
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
            {[...scansOnThisPage].map((scan) => (
              <TableScanRow
                key={scan.id}
                hover
                onClick={(event) => handleScanClick(event, scan)}
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
                    <NoThumbnailImageIcon cursor="default" />
                  )}
                </TableImageCell>
                <TableCell>{scan.id}</TableCell>
                {!isNil(scan.scan_id) && <TableCell>{scan.scan_id}</TableCell>}
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
      {showTablePagination && (
        <TablePagination
          rowsPerPageOptions={[10, 20, 100]}
          component="div"
          count={totalScansProp !== undefined ? totalScansProp : totalScans}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={onChangePage}
          onRowsPerPageChange={onChangeRowsPerPage}
          labelRowsPerPage="Scans per page"
        />
      )}
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
