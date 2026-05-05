from sqlmodel import select

from app.models.widget import Widget
from app.services.flutter_catalog import extract_widget_entries, import_widget_catalog


def test_extract_widget_entries_filters_and_deduplicates_widget_links():
    html = """
    <html>
      <body>
        <a href="https://api.flutter.dev/flutter/widgets/Container-class.html">Container</a>
        <a href="/flutter/widgets/Text-class.html">Text</a>
        <a href="/flutter/widgets/Row-class.html">Row</a>
        <a href="/flutter/widgets/Row-class.html">Row</a>
        <a href="/flutter/widgets/Bottom app bar-class.html">Bottom app bar</a>
        <a href="/flutter/rendering/RenderBox-class.html">RenderBox</a>
        <a href="/flutter/widgets/AnimatedList-class.html"> AnimatedList </a>
      </body>
    </html>
    """

    entries = extract_widget_entries(html, source_url="https://docs.flutter.dev/reference/widgets")

    assert entries == [
        {
            "name": "AnimatedList",
            "api_url": "https://api.flutter.dev/flutter/widgets/AnimatedList-class.html",
        },
        {
            "name": "Container",
            "api_url": "https://api.flutter.dev/flutter/widgets/Container-class.html",
        },
        {
            "name": "Row",
            "api_url": "https://api.flutter.dev/flutter/widgets/Row-class.html",
        },
        {
            "name": "Text",
            "api_url": "https://api.flutter.dev/flutter/widgets/Text-class.html",
        },
    ]


def test_import_widget_catalog_creates_and_updates_widgets(session):
    catalog = {
        "widgets": [
            {
                "name": "Container",
                "api_url": "https://api.flutter.dev/flutter/widgets/Container-class.html",
            },
            {
                "name": "Text",
                "api_url": "https://api.flutter.dev/flutter/widgets/Text-class.html",
                "description": "Displays a string of text.",
            },
        ]
    }

    stats = import_widget_catalog(session, catalog)
    widgets = session.exec(select(Widget)).all()

    assert stats == {
        "created": 2,
        "updated": 0,
        "skipped": 0,
        "total_catalog_widgets": 2,
    }
    assert {widget.name for widget in widgets} == {"Container", "Text"}

    updated_catalog = {
        "widgets": [
            {
                "name": "Container",
                "description": "A convenience widget that combines common painting.",
            },
            {
                "name": "Text",
                "description": "Updated description",
            },
        ]
    }

    stats = import_widget_catalog(session, updated_catalog, overwrite_descriptions=True)
    widgets = session.exec(select(Widget)).all()

    assert stats == {
        "created": 0,
        "updated": 2,
        "skipped": 0,
        "total_catalog_widgets": 2,
    }
    descriptions = {widget.name: widget.description for widget in widgets}
    assert descriptions["Container"] == "A convenience widget that combines common painting."
    assert descriptions["Text"] == "Updated description"
