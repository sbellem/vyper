FROM python:3.9.0a6-buster
#FROM python:3.8

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
        #gcc \
        #git \
        #libc6-dev \
        libc-dev \
        #libssl-dev \
        #libgmp-dev \
    && rm -rf /var/lib/apt/lists/*

ADD . /code

WORKDIR /code

# Pass `--addopts "--version"` because want to execute `python setup.py test` to include test dependencies in built docker-image, but avoid to execute the whole test suite here.
#RUN python setup.py install && \
#    python setup.py test --addopts "--version" && \
#    apt-get purge -y --auto-remove apt-utils gcc libc6-dev libc-dev libssl-dev

# dev deps
RUN apt-get update && apt-get install -y npm
RUN npm install -g ganache-cli

# Rust -- needed to build blake2b-py with Python 3.9
ENV RUSTUP_HOME /usr/local/rustup
ENV CARGO_HOME /usr/local/cargo
COPY --from=rustlang/rust:nightly-buster $RUSTUP_HOME $RUSTUP_HOME
COPY --from=rustlang/rust:nightly-buster $CARGO_HOME $CARGO_HOME
ENV PATH "${CARGO_HOME}/bin:${PATH}"

RUN pip install -e .["dev","lint","test"]
#    python setup.py test --addopts "--version" && \
#    apt-get purge -y --auto-remove apt-utils gcc libc6-dev libc-dev libssl-dev

#ENTRYPOINT ["/usr/local/bin/vyper"]
#ENTRYPOINT ["bash"]
