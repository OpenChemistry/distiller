import React, { useEffect, useState } from 'react';
import { getBlob } from '../client/blob';
import { isStatic } from '../utils';

interface Props extends React.ComponentPropsWithoutRef<'img'> {
  component: React.ElementType;
}

const dataURLtoBlob = (dataURL: string) => {
  // data URL to blob
  const [header, base64Data] = dataURL.split(',');
  const data = atob(base64Data);
  const array = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) {
    array[i] = data.charCodeAt(i);
  }
  // get the mime type
  const mime = header.substring('data:'.length, header.length - 1);

  return new Blob([array], { type: mime });
};

export const ProtectedImage: React.FC<Props> = (props) => {
  const { src, component, ...rest } = props;

  const [objectURL, setObjectURL] = useState<string | undefined>();

  useEffect(() => {
    let ignore = false;

    if (src) {
      // Special case for static mode, extract the data from the URL to create the object URL
      if (isStatic()) {
        const blob = dataURLtoBlob(src);
        setObjectURL(URL.createObjectURL(blob));

        return;
      }

      (async () => {
        const image = await getBlob(src);

        if (!ignore) {
          const url = URL.createObjectURL(image);
          setObjectURL(url);
        }
      })();
    }

    return () => {
      ignore = true;
    };
  }, [src]);

  const onLoad = () => {
    if (objectURL) {
      URL.revokeObjectURL(objectURL);
    }
  };

  if (objectURL === undefined) {
    return null;
  }

  return React.createElement(component, { src: objectURL, onLoad, ...rest });
};
