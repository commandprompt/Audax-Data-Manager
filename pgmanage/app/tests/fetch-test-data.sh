#!/bin/bash
# Downloads external sample-database fixtures used by the docker-compose test
# services (dellstore2 for Postgres, Northwind for MSSQL). Not committed to
# git due to their size.
#
# Usage: ./fetch-test-data.sh [dellstore|northwind|all]
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
trap 'rm -rf "$DIR"/.fetch-scratch-* 2>/dev/null || true' EXIT

# Downloads $1 to $2, extracting it first if $1 points at a .zip. Extraction/
# download happens entirely in a scratch dir outside $DIR, so a failed
# download or a corrupt extraction never leaves a partial file at the target.
fetch() {
    local url="$1" target="$2"

    if [ -f "$target" ]; then
        echo "$(basename "$target") already present, skipping download."
        return 0
    fi

    local workdir
    workdir="$(mktemp -d "$DIR/.fetch-scratch-XXXXXX")"

    local download="$workdir/$(basename "$url")"
    curl --fail --silent --show-error --location -o "$download" "$url"

    if [[ "$download" == *.zip ]]; then
        unzip -o "$download" -d "$workdir" >/dev/null
        download="$workdir/$(basename "$target")"
    fi

    chmod 644 "$download"
    mv "$download" "$target"
    rm -rf "$workdir"
    echo "Downloaded $(basename "$target")"
}

fetch_dellstore() {
    # pinned to a commit (not a branch) so the fetched content can't change under us
    local commit="e9ac9d7b8cc40e2ed740a6b67842bbf8956b53ba"
    fetch \
        "https://raw.githubusercontent.com/asotolongo/dell_store/$commit/dellstore2-normal-1.0.zip" \
        "$DIR/dellstore2-normal-1.0.sql"
}

fetch_northwind() {
    # Microsoft's official Northwind install script, pinned to a commit
    local commit="2f85f3724ee45776a5183ed34d064488a6e1dc53"
    fetch \
        "https://raw.githubusercontent.com/microsoft/sql-server-samples/$commit/samples/databases/northwind-pubs/instnwnd.sql" \
        "$DIR/instnwnd.sql"
}

case "${1:-all}" in
    dellstore) fetch_dellstore ;;
    northwind) fetch_northwind ;;
    all)
        fetch_dellstore
        fetch_northwind
        ;;
    *)
        echo "usage: $0 [dellstore|northwind|all]" >&2
        exit 1
        ;;
esac
