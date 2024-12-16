FROM python:3.10-slim AS builder

ARG FLIPPER_UID
ARG FLIPPER_GID

RUN apt-get update && apt-get -y install \
    libpq-dev \
    gcc

WORKDIR /app

COPY Pipfile ./
COPY Pipfile.lock ./
COPY ./src/ ./src/

RUN pip install pipenv
RUN pipenv install --deploy --system
RUN pip uninstall pipenv -y

RUN apt-get remove -y gcc
RUN apt-get autoremove -y

RUN addgroup --gid $FLIPPER_GID flipper
RUN adduser --disabled-login --disabled-password --uid $FLIPPER_UID --gid $FLIPPER_GID flipper

USER flipper

WORKDIR /app/src
ENTRYPOINT './flipper.py'
