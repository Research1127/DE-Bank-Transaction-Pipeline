# Docker Compose

**[↑ Up](README.md)** | **[← Previous](07-Dockerizing-Ingestion.md)** | **[Next →](09-Sql-Refresher.md)**

`docker-compose` allows us to launch multiple containers using a single configuration file, so that we don't have to run multiple complex `docker run` commands separately.

## Setup Docker Compose

We can copy docker run we do in **[06-PgAdmin-in-Docker.md](06-PgAdmin-in-Docker.md)** and paste both docker run command for pgadmin and postgresql in Chatgpt or Claude asking it to create the `docker-compose.yaml`.

This is the command:

```shell
# Run PostgreSQL on the network
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="bank_trans" \
  -v bank_trans_postgres_data:/var/lib/postgresql \
  -p 5433:5432 \
  --network=pg-network \
  --name pgdatabase \
  postgres:18

# In another terminal, run pgAdmin on the same network
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -v pgadmin_data:/var/lib/pgadmin \
  -p 8085:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```

Docker compose makes use of YAML files. Here's the `docker-compose.yaml` file after Claude/Chatgpt generate it:

```yaml
services:
  pgdatabase:
    image: postgres:18
    environment:
      POSTGRES_USER: root
      POSTGRES_PASSWORD: root
      POSTGRES_DB: bank_trans
    volumes:
      - bank_trans_postgres_data:/var/lib/postgresql
    ports:
      - "5433:5432"

  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: root
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    ports:
      - "8085:80"
    depends_on:
      - pgdatabase

volumes:
  bank_trans_postgres_data:
  pgadmin_data:
```

### Explanation

- We don't have to specify a network because `docker compose` takes care of it: every single container (or "service", as the file states) will run within the same network and will be able to find each other according to their names (`pgdatabase` and `pgadmin` in this example).
- All other details from the `docker run` commands (environment variables, volumes and ports) are mentioned accordingly in the file following YAML syntax.

## Start Services with Docker Compose

We can now run Docker compose by running the following command from the same directory where `docker-compose.yaml` is found. Make sure that all previous containers aren't running anymore:

```bash
docker-compose up
```

### Detached Mode

If you want to run the containers again in the background rather than in the foreground (thus freeing up your terminal), you can run them in detached mode:

```bash
docker-compose up -d
```

## Stop Services

You will have to press `Ctrl+C` in order to shut down the containers when running in foreground mode. The proper way of shutting them down is with this command:

```bash
docker-compose down
```

## Other Useful Commands

```bash
# View logs
docker-compose logs

# Stop and remove volumes
docker-compose down -v
```

## Benefits of Docker Compose

- Single command to start all services
- Automatic network creation
- Easy configuration management
- Declarative infrastructure

## Running the Ingestion Script with Docker Compose

If you want to re-run the dockerized ingest script when you run Postgres and pgAdmin with `docker compose`, you will have to find the name of the virtual network that Docker compose created for the containers.

```bash
# check the network link:
docker network ls

# it's pipeline_default (or similar based on directory name)
# now run the script:
docker run -it --rm\
  --network=dataengineer_default \
  bank_ingest:v001 \
    --pg-user=root \
    --pg-pass=root \
    --pg-host=pgdatabase \
    --pg-port=5432 \
    --pg-db=bank_trans \
    --table-name=bank_transaction
```

**[↑ Up](README.md)** | **[← Previous](07-Dockerizing-Ingestion.md)** | **[Next →](09-Sql-Refresher.md)**
