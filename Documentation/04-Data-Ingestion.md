# NY Taxi Dataset and Data Ingestion

**[↑ Up](README.md)** | **[← Previous](03-Running-Postgresql-in-Docker.md)** | **[Next →](05-Ingestion-Script.md)**

We will now create a Jupyter Notebook `notebook.ipynb` file which we will use to read a CSV file and export it to Postgres.

## Setting up Jupyter

Install Jupyter:

```bash
uv add --dev jupyter
```

Let's create a Jupyter notebook to explore the data:

```bash
uv run jupyter notebook
```

## Bank Transaction Dataset for Fraud Detection

Follow this link to download the dataset [Bank Transaction Dataset](https://www.kaggle.com/datasets/valakhorasani/bank-transaction-dataset-for-fraud-detection/data).

## Explore the Data

Setup the Api Token like **[↑ 01-Setup-Project-and-Dataset](01-Setup-Project-and-Dataset.md)** if the dataset are private

Create a new notebook and run:

```python
# Install dependencies as needed:
# pip install kagglehub[pandas-datasets]
import kagglehub
from kagglehub import KaggleDatasetAdapter

# Set the path to the file you'd like to load
file_path = "bank_transactions_data_2.csv"

# Load the latest version
df = kagglehub.dataset_load(
  KaggleDatasetAdapter.PANDAS,
  "valakhorasani/bank-transaction-dataset-for-fraud-detection",
  file_path,
)

print("Data")
print(df.head(2).transpose())

print("\n")
print("Data Types")
print(df.dtypes)

print("\n")
print("Data Shape")
print(df.shape)
```

### Handling Data Types

We need to handle the wrong data type like `TransactionDate` and `PreviousTransactionDate` before we load into our system

```python
import kagglehub
from kagglehub import KaggleDatasetAdapter

file_path = "bank_transactions_data_2.csv"

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

parse_dates = [
    "TransactionDate",
    "PreviousTransactionDate"
]

df = kagglehub.dataset_load(
    KaggleDatasetAdapter.PANDAS,
    "valakhorasani/bank-transaction-dataset-for-fraud-detection",
    file_path,
    pandas_kwargs={
        "dtype": dtype,
        "parse_dates": parse_dates
    }
)

print("Data")
print(df.head(2).transpose())
print("\n")
print("Data Types")
print(df.dtypes)
```

## Ingesting Data into Postgres

In the Jupyter notebook, we create code to:

1. Download the CSV file
2. Read it in chunks with pandas
3. Convert datetime columns
4. Insert data into PostgreSQL using SQLAlchemy

### Install SQLAlchemy

```bash
uv add sqlalchemy "psycopg[binary,pool]"
```

### Create Database Connection

```python
from sqlalchemy import create_engine
engine = create_engine('postgresql+psycopg://root:root@localhost:5433/bank_trans')
```

| Part                 | Meaning                            |
| -------------------- | ---------------------------------- |
| `postgresql+psycopg` | Driver (PostgreSQL using psycopg3) |
| `root`               | Username                           |
| `root`               | Password                           |
| `localhost`          | Host (where PostgreSQL is running) |
| `5433`               | PostgreSQL default port            |
| `bank_trans`         | Database name to connect to        |

---

### Get DDL Schema

```python
print(pd.io.sql.get_schema(df, name='bank_transactions', con=engine, dtype=dtype_sql))
```

Output:

```sql
CREATE TABLE bank_transactions (
	"TransactionID" TEXT,
	"AccountID" TEXT,
	"TransactionAmount" FLOAT(53),
	"TransactionDate" TIMESTAMP WITHOUT TIME ZONE,
	"TransactionType" TEXT,
	"Location" TEXT,
	"DeviceID" TEXT,
	"IP_Address" TEXT,
	"MerchantID" TEXT,
	"Channel" TEXT,
	"CustomerAge" BIGINT,
	"CustomerOccupation" TEXT,
	"TransactionDuration" BIGINT,
	"LoginAttempts" BIGINT,
	"AccountBalance" FLOAT(53),
	"PreviousTransactionDate" TIMESTAMP WITHOUT TIME ZONE
)

```

Define Custom Column If needed

```python
from sqlalchemy import create_engine, text
from sqlalchemy.types import VARCHAR, Float, SmallInteger, Integer, TIMESTAMP

engine = create_engine('postgresql+psycopg://root:root@localhost:5433/bank_trans')

# Define custom column types
dtype_sql = {
    "TransactionID":          VARCHAR(50),
    "AccountID":              VARCHAR(50),
    "TransactionAmount":      Float(),
    "TransactionDate":        TIMESTAMP(),
    "TransactionType":        VARCHAR(20),
    "Location":               VARCHAR(100),
    "DeviceID":               VARCHAR(50),
    "IP_Address":             VARCHAR(45),
    "MerchantID":             VARCHAR(50),
    "Channel":                VARCHAR(20),
    "CustomerAge":            SmallInteger(),
    "CustomerOccupation":     VARCHAR(50),
    "TransactionDuration":    Integer(),
    "LoginAttempts":          Integer(),
    "AccountBalance":         Float(),
    "PreviousTransactionDate": TIMESTAMP(),
}

# Preview schema first
print(pd.io.sql.get_schema(df, name='bank_transaction', con=engine, dtype=dtype_sql))
```

Now our schema preview

```sql
CREATE TABLE bank_transactions (
	"TransactionID" VARCHAR(50),
	"AccountID" VARCHAR(50),
	"TransactionAmount" FLOAT,
	"TransactionDate" TIMESTAMP WITHOUT TIME ZONE,
	"TransactionType" VARCHAR(20),
	"Location" VARCHAR(100),
	"DeviceID" VARCHAR(50),
	"IP_Address" VARCHAR(45),
	"MerchantID" VARCHAR(50),
	"Channel" VARCHAR(20),
	"CustomerAge" SMALLINT,
	"CustomerOccupation" VARCHAR(50),
	"TransactionDuration" INTEGER,
	"LoginAttempts" INTEGER,
	"AccountBalance" FLOAT,
	"PreviousTransactionDate" TIMESTAMP WITHOUT TIME ZONE
)
```

---

### Create the Table

```python
df.head(n=0).to_sql(name='bank_transaction', con=engine, if_exists='replace')
```

`head(n=0)` makes sure we only create the table, we don't add any data yet.

## Ingesting Data in Chunks

We don't want to insert all the data at once. Let's do it in batches and use an iterator for that:

```python

df_iter = pd.read_csv(csv_path, dtype=dtype,
    parse_dates=parse_dates,
    iterator=True,
    chunksize=500)

# But we dont use this as we use different method at the end. This just one to show how we iterate and use chunk

```

### Iterate Over Chunks

```python
for df_chunk in df_iter:
    print(len(df_chunk))
```

### Inserting Data

```python
df_chunk.to_sql(name='bank_transaction', con=engine, if_exists='append')
```

### Complete Ingestion Loop

```python
import kagglehub
import os
import pandas as pd
from sqlalchemy import create_engine

# ── 1. Download dataset (cached after first run) ──────────────────────────────
path = kagglehub.dataset_download("valakhorasani/bank-transaction-dataset-for-fraud-detection")
csv_path = os.path.join(path, "bank_transactions_data_2.csv")

# ── 2. Sample first to inspect ───────────────────────────────────────────────
df_sample = pd.read_csv(csv_path, nrows=100)
print(df_sample.dtypes)
print(df_sample.shape)

# ── 3. Define dtypes and parse_dates ─────────────────────────────────────────
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

parse_dates = [
    "TransactionDate",
    "PreviousTransactionDate"
]

# ── 4. Create database engine ─────────────────────────────────────────────────
engine = create_engine('postgresql+psycopg://root:root@localhost:5433/bank_trans')

# ── 5. Read CSV in chunks ─────────────────────────────────────────────────────
df_iter = pd.read_csv(
    csv_path,
    dtype=dtype,
    parse_dates=parse_dates,
    iterator=True,
    chunksize=500
)

# ── 6. Handle first chunk — create table ─────────────────────────────────────
first_chunk = next(df_iter)
first_chunk.columns = first_chunk.columns.str.replace(" ", "_")

first_chunk.head(0).to_sql(
    name="bank_transaction",
    con=engine,
    if_exists="replace"
)
print("Table created")

first_chunk.to_sql(
    name="bank_transaction",
    con=engine,
    if_exists="append"
)
print("Inserted first chunk:", len(first_chunk))

# ── 7. Insert remaining chunks ────────────────────────────────────────────────
for df_chunk in df_iter:
    df_chunk.columns = df_chunk.columns.str.replace(" ", "_")

    df_chunk.to_sql(
        name="bank_transaction",
        con=engine,
        if_exists="append"
    )
    print("Inserted chunk:", len(df_chunk))

print("Done! All chunks inserted.")

```

## Adding Progress Bar

Add `tqdm` to see progress:

```bash
uv add tqdm
```

Put it around the iterable:

```python
from tqdm.auto import tqdm

for df_chunk in tqdm(df_iter):
    ...
```

To see progress in terms of total chunks, you would have to add the `total` argument to `tqdm(df_iter)`. In our scenario, the pragmatic way is
to hardcode a value based on the number of entries in the table.

## Verify the Data

Connect to it using pgcli:

```bash
uv run pgcli -h localhost -p 5433 -u root -d bank_trans
```

And explore the data.

**[↑ Up](README.md)** | **[← Previous](04-postgres-docker.md)** | **[Next →](06-ingestion-script.md)**
