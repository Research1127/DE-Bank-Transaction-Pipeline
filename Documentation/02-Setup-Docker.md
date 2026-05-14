# Enhance Docker Setup

**[↑ Up](README.md)** | **[← Previous](01-Setup-Project-and-Dataset.md)** | **[Next →](03-Running-Postgresql-in-Docker.md)**

## Dockerfile

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
COPY pipeline.py .

ENTRYPOINT [ "python", "pipeline.py" ]
```

### Explanation

| Line                                                | Meaning                                                                                                                                                                                                                     |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FROM python:3.13.2-slim`                           | Use slim Python 3.13.2 as base image                                                                                                                                                                                        |
| `COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/` | Copy uv binary from official uv image instead of installing via pip                                                                                                                                                         |
| `WORKDIR /app`                                      | Set `/app` as working directory inside container                                                                                                                                                                            |
| `COPY pyproject.toml .python-version uv.lock ./`    | Copy dependency files first for better layer caching                                                                                                                                                                        |
| `RUN uv sync --locked`                              | Install dependencies from uv.lock file — ensures reproducible builds. Means that we dont need to run pip install everything again like local machine because we already done that in local machine and save in uv.lock file |
| `ENV PATH="/app/.venv/bin:$PATH"`                   | Add virtual environment to PATH so installed packages can be used                                                                                                                                                           |
| `COPY pipeline.py .`                                | Copy application code into container                                                                                                                                                                                        |
| `ENTRYPOINT ["python", "pipeline.py"]`              | Automatically run pipeline.py when container starts                                                                                                                                                                         |

---

## Build

```shell
docker build -t test:pandas .
```

| Part             | Meaning                             |
| ---------------- | ----------------------------------- |
| `docker build`   | Build a Docker image                |
| `-t test:pandas` | Name it `test` with tag `pandas`    |
| `.`              | Use current folder as build context |

---

## Run

### Option 1: Run automatically (using ENTRYPOINT)

Runs `pipeline.py` automatically and exits when done.

```shell
docker run -it --rm test:pandas
```

| Part          | Meaning                                |
| ------------- | -------------------------------------- |
| `docker run`  | Run a container                        |
| `-it`         | Interactive mode — keeps terminal open |
| `--rm`        | Auto delete container when it stops    |
| `test:pandas` | The image to run                       |

---

### Option 2: Run with bash shell (debug mode)

Overrides `ENTRYPOINT` and opens bash shell for manual testing.

```shell
docker run -it --rm --entrypoint=bash test:pandas
```

Then manually run inside the container:

```shell
python pipeline.py
ls
```

---

### Option 3: Run with environment variables

Use this when the Kaggle dataset is private and requires credentials.

```shell
docker run -it --rm --env-file .env test:pandas
```

---

## Save Output to Local Machine (Volume Mount)

By default, files created inside the container are deleted when the container stops. To persist files to your Mac, use a volume mount:

```shell
docker run -it --rm -v $(pwd)/output:/output test:pandas
```

| Part            | Meaning                                                       |
| --------------- | ------------------------------------------------------------- |
| `-v`            | Volume flag — creates a bridge between your Mac and container |
| `$(pwd)/output` | Your current folder + `/output` on your Mac                   |
| `:/output`      | Folder inside the container that bridges to your Mac folder   |

> `$(pwd)` is a shortcut that automatically fills in your current directory path.

So if you are inside `/Users/firdauslahmuddin/Desktop/Data Engineer/`, the real expanded command is:

```shell
docker run -it --rm -v "/Users/firdauslahmuddin/Desktop/Data Engineer/output":/output test:pandas
```

> ⚠️ Make sure `pipeline.py` saves files to `/output/` so they cross the bridge to your Mac:
>
> ```python
> df.to_csv("/output/result.csv")  # ✅ appears on your Mac
> df.to_csv("result.csv")          # ❌ stays in container, deleted on stop
> ```

After the container finishes, check your output folder:

```shell
ls output/
```

You will see:

- `Bank_Data.csv`
- `bank_transactions.parquet`

---

## Link to Another Container (Named Volume)

Use a named volume to share data between two containers.

### Step 1: Create a named volume

```shell
docker volume create mydata
```

### Step 2: Container A writes data into the volume

```shell
docker run -it --rm -v mydata:/app test:pandas
```

### Step 3: Container B reads the same data

```shell
docker run -it --rm -v mydata:/app test:another
```

Whatever Container A writes to `/app`, Container B can read — they share the same `mydata` volume.

### Real DE Use Case

```
[Container A: pipeline.py] → downloads & processes data → saves to volume
[Container B: load.py]     → reads data from volume → loads into database
```

This is the foundation of how **Docker Compose** orchestrates multi-container pipelines.
