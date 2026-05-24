from pathlib import Path
import os
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


def load_sql(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing SQL file: {path}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    load_dotenv(BACKEND_DIR / ".env", override=False)
    database_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        print(
            "SUPABASE_DB_URL is not set. Add the direct Supabase Postgres connection string "
            "to backend/.env, then run this script again."
        )
        return 2
    parsed_url = urlparse(database_url)
    if not parsed_url.scheme or not parsed_url.hostname:
        print(
            "SUPABASE_DB_URL is not a valid Postgres URL. Copy the direct connection string "
            "from Supabase Project Settings > Database, and URL-encode special characters "
            "in the password such as @, #, %, /, or spaces."
        )
        return 2

    try:
        import psycopg
    except ImportError:
        print("Missing psycopg. Run: venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        return 2

    schema_sql = load_sql(PROJECT_DIR / "supabase" / "schema.sql")
    seed_sql = load_sql(PROJECT_DIR / "supabase" / "seed.sql")

    try:
        with psycopg.connect(database_url, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(schema_sql)
                cursor.execute(seed_sql)
    except psycopg.OperationalError as exc:
        print("Could not connect to Supabase with SUPABASE_DB_URL.")
        print(
            "Check that the database URL belongs to the same Supabase project as SUPABASE_URL, "
            "and URL-encode special characters in the password."
        )
        if os.getenv("VERBOSE_DB_ERRORS") == "1":
            print(f"Connection error: {exc}")
        return 1

    print("Supabase schema and seed data applied successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
