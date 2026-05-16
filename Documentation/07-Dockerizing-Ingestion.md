# Dockerizing the Ingestion Script

**[↑ Up](README.md)** | **[← Previous](06-PgAdmin-in-Docker.md)** | **[Next →](08-Docker-Compose.md)**

Now let's containerize the ingestion script so we can run it in Docker.

## The Dockerfile

The `pipeline/Dockerfile` shows how to containerize the ingestion script:

```dockerfile
# Start with slim Python image
FROM python:3.13.2-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/


# Set working directory
WORKDIR /app


# Copy dependency files first (better layer caching)
COPY pyproject.toml .python-version uv.lock ./

# Install dependencies from lock file (ensures reproducible builds)
RUN uv sync --locked

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY pipeline/data_ingestion.py .

ENTRYPOINT [ "python", "data_ingestion.py" ]
```

### Explanation

- `FROM python:3.13.11-slim`: Start with slim Python 3.13 image for smaller size
- `COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/`: Copy uv binary from official uv image
- `WORKDIR /app`: Set working directory inside container
- `ENV PATH="/app/.venv/bin:$PATH"`: Add virtual environment to PATH
- `COPY pyproject.toml .python-version uv.lock ./`: Copy dependency files first (better caching)
- `RUN uv sync --locked`: Install all dependencies from lock file (ensures reproducible builds)
- `COPY pipeline/data_ingestion.py .`: Copy ingestion script
- `ENTRYPOINT ["python", "data_ingestion.py"]`: Set entry point to run the ingestion script

---

## Build the Docker Image

There are two ways to build the Docker image depending on your current directory.

### Option 1: Build from inside `pipeline/` folder (Not Recommended)

```bash
cd pipeline
docker build -t bank_ingest:v001 .
```

> The `.` at the end means Docker uses the current folder (`pipeline/`) as the build context — it can only see files inside that folder.

---

### Option 2: Build from project root (Recommended)

```bash
docker build -f pipeline/Dockerfile -t bank_ingest:v001 .
```

> `-f pipeline/Dockerfile` tells Docker where the Dockerfile is, and `.` sets the project root as the build context — Docker can see all files including `pyproject.toml`, `uv.lock`, and `.python-version` at the root level.

> -f = file path to Dockerfile

---

### Why Option 2 is Best Practice

|                    | Option 1 (inside pipeline/)      | Option 2 (from root) |
| ------------------ | -------------------------------- | -------------------- |
| Build context      | `pipeline/` folder only          | Entire project       |
| Access to uv files | ❌ Must copy them into pipeline/ | ✅ Already at root   |
| Duplicate files    | ❌ Yes                           | ✅ No                |
| Recommended        |                                  | ✅                   |

Always build from the project root to avoid duplicating dependency files like `pyproject.toml` and `uv.lock` into the `pipeline/` folder.

---

## Run the Containerized Ingestion

```bash
docker run -it \
  --network=pg-network \
  bank_ingest:v001 \
    --pg-user=root \
    --pg-pass=root \
    --pg-host=pgdatabase \
    --pg-port=5432 \
    --pg-db=bank_trans \
    --table-name=bank_transaction
```

### Important Notes

- We need to provide the network for Docker to find the Postgres container. It goes before the name of the image.
- Since Postgres is running on a separate container, the host argument will have to point to the container name of Postgres (`pgdatabase`).
- You can drop the table in pgAdmin beforehand if you want, but the script will automatically replace the pre-existing table.

**[↑ Up](README.md)** | **[← Previous](07-pgadmin.md)** | **[Next →](09-docker-compose.md)**
