#!/usr/bin/env python3
"""
NaturalMed — build_articles.py
=================================
Run by the GitHub Action whenever an article is saved in _content/articles/.
Also safe to run locally: python3 tools/build_articles.py

What it does:
  1. Reads every .md file in _content/articles/
  2. Generates  en/articles/YYYY-MM-slug.html  for each article
  3. Rebuilds   en/articles.html  (the listing page)
  4. Rebuilds   feed.xml          (the RSS feed)
"""

import os, re, glob, textwrap
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

# Try to import markdown; fall back to basic conversion
try:
    import markdown as md_lib
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

ROOT        = Path(__file__).parent.parent
CONTENT_DIR = ROOT / '_content' / 'articles'
ARTICLES_DIR = ROOT / 'en' / 'articles'
ARTICLES_HTML = ROOT / 'en' / 'articles.html'
FEED_XML     = ROOT / 'feed.xml'
BASE_URL     = 'https://www.naturalmed-wellness.com'

# ── Helpers ──────────────────────────────────────────────────

def parse_frontmatter(text):
    """Parse YAML-like frontmatter between --- markers."""
    if not text.startswith('---'):
        return {}, text
    end = text.find('\n---', 4)
    if end == -1:
        return {}, text
    fm_text = text[4:end]
    body    = text[end+4:].strip()
    meta = {}
    for line in fm_text.splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip().strip('"\'')
    return meta, body

def slugify(text):
    return re.sub(r'[^a-z0-9-]', '', re.sub(r'[\s_]+', '-', text.lower())).strip('-')

def md_to_html(text):
    if HAS_MARKDOWN:
        return md_lib.markdown(text, extensions=['extra', 'nl2br'])
    # Minimal fallback
    html = ''
    for para in re.split(r'\n{2,}', text):
        para = para.strip()
        if not para:
            continue
        para = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', para)
        para = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', para)
        para = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', para)
        html += f'<p>{para}</p>\n'
    return html

