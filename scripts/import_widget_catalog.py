#!/usr/bin/env python3
import argparse
from pathlib import Path

from sqlmodel import Session, SQLModel

from app.db.database import engine
from app.services.flutter_catalog import DEFAULT_CATALOG_PATH, import_widget_catalog, load_widget_catalog


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a local Flutter widget catalog JSON file into the widget table."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help=f"Input JSON path (default: {DEFAULT_CATALOG_PATH})",
    )
    parser.add_argument(
        "--overwrite-descriptions",
        action="store_true",
        help="Update existing widget descriptions from the catalog.",
    )
    args = parser.parse_args()

    catalog = load_widget_catalog(args.input)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        stats = import_widget_catalog(
            session,
            catalog,
            overwrite_descriptions=args.overwrite_descriptions,
        )

    print(f"Catalog imported from: {args.input}")
    print(
        "Created: {created} | Updated: {updated} | Skipped: {skipped} | Total catalog widgets: {total}".format(
            created=stats["created"],
            updated=stats["updated"],
            skipped=stats["skipped"],
            total=stats["total_catalog_widgets"],
        )
    )


if __name__ == "__main__":
    main()
