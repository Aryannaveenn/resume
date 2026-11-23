#!/usr/bin/env python3
"""Build the section pages, 404 page and sitemap from index.html.

index.html is the single source of truth. Edit content there, then run:

    python3 tools/build_pages.py

This rewrites projects/, experience/, education/, skills/, contact/ (each an
index.html), 404.html and sitemap.xml. Commit the results with your change.
Uses only the Python standard library.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://aryannaveen.com"
OG_IMAGE = f"{SITE}/og-image.png"
GITHUB = "https://github.com/Aryannaveenn"

# Section id -> page settings. Order is the order of the nav and sitemap.
PAGES = {
    "projects": {
        "name": "Projects",
        "title": "Projects | Aryan Naveen, Software Engineer",
        "description": "Client projects by Aryan Naveen: an NFC restaurant time clock, the BizComm loyalty platform with an AI analytics panel, and a cloud consultancy website.",
    },
    "experience": {
        "name": "Experience",
        "title": "Experience | Aryan Naveen, Software Engineer",
        "description": "Aryan Naveen's experience: founder of Done Right Coaching, cloud consultant intern at Cevo on AWS migrations, and customer service at A2B Car Rentals.",
    },
    "education": {
        "name": "Education",
        "title": "Education | Aryan Naveen, Software Engineer",
        "description": "Aryan Naveen studies a Bachelor of Engineering (Software) at UNSW with a Distinction average, after a state rank in HSC Enterprise Computing.",
    },
    "skills": {
        "name": "Skills",
        "title": "Skills | Aryan Naveen, Software Engineer",
        "description": "Aryan Naveen's technical skills: JavaScript, TypeScript, React, Node.js, Express, MongoDB, SQL, AWS, Nginx, GitHub Actions and the Anthropic API.",
    },
    "contact": {
        "name": "Contact",
        "title": "Contact | Aryan Naveen, Software Engineer",
        "description": "Contact Aryan Naveen, a software engineer in Sydney, about internships or client work. Email is the fastest way to get in touch.",
    },
}

# Links shown in the header on section pages (the index keeps its own in-page nav).
HEADER_LINKS = [("/", "Home"), ("/projects/", "Projects"), ("/experience/", "Experience"),
                ("/education/", "Education"), ("/contact/", "Contact")]


def extract(pattern: str, text: str, what: str) -> str:
    m = re.search(pattern, text, re.S)
    if not m:
        raise SystemExit(f"Could not find {what} in index.html")
    return m.group(0)


def head(title: str, description: str, url: str, assets: str, schema: dict, noindex: bool = False) -> str:
    t, d = html.escape(title), html.escape(description)
    robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large"
    canonical = "" if noindex else f'\n  <link rel="canonical" href="{url}">'
    social = "" if noindex else f'''
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Aryan Naveen">
  <meta property="og:locale" content="en_AU">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{t}">
  <meta property="og:description" content="{d}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Aryan Naveen, software engineer in Sydney">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t}">
  <meta name="twitter:description" content="{d}">
  <meta name="twitter:image" content="{OG_IMAGE}">
'''
    ld = json.dumps(schema, indent=2).replace("\n", "\n  ")
    return f'''<!doctype html>
<html lang="en-AU">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{t}</title>
  <meta name="description" content="{d}">
  <meta name="author" content="Aryan Naveen">
  <meta name="robots" content="{robots}">{canonical}
{social}
  <meta name="theme-color" content="#EEF1F4">
  <link rel="icon" href="{assets}favicon.svg" type="image/svg+xml">
  <link rel="icon" href="{assets}favicon-48.png" type="image/png" sizes="48x48">
  <link rel="apple-touch-icon" href="{assets}apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,300..800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{assets}styles.css">

  <script type="application/ld+json">
  {ld}
  </script>
</head>'''


def header(current: str | None) -> str:
    links = []
    for href, label in HEADER_LINKS:
        cur = ' aria-current="page"' if href == current else ""
        links.append(f'        <a href="{href}"{cur}>{label}</a>')
    return (
        '  <header class="topbar" id="top">\n'
        '    <div class="wrap topbar__inner">\n'
        '      <nav class="nav" aria-label="Pages">\n'
        + "\n".join(links) + "\n"
        '      </nav>\n'
        '      <button class="btn btn--quiet print-btn" type="button" data-print>Save as PDF</button>\n'
        '    </div>\n'
        '  </header>'
    )


def crumbs(name: str) -> str:
    return (
        '\n        <nav class="crumbs" aria-label="Breadcrumb">\n'
        '          <ol>\n'
        '            <li><a href="/">Home</a></li>\n'
        f'            <li aria-current="page">{name}</li>\n'
        '          </ol>\n'
        '        </nav>'
    )


def page_schema(slug: str, cfg: dict) -> dict:
    url = f"{SITE}/{slug}/"
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": f"{url}#webpage",
                "url": url,
                "name": cfg["title"],
                "description": cfg["description"],
                "inLanguage": "en-AU",
                "isPartOf": {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": "Aryan Naveen"},
                "about": {"@type": "Person", "@id": f"{SITE}/#person", "name": "Aryan Naveen", "url": f"{SITE}/", "sameAs": [GITHUB]},
                "breadcrumb": {"@id": f"{url}#breadcrumb"},
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{url}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                    {"@type": "ListItem", "position": 2, "name": cfg["name"], "item": url},
                ],
            },
        ],
    }


def as_page_section(section: str, slug: str, name: str) -> str:
    # A standalone page gets one h1, the plain background, and breadcrumbs at the top.
    section = section.replace(" section--alt", "")
    section, n = re.subn(rf'<h2 id="{slug}-title">(.*?)</h2>', rf'<h1 id="{slug}-title">\1</h1>', section, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'Section "{slug}" needs a heading like <h2 id="{slug}-title">')
    return section.replace('<div class="wrap">', '<div class="wrap">' + crumbs(name), 1)


def document(head_html: str, header_html: str, main_html: str, footer_html: str, assets: str) -> str:
    return f'''{head_html}
<body>
  <a class="skip" href="#main">Skip to content</a>

{header_html}

  <main id="main">
    {main_html}
  </main>

  {footer_html}

  <script src="{assets}main.js" defer></script>
</body>
</html>
'''


def main() -> None:
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    footer = extract(r'<footer class="footer">.*?</footer>', index, "the footer")
    if 'href="/projects/"' not in footer:
        raise SystemExit("The footer in index.html should link to the section pages (/projects/ etc.)")

    for slug, cfg in PAGES.items():
        section = extract(rf'<section\b[^>]*\bid="{slug}"[^>]*>.*?</section>', index, f'the "{slug}" section')
        out = document(
            head(cfg["title"], cfg["description"], f"{SITE}/{slug}/", "../", page_schema(slug, cfg)),
            header(f"/{slug}/"),
            as_page_section(section, slug, cfg["name"]),
            footer,
            "../",
        )
        (ROOT / slug).mkdir(exist_ok=True)
        (ROOT / slug / "index.html").write_text(out, encoding="utf-8")
        print(f"wrote {slug}/index.html")

    # 404 page: served for any missing path, so asset links are root-absolute.
    not_found = '''<section class="section" aria-labelledby="nf-title">
      <div class="wrap">
        <header class="section__head">
          <h1 id="nf-title">Page not found</h1>
          <p>This page doesn't exist or has moved. Try one of the pages below, or go back to the home page.</p>
        </header>
        <p><a class="btn btn--solid" href="/">Go to the home page</a></p>
      </div>
    </section>'''
    schema_404 = {"@context": "https://schema.org", "@type": "WebPage", "name": "Page not found"}
    (ROOT / "404.html").write_text(
        document(head("Page not found | Aryan Naveen", "This page doesn't exist.", "", "/", schema_404, noindex=True),
                 header(None), not_found, footer, "/"),
        encoding="utf-8",
    )
    print("wrote 404.html")

    today = dt.date.today().isoformat()
    urls = [f"{SITE}/"] + [f"{SITE}/{slug}/" for slug in PAGES]
    entries = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n  </url>" for u in urls
    )
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n',
        encoding="utf-8",
    )
    print("wrote sitemap.xml")


if __name__ == "__main__":
    main()
