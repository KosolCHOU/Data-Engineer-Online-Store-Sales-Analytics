import os
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSTGRES_DRIVER_JAR = PROJECT_ROOT / "drivers" / "postgresql-42.7.3.jar"
POSTGRES_DRIVER_PACKAGE = "org.postgresql:postgresql:42.7.3"

db_password = os.getenv("POSTGRES_PASSWORD", "")
if not db_password or db_password in {
    "your_postgres_password",
    "replace_this_with_your_real_postgres_password"
}:
    raise ValueError("Set POSTGRES_PASSWORD to your real PostgreSQL password before running this script.")

jdbc_host = os.getenv("POSTGRES_HOST", "localhost")
jdbc_port = os.getenv("POSTGRES_PORT", "5432")
jdbc_db = os.getenv("POSTGRES_DB", "online_store")
jdbc_url = f"jdbc:postgresql://{jdbc_host}:{jdbc_port}/{jdbc_db}"

properties = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": db_password,
    "driver": "org.postgresql.Driver"
}

spark_builder = SparkSession.builder.appName("OnlineStoreDataProfiling")
if POSTGRES_DRIVER_JAR.exists():
    spark_builder = spark_builder.config("spark.jars", str(POSTGRES_DRIVER_JAR))
else:
    spark_builder = spark_builder.config("spark.jars.packages", POSTGRES_DRIVER_PACKAGE)

spark = spark_builder.getOrCreate()

df = spark.read.jdbc(
    url=jdbc_url,
    table="online_retail",
    properties=properties
)

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
