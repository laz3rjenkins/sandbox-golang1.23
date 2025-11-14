FROM python:3.13-slim-bookworm

ARG SANDBOX_USER_UID
ARG SANDBOX_DIR

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
        nano \
        ca-certificates \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

ENV GOLANG_VERSION=1.23.3
RUN curl -OL https://go.dev/dl/go${GOLANG_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GOLANG_VERSION}.linux-amd64.tar.gz && \
    rm go${GOLANG_VERSION}.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"
ENV PYTHONPATH=/app/src

RUN pip install --upgrade pip && pip install pipenv

RUN adduser \
    --system \
    --gecos "" \
    --disabled-login \
    --disabled-password \
    --home ${SANDBOX_DIR} \
    --uid ${SANDBOX_USER_UID} \
    sandbox && \
    mkdir -p ${SANDBOX_DIR} && \
    chown root:root ${SANDBOX_DIR}

COPY ./src/Pipfile ./src/Pipfile.lock /tmp/
RUN cd /tmp && pipenv install --deploy --dev --system

RUN chmod 1777 /tmp

WORKDIR ${SANDBOX_DIR}

RUN go version && python3 --version

CMD ["gunicorn", "--pythonpath", "/app/src", "--bind", "0:9002", "app.main:app", "--reload", "-w", "1"]
