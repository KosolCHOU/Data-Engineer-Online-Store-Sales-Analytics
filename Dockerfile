FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    SPARK_LOCAL_IP=127.0.0.1 \
    PYSPARK_PYTHON=python

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        openjdk-17-jre-headless \
        procps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p drivers output charts \
    && if [ ! -f drivers/mssql-jdbc-12.6.1.jre11.jar ]; then \
        curl -fsSL \
          https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.6.1.jre11/mssql-jdbc-12.6.1.jre11.jar \
          -o drivers/mssql-jdbc-12.6.1.jre11.jar; \
      fi \
    && chmod +x scripts/run_pipeline.sh

CMD ["bash", "scripts/run_pipeline.sh"]
