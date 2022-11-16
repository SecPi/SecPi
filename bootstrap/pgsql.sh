#!/bin/bash -e
user=secpi
password=secret

declare -a DBases=("secpi-development" "secpi-testdrive" "secpi")

for db in "${DBases[@]}"
do
    cat << EOF | su - postgres -c psql
    -- Create the database user:
    CREATE USER $user WITH PASSWORD '$password';
    -- Create the database:
    CREATE DATABASE "$db" WITH OWNER=$user;
EOF
done
