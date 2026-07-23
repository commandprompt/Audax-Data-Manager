#!/bin/bash
# Downloads the dellstore2 sample database dump used by the test_db compose
# service (see docker-compose.yml). Not committed to git due to its size.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL="https://raw.githubusercontent.com/asotolongo/dell_store/master/dellstore2-normal-1.0.zip"
TARGET="$DIR/dellstore2-normal-1.0.sql"

if [ -f "$TARGET" ]; then
    echo "dellstore2-normal-1.0.sql already present, skipping download."
    exit 0
fi

TMP_ZIP="$(mktemp)"
curl -sL -o "$TMP_ZIP" "$URL"
unzip -o "$TMP_ZIP" -d "$DIR"
rm -f "$TMP_ZIP"
chmod 644 "$TARGET"
echo "Downloaded dellstore2-normal-1.0.sql"
