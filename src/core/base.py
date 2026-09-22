import importlib
import importlib.util
import pkgutil

from sqlalchemy.orm import DeclarativeBase

import src.domains as domains


class Base(DeclarativeBase):
    pass


def import_all_database_models() -> None:
    """Import domain database models into the shared SQLAlchemy metadata."""
    importlib.import_module("src.messaging.models")

    for _, name, _ in pkgutil.iter_modules(domains.__path__):
        module_path = f"src.domains.{name}.models"
        if importlib.util.find_spec(module_path) is not None:
            importlib.import_module(module_path)
