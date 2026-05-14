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





