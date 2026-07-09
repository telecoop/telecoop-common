FROM ghcr.io/astral-sh/uv:python3.13-trixie

RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt -y install locales openvpn && \
    sed -i '/fr_FR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=fr_FR.UTF-8 \
    LANGUAGE=fr_FR:fr \
    LC_ALL=fr_FR.UTF-8 \
    PATH="/app/.venv/bin:$PATH" \
    UV_CACHE_DIR=/tmp/uv_cache

RUN mkdir /opt/telecoop-common
COPY . /opt/telecoop-common
WORKDIR /opt/telecoop-common
RUN --mount=type=cache,target=UV_CACHE_DIR uv sync --upgrade
