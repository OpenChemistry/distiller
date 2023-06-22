import { configureStore, ThunkAction, Action } from '@reduxjs/toolkit';
import authReducer from '../features/auth';
import scansReducer from '../features/scans';
import notificationsReducer from '../features/notifications';
import machinesReducer from '../features/machines';
import microscopesReducer from '../features/microscopes';
import notebooksReducer from '../features/notebooks';
import jobsReducer from '../features/jobs';

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
