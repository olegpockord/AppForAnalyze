FROM python:3.12-slim-trixie

ENV PYTHONUNBUFFED=1 \
PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y curl

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt ./requirements.txt

RUN uv pip install -r requirements.txt --system

WORKDIR /AppForAnalyze

COPY . .

RUN chmod -R 777 ./
