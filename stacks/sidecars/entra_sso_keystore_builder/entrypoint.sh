#!/bin/bash

SECRETS_DIR="${1:-/run/secrets}"
KEYSTORE_PATH="${2:-/opt/output/samlKeystore.jks}"
ALIAS="${3:-huloop}"
DNAME_CN="${4:-Huloop}"
DNAME_OU="${5:-Huloop}"
DNAME_O="${6:-Huloop}"
DNAME_L="${7:-Huloop}"
DNAME_ST="${8:-Huloop}"
DNAME_C="${9:-Huloop}"

mkdir -p "$(dirname "${KEYSTORE_PATH}")"

if [ -f "${KEYSTORE_PATH}" ]; then
    echo "Removing existing keystore at ${KEYSTORE_PATH}"
    rm -f "${KEYSTORE_PATH}"
fi

"${JAVA_HOME}/bin/keytool" \
    -importcert \
    -alias adfssigning \
    -keystore "${KEYSTORE_PATH}" \
    -file "${SECRETS_DIR}/signature.cer" \
    -storepass:file "${SECRETS_DIR}/key.pass" \
    -noprompt

"${JAVA_HOME}/bin/keytool" \
    -genkeypair \
    -alias "${ALIAS}" \
    -keypass:file "${SECRETS_DIR}/key.pass" \
    -keystore "${KEYSTORE_PATH}" \
    -storepass:file "${SECRETS_DIR}/key.pass" \
    -dname "CN=${DNAME_CN}, OU=${DNAME_OU}, O=${DNAME_O}, L=${DNAME_L}, ST=${DNAME_ST}, C=${DNAME_C}" \
    -keyalg rsa \
    -keysize 2048 \
    -validity 10000

echo
echo "Keystore info:"
ls -lhd $(dirname "${KEYSTORE_PATH}")/*