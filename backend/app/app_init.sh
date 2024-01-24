#!/bin/sh

SCRIPT_DIR=$(realpath $(dirname $0))
MC_PATH=${SCRIPT_DIR}/../minio-binaries/mc

# Create the patient image bucket and make it public so that the client can reach the images
${MC_PATH} config host add localminio "http://${MINIO_SERVER_HOST}:9000" "${MINIO_SERVER_ACCESS_KEY}" "${MINIO_SERVER_SECRET_KEY}"
${MC_PATH} mb "localminio/${PATIENT_IMG_BUCKET}"
${MC_PATH} anonymous set public "localminio/${PATIENT_IMG_BUCKET}"

# If running behind a proxy like Nginx or Traefik add --proxy-headers
uvicorn app.main:app --proxy-headers --reload --host 0.0.0.0 --port 80 --root-path ${PROXY_PREFIX_PATH} || exit 1
