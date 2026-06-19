#!/usr/bin/env bash
set -euo pipefail

echo "Checking required dataset..."
if [ ! -f "data/online_retail_II.xlsx" ]; then
  echo "Missing data/online_retail_II.xlsx"
  echo "Place the dataset in the data/ folder, then run docker compose again."
  exit 1
fi

echo "Waiting for SQL Server..."
until python -c "import socket; s = socket.socket(); s.connect(('${MSSQL_HOST:-db}', 1433))" >/dev/null 2>&1; do
  sleep 2
done


echo "Running sales analytics pipeline..."
python src/01_load_to_db.py
python src/02_spark_extract.py
python src/04_data_profiling.py
python src/03_etl_cleaning.py
python src/05_aggregation.py
python src/06_visualize_charts.py

echo "Pipeline completed."
