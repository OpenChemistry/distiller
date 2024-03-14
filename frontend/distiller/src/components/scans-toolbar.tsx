import React, { useState } from 'react';

import ClearIcon from '@mui/icons-material/Clear';
import DownloadIcon from '@mui/icons-material/Download';
import FilterListIcon from '@mui/icons-material/FilterList';
import {
  Badge,
  Box,
  Button,
  Grid,
  Menu,
  MenuItem,
  Popover,
  Toolbar,
} from '@mui/material';
import Tooltip from '@mui/material/Tooltip';
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { isNull } from 'lodash';
import { DateTime } from 'luxon';
import { ExportFormat } from '../types';

type FilterPopoverProps = {
  anchorEl: HTMLElement | null;
  startDate: DateTime | null;
  endDate: DateTime | null;
  onClose: () => void;
  onStartDate: (date: DateTime | null) => void;
  onEndDate: (date: DateTime | null) => void;
};

const FilterPopover: React.FC<FilterPopoverProps> = (props) => {
  const { anchorEl, startDate, endDate, onClose, onStartDate, onEndDate } =
    props;

  const onStartDateChange = (date: DateTime | null) => {
    if (!isNull(date) && !date.isValid) {
      return;
    }

    onStartDate(date);
  };

  const onEndDateChange = (date: DateTime | null) => {
    if (!isNull(date) && !date.isValid) {
      return;
    }

    onEndDate(date);
  };

  const onResetFiltersClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    onStartDate(null);
    onEndDate(null);
  };

  return (
    <div>
      <Popover
        open={!isNull(anchorEl)}
        anchorEl={anchorEl}
        onClose={onClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <LocalizationProvider dateAdapter={AdapterLuxon}>
          <Box sx={{ flexGrow: 1, margin: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <DatePicker
                  label="Start Date"
                  format="MM/dd/yy"
                  value={startDate}
                  onChange={onStartDateChange}
                />
              </Grid>
              <Grid item xs={6}>
                <DatePicker
                  label="End Date"
                  format="MM/dd/yy"
                  value={endDate}
                  onChange={onEndDateChange}
                />
              </Grid>
            </Grid>
          </Box>
          <Box sx={{ flexGrow: 1, margin: 2 }}>
            <Grid container marginTop={2} justifyContent="flex-end">
              <Button
                onClick={onResetFiltersClick}
                size="small"
                color="primary"
                variant="outlined"
                startIcon={<ClearIcon />}
              >
                Reset
              </Button>
            </Grid>
          </Box>
        </LocalizationProvider>
      </Popover>
    </div>
  );
};

type ExportMenuProps = {
  anchorEl: HTMLElement | null;
  onClose: () => void;
  onExport: (format: ExportFormat) => void;
};

const ExportMenu: React.FC<ExportMenuProps> = (props) => {
  const { anchorEl, onClose, onExport } = props;

  const exportAsJSON = () => {
    onExport(ExportFormat.JSON);
    onClose();
  };

  const exportAsCSV = () => {
    onExport(ExportFormat.CSV);
    onClose();
  };

  const exportAsHTML = () => {
    onExport(ExportFormat.HTML);
    onClose();
  };

  return (
    <Menu
      id="basic-menu"
      anchorEl={anchorEl}
      open={!isNull(anchorEl)}
      onClose={onClose}
      MenuListProps={{
        'aria-labelledby': 'basic-button',
      }}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'center',
      }}
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
    >
      <MenuItem onClick={exportAsJSON}>Download scans as JSON</MenuItem>
      <MenuItem onClick={exportAsCSV}>Download scans as CSV</MenuItem>
      <MenuItem onClick={exportAsHTML}>Download scans as HTML</MenuItem>
    </Menu>
  );
};

type ScansToolbarProps = {
  startDate: DateTime | null;
  endDate: DateTime | null;
  onStartDate?: (date: DateTime | null) => void;
  onEndDate?: (date: DateTime | null) => void;
  onExport?: (format: ExportFormat) => void;
  showFilterBadge: boolean;
};

export const ScansToolbar: React.FC<ScansToolbarProps> = (props) => {
  const [filterAnchorEl, setFilterAnchorEl] = useState<HTMLElement | null>(
    null,
  );
  const [exportAnchorEl, setExportAnchorEl] = useState<HTMLElement | null>(
    null,
  );
  const {
    startDate,
    endDate,
    showFilterBadge,
    onExport,
    onStartDate,
    onEndDate,
  } = props;

  const onFilterClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const onExportClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setExportAnchorEl(event.currentTarget);
  };

  const onFilterClose = () => {
    setFilterAnchorEl(null);
  };

  const onExportClose = () => {
    setExportAnchorEl(null);
  };

  const showFilter = onStartDate !== undefined && onEndDate !== undefined;

  return (
    <Toolbar
      sx={{
        pl: { sm: 2 },
        pr: { xs: 1, sm: 1 },
        display: 'flex',
        justifyContent: 'flex-end',
      }}
    >
      {onExport && (
        <Box pr={1}>
          <Tooltip title="Export Scans">
            <Button
              onClick={onExportClick}
              size="small"
              color="primary"
              startIcon={<DownloadIcon />}
            >
              Export
            </Button>
          </Tooltip>
        </Box>
      )}
      {showFilter && (
        <Box>
          <Tooltip title="Filter Scans">
            <Button
              onClick={onFilterClick}
              size="small"
              color="primary"
              startIcon={
                <Badge
                  color="primary"
                  variant="dot"
                  invisible={!showFilterBadge}
                >
                  <FilterListIcon />
                </Badge>
              }
            >
              Filter
            </Button>
          </Tooltip>
        </Box>
      )}

      {showFilter && (
        <FilterPopover
          anchorEl={filterAnchorEl}
          onClose={onFilterClose}
          startDate={startDate}
          endDate={endDate}
          onStartDate={onStartDate}
          onEndDate={onEndDate}
        />
      )}
      {onExport && (
        <ExportMenu
          anchorEl={exportAnchorEl}
          onClose={onExportClose}
          onExport={onExport}
        />
      )}
    </Toolbar>
  );
};
