import React from 'react';

import { Dialog } from '@mui/material';
import { styled } from '@mui/material/styles';

const StyledDialog = styled(Dialog)(({ theme }) => ({
  width: '100%',
  maxWidth: '50rem',
  maxHeight: '50rem',
  margin: 'auto',
}));

const Image = styled('img')(({ theme }) => ({
  width: '100%',
  height: '100%',
  objectFit: 'cover',
}));

type Props = {
  open: boolean;
  src: string;
  alt: string;
  handleClose: () => void;
};

const ImageDialog: React.FC<Props> = (props) => {
  const { open, src, alt, handleClose } = props;

  return (
    <StyledDialog open={open} onClose={handleClose}>
      <Image src={src} alt={alt} />
    </StyledDialog>
  );
};

export default ImageDialog;
