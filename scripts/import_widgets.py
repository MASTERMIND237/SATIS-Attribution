#!/usr/bin/env python3
"""Importe les widgets dans la base de données Render via l'API HTTP."""
import json
import sys
from pathlib import Path

import requests

# URL de l'API Render
API_URL = "https://satis-attribution-backend.onrender.com/api/v1"

# Chemin vers le fichier JSON
CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "flutter_widgets.json"


def import_widgets():
    """Importe tous les widgets via l'API REST."""
    
    # Vérifier que le catalogue existe
    if not CATALOG_PATH.exists():
        print(f"❌ Catalogue introuvable : {CATALOG_PATH}")
        print("Lance d'abord : python scripts/scrape_flutter_widgets.py")
        sys.exit(1)
    
    # Charger le catalogue
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    
    widgets = catalog.get("widgets", [])
    print(f"📦 {len(widgets)} widgets à importer")
    print(f"🎯 API cible : {API_URL}")
    print()
    
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for i, w in enumerate(widgets, 1):
        payload = {
            "name": w["name"],
            "description": w.get("description", ""),
            "category": w.get("category", ""),
        }
        
        try:
            response = requests.post(
                f"{API_URL}/widgets/",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                widget_data = response.json()
                widget_id = widget_data.get("id", "?")
                
                # Ajouter les propriétés du widget
                properties = w.get("properties", [])
                prop_count = 0
                for prop_name in properties:
                    try:
                        prop_response = requests.post(
                            f"{API_URL}/widgets/{widget_id}/properties",
                            json={"name": prop_name},
                            timeout=10
                        )
                        if prop_response.status_code == 200:
                            prop_count += 1
                    except Exception:
                        pass
                
                print(f"  [{i}/{len(widgets)}] ✅ {w['name']} ({prop_count} propriétés)")
                success_count += 1
                
            elif response.status_code == 400 and "existe déjà" in response.text:
                print(f"  [{i}/{len(widgets)}] ⏭️  {w['name']} (déjà existant)")
                skip_count += 1
                
            else:
                print(f"  [{i}/{len(widgets)}] ❌ {w['name']}: {response.text[:100]}")
                error_count += 1
                
        except requests.exceptions.Timeout:
            print(f"  [{i}/{len(widgets)}] ⏳ {w['name']}: Timeout (Render en veille ?)")
            error_count += 1
            # Attendre un peu pour le réveil
            import time
            time.sleep(5)
            
        except Exception as e:
            print(f"  [{i}/{len(widgets)}] ❌ {w['name']}: {e}")
            error_count += 1
    
    print()
    print("=" * 50)
    print(f"✅ Succès : {success_count}")
    print(f"⏭️  Déjà existants : {skip_count}")
    print(f"❌ Erreurs : {error_count}")
    print(f"📊 Total : {len(widgets)}")
    print("=" * 50)


if __name__ == "__main__":
    print("🔧 Vérification de la connexion au backend...")
    try:
        health = requests.get(
            API_URL.replace("/api/v1", "/health/database"),
            timeout=30
        )
        print(f"   Status: {health.status_code}")
        if health.status_code != 200:
            print("⚠️  Le backend n'est pas accessible. Vérifie qu'il est en ligne.")
            print(f"   URL: {API_URL.replace('/api/v1', '/health/database')}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Impossible de joindre le backend : {e}")
        sys.exit(1)
    
    print()
    import_widgets()