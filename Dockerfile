FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    handbrake-cli \
    mkvtoolnix \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --break-system-packages

COPY . .

RUN mkdir -p /app/data
RUN python3 manage.py migrate --run-syncdb
RUN python3 manage.py loaddata initial_profiles.json || true

EXPOSE 8000
ENTRYPOINT ["./scripts/entrypoint.sh"]
