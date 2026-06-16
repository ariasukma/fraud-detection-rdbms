import os

from dotenv import load_dotenv

load_dotenv()


def create_db_adapter():
    db_type = os.getenv("DB_TYPE", "postgres")
    if db_type == "postgres":
        from .postgres import create_adapter
    elif db_type == "cockroachdb":
        from .cockroachdb import create_adapter
    elif db_type == "mysql":
        from .mysql import create_adapter
    elif db_type == "oracle":
        from .oracle import create_adapter
    elif db_type == "sqlserver":
        from .sqlserver import create_adapter
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")
    return create_adapter()

