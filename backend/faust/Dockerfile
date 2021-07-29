
FROM python:3.9-slim

RUN apt-get update -y --fix-missing \
  && apt-get install -y \
    build-essential \
    curl \
    libsnappy-dev \
    libbz2-dev \
    liblz4-dev \
    zlib1g-dev \
    librocksdb-dev

RUN apt-get remove -y \
  build-essential \
  curl \
  && rm -rf /tmp

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY *.py /app/
COPY *.env /app/

CMD ["faust", "-A", "worker", "worker", "-l", "info"]