"""Temporary settings used only by scripts/migrate_sqlite_to_mysql.py to dump SQLite data."""

import os
from pathlib import Path

from .settings import *  # noqa: F403

_sqlite_path = os.getenv(
    'SQLITE_EXPORT_PATH',
    str(Path(__file__).resolve().parent.parent / 'db.sqlite3'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _sqlite_path,
    }
}