def parse_date(date_str):
    """Parse YYYY-MM-DD into a datetime object."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def month_label(dt):
    return dt.strftime('%B %Y')

# ── Article HTML template ─────────────────────────────────────

ARTICLE_TEMPLATE = '''\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} · NaturalMed TCM Articles</title>
    <meta name="description" content="{excerpt_escaped}">
    <meta name="author" content="Nuno Pestana">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{excerpt_escaped}">
    <meta property="og:image" content="{cover_abs}">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{date_iso}">
    <link rel="icon" type="image/x-icon" href="../../assets/img/favicon.ico">
    <link rel="icon" type="image/png" sizes="32x32" href="../../assets/img/favicon-32.png">
    <link rel="alternate" type="application/rss+xml" title="NaturalMed Articles RSS" href="../../feed.xml">
    <link rel="stylesheet" href="../../assets/css/cookie-consent.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../../assets/css/style.css">
    <style>
        .article-hero {{ background: var(--jade-darkest); padding: 110px 0 0; position: relative; }}
        .article-hero::before {{ content:''; position:absolute; inset:0; background: radial-gradient(ellipse 70% 50% at 50% 0%, rgba(15,110,86,.3) 0%, transparent 70%); }}
        .article-breadcrumb {{ font-size:12px; color:var(--jade-pale); margin-bottom:1.5rem; position:relative; }}
        .article-breadcrumb a {{ color:var(--jade-pale); text-decoration:none; }}
        .article-breadcrumb a:hover {{ color:var(--gold-light); }}
        .article-category {{ font-size:11px; letter-spacing:.2em; text-transform:uppercase; color:var(--gold-light); font-weight:500; margin-bottom:1rem; position:relative; }}
        .article-title {{ font-family:var(--font-serif); font-size:clamp(2rem,4.5vw,3rem); font-weight:500; color:var(--white); line-height:1.2; max-width:700px; position:relative; margin-bottom:1.5rem; }}
        .article-meta {{ display:flex; align-items:center; gap:1.5rem; font-size:13px; color:var(--jade-pale); position:relative; padding-bottom:2.5rem; flex-wrap:wrap; }}
        .article-cover {{ width:100%; max-height:480px; object-fit:cover; display:block; }}
        .article-body-wrap {{ max-width:720px; margin:0 auto; padding:3rem 1.5rem 5rem; }}
        .article-lead {{ font-family:var(--font-serif); font-size:1.25rem; color:var(--jade-dark); line-height:1.75; margin-bottom:2rem; font-style:italic; }}
        .article-body h2 {{ font-family:var(--font-serif); font-size:1.65rem; font-weight:500; color:var(--jade-dark); margin:2.5rem 0 .9rem; }}
        .article-body h3 {{ font-family:var(--font-serif); font-size:1.25rem; font-weight:500; color:var(--jade-dark); margin:2rem 0 .7rem; }}
        .article-body p {{ font-size:16px; color:var(--text-mid); line-height:1.85; margin-bottom:1.4rem; }}
        .article-body ul, .article-body ol {{ padding-left:1.5rem; margin-bottom:1.4rem; }}
        .article-body li {{ font-size:16px; color:var(--text-mid); line-height:1.8; margin-bottom:.4rem; }}
        .article-body blockquote {{ border-left:3px solid var(--gold); padding:.8rem 1.25rem; margin:2rem 0; background:var(--gold-mist); border-radius:0 6px 6px 0; }}
        .article-body blockquote p {{ font-family:var(--font-serif); font-size:1.1rem; color:var(--jade-dark); font-style:italic; margin:0; }}
        .article-nav-bottom {{ border-top:1px solid var(--cream-dark); padding-top:2rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem; }}
        .article-nav-bottom a {{ color:var(--jade); font-size:14px; font-weight:500; text-decoration:none; display:inline-flex; align-items:center; gap:6px; }}
        @media (max-width:900px) {{ .nav-links {{ display:none; }} nav.nav-open .nav-links {{ display:flex; }} .nav-hamburger {{ display:flex; }} .nav-right .btn-nav {{ display:none; }} }}
    </style>
</head>
<body>
<nav id="mainNav">
    <a href="../../en/index.html" class="nav-logo">
        <img src="../../assets/img/naturalmed-logo.png" alt="NaturalMed" style="height:40px;width:40px;object-fit:contain" onerror="this.style.display='none';document.getElementById('navMark').style.display='flex'">
        <div id="navMark" class="nav-mark" style="display:none">N</div>
        <span class="nav-name">NaturalMed</span>
    </a>
    <ul class="nav-links">
        <li><a href="../index.html">Home</a></li>
        <li><a href="../about.html">About</a></li>
        <li><a href="../services.html">Services</a></li>
        <li><a href="../conditions.html">Conditions</a></li>
        <li><a href="../seminars.html">Seminars</a></li>
        <li><a href="../articles.html" class="active">Articles</a></li>
        <li><a href="../contact.html">Contact</a></li>
    </ul>
    <div class="nav-right">
        <div class="lang-toggle"><a href="#" class="active">EN</a><a href="#">PT</a></div>
        <button class="btn-nav" onclick="window.location.href='../contact.html'">Book Appointment</button>
    </div>
    <button class="nav-hamburger" id="navHamburger" aria-label="Open menu" aria-expanded="false">
        <span></span><span></span><span></span>
    </button>
</nav>

<section class="article-hero">
    <div class="container">
        <p class="article-breadcrumb"><a href="../articles.html">← All Articles</a></p>
        <div class="article-category">{category} · {month_label}</div>
        <h1 class="article-title">{title}</h1>
        <div class="article-meta">
            <span>Nuno Pestana, BSc TCM</span>
            <span>·</span>
            <span>{month_label}</span>
            <span>·</span>
            <span>{reading_time} min read</span>
        </div>
    </div>
</section>

{cover_img}

<main class="article-body-wrap">
    <p class="article-lead">{excerpt}</p>
    <div class="article-body">
{body_html}
    </div>
    <div class="article-nav-bottom">
        <a href="../articles.html">← Back to all articles</a>
        <a href="../contact.html">Book a consultation →</a>
    </div>
</main>

<footer>
    <div class="footer-grid">
        <div class="footer-brand">
            <a href="../index.html" class="nav-logo">
                <img src="../../assets/img/naturalmed-logo.png" alt="NaturalMed" style="height:34px;width:34px;object-fit:contain" onerror="this.style.display='none'">
                <span class="nav-name" style="font-size:19px">NaturalMed</span>
            </a>
            <p>Traditional Chinese Medicine · Mid-Wales, UK.</p>
        </div>
        <div class="footer-col"><h4>Navigate</h4><ul><li><a href="../about.html">About Nuno</a></li><li><a href="../services.html">Services</a></li><li><a href="../conditions.html">Conditions</a></li><li><a href="../seminars.html">Seminars</a></li><li><a href="../articles.html">Articles</a></li><li><a href="../contact.html">Contact</a></li></ul></div>
        <div class="footer-col"><h4>Legal</h4><ul><li><a href="../privacy.html">Privacy Policy</a></li><li><a href="#" data-cookie-settings>Cookie Settings</a></li></ul></div>
        <div class="footer-col"><h4>Contact</h4><ul><li><a href="tel:+447756339382">+44 7756 339 382</a></li><li><a href="mailto:naturalmed.wellness@gmail.com">naturalmed.wellness@gmail.com</a></li></ul></div>
    </div>
    <div class="footer-bottom"><p>©2026 NaturalMed · Traditional Chinese Medicine</p></div>
</footer>

<script src="../../assets/js/cookie-consent.js"></script>
<script>
const cookieConsent = new CookieConsentManager({{ analyticsScripts: [] }});
const nav = document.getElementById('mainNav');
window.addEventListener('scroll', () => nav.classList.toggle('scrolled', window.scrollY > 60), {{ passive:true }});
(function() {{
    var navEl=document.getElementById('mainNav'), btn=document.getElementById('navHamburger');
    if(!navEl||!btn) return;
    var dd=navEl.querySelector('.nav-links');
    function close(){{ navEl.classList.remove('nav-open'); btn.setAttribute('aria-expanded','false'); btn.setAttribute('aria-label','Open menu'); }}
    function open(){{ if(dd) dd.style.removeProperty('display'); navEl.classList.add('nav-open'); btn.setAttribute('aria-expanded','true'); btn.setAttribute('aria-label','Close menu'); }}
    window.addEventListener('pagehide', function(){{ if(dd) dd.style.display='none'; }});
    window.addEventListener('pageshow', function(){{ close(); if(dd) dd.style.removeProperty('display'); }});
    close();
    btn.addEventListener('click', function(e){{ e.stopPropagation(); navEl.classList.contains('nav-open') ? close() : open(); }});
    if(dd) dd.addEventListener('click', close);
    document.addEventListener('click', function(e){{ if(navEl.classList.contains('nav-open')&&!navEl.contains(e.target)) close(); }});
}})();
</script>
</body>
</html>
'''

# ── Card HTML for articles.html listing ──────────────────────

def make_card(slug_full, meta, pub_date):
    title      = meta.get('title', 'Untitled')
    category   = meta.get('category', 'TCM')
    excerpt    = meta.get('excerpt', '')
    cover      = meta.get('cover', '')
    ml         = month_label(pub_date)
    cover_src  = cover if cover else f'../assets/img/articles/{slug_full}-cover.jpg'

    return f'''        <article class="article-card reveal">
            <a href="articles/{slug_full}.html">
                <img class="article-card-img" src="{cover_src}" alt="{title}"
                     onerror="this.outerHTML='<div class=\\'article-card-img-placeholder\\'></div>'">
            </a>
            <div class="article-card-body">
                <div class="article-tag">{category} · {ml}</div>
                <h2 class="article-card-title">
                    <a href="articles/{slug_full}.html" style="color:inherit;text-decoration:none">{title}</a>
                </h2>
                <p class="article-card-excerpt">{excerpt}</p>
                <div class="article-card-meta">
                    <span class="article-card-date">{ml}</span>
                    <a href="articles/{slug_full}.html" class="read-more">Read article →</a>
                </div>
            </div>
        </article>'''

# ── RSS item ──────────────────────────────────────────────────

def make_rss_item(slug_full, meta, pub_date):
    title   = meta.get('title', 'Untitled')
    excerpt = meta.get('excerpt', '')
    url     = f'{BASE_URL}/en/articles/{slug_full}.html'
    rfc     = format_datetime(pub_date)
    return f'''    <item>
      <title><![CDATA[{title}]]></title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <pubDate>{rfc}</pubDate>
      <dc:creator>Nuno Pestana</dc:creator>
      <category>{meta.get('category', 'TCM')}</category>
      <description><![CDATA[{excerpt}]]></description>
      <content:encoded><![CDATA[<p>{excerpt}</p><p><a href="{url}">Read the full article →</a></p>]]></content:encoded>
    </item>'''

# ── Main ─────────────────────────────────────────────────────

def main():
    md_files = sorted(glob.glob(str(CONTENT_DIR / '*.md')), reverse=True)
    print(f'Found {len(md_files)} article(s) in _content/articles/')

    articles = []
    for md_path in md_files:
        text = Path(md_path).read_text(encoding='utf-8')
        meta, body_md = parse_frontmatter(text)
        if not meta.get('title'):
            print(f'  SKIP (no title): {md_path}')
            continue

        pub_date  = parse_date(meta.get('date', ''))
        raw_slug  = meta.get('slug') or slugify(meta.get('title', 'article'))
        slug_full = pub_date.strftime('%Y-%m') + '-' + raw_slug
        body_html = md_to_html(body_md)
        excerpt   = meta.get('excerpt', '')
        cover     = meta.get('cover', '')
        cover_abs = cover or f'{BASE_URL}/assets/img/articles/{slug_full}-cover.jpg'
        cover_img = (f'<img class="article-cover" src="{cover}" alt="{meta.get("title","")}">'
                     if cover else '')

        # Build article HTML
        html = ARTICLE_TEMPLATE.format(
            title          = meta.get('title', ''),
            title_escaped  = meta.get('title', '').replace('"', '&quot;'),
            excerpt        = excerpt,
            excerpt_escaped= excerpt[:150].replace('"', '&quot;'),
            category       = meta.get('category', 'TCM'),
            month_label    = month_label(pub_date),
            reading_time   = meta.get('reading_time', '8'),
            date_iso       = pub_date.strftime('%Y-%m-%dT00:00:00+00:00'),
            cover_abs      = cover_abs,
            cover_img      = cover_img,
            body_html      = body_html,
        )

        out_path = ARTICLES_DIR / f'{slug_full}.html'
        out_path.write_text(html, encoding='utf-8')
        print(f'  ✓ Built: en/articles/{slug_full}.html')
        articles.append((slug_full, meta, pub_date))

    # ── Rebuild articles.html listing ────────────────────────
    listing = ARTICLES_HTML.read_text(encoding='utf-8')

    if articles:
        cards = '\n'.join(make_card(*a) for a in articles)
        grid_block = f'''        <div class="articles-grid" id="articlesGrid">
{cards}
        </div>'''
    else:
        grid_block = '''        <div class="articles-grid" id="articlesGrid">
            <div class="articles-empty" style="grid-column:1/-1">
                <h3>First article coming soon</h3>
                <p>Subscribe to the newsletter below to be notified when the first article is published.</p>
            </div>
        </div>'''

    # Replace everything between the articles-grid div tags
    listing = re.sub(
        r'<div class="articles-grid"[^>]*>.*?</div>\s*(?=\s*</div>\s*</section>)',
        grid_block + '\n        ',
        listing,
        flags=re.DOTALL
    )
    ARTICLES_HTML.write_text(listing, encoding='utf-8')
    print(f'✓ Rebuilt en/articles.html ({len(articles)} article(s))')

    # ── Rebuild feed.xml ─────────────────────────────────────
    feed = FEED_XML.read_text(encoding='utf-8')
    items = '\n'.join(make_rss_item(*a) for a in articles)
    now_rfc = format_datetime(datetime.now(timezone.utc))
    feed = re.sub(r'<lastBuildDate>.*?</lastBuildDate>',
                  f'<lastBuildDate>{now_rfc}</lastBuildDate>', feed)
    # Replace everything between channel comment markers
    feed = re.sub(
        r'(<!-- Articles are added here.*?-->).*?(</channel>)',
        rf'\1\n{items}\n  \2',
        feed,
        flags=re.DOTALL
    )
    FEED_XML.write_text(feed, encoding='utf-8')
    print(f'✓ Rebuilt feed.xml ({len(articles)} item(s))')

if __name__ == '__main__':
    main()
