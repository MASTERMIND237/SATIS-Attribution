#!/usr/bin/env python3
"""
Scraper pour le catalogue des widgets Flutter officiels.
Utilise BeautifulSoup4 pour parser la documentation Flutter.
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Chemin par défaut pour sauvegarder le catalogue
DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "flutter_widgets.json"

# Headers pour simuler un navigateur
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
}


def clean_text(text: str) -> str:
    """Nettoie le texte extrait du HTML."""
    if not text:
        return ""
    # Remplacer les espaces multiples et retours à la ligne
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def fetch_page(url: str, timeout: int = 15) -> str:
    """
    Récupère le contenu HTML d'une page.
    
    Args:
        url: L'URL à scraper
        timeout: Timeout en secondes
    
    Returns:
        Le contenu HTML de la page
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"❌ Erreur lors de la récupération de {url}: {e}")
        return ""


def fetch_flutter_widget_catalog(source_url: str = "https://docs.flutter.dev/reference/widgets") -> dict[str, Any]:
    """
    Récupère le catalogue complet des widgets Flutter.
    
    Args:
        source_url: URL de la page du catalogue des widgets
    
    Returns:
        Dictionnaire contenant tous les widgets avec leurs métadonnées
    """
    print(f"🔍 Scraping du catalogue Flutter depuis: {source_url}")
    
    html_content = fetch_page(source_url)
    if not html_content:
        print("⚠️  Impossible de récupérer la page du catalogue")
        return _empty_catalog(source_url)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    widgets = []
    
    # Méthode 1: Chercher les liens dans les listes de widgets
    # La page Flutter a généralement des sections avec des liens vers les widgets
    widget_links = soup.find_all('a', href=re.compile(r'/ui/widgets/|/flutter/widgets/'))
    
    if not widget_links:
        # Méthode 2: Chercher dans les tableaux ou listes
        widget_links = soup.find_all('a', href=True)
        widget_links = [a for a in widget_links if 'widget' in a.get('href', '').lower()]
    
    print(f"📊 {len(widget_links)} liens potentiels trouvés")
    
    seen_names = set()
    
    for link in widget_links:
        href = link.get('href', '')
        name = clean_text(link.get_text())
        
        # Filtrer les liens valides
        if not name or len(name) < 2 or len(name) > 100:
            continue
        
        # Éviter les doublons
        if name.lower() in seen_names:
            continue
        
        # Éviter les faux positifs
        skip_words = ['previous', 'next', 'back', 'home', 'read more', 'learn more', 'view all']
        if any(skip in name.lower() for skip in skip_words):
            continue
        
        # Construire l'URL complète
        full_url = urljoin(source_url, href) if href.startswith('/') else href
        
        # Déterminer la catégorie à partir du contexte
        category = _determine_category(link, soup)
        
        # Récupérer la description si disponible
        description = _extract_description(link, soup)
        
        widget_entry = {
            "name": name,
            "url": full_url,
            "category": category,
            "description": description,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        
        widgets.append(widget_entry)
        seen_names.add(name.lower())
        
        # Progression
        if len(widgets) % 20 == 0:
            print(f"  ✓ {len(widgets)} widgets extraits...")
        
        # Petit délai pour être poli avec le serveur
        time.sleep(0.1)
    
    # Méthode 3: Chercher les cards ou sections de widgets
    if len(widgets) < 10:
        print("⚠️  Peu de widgets trouvés, tentative avec les cards...")
        widgets_from_cards = _extract_from_cards(soup, source_url)
        for w in widgets_from_cards:
            if w["name"].lower() not in seen_names:
                widgets.append(w)
                seen_names.add(w["name"].lower())
    
    # Trier par nom
    widgets.sort(key=lambda w: w["name"].lower())
    
    catalog = {
        "source_url": source_url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "total_widgets": len(widgets),
        "widgets": widgets,
    }
    
    print(f"✅ Total widgets extraits: {len(widgets)}")
    
    # Afficher un aperçu
    if widgets:
        print("\n📋 Aperçu des widgets:")
        for w in widgets[:10]:
            print(f"  • {w['name']} ({w['category']})")
        if len(widgets) > 10:
            print(f"  ... et {len(widgets) - 10} autres")
    
    return catalog


def _determine_category(link, soup) -> str:
    """
    Détermine la catégorie d'un widget à partir de son contexte dans la page.
    """
    # Remonter dans le DOM pour trouver un titre de section
    parent = link.parent
    for _ in range(5):
        if parent is None:
            break
        
        # Chercher un titre précédent
        heading = parent.find_previous(['h1', 'h2', 'h3', 'h4'])
        if heading:
            heading_text = clean_text(heading.get_text())
            if heading_text and len(heading_text) < 60:
                return heading_text
        
        parent = parent.parent
    
    return "Widgets"


def _extract_description(link, soup) -> str:
    """
    Extrait la description d'un widget à partir de son contexte.
    """
    # Chercher un paragraphe proche
    parent = link.parent
    for _ in range(3):
        if parent is None:
            break
        
        # Chercher un paragraphe ou une description
        desc_elem = parent.find('p')
        if desc_elem:
            return clean_text(desc_elem.get_text())[:200]
        
        parent = parent.parent
    
    return ""


def _extract_from_cards(soup: BeautifulSoup, base_url: str) -> list[dict[str, Any]]:
    """
    Méthode alternative : extraire les widgets depuis des cards ou tuiles.
    """
    widgets = []
    
    # Chercher les éléments qui ressemblent à des cards
    cards = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'card|widget|item|tile', re.I))
    
    for card in cards:
        link = card.find('a', href=True)
        if link:
            name = clean_text(link.get_text())
            if name and len(name) > 1:
                href = link.get('href', '')
                full_url = urljoin(base_url, href) if href.startswith('/') else href
                
                # Chercher une description dans la card
                desc_elem = card.find('p')
                description = clean_text(desc_elem.get_text())[:200] if desc_elem else ""
                
                widgets.append({
                    "name": name,
                    "url": full_url,
                    "category": "Widgets",
                    "description": description,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })
    
    return widgets


