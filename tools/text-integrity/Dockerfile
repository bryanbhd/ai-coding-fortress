FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/watermark-detector
COPY scan.py /opt/watermark-detector/scan.py
COPY upstream/ /opt/watermark-detector/upstream/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER 65532:65532
ENTRYPOINT ["python3", "/opt/watermark-detector/scan.py"]
