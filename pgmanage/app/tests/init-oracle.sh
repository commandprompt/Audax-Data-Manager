#!/bin/bash
# The Oracle image runs this on every start of oracle_test_db, from
# /opt/oracle/scripts/startup (see docker-compose.yml). It loads Oracle's HR
# sample schema into the FREEPDB1 pluggable database and does nothing when the
# schema is already there, which keeps a restart quick.
#
# The three hr_*.sql scripts are Oracle's own and run unchanged. Their
# hr_install.sql wrapper is not used, because it asks for the password and the
# tablespace with SQL*Plus ACCEPT, which does not read piped input reliably.
set -e

CONNECT="system/${ORACLE_PWD}@localhost:1521/FREEPDB1"

# The scripts write a spool log next to themselves, so they run from a
# writable copy and not from the read-only mount.
ALREADY=$(sqlplus -s "$CONNECT" <<'COUNT'
set pagesize 0 feedback off verify off heading off
select count(*) from all_objects where owner = 'HR';
exit
COUNT
)
if [ "$(echo "$ALREADY" | tr -d '[:space:]')" -gt 0 ] 2>/dev/null; then
    echo "HR sample schema already present."
    return 0 2>/dev/null || exit 0
fi

WORKDIR=$(mktemp -d)
cp /tmp/hr/*.sql "$WORKDIR"
cd "$WORKDIR"

sqlplus -s "$CONNECT" <<'SETUP'
WHENEVER SQLERROR EXIT FAILURE
SET ECHO OFF FEEDBACK OFF VERIFY OFF

DECLARE
   v_exists   NUMBER;
BEGIN
   SELECT COUNT(*) INTO v_exists FROM all_users WHERE username = 'HR';
   IF v_exists > 0 THEN
      EXECUTE IMMEDIATE 'DROP USER hr CASCADE';
   END IF;
END;
/

CREATE USER hr IDENTIFIED BY "hr"
               DEFAULT TABLESPACE USERS
               QUOTA UNLIMITED ON USERS;

GRANT CREATE MATERIALIZED VIEW,
      CREATE PROCEDURE,
      CREATE SEQUENCE,
      CREATE SESSION,
      CREATE SYNONYM,
      CREATE TABLE,
      CREATE TRIGGER,
      CREATE TYPE,
      CREATE VIEW
  TO hr;

-- The tree shows a tablespace node, which reads DBA_TABLESPACES.
GRANT SELECT_CATALOG_ROLE TO hr;

ALTER SESSION SET CURRENT_SCHEMA=HR;
ALTER SESSION SET NLS_LANGUAGE=American;
ALTER SESSION SET NLS_TERRITORY=America;

@hr_create.sql
@hr_populate.sql
@hr_code.sql

EXIT
SETUP

# sqlplus can report success after a failed script, so the result is checked.
OBJECTS=$(sqlplus -s "$CONNECT" <<'CHECK'
set pagesize 0 feedback off verify off heading off
select count(*) from dba_objects where owner = 'HR';
exit
CHECK
)

OBJECTS=$(echo "$OBJECTS" | tr -d '[:space:]')
if [ "${OBJECTS:-0}" -lt 1 ]; then
    echo "HR sample schema was not installed. See the output above." >&2
    exit 1
fi

echo "HR sample schema ready ($OBJECTS objects)."
