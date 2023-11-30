import { Action, ThunkAction, configureStore } from '@reduxjs/toolkit';
import authReducer from '../features/auth';
import jobsReducer from '../features/jobs';
import machinesReducer from '../features/machines';
import microscopesReducer from '../features/microscopes';
import notebooksReducer from '../features/notebooks';
import notificationsReducer from '../features/notifications';
import scansReducer from '../features/scans';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    scans: scansReducer,
    notifications: notificationsReducer,
    machines: machinesReducer,
    microscopes: microscopesReducer,
    notebooks: notebooksReducer,
    jobs: jobsReducer,
  },
});

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
export type AppThunk<ReturnType = void> = ThunkAction<
  ReturnType,
  RootState,
  unknown,
  Action<string>
>;
