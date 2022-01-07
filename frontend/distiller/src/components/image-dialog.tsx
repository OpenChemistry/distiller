import React from 'react';

import { Dialog } from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';

const useStyles = makeStyles((_theme) => ({
  dialog: {
    width: '100%',
    maxWidth: '50rem',
    maxHeight: '50rem',
    margin: 'auto',
  },
  img: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
}));

type Props = {
  open: boolean;
  src: string;
  alt: string;
  handleClose: () => void;
};

const ImageDialog: React.FC<Props> = (props) => {
  const classes = useStyles();

  const { open, src, alt, handleClose } = props;

  return (
    <Dialog open={open} className={classes.dialog} onClose={handleClose}>
      <img src={src} alt={alt} className={classes.img} />
    </Dialog>
  );
};

export default ImageDialog;
