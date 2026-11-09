#!/usr/bin/env python3
"""Static site builder for Murfreesboro Duct Cleaning.

Each file in _src/pages/ is an HTML fragment with a small front-matter block:

    ---
    title: Page <title> tag
    description: Meta description
    path: /air-duct-cleaning/
    h1: Visible H1
    ...
    ---
    <section>...</section>

Running `python3 _src/build.py` wraps every fragment in the shared layout
(header, nav, breadcrumbs, footer, JSON-LD) and writes it to the site root
(e.g. /air-duct-cleaning/index.html), then regenerates sitemap.xml.

Front-matter keys
  title, description, path      required
  layout                        home | page | sidebar   (default: sidebar)
  h1, lead, eyebrow             page hero text (not used by layout: home)
  crumbs                        "Services=/services/; Air Duct Cleaning"
  service                       Service name -> adds Service JSON-LD
  area                          City name -> Service JSON-LD areaServed
  article                       yes -> adds Article JSON-LD
  priority, changefreq          sitemap values
  noindex                       yes -> noindex + left out of sitemap

FAQ JSON-LD is generated automatically from any <details><summary> blocks.
"""
import datetime
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "_src" / "pages"
SITE = "https://murfreesboroductcleaning.com"
NAME = "Murfreesboro Duct Cleaning"
PHONE_DISPLAY = "(615) 857-5923"
PHONE_TEL = "+16158575923"
STREET = "925 S Church St"
CITY, REGION, ZIP = "Murfreesboro", "TN", "37130"
TODAY = datetime.date.today().isoformat()

SERVICES = [
    ("Residential Air Duct Cleaning", "/air-duct-cleaning/"),
    ("Commercial Duct Cleaning", "/commercial-duct-cleaning/"),
    ("Post-Construction Duct Cleaning", "/post-construction-duct-cleaning/"),
    ("Duct Sanitizing & Odor Removal", "/duct-sanitizing/"),
    ("Vent Register & Grille Cleaning", "/vent-register-cleaning/"),
    ("Air Duct Inspection", "/duct-inspection/"),
]
AREAS = [
    ("Murfreesboro", "/"),
    ("Smyrna", "/service-areas/smyrna-tn/"),
    ("La Vergne", "/service-areas/la-vergne-tn/"),
    ("Blackman", "/service-areas/blackman-tn/"),
    ("Christiana", "/service-areas/christiana-tn/"),
    ("Rockvale", "/service-areas/rockvale-tn/"),
    ("Lascassas", "/service-areas/lascassas-tn/"),
    ("Eagleville", "/service-areas/eagleville-tn/"),
    ("Walter Hill", "/service-areas/walter-hill-tn/"),
    ("Readyville", "/service-areas/readyville-tn/"),
]
GUIDES = [
    ("Air Duct Cleaning Cost in Murfreesboro", "/air-duct-cleaning-cost/"),
    ("How Often Should You Clean Your Air Ducts?", "/resources/how-often-clean-air-ducts/"),
    ("8 Signs Your Air Ducts Need Cleaning", "/resources/signs-air-ducts-need-cleaning/"),
    ("How to Spot a $49 Duct Cleaning Scam", "/resources/duct-cleaning-scams/"),
]

LOGO_SVG = """<svg class="logo-mark" viewBox="0 0 48 48" aria-hidden="true">
          <circle cx="24" cy="24" r="22" fill="{bg}"/>
          <path d="M12 20c4-4 8-4 12 0s8 4 12 0M12 28c4-4 8-4 12 0s8 4 12 0" stroke="{fg}" stroke-width="3.5" fill="none" stroke-linecap="round"/>
        </svg>"""


