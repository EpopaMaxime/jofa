#!/usr/bin/env python
"""
Migrate JOFA data from a local SQLite database to MySQL.

Prerequisites:
  1. MySQL server running
  2. Copy .env.example → .env and set MYSQL_* credentials
  3. pip install -r requirements.txt

Usage (from project root):
  python scripts/migrate_sqlite_to_mysql.py
  python scripts/migrate_sqlite_to_mysql.py --sqlite-path db.sqlite3
  python scripts/migrate_sqlite_to_mysql.py --skip-export
  python scripts/migrate_sqlite_to_mysql.py --skip-load
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
FIXTURE_DIR = BASE_DIR / 'fixtures'
DEFAULT_FIXTURE = FIXTURE_DIR / 'sqlite_export.json'

load_dotenv(BASE_DIR / '.env')

DUMP_EXCLUDE = [
    'contenttypes',
    'auth.Permission',
    'admin.LogEntry',
    'sessions.Session',
]


def mysql_settings() -> dict:
    return {
        'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'jofa'),
    }


def ensure_mysql_database() -> None:
    cfg = mysql_settings()
    print(f"[1/4] Creating MySQL database `{cfg['database']}` if needed...")
    connection = pymysql.connect(
        host=cfg['host'],
        port=cfg['port'],
        user=cfg['user'],
        password=cfg['password'],
        charset='utf8mb4',
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        print(f"      Ready: {cfg['database']} @ {cfg['host']}:{cfg['port']}")
    finally:
        connection.close()


def run_manage(*args: str, extra_env: dict | None = None) -> None:
    env = {
        **os.environ,
        'PYTHONUTF8': '1',
        'PYTHONIOENCODING': 'utf-8',
    }
    if extra_env:
        env.update(extra_env)
    command = [sys.executable, str(BASE_DIR / 'manage.py'), *args]
    result = subprocess.run(command, cwd=BASE_DIR, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}")


def sqlite_env(sqlite_path: Path) -> dict:
    return {
        **os.environ,
        'DJANGO_SETTINGS_MODULE': 'jofa_brand.settings_sqlite_export',
        'SQLITE_EXPORT_PATH': str(sqlite_path.resolve()),
        'PYTHONUTF8': '1',
        'PYTHONIOENCODING': 'utf-8',
    }


def clean_sqlite_orphans(sqlite_path: Path) -> None:
    """Remove broken FK rows that block dumpdata / MySQL NOT NULL constraints."""
    print('      Cleaning orphaned SQLite rows...')
    cleanup_code = r"""
import django
django.setup()
from django.contrib.auth.models import User
from django.db.models import Q
from orders.models import Order
from reviews.models import Review
from rewards.models import RewardPoint
from products.models import Wishlist
from accounts.models import Profile

valid_users = set(User.objects.values_list('id', flat=True))

def purge(model, label):
    orphans = model.objects.filter(Q(user_id__isnull=True) | ~Q(user_id__in=valid_users))
    count = orphans.count()
    if count:
        orphans.delete()
        print(f'Removed {count} orphan {label}.')
    else:
        print(f'No orphan {label} found.')

purge(Order, 'order(s)')
purge(Review, 'review(s)')
purge(RewardPoint, 'reward point(s)')
purge(Wishlist, 'wishlist(s)')
purge(Profile, 'profile(s)')
"""
    result = subprocess.run(
        [sys.executable, '-c', cleanup_code],
        cwd=BASE_DIR,
        env=sqlite_env(sqlite_path),
    )
    if result.returncode != 0:
        raise RuntimeError('SQLite cleanup failed — see output above.')


def export_sqlite_data(sqlite_path: Path, fixture_path: Path) -> None:
    print(f"[2/4] Exporting data from SQLite: {sqlite_path}")
    if not sqlite_path.exists():
        raise FileNotFoundError(
            f"SQLite file not found: {sqlite_path}\n"
            "Pass --sqlite-path or place db.sqlite3 at the project root."
        )

    clean_sqlite_orphans(sqlite_path)

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    exclude_args: list[str] = []
    for item in DUMP_EXCLUDE:
        exclude_args.extend(['-e', item])

    env = sqlite_env(sqlite_path)
    # Use primary keys (not natural keys): safer with legacy / partial data.
    command = [
        sys.executable,
        str(BASE_DIR / 'manage.py'),
        'dumpdata',
        *exclude_args,
        '--indent',
        '2',
        '-o',
        str(fixture_path),
    ]
    result = subprocess.run(command, cwd=BASE_DIR, env=env)
    if result.returncode != 0:
        raise RuntimeError('dumpdata failed — see output above.')

    size_kb = fixture_path.stat().st_size / 1024
    print(f"      Fixture written: {fixture_path} ({size_kb:.1f} KB)")


def migrate_mysql_schema() -> None:
    print("[3/4] Applying Django migrations on MySQL...")
    run_manage('migrate', '--noinput')
    print("      Schema migrated.")


def load_fixture_into_mysql(fixture_path: Path) -> None:
    print(f"[4/4] Loading fixture into MySQL: {fixture_path}")
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    # Clear existing rows so re-running the migration stays idempotent.
    run_manage('flush', '--noinput')
    run_manage('loaddata', str(fixture_path))
    print("      Data imported successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Migrate JOFA from SQLite to MySQL.')
    parser.add_argument(
        '--sqlite-path',
        type=Path,
        default=BASE_DIR / 'db.sqlite3',
        help='Path to the source SQLite database (default: db.sqlite3)',
    )
    parser.add_argument(
        '--fixture',
        type=Path,
        default=DEFAULT_FIXTURE,
        help='Path to the JSON fixture used for import',
    )
    parser.add_argument(
        '--skip-export',
        action='store_true',
        help='Skip SQLite dump and reuse an existing fixture',
    )
    parser.add_argument(
        '--skip-load',
        action='store_true',
        help='Only create DB + run migrations (no data import)',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture_path = args.fixture

    print('=== JOFA: SQLite -> MySQL migration ===')
    cfg = mysql_settings()
    print(f"Target: {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']}")

    try:
        ensure_mysql_database()

        if args.skip_export:
            print('[2/4] Skipping export (using existing fixture).')
            if not args.skip_load and not fixture_path.exists():
                raise FileNotFoundError(
                    f"--skip-export used but fixture missing: {fixture_path}"
                )
        else:
            export_sqlite_data(args.sqlite_path.resolve(), fixture_path)

        migrate_mysql_schema()

        if args.skip_load:
            print('[4/4] Skipping data load (--skip-load).')
        else:
            load_fixture_into_mysql(fixture_path)

    except Exception as exc:
        print(f'\nMigration failed: {exc}', file=sys.stderr)
        return 1

    print('\nDone. Start the app with:')
    print('  python manage.py runserver')
    print('\nKeep db.sqlite3 as a backup, then delete it when you no longer need it.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
