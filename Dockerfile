FROM python:3.10-slim AS builder

RUN apt-get update && apt-get -y install \
    libpq-dev \
    gcc


FROM builder AS build

ARG FLIPPER_UID
ARG FLIPPER_GID

WORKDIR /app

COPY Pipfile ./
COPY Pipfile.lock ./

RUN pip install pipenv && \
    pipenv install --deploy --system && \
    pip uninstall pipenv -y && \
    apt-get remove -y gcc && \
    apt-get autoremove -y

COPY ./src/ ./src/


FROM build AS runtime

RUN addgroup --gid $FLIPPER_GID flipper && \
    adduser --disabled-login --disabled-password --uid $FLIPPER_UID --gid $FLIPPER_GID flipper

USER flipper

WORKDIR /app/src
ENTRYPOINT ["python", "flipper.py"]
