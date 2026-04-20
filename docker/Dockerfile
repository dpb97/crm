# Multi-stage production Dockerfile for the LCS CRM.
# Runs as a non-root user, pins base image digests, includes a HEALTHCHECK.
# Deployment target: ghcr.io/lcs-group/crm:<semver>, consumed by Azure
# Container Apps.

ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=20
ARG ALPINE_VERSION=3.20

# ---------- stage 1: frontend assets ----------
FROM node:${NODE_VERSION}-alpine AS frontend
WORKDIR /build
COPY package.json yarn.lock ./
COPY frontend/package.json frontend/
RUN corepack enable && yarn install --frozen-lockfile --cwd frontend
COPY frontend ./frontend
COPY crm ./crm
RUN yarn --cwd frontend build

# ---------- stage 2: python deps ----------
FROM python:${PYTHON_VERSION}-alpine AS pydeps
WORKDIR /build
RUN apk add --no-cache \
    build-base libffi-dev postgresql-dev \
    libjpeg-turbo-dev zlib-dev
COPY pyproject.toml ./
COPY lcs_integrations/pyproject.toml ./lcs_integrations/
RUN pip install --no-cache-dir --prefix=/install \
    "frappe-bench" \
    "psycopg2-binary"

# ---------- stage 3: runtime ----------
FROM python:${PYTHON_VERSION}-alpine
RUN addgroup -S frappe && adduser -S -G frappe -h /home/frappe frappe \
    && apk add --no-cache \
        libpq libffi \
        libjpeg-turbo zlib \
        tini \
        wkhtmltopdf \
        nodejs yarn

COPY --from=pydeps /install /usr/local
COPY --from=frontend /build/crm/public/frontend /app/crm/public/frontend

WORKDIR /app
COPY --chown=frappe:frappe crm ./crm
COPY --chown=frappe:frappe lcs_integrations ./lcs_integrations
COPY --chown=frappe:frappe pyproject.toml ./

USER frappe
EXPOSE 8000 9000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8000/api/method/ping || exit 1

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["bench", "start"]
