import {
  createAsyncThunk,
  createSlice,
  createEntityAdapter,
  PayloadAction,
} from '@reduxjs/toolkit';
import { RootState } from '../../app/store';
import { getMicroscopes as getMicroscopesAPI } from './api';
import { IdType, Microscope } from '../../types';

export const microscopesAdapter = createEntityAdapter<Microscope>({
  selectId: (microscope) => microscope.id,
  sortComparer: (a, b) => a.name.localeCompare(b.name),
});

export interface MicroscopesState
  extends ReturnType<typeof microscopesAdapter.getInitialState> {
  status: 'pending' | 'error' | 'loading' | 'complete';
  selected: IdType | null;
}

const initialState: MicroscopesState = microscopesAdapter.getInitialState({
  status: 'pending',
  selected: null,
});

export const getMicroscopes = createAsyncThunk<Microscope[]>(
  'microscopes/fetch',
  async (_payload, _thunkAPI) => {
    const result = await getMicroscopesAPI();

    return result.map((microscope) => ({
      ...microscope,
    }));
  }
);

export const microscopesSlice = createSlice({
  name: 'microscopes',
  initialState,
  reducers: {
    updateMicroscope(state, action: PayloadAction<Partial<Microscope>>) {
      const { id, ...changes } = action.payload;
      if (id !== undefined) {
        microscopesAdapter.updateOne(state, { id, changes });
      }
    },
  },
  // The `extraReducers` field lets the slice handle actions defined elsewhere,
  // including actions generated by createAsyncThunk or in other slices.
  extraReducers: (builder) => {
    builder
      .addCase(getMicroscopes.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(getMicroscopes.rejected, (state) => {
        state.status = 'error';
      })
      .addCase(getMicroscopes.fulfilled, (state, action) => {
        const microscopes = action.payload;

        state.status = 'complete';
        microscopesAdapter.setAll(state, microscopes);
      });
  },
});

export const microscopesState = (rootState: RootState) => rootState.microscopes;
export const microscopesSelectors = microscopesAdapter.getSelectors();
export const { updateMicroscope } = microscopesSlice.actions;

export default microscopesSlice.reducer;
