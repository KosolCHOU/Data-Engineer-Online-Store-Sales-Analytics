import os
import pymssql
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "online_retail_II.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
CSV_TEMP_PATH = OUTPUT_DIR / "retail.tsv"

db_user = os.getenv("MSSQL_USER", "sa")
db_password = os.getenv("MSSQL_PASSWORD", "")
db_host = os.getenv("MSSQL_HOST", r"localhost\SQLEXPRESS01")
db_port = os.getenv("MSSQL_PORT", "1433")
db_name = os.getenv("MSSQL_DB", "online_store")

if not db_password or db_password in {
    "your_mssql_password",
    "replace_this_with_your_real_mssql_password",
}:
    raise ValueError(
        "Set MSSQL_PASSWORD to your real MS SQL Server password before running this script."
    )

# Read dataset
print("Reading dataset...")
sheet_frames = pd.read_excel(DATA_PATH, sheet_name=None)
df = pd.concat(sheet_frames.values(), ignore_index=True)

df = df.rename(
    columns={
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
        "Country": "country",
    }
)

# Filter out rows or format them
df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
df["customer_id"] = df["customer_id"].astype("Int64").astype(str).replace("<NA>", "")

# Select required columns
df = df[
    [
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "country",
    ]
]

# Convert customer_id to standard format (empty instead of nan / <NA> / etc)
df["customer_id"] = df["customer_id"].apply(
    lambda x: (
        ""
        if pd.isnull(x) or str(x).strip().lower() in {"nan", "<na>", ""}
        else str(x).strip()
    )
)

# Clean up description to remove tab, newline, and carriage return characters which could break TSV format
df["description"] = df["description"].apply(
    lambda x: (
        str(x).replace("\t", " ").replace("\n", " ").replace("\r", " ")
        if not pd.isnull(x)
        else ""
    )
)

# Write to TSV file
print("Writing temporary TSV file for bulk copy...")
# We use tab separation because descriptions might contain commas
df.to_csv(CSV_TEMP_PATH, sep="\t", index=False, header=True, na_rep="")

# Connect to MS SQL Server
print("Connecting to SQL Server master database to verify/create target database...")
master_conn_kwargs = {
    "server": db_host,
    "user": db_user,
    "password": db_password,
    "database": "master",
    "autocommit": True,
}
if "\\" not in db_host:
    master_conn_kwargs["port"] = db_port

conn = pymssql.connect(**master_conn_kwargs)
cursor = conn.cursor()
cursor.execute(
    f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{db_name}') CREATE DATABASE [{db_name}]"
)
conn.close()

# Reconnect to target database
print(f"Connecting to database '{db_name}'...")
db_conn_kwargs = {
    "server": db_host,
    "user": db_user,
    "password": db_password,
    "database": db_name,
    "autocommit": True,
}
if "\\" not in db_host:
    db_conn_kwargs["port"] = db_port

conn = pymssql.connect(**db_conn_kwargs)
cursor = conn.cursor()

# Read sql/01_create_table.sql and execute it
create_table_path = PROJECT_ROOT / "sql" / "01_create_table.sql"
with open(create_table_path, "r") as f:
    create_table_sql = f.read()

# Executing CREATE TABLE
cursor.execute(create_table_sql)

print("Performing bulk insert...")
# In docker compose, the path '/var/opt/mssql/output/retail.tsv' is the file in db container
# On host/local development, it's CSV_TEMP_PATH.
# We can dynamically decide the container path vs local path:
if db_host == "db":
    # Running inside docker compose
    bulk_source_path = "/var/opt/mssql/output/retail.tsv"
else:
    # Running locally
    bulk_source_path = str(CSV_TEMP_PATH.resolve())

bulk_sql = f"""
BULK INSERT online_retail
FROM '{bulk_source_path}'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = '\\t',
    ROWTERMINATOR = '\\n',
    TABLOCK
);
"""

cursor.execute(bulk_sql)
conn.close()

# Delete temp file
CSV_TEMP_PATH.unlink(missing_ok=True)

print("Data loaded successfully.")
print(df.shape)
