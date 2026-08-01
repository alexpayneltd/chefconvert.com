#!/usr/bin/env python3
"""
Generates the cooking-conversion page cluster from densities.json using the
unit-converter-template.html base template.

Produces two conversion types per ingredient (the two most-searched patterns
for this cluster: "X cups Y in grams" and "X tablespoons Y in grams"),
a category hub page, and a sitemap.xml.

Run: python3 generate.py
"""
import json
import os
from datetime import date

TEMPLATE_PATH = "/home/claude/calc-templates/unit-converter-template.html"
DATA_PATH = "/home/claude/cooking-cluster/data/densities.json"
OUT_DIR = "/home/claude/cooking-cluster/output/cooking"
SITE_BASE = "https://chefconvert.com"
TODAY = date.today().isoformat()

CONVERSIONS = [
    # (from_unit, from_symbol, density_field, gauge_max, table_step)
    ("Cups", "cup", "grams_per_cup", 4, 0.25),
    ("Tablespoons", "tbsp", "grams_per_tbsp", 16, 1),
    ("Teaspoons", "tsp", "grams_per_tsp", 12, 1),
]

def load_template():
    with open(TEMPLATE_PATH, "r") as f:
        return f.read()

def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def pick_related(ingredient, all_ingredients, conv_label_slug, n=4):
    """Pick related pages: same category first, then fill from elsewhere."""
    same_cat = [i for i in all_ingredients if i["category"] == ingredient["category"] and i["slug"] != ingredient["slug"]]
    others = [i for i in all_ingredients if i["category"] != ingredient["category"] and i["slug"] != ingredient["slug"]]
    pool = (same_cat + others)[:n]
    related = []
    for r in pool:
        related.append({
            "slug": f"{conv_label_slug}-to-grams-{r['slug']}",
            "label": f"{conv_label_slug.replace('-', ' ').title()} to Grams — {r['name']}"
        })
    return related

def build_page(template, ingredient, conv, all_ingredients):
    from_unit, from_symbol, density_field, gauge_max, table_step = conv
    density = ingredient[density_field]
    conv_slug = from_unit.lower()  # "cups" or "tablespoons"
    page_slug = f"{conv_slug}-to-grams-{ingredient['slug']}"
    related = pick_related(ingredient, all_ingredients, conv_slug, 4)

    html = template
    replacements = {
        "{{FROM_UNIT}}": from_unit,
        "{{FROM_UNIT_SYMBOL}}": from_symbol,
        "{{TO_UNIT}}": "Grams",
        "{{TO_UNIT_SYMBOL}}": "g",
        "{{SUBSTANCE}}": ingredient["name"],
        "{{SUBSTANCE_DENSITY}}": str(density),
        "{{CATEGORY}}": "Cooking Conversions",
        "{{CATEGORY_SLUG}}": "cooking",
        "{{PAGE_SLUG}}": page_slug,
        "{{DEFAULT_VALUE}}": "1",
        "{{GAUGE_MAX}}": str(gauge_max),
        "{{TABLE_STEP}}": str(table_step),
        "{{LAST_UPDATED}}": TODAY,
        "{{MELT_STATE_NOTE}}": ingredient["melt_note"],
        "{{RELATED_1_SLUG}}": related[0]["slug"], "{{RELATED_1_LABEL}}": related[0]["label"],
        "{{RELATED_2_SLUG}}": related[1]["slug"], "{{RELATED_2_LABEL}}": related[1]["label"],
        "{{RELATED_3_SLUG}}": related[2]["slug"], "{{RELATED_3_LABEL}}": related[2]["label"],
        "{{RELATED_4_SLUG}}": related[3]["slug"], "{{RELATED_4_LABEL}}": related[3]["label"],
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    return page_slug, html

def build_hub_page(all_ingredients):
    """Simple category hub linking to every generated page — required for
    crawl discoverability, not just sitemap reliance."""
    rows = []
    for ing in all_ingredients:
        for from_unit, from_symbol, *_ in CONVERSIONS:
            slug = f"{from_unit.lower()}-to-grams-{ing['slug']}"
            rows.append(f'<li><a href="/cooking/{slug}">{from_unit} to Grams — {ing["name"]}</a></li>')
    body = "\n    ".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Cooking Conversions — ChefConvert</title>
<meta name="description" content="Every cup, tablespoon, and gram conversion for common cooking ingredients — butter, sugar, flour, and more.">
</head><body>
<h1>Cooking Conversions</h1>
<p>{len(all_ingredients) * len(CONVERSIONS)} conversion pages across {len(all_ingredients)} ingredients.</p>
<ul>
    {body}
</ul>
</body></html>"""

def build_sitemap(all_slugs):
    entries = "\n".join(
        f"  <url><loc>{SITE_BASE}/cooking/{slug}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq></url>"
        for slug in all_slugs
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>"""

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    template = load_template()
    ingredients = load_data()

    all_slugs = []
    page_count = 0
    for ingredient in ingredients:
        for conv in CONVERSIONS:
            slug, html = build_page(template, ingredient, conv, ingredients)
            with open(os.path.join(OUT_DIR, f"{slug}.html"), "w") as f:
                f.write(html)
            all_slugs.append(slug)
            page_count += 1

    with open(os.path.join(OUT_DIR, "index.html"), "w") as f:
        f.write(build_hub_page(ingredients))
    all_slugs.append("")  # hub page itself, not counted in page_count

    with open(os.path.join(os.path.dirname(OUT_DIR), "sitemap-cooking.xml"), "w") as f:
        f.write(build_sitemap([s for s in all_slugs if s]))

    print(f"Generated {page_count} conversion pages across {len(ingredients)} ingredients.")
    print(f"Output: {OUT_DIR}")
    print(f"Sitemap: {os.path.join(os.path.dirname(OUT_DIR), 'sitemap-cooking.xml')}")

if __name__ == "__main__":
    main()
