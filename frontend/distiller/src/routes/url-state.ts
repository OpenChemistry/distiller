import { useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

export type Serializer<T> = (value: T) => string;
export type Deserializer<T> = (value: string) => T;
export type Comparer<T> = (prevValue: T, currValue: T) => boolean;

function defaultComparer<T>(prev: T, curr: T): boolean {
  return prev === curr;
}

export function useUrlState<T>(
  key: string,
  initialValue: T,
  serializer: Serializer<T>,
  deserializer: Deserializer<T>,
  comparer: Comparer<T> = defaultComparer
): [T, (value: T) => void] {
  const refValue = useRef<T>(initialValue);

  const [searchParams, setSearchParams] = useSearchParams();

  const rawValue = searchParams.get(key);

  const value: T = rawValue ? deserializer(rawValue) : initialValue;

  if (!comparer(value, refValue.current)) {
    refValue.current = value;
  }

  const setValue = useCallback(
    (newValue: T) => {
      const prevParams = new URLSearchParams(window.location.search);

      const newParams = {
        ...Object.fromEntries(prevParams),
        [key]: serializer(newValue),
      };

      setSearchParams(newParams, { replace: true });
    },
    [key, serializer, setSearchParams]
  );

  return [refValue.current, setValue];
}
