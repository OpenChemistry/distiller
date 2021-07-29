FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

WORKDIR /app/

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY ./app /app/app
COPY ./.env /app/

ENV PYTHONPATH=/app
