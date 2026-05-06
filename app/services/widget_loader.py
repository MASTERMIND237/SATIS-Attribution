"""
Service de chargement et de gestion du catalogue des widgets Flutter.
"""
import json
import random
from pathlib import Path
from typing import Any


# Chemin vers le fichier JSON des widgets
WIDGETS_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "flutter_widgets.json"


def load_widget_catalog() -> dict[str, Any]:
    """Charge le catalogue complet des widgets Flutter."""
    if not WIDGETS_CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Catalogue des widgets introuvable : {WIDGETS_CATALOG_PATH}\n"
            "Créez le fichier data/flutter_widgets.json avec la liste des widgets."
        )
    
    with open(WIDGETS_CATALOG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_widgets() -> list[dict[str, Any]]:
    """Retourne tous les widgets du catalogue."""
    catalog = load_widget_catalog()
    return catalog.get("widgets", [])


def get_widget_names() -> list[str]:
    """Retourne la liste de tous les noms de widgets."""
    return [w["name"] for w in get_all_widgets()]


def get_widget_by_name(name: str) -> dict[str, Any] | None:
    """Retourne un widget par son nom exact."""
    for widget in get_all_widgets():
        if widget["name"].lower() == name.lower():
            return widget
    return None


def get_widgets_by_category(category: str) -> list[dict[str, Any]]:
    """Retourne les widgets d'une catégorie donnée."""
    return [w for w in get_all_widgets() if w.get("category", "").lower() == category.lower()]


def get_widget_names_by_category(category: str) -> list[str]:
    """Retourne les noms des widgets d'une catégorie donnée."""
    return [w["name"] for w in get_widgets_by_category(category)]


def get_categories() -> list[str]:
    """Retourne la liste de toutes les catégories disponibles."""
    categories = set()
    for widget in get_all_widgets():
        if "category" in widget:
            categories.add(widget["category"])
    return sorted(categories)


def get_random_widgets(count: int = 5, category: str | None = None) -> list[dict[str, Any]]:
    """
    Retourne des widgets aléatoires.
    
    Args:
        count: Nombre de widgets à retourner
        category: Filtrer par catégorie (optionnel)
    
    Returns:
        Liste de widgets sélectionnés aléatoirement
    """
    widgets = get_all_widgets()
    
    if category:
        widgets = get_widgets_by_category(category)
    
    if not widgets:
        return []
    
    selected = random.sample(widgets, min(count, len(widgets)))
    return selected


def get_random_widget_names(count: int = 5, category: str | None = None) -> list[str]:
    """Retourne des noms de widgets aléatoires."""
    return [w["name"] for w in get_random_widgets(count, category)]


def get_widget_properties(widget_name: str) -> list[str]:
    """Retourne les propriétés d'un widget spécifique."""
    widget = get_widget_by_name(widget_name)
    if widget:
        return widget.get("properties", [])
    return []


def get_widget_description(widget_name: str) -> str:
    """Retourne la description d'un widget spécifique."""
    widget = get_widget_by_name(widget_name)
    if widget:
        return widget.get("description", "")
    return ""