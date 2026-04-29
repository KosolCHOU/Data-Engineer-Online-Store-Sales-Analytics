import os
from pathlib import Path

from pyspark.sql import SparkSession
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSTGRES_DRIVER_JAR = PROJECT_ROOT / "drivers" / "postgresql-42.7.3.jar"
POSTGRES_DRIVER_PACKAGE = "org.postgresql:postgresql:42.7.3"

spark_builder = SparkSession.builder.appName("OnlineStoreSalesAnalytics")

if POSTGRES_DRIVER_JAR.exists():
    spark_builder = spark_builder.config("spark.jars", str(POSTGRES_DRIVER_JAR))
else:
    spark_builder = spark_builder.config(
        "spark.jars.packages",
        POSTGRES_DRIVER_PACKAGE
    )

spark = spark_builder.getOrCreate()

jdbc_host = os.getenv("POSTGRES_HOST", "localhost")
jdbc_port = os.getenv("POSTGRES_PORT", "5432")
jdbc_db = os.getenv("POSTGRES_DB", "online_store")
jdbc_url = f"jdbc:postgresql://{jdbc_host}:{jdbc_port}/{jdbc_db}"
db_password = os.getenv("POSTGRES_PASSWORD", "")

if not db_password or db_password in {
    "your_postgres_password",
    "replace_this_with_your_real_postgres_password"
}:
    raise ValueError("Set POSTGRES_PASSWORD to your real PostgreSQL password before running this script.")

properties = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": db_password,
    "driver": "org.postgresql.Driver"
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
