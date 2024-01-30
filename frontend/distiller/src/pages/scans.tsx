import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { useNavigate, useParams } from 'react-router-dom';

import { Box, Typography } from '@mui/material';
import LinearProgress, {
  linearProgressClasses,
} from '@mui/material/LinearProgress';
import { styled } from '@mui/material/styles';
import { DateTime } from 'luxon';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { machineSelectors, machineState } from '../features/machines';
import {
  getScans,
  totalCount,
  scansInCurrentPageSelector,
} from '../features/scans';
import { ExportFormat, IdType, Metadata, Microscope, Scan } from '../types';

import { isNil } from 'lodash';
import { ScansToolbar } from '../components/scans-toolbar';
import {
  microscopesSelectors,
  microscopesState,
} from '../features/microscopes';
import { canonicalMicroscopeName } from '../utils/microscopes';

import { ScansTableContainer } from '../components/scans-table-container';
import { SCANS } from '../routes';
import {
  useUrlState,
  intDeserializer,
  intSerializer,
  dateTimeDeserializer,
  dateTimeSerializer,
} from '../routes/url-state';

const bytesToSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return 'n/a';
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    sizes.length - 1,
  );
  if (i === 0) return `${bytes} ${sizes[i]}`;
  return `${(bytes / 1024 ** i).toFixed(1)} ${sizes[i]}`;
};

export interface ScansPageProps {}

const ScansPage: React.FC<ScansPageProps> = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const totalScans = useAppSelector(totalCount);
  const scansInCurrentPage = useAppSelector(scansInCurrentPageSelector);
  const sortedScansInCurrentPage = useMemo(() => {
    return scansInCurrentPage.sort((a, b) =>
      b.created.localeCompare(a.created),
    );
  }, [scansInCurrentPage]);
  const machines = useAppSelector((state) =>
    machineSelectors.selectAll(machineState(state)),
  );
  const machineNames = useMemo(
    () => machines.map((machine) => machine.name),
    [machines],
  );

  const [page, setPage] = useUrlState(
    'page',
    0,
    intSerializer,
    intDeserializer,
  );

  const [rowsPerPage, setRowsPerPage] = useUrlState(
    'rowsPerPage',
    20,
    intSerializer,
    intDeserializer,
  );

  const [startDateFilter, setStartDateFilter] = useUrlState<DateTime | null>(
    'startDate',
    null,
    dateTimeSerializer,
    dateTimeDeserializer,
  );

  const [endDateFilter, setEndDateFilter] = useUrlState<DateTime | null>(
    'endDate',
    null,
    dateTimeSerializer,
    dateTimeDeserializer,
  );

  const [selectedScanIDs, setSelectedScanIDs] = useState<Set<IdType>>(
    new Set<IdType>(),
  );

  let microscope: Microscope | null = null;
  const microscopes = useAppSelector((state) =>
    microscopesSelectors.selectAll(microscopesState(state)),
  );

  const microscopesByCanonicalName = microscopes.reduce(
    (obj: { [key: string]: Microscope }, microscope) => {
      obj[canonicalMicroscopeName(microscope.name)] = microscope;

      return obj;
    },
    {},
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
    if (microscopeId === undefined) {
      return;
    }

    dispatch(
      getScans({
        skip: page * rowsPerPage,
        limit: rowsPerPage,
        start: startDateFilter || undefined,
        end: endDateFilter || undefined,
        microscopeId: microscopeId,
      }),
    );
  }, [
    dispatch,
    page,
    rowsPerPage,
    startDateFilter,
    endDateFilter,
    microscopeId,
  ]);

  useEffect(() => {
    setSelectedScanIDs(new Set<IdType>());
  }, [scansInCurrentPage]);

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

  const onScanClick = useCallback(
    (scan: Scan) => {
      if (microscope === null) {
        return;
      }
      const canonicalName = canonicalMicroscopeName(microscopeName as string);
      navigate(`/${canonicalName}/${SCANS}/${scan.id}`);
    },
    [canonicalMicroscopeName, microscopeName, microscope, navigate],
  );

  const onScansPerPageChange = useCallback(
    (scansPerPage: number) => {
      setRowsPerPage(scansPerPage);
      setPage(0);
    },
    [setRowsPerPage, setPage],
  );

  const onStartDate = useCallback(
    (date: DateTime | null) => {
      setPage(0);
      setStartDateFilter(date);
    },
    [setPage, setStartDateFilter],
  );

  const onEndDate = useCallback(
    (date: DateTime | null) => {
      setPage(0);
      setEndDateFilter(date);
    },
    [setPage, setEndDateFilter],
  );

  const selectedScans = () => {
    if (selectedScanIDs.size > 0) {
      return sortedScansInCurrentPage.filter((scan: Scan) =>
        selectedScanIDs.has(scan.id),
      );
    }

    return sortedScansInCurrentPage;
  };

  const hasScanIDs = useMemo(() => {
    const ids = new Set(scansInCurrentPage.map((scan) => scan.scan_id));

    return ids.size > 1 || !ids.has(null);
  }, [scansInCurrentPage]);

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

    if (hasScanIDs) {
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
        : header.toUpperCase(),
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

  const onSelectAll = useCallback(
    (checked: boolean) => {
      if (checked) {
        setSelectedScanIDs(
          new Set<IdType>(scansInCurrentPage.map((s) => s.id)),
        );
      } else {
        setSelectedScanIDs(new Set<IdType>());
      }
    },
    [setSelectedScanIDs, scansInCurrentPage],
  );

  const onScanSelect = useCallback(
    (scan: Scan) => {
      if (!selectedScanIDs.has(scan.id)) {
        setSelectedScanIDs(new Set<IdType>(selectedScanIDs).add(scan.id));
      } else {
        setSelectedScanIDs(
          new Set<IdType>(
            Array.from(selectedScanIDs).filter(
              (selectedId: IdType) => selectedId !== scan.id,
            ),
          ),
        );
      }
    },
    [selectedScanIDs, setSelectedScanIDs],
  );

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
      {disk_usage && (
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
      <ScansToolbar
        startDate={startDateFilter}
        endDate={endDateFilter}
        onStartDate={onStartDate}
        onEndDate={onEndDate}
        onExport={onExport}
        showFilterBadge={!isNil(startDateFilter) || !isNil(endDateFilter)}
      />
      <ScansTableContainer
        currentPage={page}
        scansPerPage={rowsPerPage}
        scansInCurrentPage={sortedScansInCurrentPage}
        totalNumberOfScans={totalScans}
        displayIDs={hasScanIDs}
        selectedScanIDs={selectedScanIDs}
        machineNames={machineNames}
        onScanClick={onScanClick}
        onSelectAll={onSelectAll}
        onScanSelect={onScanSelect}
        onCurrentPageChange={setPage}
        onScansPerPageChange={onScansPerPageChange}
      />
    </React.Fragment>
  );
};

export default ScansPage;
