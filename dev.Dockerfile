FROM python:3.8-slim

# Specify label-schema specific arguments and labels.
ARG BUILD_DATE
ARG VCS_REF
LABEL org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.name="Vyper" \
    org.label-schema.description="Vyper is an experimental programming language" \
    org.label-schema.url="https://vyper.readthedocs.io/en/latest/" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/vyperlang/vyper" \
    org.label-schema.vendor="Vyper Team" \
    org.label-schema.schema-version="1.0"

# coincurve requires libgmp
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        apt-utils \
        build-essential \
        gcc \
        git \
        libc6-dev \
        libc-dev \
        libssl-dev \
        libgmp-dev \
    && rm -rf /var/lib/apt/lists/*

ADD . /code

WORKDIR /code

# dev deps
RUN apt-get update && apt-get install -y npm
RUN npm install -g ganache-cli

RUN pip install -e .["dev","lint","test"]
RUN pip install astunparse
