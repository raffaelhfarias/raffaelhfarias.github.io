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

COPY src ./src
COPY tests ./tests
COPY pytest.ini .

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PG_JDBC_JAR=/opt/jars/postgresql.jar

CMD ["python", "-m", "pipeline.run_pipeline", "--load-postgres"]
