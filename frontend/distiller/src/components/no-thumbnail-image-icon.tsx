import ImageIcon from '@mui/icons-material/Image';
import { pink } from '@mui/material/colors';
import { styled } from '@mui/material/styles';

type NoThumbnailImageIconProps = {
  width?: string;
  height?: string;
  cursor?: string;
};

export const NoThumbnailImageIcon = styled(
  ImageIcon,
)<NoThumbnailImageIconProps>(
  ({ width = '60%', height = '60%', cursor = 'pointer' }) => ({
    width,
    height,
    objectFit: 'contain',
    color: pink.A400,
    cursor,
  }),
);
