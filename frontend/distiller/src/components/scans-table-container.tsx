import React, { useState, useCallback } from 'react';

import { Scan, IdType } from '../types';

import { useAppDispatch } from '../app/hooks';

import { patchScan, removeScan } from '../features/scans';

import { staticURL } from '../client';

import { ScansTable } from './scans-table';
import ImageDialog from './image-dialog';
import {
  RemoveScanFilesConfirmDialog,
  ScanDeleteConfirmDialog,
} from './scan-confirm-dialog';

type Props = {
  currentPage: number;
  scansPerPage: number;
  scansInCurrentPage: Scan[];
  totalNumberOfScans: number;
  displayIDs: boolean;
  selectedScanIDs: Set<IdType>;
  machineNames: string[];
  onScanClick: (scan: Scan) => void;
  onSelectAll: (checked: boolean) => void;
  onScanSelect: (scan: Scan) => void;
  onCurrentPageChange: (page: number) => void;
  onScansPerPageChange: (scansPerPage: number) => void;
};

export const ScansTableContainer: React.FC<Props> = (props) => {
  const {
    currentPage,
    scansPerPage,
    scansInCurrentPage,
    totalNumberOfScans,
    displayIDs,
    selectedScanIDs,
    machineNames,
    onScanClick,
    onSelectAll,
    onScanSelect,
    onCurrentPageChange,
    onScansPerPageChange,
  } = props;

  const dispatch = useAppDispatch();

  const [maximizeImg, setMaximizeImg] = useState(false);
  const [activeImg, setActiveImg] = useState('');
  const [scanToDelete, setScanToDelete] = React.useState<Scan | null>(null);
  const [scanFilesToRemove, setScanFilesToRemove] = React.useState<Scan | null>(
    null,
  );
  const [onScanFilesRemovalConfirm, setOnScanFilesRemovalConfirm] =
    React.useState<(params: { [key: string]: any }) => void | undefined>();

  const onSaveScanNotes = useCallback(
    (scan: Scan, notes: string) => {
      return dispatch(patchScan({ id: scan.id, updates: { notes } }));
    },
    [dispatch, patchScan],
  );

  const onScanImageClick = useCallback(
    (scan: Scan) => {
      setActiveImg(`${staticURL}${scan.image_path!}`);
      setMaximizeImg(true);
    },
    [setActiveImg, setMaximizeImg],
  );

  const onScanDelete = useCallback(
    (scan: Scan) => {
      setScanToDelete(scan);
    },
    [setScanToDelete],
  );

  const onScanDeleteConfirm = useCallback(
    (params: { [key: string]: any }) => {
      const { confirm, removeScanFiles } = params;

      if (confirm && scanToDelete !== null) {
        const id = scanToDelete.id;
        dispatch(removeScan({ id, removeScanFiles }));
      }

      setScanToDelete(null);
    },
    [dispatch, removeScan, setScanToDelete],
  );

  const onScanFilesDelete = useCallback(
    (scan: Scan) => {
      return new Promise<boolean>((resolve) => {
        setScanFilesToRemove(scan);
        setOnScanFilesRemovalConfirm(() => (params: { [key: string]: any }) => {
          const { confirm } = params;
          resolve(confirm);
          setScanFilesToRemove(null);
        });
      });
    },
    [setScanFilesToRemove, setOnScanFilesRemovalConfirm],
  );

  const onCloseDialog = useCallback(() => {
    setMaximizeImg(false);
  }, [setMaximizeImg]);

  return (
    <React.Fragment>
      <ScansTable
        currentPage={currentPage}
        scansPerPage={scansPerPage}
        scansInCurrentPage={scansInCurrentPage}
        totalNumberOfScans={totalNumberOfScans}
        displayIDs={displayIDs}
        selectedScanIDs={selectedScanIDs}
        machineNames={machineNames}
        onScanClick={onScanClick}
        onScanDelete={onScanDelete}
        onScanImageClick={onScanImageClick}
        onScanFilesDelete={onScanFilesDelete}
        onSaveScanNotes={onSaveScanNotes}
        onSelectAll={onSelectAll}
        onScanSelect={onScanSelect}
        onCurrentPageChange={onCurrentPageChange}
        onScansPerPageChange={onScansPerPageChange}
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
