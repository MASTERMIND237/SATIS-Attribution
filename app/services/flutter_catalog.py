import json
import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import urlopen

from sqlmodel import Session, select

from ..models.widget import Widget

FLUTTER_WIDGET_INDEX_URL = "https://docs.flutter.dev/reference/widgets"
FLUTTER_API_BASE_URL = "https://api.flutter.dev"
DEFAULT_CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "flutter_widgets_catalog.json"
WIDGET_CLASS_HREF_PATTERN = re.compile(r"/flutter/widgets/.+?-class\.html$")
WIDGET_NAME_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9_]*$")


class _AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._current_href: str | None = None
        self._current_chunks: list[str] = []
        self.anchors: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attrs_map = dict(attrs)
        href = attrs_map.get("href")
        if not href:
            return
        self._current_href = href
        self._current_chunks = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._current_href is None:
            return
        text = " ".join(chunk.strip() for chunk in self._current_chunks if chunk.strip()).strip()
        if text:
            self.anchors.append((self._current_href, unescape(text)))
        self._current_href = None
        self._current_chunks = []


def _normalize_widget_name(name: str) -> str:
    return re.sub(r"\s+", "", name.strip())


def _is_widget_anchor(href: str, text: str) -> bool:
    if not WIDGET_CLASS_HREF_PATTERN.search(href):
        return False
    normalized_name = _normalize_widget_name(text)
    return bool(WIDGET_NAME_PATTERN.fullmatch(normalized_name))


def _normalize_api_url(href: str, source_url: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/flutter/"):
        return urljoin(FLUTTER_API_BASE_URL, href)
    return urljoin(source_url, href)


def extract_widget_entries(html: str, source_url: str = FLUTTER_WIDGET_INDEX_URL) -> list[dict[str, str]]:
    parser = _AnchorCollector()
    parser.feed(html)

    unique_entries: dict[str, dict[str, str]] = {}
    for href, text in parser.anchors:
        if not _is_widget_anchor(href, text):
            continue
        name = _normalize_widget_name(text)
        unique_entries[name] = {
            "name": name,
            "api_url": _normalize_api_url(href, source_url),
        }

    return [unique_entries[name] for name in sorted(unique_entries)]


def fetch_flutter_widget_catalog(source_url: str = FLUTTER_WIDGET_INDEX_URL, timeout: int = 30) -> dict[str, Any]:
    with urlopen(source_url, timeout=timeout) as response:
        html = response.read().decode("utf-8")

    widgets = extract_widget_entries(html, source_url=source_url)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "total_widgets": len(widgets),
        "widgets": widgets,
    }


def save_widget_catalog(catalog: dict[str, Any], output_path: Path = DEFAULT_CATALOG_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=True), encoding="utf-8")
    return output_path


def load_widget_catalog(catalog_path: Path = DEFAULT_CATALOG_PATH) -> dict[str, Any]:
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def import_widget_catalog(
    session: Session,
    catalog: dict[str, Any],
    overwrite_descriptions: bool = False,
) -> dict[str, int]:
    created = 0
    updated = 0
    skipped = 0

    for entry in catalog.get("widgets", []):
        name = entry["name"].strip()
        api_url = entry.get("api_url", "").strip()
        description = entry.get("description", "").strip() or (
            f"Imported from Flutter official catalog: {api_url}" if api_url else "Imported from Flutter official catalog."
        )

        widget = session.exec(select(Widget).where(Widget.name == name)).first()
        if widget:
            if overwrite_descriptions and widget.description != description:
                widget.description = description
                session.add(widget)
                updated += 1
            else:
                skipped += 1
            continue

        session.add(Widget(name=name, description=description))
        created += 1

    session.commit()
    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total_catalog_widgets": len(catalog.get("widgets", [])),
    }
