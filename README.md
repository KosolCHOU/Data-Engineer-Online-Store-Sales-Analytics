# Online Retail Sales Data Profiling and Aggregation

## Project Objective

This project loads the Kaggle Online Retail dataset into PostgreSQL, extracts it with Spark JDBC, profiles raw data quality, cleans the data with Spark ETL, creates aggregation tables, and exports CSV outputs for reporting and visualization.

## Dataset

Source: Kaggle Online Retail / Online Retail II dataset.

Place the raw file in:

```bash
data/online_retail_II.xlsx
```

## Project Structure

```text
data/
drivers/
output/
sql/
src/
  01_load_to_db.py
  02_spark_extract.py
  03_etl_cleaning.py
  04_data_profiling.py
  05_aggregation.py
  06_visualize_charts.py
```

The Spark scripts use `drivers/postgresql-42.7.3.jar` if it exists. If it does not exist, Spark downloads the PostgreSQL JDBC driver with `spark.jars.packages`.

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```bash
MSSQL_USER=sa
MSSQL_PASSWORD=replace_this_with_your_real_mssql_password
MSSQL_DB=online_store
MSSQL_HOST=localhost
MSSQL_PORT=1433
```

Make sure your password is strong (e.g. at least 8 characters, containing uppercase, lowercase, numbers, and special characters). Do not commit `.env`.

## Run With Docker

This is the easiest setup for another machine because Docker runs both MS SQL Server
and the Python/Spark app.

Prerequisites:

- Docker Desktop, or Docker Engine with Docker Compose
- The dataset at `data/online_retail_II.xlsx`

Optional: create a Docker-specific env file if you want to override the default
MS SQL Server credentials used by Compose:

```bash
cp .env.docker.example .env.docker
```

Then run the complete pipeline:

```bash
docker compose up --build app
```

If you created `.env.docker`, run:

```bash
docker compose --env-file .env.docker up --build app
```

The app container runs these steps in order:

```bash
python src/01_load_to_db.py
python src/02_spark_extract.py
python src/04_data_profiling.py
python src/03_etl_cleaning.py
python src/05_aggregation.py
python src/06_visualize_charts.py
```

Generated CSV files are written to `output/`, and charts are written to
`charts/` on your host machine.

To stop the containers:

```bash
docker compose down
```

To reset database data and rerun from a clean database:

```bash
docker compose down -v
docker compose up --build app
```

## Execution Order

Run from the project root:

```bash
python src/01_load_to_db.py
python src/02_spark_extract.py
python src/04_data_profiling.py
python src/03_etl_cleaning.py
python src/05_aggregation.py
python src/06_visualize_charts.py
```

## Expected Success

Successful loading should show:

```text
COPY 1067356
Data loaded successfully.
```

Successful Spark extraction should show:

```text
Total rows: 1067356
```

Successful verification should show:

```text
PROJECT VERIFICATION PASSED
```

## Aggregation Outputs

The aggregation step writes these PostgreSQL tables and CSV folders:

```text
sales_by_country
top_products
monthly_sales
customer_summary
hourly_sales
```

CSV folders are saved under `output/`, each with a Spark `part-*.csv` file.

## Troubleshooting

`ModuleNotFoundError: No module named 'dotenv'`

Install dependencies:

```bash
pip install -r requirements.txt
```

`FATAL: password authentication failed`

Check `.env` and use your real MS SQL Server password:

```bash
MSSQL_PASSWORD=replace_this_with_your_real_mssql_password
```

`relation "online_retail" does not exist`

Run the loader first:

```bash
python src/01_load_to_db.py
```

Spark warns that the local JDBC jar is missing

This is acceptable if Spark resolves `com.microsoft.sqlserver:mssql-jdbc:12.6.1.jre11` from Maven. To work fully offline, place `mssql-jdbc-12.6.1.jre11.jar` in `drivers/`.
# Data-Engineer-Online-Store-Sales-Analytics
