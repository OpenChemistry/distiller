FROM python:3.11-slim-bookworm

WORKDIR /app/

COPY ./requirements.txt /app/

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app/app
COPY ./.env /app/
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/

ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=80

EXPOSE 80

CMD ["sh", "-c", "exec uvicorn app.main:app --host ${HOST} --port ${PORT}"]
