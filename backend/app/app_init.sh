#!/bin/sh

SCRIPT_DIR=$(realpath $(dirname $0))
${SCRIPT_DIR}/minio_init.sh || exit 1

# If running behind a proxy like Nginx or Traefik add --proxy-headers
uvicorn app.main:app --proxy-headers --reload --host 0.0.0.0 --port 80 --root-path ${PROXY_PREFIX_PATH} || exit 1
