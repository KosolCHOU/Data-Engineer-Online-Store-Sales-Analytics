import os
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, countDistinct, desc, sum


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
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

spark_builder = SparkSession.builder.appName("OnlineStoreAggregation")
if MSSQL_DRIVER_JAR.exists():
    spark_builder = spark_builder.config("spark.jars", str(MSSQL_DRIVER_JAR))
else:
    spark_builder = spark_builder.config("spark.jars.packages", MSSQL_DRIVER_PACKAGE)

spark = spark_builder.getOrCreate()

df = spark.read.jdbc(url=jdbc_url, table="clean_online_retail", properties=properties)

print("========== AGGREGATION REPORT ==========")
print(f"Source table: clean_online_retail")
print(f"Clean row count: {df.count()}")

sales_by_country = (
    df.groupBy("country")
    .agg(
        sum("revenue").alias("total_revenue"),
        countDistinct("invoice_no").alias("total_orders"),
        countDistinct("customer_id").alias("total_customers"),
    )
    .orderBy(desc("total_revenue"))
)

top_products = (
    df.groupBy("stock_code", "description")
    .agg(sum("quantity").alias("total_quantity"), sum("revenue").alias("total_revenue"))
    .orderBy(desc("total_revenue"))
)

monthly_sales = (
    df.groupBy("year", "month")
    .agg(
        sum("revenue").alias("total_revenue"),
        countDistinct("invoice_no").alias("total_orders"),
    )
    .orderBy("year", "month")
)

customer_summary = (
    df.filter(col("customer_id") != "")
    .groupBy("customer_id")
    .agg(
        countDistinct("invoice_no").alias("total_orders"),
        sum("revenue").alias("total_spent"),
        avg("revenue").alias("avg_item_revenue"),
    )
    .orderBy(desc("total_spent"))
)

hourly_sales = (
    df.groupBy("hour")
    .agg(
        countDistinct("invoice_no").alias("total_orders"),
        sum("revenue").alias("total_revenue"),
    )
    .orderBy("hour")
)

outputs = {
    "sales_by_country": sales_by_country,
    "top_products": top_products,
    "monthly_sales": monthly_sales,
    "customer_summary": customer_summary,
    "hourly_sales": hourly_sales,
}

for name, result_df in outputs.items():
    print(f"\n{name}:")
    result_df.show(10, truncate=False)

    result_df.write.jdbc(
        url=jdbc_url, table=name, mode="overwrite", properties=properties
    )
    print(f"Saved database table: {name}")

    csv_path = OUTPUT_DIR / name
    result_df.coalesce(1).write.option("quoteAll", "true").option("escape", '"').csv(
        str(csv_path), header=True, mode="overwrite"
    )
    print(f"Saved CSV output folder: {csv_path}")

spark.stop()
