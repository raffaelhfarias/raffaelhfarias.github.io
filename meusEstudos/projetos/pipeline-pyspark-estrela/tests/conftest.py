import pytest

from pipeline.spark_session import get_spark


@pytest.fixture(scope="session")
def spark():
    """Uma única sessão Spark para todos os testes. Usa get_spark() para que o driver JDBC do
    PostgreSQL esteja disponível (no container) nos testes de integração."""
    sessao = get_spark("testes", shuffle_partitions=2, ui=False)
    sessao.sparkContext.setLogLevel("ERROR")
    yield sessao
    sessao.stop()
