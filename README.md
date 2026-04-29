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

Start PostgreSQL:

```bash
sudo systemctl start postgresql
pg_isready -h localhost -p 5432
```

Create the project database once:

```bash
psql -U postgres -h localhost -p 5432 -f sql/00_create_database.sql
```

Create a `.env` file in the project root:

```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=replace_this_with_your_real_postgres_password
POSTGRES_DB=online_store
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Use the same password you type when `psql` asks for `Password for user postgres:`. Do not commit `.env`.

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

`FATAL: database "online_store" does not exist`

Create the database:

```bash
psql -U postgres -h localhost -p 5432 -f sql/00_create_database.sql
```

`FATAL: password authentication failed`

Check `.env` and use your real PostgreSQL password:

```bash
POSTGRES_PASSWORD=replace_this_with_your_real_postgres_password
```

`relation "online_retail" does not exist`

Run the loader first:

```bash
python src/01_load_to_db.py
```

Spark warns that the local JDBC jar is missing

This is acceptable if Spark resolves `org.postgresql:postgresql:42.7.3` from Maven. To work fully offline, place `postgresql-42.7.3.jar` in `drivers/`.
# Data-Engineer-Online-Store-Sales-Analytics
