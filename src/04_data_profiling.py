import os
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MSSQL_DRIVER_JAR = PROJECT_ROOT / "drivers" / "mssql-jdbc-12.6.1.jre11.jar"
MSSQL_DRIVER_PACKAGE = "com.microsoft.sqlserver:mssql-jdbc:12.6.1.jre11"

db_password = os.getenv("MSSQL_PASSWORD", "")
if not db_password or db_password in {
    "your_mssql_password",
    "replace_this_with_your_real_mssql_password",
}:
    raise ValueError(
        "Set MSSQL_PASSWORD to your real MS SQL Server password before running this script."
    )

jdbc_host = os.getenv("MSSQL_HOST", r"localhost\SQLEXPRESS01")
jdbc_port = os.getenv("MSSQL_PORT", "1433")
jdbc_db = os.getenv("MSSQL_DB", "online_store")
if "\\" in jdbc_host:
    jdbc_url = f"jdbc:sqlserver://{jdbc_host};databaseName={jdbc_db};trustServerCertificate=true"
else:
    jdbc_url = f"jdbc:sqlserver://{jdbc_host}:{jdbc_port};databaseName={jdbc_db};trustServerCertificate=true"

properties = {
    "user": os.getenv("MSSQL_USER", "sa"),
    "password": db_password,
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
}

spark_builder = SparkSession.builder.appName("OnlineStoreDataProfiling")
if MSSQL_DRIVER_JAR.exists():
    spark_builder = spark_builder.config("spark.jars", str(MSSQL_DRIVER_JAR))
else:
    spark_builder = spark_builder.config("spark.jars.packages", MSSQL_DRIVER_PACKAGE)

spark = spark_builder.getOrCreate()

df = spark.read.jdbc(url=jdbc_url, table="online_retail", properties=properties)

total_rows = df.count()
duplicate_rows = total_rows - df.dropDuplicates().count()
invalid_quantity = df.filter(col("quantity") <= 0).count()
invalid_price = df.filter(col("unit_price") <= 0).count()

print("========== RAW DATA PROFILING REPORT ==========")
print(f"Source table: online_retail")
print(f"Total rows: {total_rows}")
print(f"Duplicate rows: {duplicate_rows}")
print(f"Invalid quantity rows: {invalid_quantity}")
print(f"Invalid price rows: {invalid_price}")

print("\nMissing values per column:")
for column in df.columns:
    missing_count = df.filter(col(column).isNull()).count()
    print(f"- {column}: {missing_count}")

print("\nUnique counts:")
print(f"Unique invoices: {df.select('invoice_no').distinct().count()}")
print(f"Unique products: {df.select('stock_code').distinct().count()}")
print(f"Unique customers: {df.select('customer_id').distinct().count()}")
print(f"Unique countries: {df.select('country').distinct().count()}")

spark.stop()
