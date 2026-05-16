FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    handbrake-cli \
    mkvtoolnix \
    ffmpeg \
    gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --break-system-packages

COPY . .
RUN chmod +x scripts/entrypoint.sh scripts/rqworker.sh
RUN mkdir -p /app/data

EXPOSE 8000
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