def _empty_catalog(source_url: str) -> dict[str, Any]:
    """Retourne un catalogue vide."""
    return {
        "source_url": source_url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "total_widgets": 0,
        "widgets": [],
    }


def save_widget_catalog(catalog: dict[str, Any], output_path: Path) -> Path:
    """
    Sauvegarde le catalogue des widgets dans un fichier JSON.
    
    Args:
        catalog: Le dictionnaire du catalogue
        output_path: Chemin du fichier de sortie
    
    Returns:
        Le chemin du fichier sauvegardé
    """
    # Créer le dossier parent si nécessaire
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    
    return output_path


def load_widget_catalog(catalog_path: Path = DEFAULT_CATALOG_PATH) -> dict[str, Any]:
    """
    Charge le catalogue des widgets depuis un fichier JSON.
    
    Args:
        catalog_path: Chemin du fichier JSON
    
    Returns:
        Le dictionnaire du catalogue
    """
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalogue non trouvé: {catalog_path}")
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_widget_names(catalog_path: Path = DEFAULT_CATALOG_PATH) -> list[str]:
    """
    Retourne la liste des noms de widgets.
    
    Args:
        catalog_path: Chemin du fichier JSON
    
    Returns:
        Liste des noms de widgets
    """
    catalog = load_widget_catalog(catalog_path)
    return [w["name"] for w in catalog.get("widgets", [])]


def get_widgets_by_category(catalog_path: Path = DEFAULT_CATALOG_PATH) -> dict[str, list[str]]:
    """
    Retourne les widgets groupés par catégorie.
    
    Args:
        catalog_path: Chemin du fichier JSON
    
    Returns:
        Dictionnaire {catégorie: [noms des widgets]}
    """
    catalog = load_widget_catalog(catalog_path)
    categories: dict[str, list[str]] = {}
    
    for widget in catalog.get("widgets", []):
        category = widget.get("category", "Non catégorisé")
        if category not in categories:
            categories[category] = []
        categories[category].append(widget["name"])
    
    return categories