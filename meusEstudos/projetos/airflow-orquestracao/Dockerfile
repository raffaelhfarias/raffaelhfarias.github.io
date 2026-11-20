FROM apache/airflow:2.10.5-python3.12

USER root
# Java é requisito do Spark; procps é usado pelos scripts internos do Spark.
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless curl procps \
    && rm -rf /var/lib/apt/lists/*

# Driver JDBC do PostgreSQL (carga da camada gold no DW).
RUN mkdir -p /opt/jars \
    && curl -fsSL -o /opt/jars/postgresql.jar \
       https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar

USER airflow
# O código da pipeline PySpark NÃO é copiado para a imagem: o compose o monta de
# ../pipeline-pyspark-estrela/src, então há uma única fonte da verdade para o código.
RUN pip install --no-cache-dir pyspark==3.5.3 pytest==8.3.4
