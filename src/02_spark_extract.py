import os
from pathlib import Path

from pyspark.sql import SparkSession
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MSSQL_DRIVER_JAR = PROJECT_ROOT / "drivers" / "mssql-jdbc-12.6.1.jre11.jar"
MSSQL_DRIVER_PACKAGE = "com.microsoft.sqlserver:mssql-jdbc:12.6.1.jre11"

spark_builder = SparkSession.builder.appName("OnlineStoreSalesAnalytics")

if MSSQL_DRIVER_JAR.exists():
    spark_builder = spark_builder.config("spark.jars", str(MSSQL_DRIVER_JAR))
else:
    spark_builder = spark_builder.config(
        "spark.jars.packages",
        MSSQL_DRIVER_PACKAGE
    )

spark = spark_builder.getOrCreate()

jdbc_host = os.getenv("MSSQL_HOST", "localhost")
jdbc_port = os.getenv("MSSQL_PORT", "1433")
jdbc_db = os.getenv("MSSQL_DB", "online_store")
jdbc_url = f"jdbc:sqlserver://{jdbc_host}:{jdbc_port};databaseName={jdbc_db};trustServerCertificate=true"
db_password = os.getenv("MSSQL_PASSWORD", "")

if not db_password or db_password in {
    "your_mssql_password",
    "replace_this_with_your_real_mssql_password"
}:
    raise ValueError("Set MSSQL_PASSWORD to your real MS SQL Server password before running this script.")

properties = {
    "user": os.getenv("MSSQL_USER", "sa"),
    "password": db_password,
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver"
}

df = spark.read.jdbc(
    url=jdbc_url,
    table="online_retail",
    properties=properties
)

df.printSchema()
df.show(5)
print("Total rows:", df.count())

spark.stop()
