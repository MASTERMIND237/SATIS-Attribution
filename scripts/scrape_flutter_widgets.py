#!/usr/bin/env python3
import argparse
from pathlib import Path

from app.services.flutter_catalog import (
    DEFAULT_CATALOG_PATH,
    fetch_flutter_widget_catalog,
    save_widget_catalog,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape the official Flutter widget catalog into a local JSON file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help=f"Output JSON path (default: {DEFAULT_CATALOG_PATH})",
    )
    parser.add_argument(
        "--source-url",
        default="https://docs.flutter.dev/reference/widgets",
        help="Official Flutter widget catalog URL to scrape.",
    )
    args = parser.parse_args()

    catalog = fetch_flutter_widget_catalog(source_url=args.source_url)
    output_path = save_widget_catalog(catalog, output_path=args.output)

    print(f"Widget catalog saved to: {output_path}")
    print(f"Total widgets scraped: {catalog['total_widgets']}")
    print(f"Source URL: {catalog['source_url']}")


if __name__ == "__main__":
    main()
