import os
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, dayofmonth, hour, month, to_timestamp, year


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

spark_builder = SparkSession.builder.appName("OnlineStoreETL")
if MSSQL_DRIVER_JAR.exists():
    spark_builder = spark_builder.config("spark.jars", str(MSSQL_DRIVER_JAR))
else:
    spark_builder = spark_builder.config("spark.jars.packages", MSSQL_DRIVER_PACKAGE)

spark = spark_builder.getOrCreate()

df = spark.read.jdbc(url=jdbc_url, table="online_retail", properties=properties)

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
    url=jdbc_url, table="clean_online_retail", mode="overwrite", properties=properties
)

print("Saved clean_online_retail to MS SQL Server.")

spark.stop()
