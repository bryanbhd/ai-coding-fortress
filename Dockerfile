FROM python:3.11-slim

RUN pip install --no-cache-dir garak

WORKDIR /srv/fortress
COPY scripts/ /srv/fortress/scripts/

CMD ["garak", "--help"]