def parse(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"{path}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if line.strip():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    for key in ("title", "description", "path"):
        if key not in meta:
            raise SystemExit(f"{path}: missing '{key}'")
    return meta, m.group(2)


def esc(s):
    return html.escape(s, quote=True)


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def crumbs_of(meta):
    items = [("Home", "/")]
    raw = meta.get("crumbs", "")
    for part in [p.strip() for p in raw.split(";") if p.strip()]:
        name, _, href = part.partition("=")
        items.append((name.strip(), href.strip() or meta["path"]))
    return items


def business():
    return {
        "@type": "LocalBusiness",
        "@id": f"{SITE}/#business",
        "name": NAME,
        "url": f"{SITE}/",
        "telephone": "+1-615-857-5923",
        "image": f"{SITE}/og-image.png",
        "logo": f"{SITE}/favicon.svg",
        "priceRange": "$$",
        "description": "Air duct cleaning for homes and businesses in Murfreesboro and Rutherford County, TN.",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": STREET,
            "addressLocality": CITY,
            "addressRegion": REGION,
            "postalCode": ZIP,
            "addressCountry": "US",
        },
        "hasMap": "https://www.google.com/maps?q=925+S+Church+St,+Murfreesboro,+TN+37130",
        "areaServed": [{"@type": "City", "name": f"{a}, TN"} for a, _ in AREAS]
        + [{"@type": "AdministrativeArea", "name": "Rutherford County, TN"}],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Air Duct Cleaning Services",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "url": SITE + h}}
                for n, h in SERVICES
            ],
        },
    }


def jsonld(meta, body):
    url = SITE + meta["path"]
    graph = [
        business(),
        {
            "@type": "WebSite",
            "@id": f"{SITE}/#website",
            "url": f"{SITE}/",
            "name": NAME,
            "publisher": {"@id": f"{SITE}/#business"},
        },
        {
            "@type": "WebPage",
            "@id": f"{url}#webpage",
            "url": url,
            "name": meta["title"],
            "description": meta["description"],
            "isPartOf": {"@id": f"{SITE}/#website"},
            "about": {"@id": f"{SITE}/#business"},
            "dateModified": TODAY,
        },
    ]
    crumbs = crumbs_of(meta)
    if len(crumbs) > 1:
        graph.append({
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + h}
                for i, (n, h) in enumerate(crumbs)
            ],
        })
    if meta.get("service"):
        area = meta.get("area")
        graph.append({
            "@type": "Service",
            "name": meta["service"],
            "serviceType": "Air duct cleaning",
            "url": url,
            "description": meta["description"],
            "provider": {"@id": f"{SITE}/#business"},
            "areaServed": {"@type": "City", "name": f"{area}, TN"} if area
            else [{"@type": "City", "name": f"{a}, TN"} for a, _ in AREAS],
        })
    if meta.get("article") == "yes":
        graph.append({
            "@type": "Article",
            "headline": meta.get("h1", meta["title"]),
            "description": meta["description"],
            "mainEntityOfPage": {"@id": f"{url}#webpage"},
            "author": {"@id": f"{SITE}/#business"},
            "publisher": {"@id": f"{SITE}/#business"},
            "image": f"{SITE}/og-image.png",
            "datePublished": meta.get("published", TODAY),
            "dateModified": TODAY,
        })
    faqs = re.findall(r"<details>\s*<summary>(.*?)</summary>(.*?)</details>", body, re.S)
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": strip_tags(q),
                    "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)},
                }
                for q, a in faqs
            ],
        })
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2)


def nav(current):
    def link(name, href):
        cur = ' aria-current="page"' if href == current else ""
        return f'<a href="{href}"{cur}>{esc(name)}</a>'

    svc = "\n".join(f"              {link(n, h)}" for n, h in SERVICES)
    areas = "\n".join(f"              {link(n + ', TN', h)}" for n, h in AREAS[1:])
    return f"""<nav class="nav" id="site-nav" aria-label="Main">
        <div class="nav-item has-menu">
          <a href="/services/" class="nav-top">Services</a>
          <div class="submenu">
{svc}
            <a href="/services/" class="submenu-all">All services →</a>
          </div>
        </div>
        <div class="nav-item has-menu">
          <a href="/service-areas/" class="nav-top">Service Areas</a>
          <div class="submenu">
{areas}
            <a href="/service-areas/" class="submenu-all">All service areas →</a>
          </div>
        </div>
        <div class="nav-item">{link("Pricing", "/air-duct-cleaning-cost/")}</div>
        <div class="nav-item">{link("Resources", "/resources/")}</div>
        <div class="nav-item">{link("About", "/about/")}</div>
        <div class="nav-item">{link("Contact", "/contact/")}</div>
        <a href="tel:{PHONE_TEL}" class="btn btn-orange btn-sm">Call Now</a>
      </nav>"""


