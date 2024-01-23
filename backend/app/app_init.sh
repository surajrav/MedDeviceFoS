#!/bin/sh

SCRIPT_DIR=$(realpath $(dirname $0))

# Make the default bucket public so that the client can reach the images
${SCRIPT_DIR}/../minio-binaries/mc config host add localminio "http://${MINIO_SERVER_HOST}:9000" "${MINIO_SERVER_ACCESS_KEY}" "${MINIO_SERVER_SECRET_KEY}"
${SCRIPT_DIR}/../minio-binaries/mc anonymous set public "localminio/${PATIENT_IMG_BUCKET}"

# If running behind a proxy like Nginx or Traefik add --proxy-headers
uvicorn app.main:app --proxy-headers --reload --host 0.0.0.0 --port 80 --root-path ${PROXY_PREFIX_PATH}
