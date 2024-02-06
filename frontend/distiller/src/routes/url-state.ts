import { useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { isNil } from 'lodash';
import { DateTime } from 'luxon';

export type Serializer<T> = (value: T | undefined) => string;
export type Deserializer<T> = (value: string) => T | undefined;

export function useUrlState<T>(
  key: string,
  initialValue: T,
  serializer: Serializer<T>,
  deserializer: Deserializer<T>,
): [T, (value: T) => void] {
  const refValue = useRef<T>(initialValue);
  const refInitialized = useRef(false);

  const [searchParams, setSearchParams] = useSearchParams();

  if (!refInitialized.current) {
    const rawValue = searchParams.get(key);

    const value: T = rawValue
      ? deserializer(rawValue) || initialValue
      : initialValue;

    refValue.current = value;
    refInitialized.current = true;
  }

  const setValue = useCallback(
    (newValue: T) => {
      const prevParams = new URLSearchParams(window.location.search);

      const newValueStr = serializer(newValue);

      const newParams = Object.fromEntries(prevParams);

      if (newValueStr === '') {
        delete newParams[key];
        refValue.current = initialValue;
      } else {
        newParams[key] = newValueStr;
        refValue.current = newValue;
      }

      setSearchParams(newParams, { replace: true });
    },
    [key, initialValue, serializer, setSearchParams],
  );

  return [refValue.current, setValue];
}

export const dateTimeSerializer: Serializer<DateTime | null> = (dt) => {
  if (!isNil(dt)) {
    return dt.toString();
  } else {
    return '';
  }
};

export const dateTimeDeserializer: Deserializer<DateTime | null> = (dtStr) => {
  const dt = DateTime.fromISO(dtStr);
  if (dt.isValid) {
    return dt;
  } else {
    return null;
  }
};

export const intSerializer: Serializer<number> = (n) => {
  if (isNil(n)) {
    return '';
  } else {
    return n.toString();
  }
};

export const intDeserializer: Deserializer<number> = (nStr) => {
  const n = parseInt(nStr);

  if (!Number.isFinite(n)) {
    return undefined;
  }

  return n;
};
