import {
  createAsyncThunk,
  createSlice,
  createEntityAdapter,
  PayloadAction,
  createSelector,
} from '@reduxjs/toolkit';
import { RootState } from '../../app/store';
import {
  getScans as getScansAPI,
  getScan as getScanAPI,
  patchScan as patchScanAPI,
  removeScanFiles as removeScanFilesAPI,
  removeScan as removeScanAPI,
} from './api';
import { Scan, IdType, ScansRequestResult } from '../../types';
import { DateTime } from 'luxon';

export const scansAdapter = createEntityAdapter<Scan>();

export interface ScansState
  extends ReturnType<(typeof scansAdapter)['getInitialState']> {
  status: 'idle' | 'loading' | 'complete';
  totalCount: number;
}

const initialState: ScansState = scansAdapter.getInitialState({
  status: 'idle',
  totalCount: -1,
});

export const getScans = createAsyncThunk<
  ScansRequestResult,
  {
    skip: number;
    limit: number;
    start?: DateTime;
    end?: DateTime;
    microscopeId: IdType;
  }
>('scans/fetch', async (_payload, _thunkAPI) => {
  const { skip, limit, start, end, microscopeId } = _payload;
  const result = await getScansAPI(microscopeId, skip, limit, start, end);

  return result;
});

export const getScan = createAsyncThunk<Scan, { id: IdType }>(
  'scan/fetch',
  async (payload, _thunkAPI) => {
    const { id } = payload;
    const scan = await getScanAPI(id);

    return scan;
  }
);

export const patchScan = createAsyncThunk<
  Scan,
  { id: IdType; updates: Partial<Scan> }
>('scans/patch', async (payload, _thunkAPI) => {
  const { id, updates } = payload;
  const scan = await patchScanAPI(id, updates);

  return scan;
});

export const removeScanFiles = createAsyncThunk<
  void,
  { id: IdType; host: string }
>('scans/remove-files', async (payload, _thunkAPI) => {
  const { id, host } = payload;
  await removeScanFilesAPI(id, host);
});

export const removeScan = createAsyncThunk<
  IdType,
  { id: IdType; removeScanFiles: boolean }
>('scans/remove', async (payload, _thunkAPI) => {
  const { id, removeScanFiles } = payload;
  await removeScanAPI(id, removeScanFiles);

  return id;
});

export const scansSlice = createSlice({
  name: 'scans',
  initialState,
  reducers: {
    setScan(state, action: PayloadAction<Scan>) {
      state.totalCount = state.totalCount + 1;
      scansAdapter.setOne(state, action.payload);
    },
    updateScan(state, action: PayloadAction<Partial<Scan>>) {
      // const currentScan = scansSelector.selectById
      const { id, ...changes } = action.payload;
      if (id !== undefined) {
        scansAdapter.updateOne(state, { id, changes });
      }
    },
  },
  // The `extraReducers` field lets the slice handle actions defined elsewhere,
  // including actions generated by createAsyncThunk or in other slices.
  extraReducers: (builder) => {
    builder
      .addCase(getScans.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(getScans.rejected, (state) => {
        state.status = 'idle';
      })
      .addCase(getScans.fulfilled, (state, action) => {
        const { totalCount, scans } = action.payload;

        state.status = 'complete';
        state.totalCount = totalCount;
        scansAdapter.setAll(state, scans);
      })
      .addCase(getScan.fulfilled, (state, action) => {
        scansAdapter.setOne(state, action.payload);
      })
      .addCase(patchScan.fulfilled, (state, action) => {
        const update = {
          id: action.payload.id,
          changes: action.payload,
        };
        scansAdapter.updateOne(state, update);
      })
      .addCase(removeScan.fulfilled, (state, action) => {
        scansAdapter.removeOne(state, action.payload);
      });
  },
});

export const scansSelector = scansAdapter.getSelectors<RootState>(
  (state) => state.scans
);

const scanState = (rootState: RootState) => rootState.scans;
const { selectById } = scansAdapter.getSelectors();
export const scanSelector = (id: IdType) => {
  return createSelector(scanState, (state) => selectById(state, id));
};

export const totalCount = (state: RootState) => state.scans.totalCount;

export const { setScan, updateScan } = scansSlice.actions;

export default scansSlice.reducer;
