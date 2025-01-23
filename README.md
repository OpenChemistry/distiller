# Distiller

Distiller is designed to streamline data acquisition and processing workflows for microscopy data. It integrates real-time monitoring, remote job launching, and post-processing capabilities, leveraging NERSC's high-performance computing (HPC) resources.

## Features

- **Real-time Monitoring**: Detects new microscopy data and displays metadata.
- **Automated HPC Processing**: Launches jobs at NERSC for data transfer and electron counting using [stempy](https://github.com/openchemistry/stempy).
- **Streaming Sessions**: Enables real-time data processing on NERSC compute nodes.
- **Jupyter Notebooks**: Facilitates post-processing via NERSC's Jupyter hub.

## Technologies

- **Frontend**: React
- **Backend**: FastAPI, Kafka, Microservices
- **Integration**: Superfacility API (NERSC)

## Videos

- **Scans Page**
  - Shows recent acquisitions. One can filter acquisitions to a date range on this page.

<https://github.com/user-attachments/assets/6217e5b9-318c-498b-83ab-f5705eb9532f>

- **Scan Page and Jupyter@NERSC**
  - Shows individual scan, and launching an electron counting job on NERSC compute nodes. After the data is processed, we can create a templated Jupyter notebook running on [NERSC's Jupyterhub](https://docs.nersc.gov/services/jupyter/) for post-processing

<https://github.com/user-attachments/assets/012624bf-6e3c-48e1-a4ea-515e9b33c869>

- **Streaming Session**
  - A streaming session runs in Distiller (left) while collecting data on the TEAM 0.5 microscope with DigitalMicrograph (right).

<https://github.com/user-attachments/assets/d64886ed-9a8a-4be0-bca7-3487537e4400>
