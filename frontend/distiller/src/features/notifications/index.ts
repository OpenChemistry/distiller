import {
  createAsyncThunk,
  createSlice,
  PayloadAction,
  ThunkDispatch,
  AnyAction,
} from '@reduxjs/toolkit';

import { apiClient } from '../../client';
import { startMockNotifications } from './mock';
import {
  isJobUpdatedEvent,
  isJobSubmitEvent,
  isMicroscopeUpdatedEvent,
  isScanCreatedEvent,
  isScanUpdatedEvent,
} from './events';
import { setScan, updateScan } from '../scans';
import { updateMicroscope } from '../microscopes';
import { updateJob, setJob } from '../jobs';

class NotificationHub {
  constructor(
    ws: WebSocket,
    dispatch: ThunkDispatch<unknown, unknown, AnyAction>
  ) {
    const messageListener = (ev: MessageEvent<string>) => {
      let msg: any = undefined;
      try {
        msg = JSON.parse(ev.data);
      } catch {}

      if (isScanCreatedEvent(msg)) {
        const scan = { ...msg, jobs: [] };
        dispatch(setScan(scan));
      } else if (isScanUpdatedEvent(msg)) {
        dispatch(updateScan(msg));
      } else if (isMicroscopeUpdatedEvent(msg)) {
        dispatch(updateMicroscope(msg));
      } else if (isJobSubmitEvent(msg)) {
        const { job } = { ...msg };
        dispatch(setJob(job));
      } else if (isJobUpdatedEvent(msg)) {
        dispatch(updateJob(msg));
      }
    };

    ws.addEventListener('message', messageListener);
    ws.addEventListener('close', () => {
      dispatch(setStatus('disconnected'));
      ws.removeEventListener('message', messageListener);
    });
  }
}

let notificationHub: NotificationHub | undefined = undefined;

export interface NotificationsState {
  status: 'connected' | 'disconnected' | 'connecting';
}

const initialState: NotificationsState = {
  status: 'disconnected',
};

type ConnectPayload = { microscopeID: number };
export const connectNotifications = createAsyncThunk<void, ConnectPayload>(
  'notifications/connect',
  async (payload, thunkAPI) => {
    const { dispatch } = thunkAPI;
    const { microscopeID } = payload;

    let ws: WebSocket = await apiClient.ws({
      url: 'notifications',
      params: { microscope_id: microscopeID },
    });

    notificationHub = new NotificationHub(ws, dispatch);

    const mock = process.env.NODE_ENV === 'development';

    if (mock) {
      startMockNotifications(ws);
    }
  }
);

export const notificationsSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    setStatus(state, action: PayloadAction<NotificationsState['status']>) {
      state.status = action.payload;
    },
  },
  // The `extraReducers` field lets the slice handle actions defined elsewhere,
  // including actions generated by createAsyncThunk or in other slices.
  extraReducers: (builder) => {
    builder
      .addCase(connectNotifications.pending, (state) => {
        state.status = 'connecting';
      })
      .addCase(connectNotifications.rejected, (state) => {
        state.status = 'disconnected';
      })
      .addCase(connectNotifications.fulfilled, (state, _action) => {
        state.status = 'connected';
      });
  },
});

export const { setStatus } = notificationsSlice.actions;

export function getNotificationHub() {
  return notificationHub;
}

export default notificationsSlice.reducer;
