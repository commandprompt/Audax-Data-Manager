#!/bin/bash
# Runs inside the mssql_test_db_init sidecar (see docker-compose.yml) once
# mssql_test_db reports healthy: creates the northwind_test database and
# loads the Northwind fixture into it. Idempotent - safe to re-run.
set -e

SQLCMD=/opt/mssql-tools18/bin/sqlcmd
HOST=mssql_test_db

run() {
    "$SQLCMD" -S "$HOST" -U sa -P "$MSSQL_SA_PASSWORD" -C "$@"
}

run -Q "IF DB_ID('northwind_test') IS NULL CREATE DATABASE northwind_test"
run -d northwind_test -i /tmp/instnwnd.sql
echo "northwind_test database ready."