def breadcrumbs(meta):
    items = crumbs_of(meta)
    if len(items) < 2:
        return ""
    parts = []
    for i, (n, h) in enumerate(items):
        if i == len(items) - 1:
            parts.append(f'<li aria-current="page">{esc(n)}</li>')
        else:
            parts.append(f'<li><a href="{h}">{esc(n)}</a></li>')
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>{"".join(parts)}</ol></nav>'


def page_hero(meta):
    eyebrow = meta.get("eyebrow", "Murfreesboro Duct Cleaning")
    return f"""<section class="page-hero">
      <div class="container">
        {breadcrumbs(meta)}
        <p class="eyebrow">{esc(eyebrow)}</p>
        <h1>{meta.get("h1", meta["title"])}</h1>
        <p class="lead">{meta.get("lead", "")}</p>
        <div class="hero-ctas">
          <a href="tel:{PHONE_TEL}" class="btn btn-orange btn-lg">📞 Call {PHONE_DISPLAY}</a>
          <a href="/contact/#quote" class="btn btn-outline btn-lg">Get a Free Quote</a>
        </div>
      </div>
    </section>"""


def sidebar(current):
    def li(n, h):
        cur = ' aria-current="page"' if h == current else ""
        return f'<li><a href="{h}"{cur}>{esc(n)}</a></li>'

    svc = "\n".join(li(n, h) for n, h in SERVICES)
    guides = "\n".join(li(n, h) for n, h in GUIDES)
    return f"""<aside class="sidebar">
          <div class="side-card side-cta">
            <h2>Free, Upfront Quote</h2>
            <p>Talk to a real person in Murfreesboro. We'll give you a price before any work starts.</p>
            <a href="tel:{PHONE_TEL}" class="btn btn-orange btn-block">📞 {PHONE_DISPLAY}</a>
            <a href="/contact/#quote" class="btn btn-purple-outline btn-block">Request Online</a>
          </div>
          <div class="side-card">
            <h2>Our Services</h2>
            <ul class="side-links">{svc}</ul>
          </div>
          <div class="side-card">
            <h2>Helpful Guides</h2>
            <ul class="side-links">{guides}</ul>
          </div>
        </aside>"""


def cta_band():
    return f"""<section class="cta-band">
      <div class="container cta-inner">
        <div>
          <h2>Ready for Cleaner Air in Your Home?</h2>
          <p>Call Murfreesboro Duct Cleaning today for a free, no-obligation quote.</p>
        </div>
        <a href="tel:{PHONE_TEL}" class="btn btn-white btn-lg">📞 {PHONE_DISPLAY}</a>
      </div>
    </section>"""


def footer():
    svc = "\n".join(f'          <li><a href="{h}">{esc(n)}</a></li>' for n, h in SERVICES)
    areas = "\n".join(f'          <li><a href="{h}">{esc(n)}, TN</a></li>' for n, h in AREAS)
    guides = "\n".join(f'          <li><a href="{h}">{esc(n)}</a></li>' for n, h in GUIDES)
    return f"""<footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <a href="/" class="logo logo-footer">
          {LOGO_SVG.format(bg="#ff7a1a", fg="#fff")}
          <span class="logo-text">Murfreesboro<strong>Duct Cleaning</strong></span>
        </a>
        <p>Professional air duct cleaning for homes and businesses in Murfreesboro and Rutherford County, TN.</p>
        <address>
          {NAME}<br>
          {STREET}<br>
          {CITY}, {REGION} {ZIP}<br>
          <a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a>
        </address>
      </div>
      <div>
        <h2 class="footer-h">Services</h2>
        <ul>
{svc}
        </ul>
      </div>
      <div>
        <h2 class="footer-h">Service Areas</h2>
        <ul class="footer-cols">
{areas}
        </ul>
      </div>
      <div>
        <h2 class="footer-h">Resources</h2>
        <ul>
{guides}
          <li><a href="/faq/">FAQ</a></li>
          <li><a href="/about/">About Us</a></li>
          <li><a href="/contact/">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="container footer-bottom">
      <p>&copy; <span id="year">2026</span> {NAME}. All rights reserved. · <a href="/sitemap.xml">Sitemap</a></p>
    </div>
  </footer>"""


