FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONUNBUFFERED True
ARG PORT=8080

WORKDIR /app
COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 0 main:app
