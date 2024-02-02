import React from 'react';

import { Dialog } from '@mui/material';
import { styled } from '@mui/material/styles';
import { ProtectedImage } from '../components/protected-image';

const StyledDialog = styled(Dialog)(({ theme }) => ({
  width: '100%',
  maxWidth: '50rem',
  maxHeight: '50rem',
  margin: 'auto',
}));

const Image = styled('img')(({ theme }) => ({
  width: '100%',
  height: '100%',
  objectFit: 'contain',
}));

type Props = {
  open: boolean;
  src: string;
  alt: string;
  handleClose: (event: React.MouseEvent) => void;
};

const ImageDialog: React.FC<Props> = (props) => {
  const { open, src, alt, handleClose } = props;

  return (
    <StyledDialog
      open={open}
      onClose={handleClose}
      PaperProps={{ style: { minWidth: '100%', minHeight: '100%' } }}
    >
      <ProtectedImage component={Image} src={src} alt={alt} />
    </StyledDialog>
  );
};

export default ImageDialog;
