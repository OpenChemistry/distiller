import {
  AnyAction,
  createAsyncThunk,
  createSlice,
  ThunkDispatch,
} from '@reduxjs/toolkit';
import { isNil } from 'lodash';
import { matchPath, Path } from 'react-router';
import { RootState } from '../../app/store';
import { apiClient } from '../../client';
import { Microscope, User } from '../../types';
import { canonicalMicroscopeName } from '../../utils/microscopes';
import { getMachines } from '../machines';
import { getMicroscopes } from '../microscopes';
import { connectNotifications } from '../notifications';
import {
  authenticate as authenticateAPI,
  deleteRefreshToken as deleteRefreshTokenAPI,
  getUser as getUserAPI,
  refreshToken as refreshTokenAPI,
} from './api';
import { isStatic } from '../../utils';
import { loginInteractem } from '@interactem/interactem';

export interface AuthState {
  user?: User;
  status: 'unknown' | 'authenticated' | 'authenticating' | 'anonymous';
}

const initialState: AuthState = {
  user: undefined,
  status: 'unknown',
};

let refreshController = new AbortController();

const getMicroscopeID = (microscopes: Microscope[], pathName: string) => {
  // Get microscopes by canonical name
  const microscopesByCanonicalName = microscopes.reduce(
    (obj: { [key: string]: Microscope }, microscope) => {
      obj[canonicalMicroscopeName(microscope.name)] = microscope;

      return obj;
    },
    {},
  );

  const pathMatch = matchPath({ path: '/:microscopeName/*' }, pathName);
  // Default to 4dcamera
  if (pathMatch === null) {
    return microscopes[0].id;
  }

  const { microscopeName } = pathMatch.params;
  if (isNil(microscopeName)) {
    throw new Error('Unable to extract microscope');
  }
  const canonicalName = canonicalMicroscopeName(microscopeName);
  // Look up the microscope id
  if (!(canonicalName in microscopesByCanonicalName)) {
    throw new Error('Unable to find microscope ID');
  }

  const microscope = microscopesByCanonicalName[canonicalName];
  const microscopeID = microscope.id;

  return microscopeID;
};

type AuthenticatePayload = { username: string; password: string; from: Path };
export const login = createAsyncThunk<User, AuthenticatePayload>(
  'auth/authenticate',
  async (payload, thunkAPI) => {
    const { username, password, from } = payload;
    const { dispatch } = thunkAPI;

    const auth = await authenticateAPI(username, password);

    const { access_token, exp } = auth;
    apiClient.setToken(access_token);
    const res = await loginInteractem(access_token);
    if (!res.success) {
      console.error(res.error);
    }

    refreshController.abort();
    const controller = new AbortController();
    refreshController = controller;

    setTimeout(
      () => {
        refreshToken(true, thunkAPI.dispatch, controller.signal);
      },
      (exp - 30) * 1000,
    ); // Refresh 30 seconds before actual expiration

    const microscopes = await dispatch(getMicroscopes()).unwrap();
    const microscopeID = getMicroscopeID(microscopes, from.pathname);
    dispatch(connectNotifications({ microscopeID }));
    dispatch(getMachines());

    const user = await getUserAPI();

    return user;
  },
);

async function refreshToken(
  autoRefresh: boolean,
  dispatch: ThunkDispatch<unknown, unknown, AnyAction>,
  signal: AbortSignal,
) {
  try {
    const auth = await refreshTokenAPI();

    const { access_token, exp } = auth;
    apiClient.setToken(access_token);
    const res = await loginInteractem(access_token);
    if (!res.success) {
      console.error(res.error);
    }

    if (autoRefresh) {
      setTimeout(
        () => {
          if (!signal.aborted) {
            refreshToken(autoRefresh, dispatch, signal);
          }
        },
        (exp - 30) * 1000,
      ); // Refresh 30 seconds before actual expiration
    }
  } catch (e) {
    dispatch(logout());
    throw e;
  }
}

export const restoreSession = createAsyncThunk<User, void>(
  'auth/restore_session',
  async (_payload, thunkAPI) => {
    const { dispatch } = thunkAPI;

    refreshController.abort();
    const controller = new AbortController();
    refreshController = controller;

    await refreshToken(true, thunkAPI.dispatch, controller.signal);
    const microscopes = await dispatch(getMicroscopes()).unwrap();
    // Only connect notifications if not in static mode
    if (!isStatic()) {
      const microscopeID = getMicroscopeID(
        microscopes,
        window.location.pathname,
      );
      dispatch(connectNotifications({ microscopeID }));
    }
    dispatch(getMachines());

    const user = await getUserAPI();

    return user;
  },
);

export const logout = createAsyncThunk<void, void>(
  'auth/logout',
  async (_payload, _thunkAPI) => {
    refreshController.abort();
    await deleteRefreshTokenAPI();
    apiClient.setToken(undefined);
  },
);

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {},
  // The `extraReducers` field lets the slice handle actions defined elsewhere,
  // including actions generated by createAsyncThunk or in other slices.
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.status = 'authenticating';
        state.user = undefined;
      })
      .addCase(login.rejected, (state) => {
        state.status = 'anonymous';
        state.user = undefined;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = 'authenticated';
        state.user = action.payload;
      })
      .addCase(logout.fulfilled, (state) => {
        state.status = 'anonymous';
        state.user = undefined;
      })
      .addCase(restoreSession.fulfilled, (state, action) => {
        state.status = 'authenticated';
        state.user = action.payload;
      });
  },
});

export const isAuthenticated = (state: RootState) =>
  state.auth.status === 'authenticated';
export const authStatus = (state: RootState) => state.auth.status;
export const getUser = (state: RootState) => state.auth.user;

export default authSlice.reducer;
