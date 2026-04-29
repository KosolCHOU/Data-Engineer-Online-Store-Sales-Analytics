import os
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "online_retail_II.xlsx"
CREATE_TABLE_SQL = PROJECT_ROOT / "sql" / "01_create_table.sql"

db_user = os.getenv("POSTGRES_USER", "postgres")
raw_db_password = os.getenv("POSTGRES_PASSWORD", "")
if not raw_db_password or raw_db_password in {
    "your_postgres_password",
    "replace_this_with_your_real_postgres_password"
}:
    raise ValueError("Set POSTGRES_PASSWORD to your real PostgreSQL password before running this script.")

db_host = os.getenv("POSTGRES_HOST", "localhost")
db_port = os.getenv("POSTGRES_PORT", "5432")
db_name = os.getenv("POSTGRES_DB", "online_store")

sheet_frames = pd.read_excel(DATA_PATH, sheet_name=None)
df = pd.concat(sheet_frames.values(), ignore_index=True)

df = df.rename(columns={
    "Invoice": "invoice_no",
    "InvoiceNo": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "unit_price",
    "UnitPrice": "unit_price",
    "Customer ID": "customer_id",
    "CustomerID": "customer_id",
    "Country": "country"
})

required_columns = {
    "invoice_no",
    "stock_code",
    "description",
    "quantity",
    "invoice_date",
    "unit_price",
    "customer_id",
    "country"
}
missing_columns = required_columns - set(df.columns)
if missing_columns:
    raise ValueError(f"Missing expected columns: {sorted(missing_columns)}")

df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
df["customer_id"] = df["customer_id"].astype("Int64").astype(str).replace("<NA>", "")

df = df[
    [
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "country"
    ]
]

psql_env = os.environ.copy()
psql_env["PGPASSWORD"] = raw_db_password
psql_base_cmd = [
    "psql",
    "-h",
    db_host,
    "-p",
    db_port,
    "-U",
    db_user,
    "-d",
    db_name
]

subprocess.run(
    [*psql_base_cmd, "-f", str(CREATE_TABLE_SQL)],
    env=psql_env,
    check=True
)

with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as csv_file:
    csv_path = Path(csv_file.name)
    df.to_csv(csv_file, index=False)

try:
    copy_sql = (
        "\\copy online_retail "
        "(invoice_no, stock_code, description, quantity, invoice_date, unit_price, customer_id, country) "
        f"FROM '{csv_path}' WITH (FORMAT csv, HEADER true)"
    )
    subprocess.run(
        [*psql_base_cmd, "-c", copy_sql],
        env=psql_env,
        check=True
    )
finally:
    csv_path.unlink(missing_ok=True)

print("Data loaded successfully.")
print(df.shape)
