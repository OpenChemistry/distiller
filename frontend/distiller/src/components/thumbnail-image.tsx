import { styled } from '@mui/material/styles';

type ThumbnailImageProps = {
  width?: string;
  height?: string;
  cursor?: string;
};

export const ThumbnailImage = styled('img')<ThumbnailImageProps>(
  ({ width = '100%', height = '100%', cursor = 'pointer' }) => ({
    width,
    height,
    objectFit: 'contain',
    cursor,
  }),
);
