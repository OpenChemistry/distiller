import React, { useEffect, useState } from 'react';
import { getBlob } from '../client/blob';

interface Props extends React.ComponentPropsWithoutRef<'img'> {
  component: React.ElementType;
}

export const ProtectedImage: React.FC<Props> = (props) => {
  const { src, component, ...rest } = props;

  const [objectURL, setObjectURL] = useState<string | undefined>();

  useEffect(() => {
    let ignore = false;

    if (src) {
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
