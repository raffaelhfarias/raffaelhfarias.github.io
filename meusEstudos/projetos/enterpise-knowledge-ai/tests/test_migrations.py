from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base, Membership, Tenant, User
from scripts import seed_demo


def test_migration_roundtrip_and_idempotent_seed(tmp_path, monkeypatch):
    database_url = f"sqlite:///{(tmp_path / 'migration.db').as_posix()}"
    monkeypatch.setattr(settings(), "database_url", database_url)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
        monkeypatch.setattr(seed_demo, "SessionLocal", sessionmaker(bind=engine))
        seed_demo.main()
        seed_demo.main()
        with engine.connect() as connection:
            assert connection.scalar(select(func.count()).select_from(Tenant)) == 2
            assert connection.scalar(select(func.count()).select_from(User)) == 3
            assert connection.scalar(select(func.count()).select_from(Membership)) == 3
        command.downgrade(config, "base")
        assert set(inspect(engine).get_table_names()) == {"alembic_version"}
        command.upgrade(config, "head")
        assert "documents" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
