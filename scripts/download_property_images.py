"""
Download high-resolution luxury real estate images from Unsplash API
and save them locally to platform/public/images/properties/ and web/static/images/properties/.
"""

import os
import sys
from pathlib import Path

import requests

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "_zaBEnB-9EtPZQX5JkORj7nTpciV0DoggydFz5ocR18")

SEARCH_CATEGORIES = [
    {
        "key": "nile_tower_exterior",
        "query": "modern luxury apartment building exterior",
        "filename": "nile_tower_ext.jpg"
    },
    {
        "key": "nile_tower_penthouse",
        "query": "luxury penthouse living room city view",
        "filename": "nile_tower_penthouse.jpg"
    },
    {
        "key": "nile_tower_bedroom",
        "query": "luxury master bedroom modern",
        "filename": "nile_tower_bed.jpg"
    },
    {
        "key": "zamalek_residence_exterior",
        "query": "luxury residential building waterfront",
        "filename": "zamalek_ext.jpg"
    },
    {
        "key": "zamalek_living",
        "query": "luxury living room marble modern",
        "filename": "zamalek_living.jpg"
    },
    {
        "key": "zamalek_kitchen",
        "query": "modern luxury kitchen marble island",
        "filename": "zamalek_kitchen.jpg"
    },
    {
        "key": "alexandria_seafront_exterior",
        "query": "luxury modern beachfront residence",
        "filename": "alexandria_ext.jpg"
    },
    {
        "key": "alexandria_sea_balcony",
        "query": "luxury balcony ocean view sunset",
        "filename": "alexandria_balcony.jpg"
    },
    {
        "key": "alexandria_suite",
        "query": "luxury suite bedroom view",
        "filename": "alexandria_suite.jpg"
    },
    {
        "key": "giza_estate_exterior",
        "query": "luxury modern residential estate",
        "filename": "giza_ext.jpg"
    },
    {
        "key": "giza_lounge",
        "query": "modern contemporary luxury lounge",
        "filename": "giza_lounge.jpg"
    },
    {
        "key": "new_cairo_villa_exterior",
        "query": "luxury modern villa pool",
        "filename": "new_cairo_ext.jpg"
    },
    {
        "key": "new_cairo_foyer",
        "query": "luxury villa interior foyer staircase",
        "filename": "new_cairo_foyer.jpg"
    },
    {
        "key": "luxury_bathroom",
        "query": "luxury modern bathroom marble tub",
        "filename": "luxury_bath.jpg"
    },
    {
        "key": "rooftop_pool",
        "query": "luxury rooftop pool modern sunset",
        "filename": "rooftop_pool.jpg"
    }
]

def download_images():
    root_dir = Path(__file__).resolve().parent.parent
    dest_dirs = [
        root_dir / "platform" / "public" / "images" / "properties",
        root_dir / "web" / "static" / "images" / "properties"
    ]

    for d in dest_dirs:
        d.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    session = requests.Session()

    print("[*] Connecting to Unsplash API with Access Key...")

    downloaded = 0
    for item in SEARCH_CATEGORIES:
        query = item["query"]
        filename = item["filename"]
        print(f"[*] Searching Unsplash for '{item['key']}': {query}...")

        try:
            res = session.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 3, "orientation": "landscape"},
                headers=headers,
                timeout=12
            )
            if res.status_code != 200:
                print(f"[!] Unsplash API error {res.status_code}")
                continue

            results = res.json().get("results", [])
            if not results:
                print(f"[!] No image found for query: {query}")
                continue

            photo_url = results[0]["urls"]["regular"]
            photo_id = results[0].get("id", "unknown")
            print(f"    -> Found image {photo_id}. Downloading...")

            img_data = session.get(photo_url, timeout=15).content

            for target_dir in dest_dirs:
                file_path = target_dir / filename
                with open(file_path, "wb") as f:
                    f.write(img_data)
                print(f"    + Saved to {file_path.name}")

            downloaded += 1
        except Exception as e:
            print(f"[!] Error downloading {filename}: {e}")

    print(f"\n[+] Successfully downloaded {downloaded}/{len(SEARCH_CATEGORIES)} luxury property images locally!")

if __name__ == "__main__":
    download_images()
