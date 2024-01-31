#!/bin/sh

SCRIPT_DIR=$(realpath $(dirname $0))
MC_PATH=${SCRIPT_DIR}/../minio-binaries/mc

# Create the patient image bucket and make it public so that the client can reach the images
${MC_PATH} config host add localminio "http://${MINIO_SERVER_HOST}:9000" "${MINIO_SERVER_ACCESS_KEY}" "${MINIO_SERVER_SECRET_KEY}"
${MC_PATH} mb "localminio/${PATIENT_IMG_BUCKET}"
${MC_PATH} mb "localminio/${TEST_PATIENT_IMG_BUCKET}"

# sleep for a bit to give bucket above to be created
# else sometimes the app tries to upload to this bucket right after and fails (occasionally)
sleep 1

${MC_PATH} anonymous set public "localminio/${PATIENT_IMG_BUCKET}"
${MC_PATH} anonymous set public "localminio/${TEST_PATIENT_IMG_BUCKET}"
