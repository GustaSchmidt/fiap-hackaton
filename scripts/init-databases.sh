#!/bin/bash
set -e

# Create multiple databases for different services
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE fiapx_auth;
    CREATE DATABASE fiapx_videos;
    GRANT ALL PRIVILEGES ON DATABASE fiapx_auth TO fiapx;
    GRANT ALL PRIVILEGES ON DATABASE fiapx_videos TO fiapx;
EOSQL
