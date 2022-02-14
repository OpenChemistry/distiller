import React from 'react';

export function stopPropagation(fn: (ev: React.MouseEvent) => void) {
  return function (ev: React.MouseEvent) {
    if (ev.stopPropagation) {
      ev.stopPropagation();
    } else if (window.event) {
      window.event.cancelBubble = true;
    }

    fn(ev);
  };
}

export function isNil<T>(val: T | undefined | null): val is undefined | null {
  return val === undefined || val === null;
}

export function pickNil<T, N extends undefined | null>(
  val: T | undefined | null,
  nil: N
): T | N {
  if (isNil(val)) {
    return nil;
  } else {
    return val;
  }
}
