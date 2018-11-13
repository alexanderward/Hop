#!/usr/bin/env bash
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update -y
sudo apt-get install -y pgbouncer
sudo apt-get install -y postgresql-client

sudo bash -c "echo \"ulimit -n 16384\" >> /etc/default/pgbouncer"


# https://github.com/ankane/shorts/blob/master/PgBouncer-Setup.md
# Modify other files to get it to work with the right endpoints passwords