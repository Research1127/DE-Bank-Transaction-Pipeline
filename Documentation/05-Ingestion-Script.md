# Creating the Data Ingestion Script

**[↑ Up](README.md)** | **[← Previous](04-Data-Ingestion.md)** | **[Next →](07-pgadmin.md)**

---

Now let's convert the notebook to a Python script.

## Convert Notebook to Script (Python File)

```bash
uv run jupyter nbconvert --to=script data_ingestion.ipynb
```

So the `data_ingestion.ipynb` will be converted to `data_ingestion.py`

---

## Parameterized The Python File

### File: data_ingestion.py

```python
# Parameterize DbConnection details

pg_user = "root"
pg_pass = "root"
pg_host = "localhost"
pg_port = 5433
pg_db = "bank_trans"
table_name = "bank_transaction"
chunksize = 500

```

> Note that it still hardcoded in the python file. Later on we will use command line to put these values

---

## Setup Function

```python

def run():
    # Code logic here

if __name__ == "__main__":
run()
```

#### Script Structure

The script uses `def run()` and `if __name__ == "__main__"` as a standard Python pattern.

**`def run()`** wraps all the ingestion logic into a function. This is required because
`@click.command()` needs a function to decorate. It also prevents the code from running
automatically when the file is imported by another script.

**`if __name__ == "__main__": run()`** is the entry point. When you run the script directly
(`python ingest_data.py`), Python sets `__name__` to `"__main__"` and `run()` gets called.
When the file is imported elsewhere, `__name__` is the filename instead, so `run()` is skipped.

Together they follow a simple rule: **define at the top, execute at the bottom.**

---

## The Complete Ingestion Script

Here's the full structure:

```python
import kagglehub
import os
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm


def run():
    # ── Parameters ────────────────────────────────────────────────────────────
    pg_user = "root"
    pg_pass = "root"
    pg_host = "localhost"
    pg_port = 5433
    pg_db = "bank_trans"
    table_name = "bank_transaction"
    chunksize = 500
    filepath = "valakhorasani/bank-transaction-dataset-for-fraud-detection"
    filename = "bank_transactions_data_2.csv"

    # ── 1. Download dataset ───────────────────────────────────────────────────
    path = kagglehub.dataset_download(filepath)
    csv_path = os.path.join(path, filename)

    # ── 2. Define dtypes and parse_dates ──────────────────────────────────────
    dtype = {
        "TransactionID": "string",
        "AccountID": "string",
        "TransactionAmount": "float64",
        "TransactionType": "category",
        "Location": "category",
        "DeviceID": "string",
        "IP Address": "string",
        "MerchantID": "string",
        "Channel": "category",
        "CustomerAge": "Int64",
        "CustomerOccupation": "category",
        "TransactionDuration": "Int64",
        "LoginAttempts": "Int64",
        "AccountBalance": "float64",
    }
    parse_dates = ["TransactionDate", "PreviousTransactionDate"]

    # ── 3. Create engine ──────────────────────────────────────────────────────
    engine = create_engine(
        f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    )

    # ── 4. Read CSV in chunks ─────────────────────────────────────────────────
    df_iter = pd.read_csv(
        csv_path,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize,
    )

    # ── 5. First chunk — create table ─────────────────────────────────────────
    first_chunk = next(df_iter)
    first_chunk.columns = first_chunk.columns.str.replace(" ", "_")

    first_chunk.head(0).to_sql(name=table_name, con=engine, if_exists="replace")
    print("Table created")

    first_chunk.to_sql(name=table_name, con=engine, if_exists="append")
    print(f"Inserted first chunk: {len(first_chunk)}")

    # ── 6. Remaining chunks ───────────────────────────────────────────────────
    for df_chunk in tqdm(df_iter):
        df_chunk.columns = df_chunk.columns.str.replace(" ", "_")
        df_chunk.to_sql(name=table_name, con=engine, if_exists="append")

    print("Done! All chunks inserted.")


if __name__ == "__main__":
    run()


```

> Note: This code are not finalized yet because it is hardcoded

---

### Run

We run using hardcoded value in data_ingestion.py

```shell
uv run python data_ingestion.py
```

---

## Click Integration

### Install Click

```shell
uv add click
```

The script uses `click` for command-line argument parsing:

