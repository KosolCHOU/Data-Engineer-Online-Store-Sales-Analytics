import os
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, dayofmonth, hour, month, to_timestamp, year


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

spark_builder = SparkSession.builder.appName("OnlineStoreETL")
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

raw_count = df.count()

df_clean = (
    df.dropDuplicates()
    .withColumn("invoice_date", to_timestamp(col("invoice_date")))
    .filter(col("description").isNotNull())
    .filter(col("quantity") > 0)
    .filter(col("unit_price") > 0)
    .filter(col("invoice_date").isNotNull())
    .withColumn("revenue", col("quantity") * col("unit_price"))
    .withColumn("year", year(col("invoice_date")))
    .withColumn("month", month(col("invoice_date")))
    .withColumn("day", dayofmonth(col("invoice_date")))
    .withColumn("hour", hour(col("invoice_date")))
)

clean_count = df_clean.count()
removed_count = raw_count - clean_count

print("========== ETL CLEANING REPORT ==========")
print(f"Raw row count: {raw_count}")
print(f"Clean row count: {clean_count}")
print(f"Removed row count: {removed_count}")
print("\nFinal schema:")
df_clean.printSchema()
print("\nSample clean rows:")
df_clean.show(10, truncate=False)

df_clean.write.jdbc(
    url=jdbc_url,
    table="clean_online_retail",
    mode="overwrite",
    properties=properties
)

print("Saved clean_online_retail to PostgreSQL.")

spark.stop()