def render(meta, body):
    path = meta["path"]
    layout = meta.get("layout", "sidebar")
    url = SITE + path
    robots = "noindex, follow" if meta.get("noindex") == "yes" else "index, follow, max-image-preview:large"

    if layout == "home":
        main = body
    elif layout == "page":
        main = f"""{page_hero(meta)}
    {body}
    {cta_band()}"""
    else:
        main = f"""{page_hero(meta)}
    <div class="section">
      <div class="container with-sidebar">
        <article class="prose">
{body}
        </article>
        {sidebar(path)}
      </div>
    </div>
    {cta_band()}"""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(meta["title"])}</title>
  <meta name="description" content="{esc(meta["description"])}">
  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{url}">
  <meta property="og:site_name" content="{NAME}">
  <meta property="og:title" content="{esc(meta.get("og_title", meta["title"]))}">
  <meta property="og:description" content="{esc(meta["description"])}">
  <meta property="og:type" content="{"article" if meta.get("article") == "yes" else "website"}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{SITE}/og-image.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="geo.region" content="US-TN">
  <meta name="geo.placename" content="Murfreesboro">
  <meta name="theme-color" content="#5b2a86">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/styles.css">
  <script type="application/ld+json">
{jsonld(meta, body)}
  </script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <div class="topbar">
    <div class="container topbar-inner">
      <span>📍 {STREET}, {CITY}, {REGION} {ZIP}</span>
      <a href="tel:{PHONE_TEL}">📞 {PHONE_DISPLAY}</a>
    </div>
  </div>

  <header class="site-header">
    <div class="container header-inner">
      <a href="/" class="logo" aria-label="{NAME} home">
        {LOGO_SVG.format(bg="#5b2a86", fg="#ff7a1a")}
        <span class="logo-text">Murfreesboro<strong>Duct Cleaning</strong></span>
      </a>
      <button class="nav-toggle" aria-label="Open menu" aria-controls="site-nav" aria-expanded="false">☰</button>
      {nav(path)}
    </div>
  </header>

  <main id="main">
    {main}
  </main>

  {footer()}

  <a href="tel:{PHONE_TEL}" class="mobile-call">📞 Call Now: {PHONE_DISPLAY}</a>

  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    const toggle = document.querySelector('.nav-toggle');
    const nav = document.querySelector('.nav');
    toggle.addEventListener('click', () => {{
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open);
    }});
  </script>
</body>
</html>
"""


def out_file(path):
    if path.endswith(".html"):
        return ROOT / path.lstrip("/")
    return ROOT / path.strip("/") / "index.html"


def relativize(page_html, path):
    """Rewrite root-absolute href/src ("/about/") to paths relative to the page,
    so the site works from any folder or subpath (file://, GitHub Pages
    project sites, previews), not only at a domain root. Absolute URLs used for
    canonical/OG/schema are untouched. The 404 page can be served at any URL,
    so it gets absolute site URLs instead."""
    if path.endswith(".html"):
        if path == "/404.html":
            return re.sub(r'((?:href|src)=")/(?!/)', r"\1" + SITE + "/", page_html)
        depth = path.count("/") - 1
    else:
        depth = len([seg for seg in path.split("/") if seg])
    prefix = "../" * depth

    def fix(m):
        target = m.group(2)[1:]
        if target.endswith("/") or target == "":
            target += "index.html"
        return f'{m.group(1)}{prefix}{target}'

    return re.sub(r'((?:href|src)=")(/(?!/)[^"#]*)', fix, page_html)


def main():
    entries = []
    for src in sorted(PAGES.rglob("*.html")):
        meta, body = parse(src)
        dest = out_file(meta["path"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(relativize(render(meta, body), meta["path"]))
        print(f"built {dest.relative_to(ROOT)}")
        if meta.get("noindex") != "yes":
            entries.append((meta["path"], meta.get("priority", "0.6"), meta.get("changefreq", "monthly")))

    entries.sort(key=lambda e: (-float(e[1]), e[0]))
    urls = "\n".join(
        f"  <url>\n    <loc>{SITE}{p}</loc>\n    <lastmod>{TODAY}</lastmod>\n"
        f"    <changefreq>{c}</changefreq>\n    <priority>{pr}</priority>\n  </url>"
        for p, pr, c in entries
    )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n"
    )
    print(f"built sitemap.xml ({len(entries)} URLs)")


if __name__ == "__main__":
    main()
