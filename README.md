# TeleCoop Common Tools

This project provides :
1. a cursor wrapper to use around a psycopg2 cursor
2. a connector for the Sellsy API built arount the package sellsy_api

## Init dev env

Dev env uses uv (see [Installation | uv](https://docs.astral.sh/uv/getting-started/installation/))

```sh
# Copy and edit .env
cp .env.example .env
vim .env

# Copy conf file
cp conf/conf-dist.cfg conf/conf.cfg
vim conf/conf.cfg

# Sync the environment from pyproject.toml
uv sync --locked

# Init mandatory containers
docker compose up -d postgres-logs nats

# Create log file
sudo mkdir -p /var/log/common
sudo touch /var/log/common/telecoop-common.log
sudo chown $(id -u):$(id -g) /var/log/common/telecoop-common.log

# Run test
uv run pytest --color=yes

# Run command
uv run --env-file .env ./src/cli.py submodule:command-name arg
```