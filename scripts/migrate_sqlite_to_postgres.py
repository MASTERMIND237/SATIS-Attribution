#!/usr/bin/env python3
"""
Script simple pour migrer les données de la base SQLite locale
vers une base Postgres (Supabase). Utilisation:

  export DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/dbname"
  cd env/backend
  python scripts/migrate_sqlite_to_postgres.py

Le script crée d'abord les tables cibles, puis copie les lignes
dans l'ordre: Student, Widget, WidgetProperty, Assignment.
"""
import os
from sqlalchemy import text
from sqlmodel import Session, SQLModel, select

from app.db.database import build_engine, normalize_database_url
from app.models.student import Student
from app.models.widget import Widget, WidgetProperty
from app.models.assignment import Assignment


SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///./satis_attribution.db")
PG_URL = os.getenv("DATABASE_URL")

if not PG_URL:
    raise SystemExit("Please set DATABASE_URL to your Postgres (Supabase) connection string")

sqlite_engine = build_engine(SQLITE_URL)
pg_engine = build_engine(PG_URL)


def _filter_row_data(row):
    data = row.model_dump()
    # Remove relationship fields (lists or nested dicts)
    for k, v in list(data.items()):
        if isinstance(v, (list, dict)):
            data.pop(k)
    return data


def copy_model(Model):
    with Session(sqlite_engine) as s_sql, Session(pg_engine) as s_pg:
        rows = s_sql.exec(select(Model)).all()
        for r in rows:
            data = _filter_row_data(r)
            row_id = data.get("id")
            if row_id is not None and s_pg.get(Model, row_id):
                continue
            inst = Model(**data)
            s_pg.add(inst)
        s_pg.commit()

    # try to set sequence value on Postgres (if serial sequence exists)
    table = getattr(Model, "__tablename__", Model.__name__.lower())
    try:
        with pg_engine.connect() as conn:
            conn.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table}','id'), (SELECT COALESCE(MAX(id),1) FROM {table}));"
                )
            )
            conn.commit()
    except Exception as e:
        print(f"Could not set sequence for {table}: {e}")


def main():
    print(f"SQLite source: {normalize_database_url(SQLITE_URL)}")
    print(f"Postgres target: {normalize_database_url(PG_URL)}")
    print("Creating tables on target Postgres...")
    SQLModel.metadata.create_all(pg_engine)

    print("Copying students...")
    copy_model(Student)

    print("Copying widgets...")
    copy_model(Widget)

    print("Copying widget properties...")
    copy_model(WidgetProperty)

    print("Copying assignments...")
    copy_model(Assignment)

    print("Migration complete.")


if __name__ == "__main__":
    main()
