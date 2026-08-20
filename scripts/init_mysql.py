#!/usr/bin/env python
"""
Create the MySQL database for JOFA (no data migration).

Usage:
  python scripts/init_mysql.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def main() -> int:
    host = os.getenv('MYSQL_HOST', '127.0.0.1')
    port = int(os.getenv('MYSQL_PORT', '3306'))
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'jofa')

    print(f'Connecting to MySQL at {host}:{port} as {user}...')
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4',
            autocommit=True,
        )
    except pymysql.Error as exc:
        print(f'Connection failed: {exc}', file=sys.stderr)
        print('Check MYSQL_* values in .env and that MySQL is running.', file=sys.stderr)
        return 1

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f'CREATE DATABASE IF NOT EXISTS `{database}` '
                'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
            )
        print(f'Database `{database}` is ready.')
    finally:
        connection.close()

    print('Next:')
    print('  python manage.py migrate')
    print('  # or, to import existing SQLite data:')
    print('  python scripts/migrate_sqlite_to_mysql.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
