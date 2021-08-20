import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';

import { AppDispatch, RootState } from "../../app/store";
import { apiClient } from '../../client';
import { startMockNotifications } from './mock';
import { isCreatedEvent, isUpdatedEvent } from './events';
import { setScan, updateScan } from '../scans';

class NotificationHub {
  constructor(ws: WebSocket, getState: () => RootState, dispatch: AppDispatch) {
    const messageListener = (ev: MessageEvent<string>) => {
      let msg: any = undefined;
      try {
        msg = JSON.parse(ev.data);
      } catch {}

      if (isCreatedEvent(msg)) {
        dispatch(setScan(msg));
      } else if (isUpdatedEvent(msg)) {
        dispatch(updateScan(msg));
      }
    };

    ws.addEventListener('message', messageListener);
    ws.addEventListener('close', () => {
      dispatch(setStatus('disconnected'));
      ws.removeEventListener('message', messageListener);
    })
  }
}

let notificationHub: NotificationHub | undefined = undefined;

export interface NotificationsState {
  status: 'connected' | 'disconnected' | 'connecting';
}

const initialState: NotificationsState = {
  status: 'disconnected',
}

export const connectNotifications = createAsyncThunk(
  'notifications/connect',
  async (_payload, thunkAPI) => {
    const {dispatch, getState} = thunkAPI;

    let ws: WebSocket = await apiClient.ws({url: 'notifications'})

    notificationHub = new NotificationHub(ws, getState as any, dispatch);

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
    }
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

export const {setStatus} = notificationsSlice.actions;

export function getNotificationHub() {
  return notificationHub;
};

export default notificationsSlice.reducer;