```python
import click

@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5433, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='bank_trans', help='PostgreSQL database name')
@click.option('--table-name', default='bank_transaction', help='Target table name')
@click.option('--chunksize', default=500, type=int, help='Size of each chunk to insert')
@click.option('--filepath', default="valakhorasani/bank-transaction-dataset-for-fraud-detection", help='Kaggle dataset path')
@click.option('--filename', default="bank_transactions_data_2.csv", help='Name of the CSV file to process')
def run(pg_user, pg_pass, pg_host, pg_port, pg_db, table_name, chunksize, filepath, filename):
    # Ingestion logic here
    pass
```

> Delete the parameter part as we use `click.option` already

> Insert parameter name in our `run function`

---

## Check the Parameter Using Help

```shell
uv run python data_ingestion.py --help
```

The Output will be:

```shell
Usage: data_ingestion.py [OPTIONS]

Options:
  --pg-user TEXT       PostgreSQL user
  --pg-pass TEXT       PostgreSQL password
  --pg-host TEXT       PostgreSQL host
  --pg-port INTEGER    PostgreSQL port
  --pg-db TEXT         PostgreSQL database name
  --table-name TEXT    Target table name
  --chunksize INTEGER  Size of each chunk to insert
  --filepath TEXT      Kaggle dataset path
  --filename TEXT      Name of the CSV file to process
  --help               Show this message and exit.
```

---

## Running the Script

The script reads data in chunks (100,000 rows at a time) to handle large files efficiently without running out of memory.

Example usage:

```bash
uv run python data_ingestion.py \
  --pg-user=root \
  --pg-pass=root \
  --pg-host=localhost \
  --pg-port=5433 \
  --pg-db=bank_trans \
  --table-name=bank_transaction \
  --chunksize=500 \
  --filepath=valakhorasani/bank-transaction-dataset-for-fraud-detection \
  --filename=bank_transactions_data_2.csv
```

---

## Last Updated File

### File: data_ingestion.py

> This is the final version of `data_ingestion.py` after all changes in this section.

```python
import kagglehub
import os
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm
import click

@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5433, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='bank_trans', help='PostgreSQL database name')
@click.option('--table-name', default='bank_transaction', help='Target table name')
@click.option('--chunksize', default=500, type=int, help='Size of each chunk to insert')
@click.option('--filepath', default="valakhorasani/bank-transaction-dataset-for-fraud-detection", help='Kaggle dataset path')
@click.option('--filename', default="bank_transactions_data_2.csv", help='Name of the CSV file to process')
def run(pg_user, pg_pass, pg_host, pg_port, pg_db, table_name, chunksize, filepath, filename):

    # ── 1. Download dataset ───────────────────────────────────────────────────
    path = kagglehub.dataset_download(filepath)
    csv_path = os.path.join(path, filename)

    # ── 2. Define dtypes and parse_dates ──────────────────────────────────────
    dtype = {
        "TransactionID": "string",
        "AccountID": "string",
        "TransactionAmount": "float64",
        "TransactionType": "category",
        "Location": "category",
        "DeviceID": "string",
        "IP Address": "string",
        "MerchantID": "string",
        "Channel": "category",
        "CustomerAge": "Int64",
        "CustomerOccupation": "category",
        "TransactionDuration": "Int64",
        "LoginAttempts": "Int64",
        "AccountBalance": "float64",
    }
    parse_dates = ["TransactionDate", "PreviousTransactionDate"]

    # ── 3. Create engine ──────────────────────────────────────────────────────
    engine = create_engine(
        f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    )

    # ── 4. Read CSV in chunks ─────────────────────────────────────────────────
    df_iter = pd.read_csv(
        csv_path,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize,
    )

    # ── 5. First chunk — create table ─────────────────────────────────────────
    first_chunk = next(df_iter)
    first_chunk.columns = first_chunk.columns.str.replace(" ", "_")

    first_chunk.head(0).to_sql(name=table_name, con=engine, if_exists="replace")
    print("Table created")

    first_chunk.to_sql(name=table_name, con=engine, if_exists="append")
    print(f"Inserted first chunk: {len(first_chunk)}")

    # ── 6. Remaining chunks ───────────────────────────────────────────────────
    for df_chunk in tqdm(df_iter):
        df_chunk.columns = df_chunk.columns.str.replace(" ", "_")
        df_chunk.to_sql(name=table_name, con=engine, if_exists="append")

    print("Done! All chunks inserted.")


if __name__ == "__main__":
    run()

```

---

**[↑ Up](README.md)** | **[← Previous](04-Data-Ingestion.md)** | **[Next →](07-pgadmin.md)**
