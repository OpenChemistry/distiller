import React, { useEffect, useState, useRef } from 'react';

import { styled } from '@mui/material';
import ImageIcon from '@mui/icons-material/Image';
import { pink } from '@mui/material/colors';
import { Scan } from '../types';
import { staticURL } from '../client';
import ImageDialog from './image-dialog';

const ThumbnailImage = styled('img')(({ theme }) => ({
  width: '10%',
  height: '10%',
  objectFit: 'cover',
  cursor: 'pointer',
}));

const NoThumbnailImageIcon = styled(ImageIcon)(({ theme }) => ({
  width: '10%',
  height: '10%',
  objectFit: 'cover',
  color: pink.A400,
}));

const ImageContainer = styled('div')({
  display: 'flex',
  overflowX: 'auto',
  scrollBehavior: 'smooth',
  '&::-webkit-scrollbar': {
    display: 'none',
  },
});

interface ImageGalleryProps {
  scans: Scan[];
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ scans }) => {
  const [activeImg, setActiveImg] = useState('');
  const [maximizeImg, setMaximizeImg] = useState(false);
  let limit = 10;

  const containerRef = useRef<HTMLDivElement | null>(null);

  const onImgClick = (event: React.MouseEvent, scan: Scan) => {
    event.stopPropagation();
    setActiveImg(`${staticURL}${scan.image_path!}`);
    setMaximizeImg(true);
  };

  const onCloseDialog = (event: React.MouseEvent) => {
    event.stopPropagation();
    setMaximizeImg(false);
  };

  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      if (e.deltaY === 0) return;

      e.preventDefault();

      containerRef.current!.scrollLeft += e.deltaY + e.deltaX;
    };

    const element = containerRef.current!;
    element.addEventListener('wheel', handleWheel);

    return () => {
      element.removeEventListener('wheel', handleWheel);
    };
  }, []);

  return (
    <React.Fragment>
      <ImageContainer ref={containerRef}>
        {scans.slice(0, limit).map((scan) => {
          return scan.image_path ? (
            <ThumbnailImage
              key={scan.id}
              src={`${staticURL}${scan.image_path}`}
              alt="scan thumbnail"
              onClick={(event) => onImgClick(event, scan)}
            />
          ) : (
            <NoThumbnailImageIcon key={scan.id} />
          );
        })}
      </ImageContainer>
      <ImageDialog
        open={maximizeImg}
        src={activeImg}
        alt="scan image"
        handleClose={onCloseDialog}
      />
    </React.Fragment>
  );
};

export default ImageGallery;
