FROM python:3.14-slim

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

ARG OPENTOFU_VERSION=1.11.6
ARG GH_VERSION=2.91.0
ARG ACT_VERSION=0.2.87

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy

# Install OpenTofu
RUN curl -fsSL "https://github.com/opentofu/opentofu/releases/download/v${OPENTOFU_VERSION}/tofu_${OPENTOFU_VERSION}_linux_amd64.zip" \
    -o /tmp/opentofu.zip \
    && unzip /tmp/opentofu.zip -d /usr/local/bin/ tofu \
    && rm /tmp/opentofu.zip \
    && tofu -install-autocomplete

# Install GitHub CLI
RUN curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.tar.gz" \
    -o /tmp/gh.tar.gz \
    && tar -xzf /tmp/gh.tar.gz -C /tmp \
    && mv /tmp/gh_${GH_VERSION}_linux_amd64/bin/gh /usr/local/bin/gh \
    && rm -rf /tmp/gh.tar.gz /tmp/gh_${GH_VERSION}_linux_amd64

# Install act
RUN curl -fsSL "https://github.com/nektos/act/releases/download/v${ACT_VERSION}/act_Linux_x86_64.tar.gz" \
    -o /tmp/act.tar.gz \
    && tar -xzf /tmp/act.tar.gz -C /usr/local/bin/ act \
    && rm /tmp/act.tar.gz

WORKDIR /workspaces/cloudporter
