import React, { useEffect, useState } from 'react';

import {
  Toolbar,
  Popover,
  TextField,
  Box,
  Grid,
  Button,
  Menu,
  MenuItem,
  Badge,
} from '@mui/material';
import Tooltip from '@mui/material/Tooltip';
import ClearIcon from '@mui/icons-material/Clear';
import FilterListIcon from '@mui/icons-material/FilterList';
import DownloadIcon from '@mui/icons-material/Download';

import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { DateTime } from 'luxon';

import { ExportFormat } from '../types';
import { isNull } from 'lodash';

export type FilterCriteria = {
  start?: DateTime;
  end?: DateTime;
};

type FilterPopoverProps = {
  anchorEl: HTMLElement | null;
  onClose: () => void;
  onFilter: (criteria: FilterCriteria | null) => void;
};

const FilterPopover: React.FC<FilterPopoverProps> = (props) => {
  const { anchorEl, onClose, onFilter } = props;
  const [startDate, setStartDate] = useState<DateTime | null>(null);
  const [endDate, setEndDate] = useState<DateTime | null>(null);
  const [filterCriteria, setFilterCriteria] = useState<FilterCriteria | null>(
    null
  );

  useEffect(() => {
    onFilter(filterCriteria);
  }, [onFilter, filterCriteria]);

  useEffect(() => {
    if (
      (!isNull(startDate) && !startDate.isValid) ||
      (!isNull(endDate) && !endDate.isValid)
    ) {
      return;
    }

    let criteria: FilterCriteria | null = null;
    if (!isNull(startDate)) {
      criteria = {};
      criteria.start = startDate;
    }

    if (!isNull(endDate)) {
      if (criteria === null) {
        criteria = {};
      }
      criteria.end = endDate;
    }

    setFilterCriteria(criteria);
  }, [startDate, endDate]);

  const onStartDateChange = (date: DateTime | null) => {
    setStartDate(date);
  };

  const onEndDateChange = (date: DateTime | null) => {
    setEndDate(date);
  };

  const onResetFiltersClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setStartDate(null);
    setEndDate(null);
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
                  label="Start Date Range"
                  inputFormat="MM/dd/yy"
                  value={startDate}
                  onChange={onStartDateChange}
                  renderInput={(params) => <TextField {...params} />}
                />
              </Grid>
              <Grid item xs={6}>
                <DatePicker
                  label="End Date Range"
                  inputFormat="MM/dd/yy"
                  value={endDate}
                  onChange={onEndDateChange}
                  renderInput={(params) => <TextField {...params} />}
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
    </Menu>
  );
};

type ScansToolbarProps = {
  onFilter: (criteria: FilterCriteria | null) => void;
  onExport: (format: ExportFormat) => void;
  showFilterBadge: boolean;
};

export const ScansToolbar: React.FC<ScansToolbarProps> = (props) => {
  const [filterAnchorEl, setFilterAnchorEl] = useState<HTMLElement | null>(
    null
  );
  const [exportAnchorEl, setExportAnchorEl] = useState<HTMLElement | null>(
    null
  );
  const { onFilter, showFilterBadge, onExport } = props;

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

  return (
    <Toolbar
      sx={{
        pl: { sm: 2 },
        pr: { xs: 1, sm: 1 },
        display: 'flex',
        justifyContent: 'flex-end',
      }}
    >
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
      <Box>
        <Tooltip title="Filter Scans">
          <Button
            onClick={onFilterClick}
            size="small"
            color="primary"
            startIcon={
              <Badge color="primary" variant="dot" invisible={!showFilterBadge}>
                <FilterListIcon />
              </Badge>
            }
          >
            Filter
          </Button>
        </Tooltip>
      </Box>

      <FilterPopover
        anchorEl={filterAnchorEl}
        onClose={onFilterClose}
        onFilter={onFilter}
      />
      <ExportMenu
        anchorEl={exportAnchorEl}
        onClose={onExportClose}
        onExport={onExport}
      />
    </Toolbar>
  );
};
