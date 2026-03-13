#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE fiapx_auth' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'fiapx_auth')\gexec
    SELECT 'CREATE DATABASE fiapx_videos' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'fiapx_videos')\gexec
    GRANT ALL PRIVILEGES ON DATABASE fiapx_auth TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE fiapx_videos TO $POSTGRES_USER;
EOSQL
