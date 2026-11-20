FROM python:3.12-slim-bookworm

# Java é requisito do Spark (JVM); procps é usado pelos scripts internos do Spark.
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless curl procps \
    && rm -rf /var/lib/apt/lists/*

# Driver JDBC do PostgreSQL (carga da camada gold no banco).
RUN mkdir -p /opt/jars \
    && curl -fsSL -o /opt/jars/postgresql.jar \
       https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Driver JDBC do SQL Server. Fica depois do pip de propósito: mexer nos drivers não refaz a camada
# do PySpark (300 MB), que é a mais cara da imagem.
RUN curl -fsSL -o /opt/jars/mssql-jdbc.jar \
    https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.8.1.jre11/mssql-jdbc-12.8.1.jre11.jar

COPY src ./src
COPY tests ./tests
COPY pytest.ini .
COPY sql ./sql

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

CMD ["python", "-m", "pipeline.run_pipeline", "--load-postgres"]
