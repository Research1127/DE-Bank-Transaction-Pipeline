# Running PostgreSQL with Docker

**[↑ Up](README.md)** | **[← Previous](02-Setup-Docker.md)** | **[Next →](04-Data-Ingestion.md)**

Now we want to do real data engineering. Let's use a Postgres database for that.

You can run a containerized version of Postgres that doesn't require any installation steps. You only need to provide a few environment variables to it as well as a volume for storing data.

---

## Check Docker Volume

To find is there any volume exist or not

```shell
docker volume ls
```

---

## Running PostgreSQL in a Container

```shell
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="bank_trans" \
  -v bank_trans_postgres_data:/var/lib/postgresql \
  -p 5433:5432 \
  postgres:18
```

### Explanation of Parameters

- `e` sets environment variables (user, password, database name)
- `v` ny_taxi_postgres_data:/var/lib/postgresql creates a named volume
  - Docker manages this volume automatically
  - Data persists even after container is removed
  - Volume is stored in Docker's internal storage
- `p` 5432:5432 maps port 5432 from container to host
- `postgres:18` uses PostgreSQL version 18 (latest as of Dec 2025)

---

### Alternative Approach - Bind Mount

First create the directory, then map it:

```shell
mkdir bank_trans_postgres_data

docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="bank_trans" \
  -v $(pwd)/bank_trans_postgres_data:/var/lib/postgresql \
  -p 5433:5432 \
  postgres:18
```

## Connecting to PostgreSQL

Once the container is running, we can log into our database with pgcli.

Install pgcli:

```shell
uv add --dev pgcli
```

The `--dev` flag marks this as a development dependency (not needed in production). It will be added to the `[dependency-groups]` section of `pyproject.toml` instead of the main dependencies section.

Now use it to connect to Postgres:

```shell
uv run pgcli -h localhost -p 5433 -u root -d bank_trans
```

- `uv` run executes a command in the context of the virtual environment
- `h` is the host. Since we're running locally we can use `localhost`.
- `p` is the port.
- `u` is the username.
- `d` is the database name.
- The password is not provided; it will be requested after running the command.

When prompted, enter the password: `root`

**Notes**

You can get error here if the `localhost` like your computer have another postgresql run on port `5432` so to be safe we can change the port to `5433` or any other available port. Here I am using `5433` as step above.

---

## Basic SQL Commands

Try some SQL commands:

```sql
-- List tables
\dt

-- Create a test table
CREATE TABLE test (id INTEGER, name VARCHAR(50));

-- Insert data
INSERT INTO test VALUES (1, 'Hello Docker');

-- Query data
SELECT * FROM test;

-- Exit
\q
```

---

## Last Test

- Try stop the container `[CTRL+C]`
- Open again

```shell
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="bank_trans" \
  -v bank_trans_postgres_data:/var/lib/postgresql \  # ← mounts same volume
  -p 5433:5432 \
  postgres:18
```

We still can see the data we created earlier because:

```text
Container  →  temporary (dies with --rm + CTRL+C)
Volume     →  persists forever (until you delete it)
```

#### **Think of it like:**

```text
Container = a machine
Volume    = a hard drive

You can throw away the machine (--rm)
But the hard drive (volume) still has all your data
Plug it into a new machine → data is back!
```

That's exactly why volumes exist — to separate data from the container lifecycle. Container is disposable, data is not. ✅
