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
