FROM python:3.11-slim

RUN pip install --no-cache-dir garak

RUN groupadd --gid 1000 fortress \
    && useradd --uid 1000 --gid fortress --create-home --shell /usr/sbin/nologin fortress

WORKDIR /srv/fortress
COPY scripts/ /srv/fortress/scripts/
RUN chown -R fortress:fortress /srv/fortress

USER fortress

CMD ["garak", "--help"]