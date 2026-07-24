#!/bin/bash
# Downloads the dellstore2 sample database dump used by the test_db compose
# service (see docker-compose.yml). Not committed to git due to its size.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# pinned to a commit (not a branch) so the fetched content can't change under us
COMMIT="e9ac9d7b8cc40e2ed740a6b67842bbf8956b53ba"
URL="https://raw.githubusercontent.com/asotolongo/dell_store/$COMMIT/dellstore2-normal-1.0.zip"
TARGET="$DIR/dellstore2-normal-1.0.sql"

if [ -f "$TARGET" ]; then
    echo "dellstore2-normal-1.0.sql already present, skipping download."
    exit 0
fi

WORKDIR="$(mktemp -d "$DIR/.fetch-dellstore.XXXXXX")"
trap 'rm -rf "$WORKDIR"' EXIT

curl --fail --silent --show-error --location -o "$WORKDIR/dellstore2-normal-1.0.zip" "$URL"
unzip -o "$WORKDIR/dellstore2-normal-1.0.zip" -d "$WORKDIR" >/dev/null
chmod 644 "$WORKDIR/dellstore2-normal-1.0.sql"

# extraction happens entirely outside $DIR, so a failed download or a corrupt
# extraction never leaves a partial file at $TARGET
mv "$WORKDIR/dellstore2-normal-1.0.sql" "$TARGET"
echo "Downloaded dellstore2-normal-1.0.sql"
