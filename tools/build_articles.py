#!/usr/bin/env python3
"""
NaturalMed — build_articles.py
=================================
Run by the GitHub Action whenever an article is saved in _content/articles/
or an artigo is saved in _content/articles-pt/.
Also safe to run locally: python3 tools/build_articles.py

What it does:
  1. Reads every .md file in _content/articles/      → en/articles/YYYY-MM-slug.html
  2. Reads every .md file in _content/articles-pt/   → pt/artigos/YYYY-MM-slug.html
  3. Rebuilds   en/articles.html  (listing EN)
  4. Rebuilds   pt/artigos.html   (listing PT)
  5. Rebuilds   feed.xml          (RSS feed EN)
  6. Rebuilds   en/seminars.html
  7. Updates    en/index.html, en/about.html, en/conditions.html
  8. Generates  newsletter/ HTML files
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

# ── EN paths ──────────────────────────────────────────────────
CONTENT_DIR_EN   = ROOT / '_content' / 'articles'
ARTICLES_DIR_EN  = ROOT / 'en' / 'articles'
ARTICLES_HTML_EN = ROOT / 'en' / 'articles.html'

# ── PT paths ──────────────────────────────────────────────────
CONTENT_DIR_PT   = ROOT / '_content' / 'articles-pt'
ARTICLES_DIR_PT  = ROOT / 'pt' / 'artigos'
ARTICLES_HTML_PT = ROOT / 'pt' / 'artigos.html'

FEED_XML      = ROOT / 'feed.xml'
BASE_URL      = 'https://www.naturalmed-wellness.com'
SEMINARS_YML  = ROOT / '_content' / 'seminars.yml'
SEMINARS_HTML = ROOT / 'en' / 'seminars.html'
NEWSLETTER_DIR = ROOT / 'newsletter'

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

def absolutise(url):
    """Turn a site-root path into a full URL. Leaves full URLs untouched."""
    if not url:
        return ''
    if url.startswith('http://') or url.startswith('https://'):
        return url
    return BASE_URL + '/' + url.lstrip('/')

def parse_date(date_str):
    """Parse YYYY-MM-DD into a datetime object."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def month_label(dt, lang='en'):
    if lang == 'pt':
        months_pt = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                     'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
        return f'{months_pt[dt.month - 1]} {dt.year}'
    return dt.strftime('%B %Y')

# ── Article HTML template (EN) ────────────────────────────────

ARTICLE_TEMPLATE_EN = '''\
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
    <meta property="og:url" content="{page_url}">
    <meta property="og:site_name" content="NaturalMed">
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
        <img src="../../assets/img/naturalmed-logo.svg" alt="NaturalMed" style="height:40px;width:40px;object-fit:contain" onerror="this.style.display='none';document.getElementById('navMark').style.display='flex'">
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
                <img src="../../assets/img/naturalmed-logo.svg" alt="NaturalMed" style="height:34px;width:34px;object-fit:contain" onerror="this.style.display='none'">
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

# ── Article HTML template (PT) ────────────────────────────────

ARTICLE_TEMPLATE_PT = '''\
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} · NaturalMed Artigos MTC</title>
    <meta name="description" content="{excerpt_escaped}">
    <meta name="author" content="Nuno Pestana">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{excerpt_escaped}">
    <meta property="og:image" content="{cover_abs}">
    <meta property="og:url" content="{page_url}">
    <meta property="og:site_name" content="NaturalMed">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{date_iso}">
    <link rel="icon" type="image/x-icon" href="../../assets/img/favicon.ico">
    <link rel="icon" type="image/png" sizes="32x32" href="../../assets/img/favicon-32.png">
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
    <a href="../../pt/index.html" class="nav-logo">
        <img src="../../assets/img/naturalmed-logo.svg" alt="NaturalMed" style="height:40px;width:40px;object-fit:contain" onerror="this.style.display='none';document.getElementById('navMark').style.display='flex'">
        <div id="navMark" class="nav-mark" style="display:none">N</div>
        <span class="nav-name">NaturalMed</span>
    </a>
    <ul class="nav-links">
        <li><a href="../index.html">Início</a></li>
        <li><a href="../sobre.html">Sobre</a></li>
        <li><a href="../servicos.html">Serviços</a></li>
        <li><a href="../condicoes.html">Condições</a></li>
        <li><a href="../seminarios.html">Seminários</a></li>
        <li><a href="../artigos.html" class="active">Artigos</a></li>
        <li><a href="../contacto.html">Contacto</a></li>
    </ul>
    <div class="nav-right">
        <div class="lang-toggle"><a href="#">EN</a><a href="#" class="active">PT</a></div>
        <button class="btn-nav" onclick="window.location.href='../contacto.html'">Marcar Consulta</button>
    </div>
    <button class="nav-hamburger" id="navHamburger" aria-label="Abrir menu" aria-expanded="false">
        <span></span><span></span><span></span>
    </button>
</nav>

<section class="article-hero">
    <div class="container">
        <p class="article-breadcrumb"><a href="../artigos.html">← Todos os Artigos</a></p>
        <div class="article-category">{category} · {month_label}</div>
        <h1 class="article-title">{title}</h1>
        <div class="article-meta">
            <span>Nuno Pestana, BSc MTC</span>
            <span>·</span>
            <span>{month_label}</span>
            <span>·</span>
            <span>{reading_time} min de leitura</span>
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
        <a href="../artigos.html">← Todos os artigos</a>
        <a href="../contacto.html">Marcar consulta →</a>
    </div>
</main>

<footer>
    <div class="footer-grid">
        <div class="footer-brand">
            <a href="../index.html" class="nav-logo">
                <img src="../../assets/img/naturalmed-logo.svg" alt="NaturalMed" style="height:34px;width:34px;object-fit:contain" onerror="this.style.display='none'">
                <span class="nav-name" style="font-size:19px">NaturalMed</span>
            </a>
            <p>Medicina Tradicional Chinesa · Mid-Wales, Reino Unido.</p>
        </div>
        <div class="footer-col"><h4>Navegar</h4><ul><li><a href="../sobre.html">Sobre o Nuno</a></li><li><a href="../servicos.html">Serviços</a></li><li><a href="../condicoes.html">Condições</a></li><li><a href="../seminarios.html">Seminários</a></li><li><a href="../artigos.html">Artigos</a></li><li><a href="../contacto.html">Contacto</a></li></ul></div>
        <div class="footer-col"><h4>Legal</h4><ul><li><a href="../privacidade.html">Política de Privacidade</a></li><li><a href="#" data-cookie-settings>Definições de Cookies</a></li></ul></div>
        <div class="footer-col"><h4>Contacto</h4><ul><li><a href="tel:+447756339382">+44 7756 339 382</a></li><li><a href="mailto:naturalmed.wellness@gmail.com">naturalmed.wellness@gmail.com</a></li></ul></div>
    </div>
    <div class="footer-bottom"><p>©2026 NaturalMed · Medicina Tradicional Chinesa</p></div>
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
    function close(){{ navEl.classList.remove('nav-open'); btn.setAttribute('aria-expanded','false'); btn.setAttribute('aria-label','Abrir menu'); }}
    function open(){{ if(dd) dd.style.removeProperty('display'); navEl.classList.add('nav-open'); btn.setAttribute('aria-expanded','true'); btn.setAttribute('aria-label','Fechar menu'); }}
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

# ── Card HTML for articles.html listing (EN) ─────────────────

def make_card_en(slug_full, meta, pub_date):
    title      = meta.get('title', 'Untitled')
    category   = meta.get('category', 'TCM')
    excerpt    = meta.get('excerpt', '')
    cover      = meta.get('cover', '')
    ml         = month_label(pub_date, 'en')
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

# ── Card HTML for artigos.html listing (PT) ──────────────────

def make_card_pt(slug_full, meta, pub_date):
    title      = meta.get('title', 'Sem título')
    category   = meta.get('category', 'MTC')
    excerpt    = meta.get('excerpt', '')
    cover      = meta.get('cover', '')
    ml         = month_label(pub_date, 'pt')
    cover_src  = cover if cover else f'../assets/img/articles/{slug_full}-cover.jpg'

    return f'''        <article class="article-card reveal">
            <a href="artigos/{slug_full}.html">
                <img class="article-card-img" src="{cover_src}" alt="{title}"
                     onerror="this.outerHTML='<div class=\\'article-card-img-placeholder\\'></div>'">
            </a>
            <div class="article-card-body">
                <div class="article-tag">{category} · {ml}</div>
                <h2 class="article-card-title">
                    <a href="artigos/{slug_full}.html" style="color:inherit;text-decoration:none">{title}</a>
                </h2>
                <p class="article-card-excerpt">{excerpt}</p>
                <div class="article-card-meta">
                    <span class="article-card-date">{ml}</span>
                    <a href="artigos/{slug_full}.html" class="read-more">Ler artigo →</a>
                </div>
            </div>
        </article>'''

# ── RSS item (EN only) ────────────────────────────────────────

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

# ── Inject helper ─────────────────────────────────────────────

def _inject(html, marker, new_content):
    """Replace content between <!-- CMS:marker --> and <!-- /CMS:marker -->."""
    start = f'<!-- CMS:{marker} -->'
    end   = f'<!-- /CMS:{marker} -->'
    if start not in html or end not in html:
        return html  # marker not found, skip silently
    before = html[:html.index(start) + len(start)]
    after  = html[html.index(end):]
    return before + new_content + after

# ── Core article builder (shared logic) ──────────────────────

def build_articles(content_dir, output_dir, template, lang='en'):
    """
    Build individual article HTML files from .md sources.
    Returns list of (slug_full, meta, pub_date) tuples sorted newest-first.
    """
    import glob as _glob
    output_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(_glob.glob(str(content_dir / '*.md')), reverse=True)
    articles = []
    for md_path in md_files:
        text = Path(md_path).read_text(encoding='utf-8')
        meta, body_md = parse_frontmatter(text)
        if not meta.get('title'):
            print(f'  SKIP (sem título): {md_path}')
            continue
        pub_date  = parse_date(meta.get('date', ''))
        raw_slug  = meta.get('slug') or slugify(meta.get('title', 'artigo'))
        slug_full = pub_date.strftime('%Y-%m') + '-' + raw_slug
        body_html = md_to_html(body_md)
        excerpt   = meta.get('excerpt', '')
        cover     = meta.get('cover', '')
        cover_abs = absolutise(cover) or f'{BASE_URL}/assets/img/articles/{slug_full}-cover.jpg'
        sub_dir   = 'pt/artigos' if lang == 'pt' else 'en/articles'
        page_url  = f'{BASE_URL}/{sub_dir}/{slug_full}.html'
        cover_img = (f'<img class="article-cover" src="{cover}" alt="{meta.get("title","")}">'
                     if cover else '')
        ml = month_label(pub_date, lang)

        html = template.format(
            title           = meta.get('title', ''),
            title_escaped   = meta.get('title', '').replace('"', '&quot;'),
            excerpt         = excerpt,
            excerpt_escaped = excerpt[:150].replace('"', '&quot;'),
            category        = meta.get('category', 'MTC' if lang == 'pt' else 'TCM'),
            month_label     = ml,
            reading_time    = meta.get('reading_time', '8'),
            date_iso        = pub_date.strftime('%Y-%m-%dT00:00:00+00:00'),
            cover_abs       = cover_abs,
            page_url        = page_url,
            cover_img       = cover_img,
            body_html       = body_html,
        )
        out_path = output_dir / f'{slug_full}.html'
        out_path.write_text(html, encoding='utf-8')
        lang_label = 'pt/artigos' if lang == 'pt' else 'en/articles'
        print(f'  ✓ Built: {lang_label}/{slug_full}.html')
        articles.append((slug_full, meta, pub_date))
    return articles

# ── Rebuild listing page ──────────────────────────────────────

def rebuild_listing(listing_path, articles, make_card_fn, lang='en'):
    """Inject article cards grid into the listing page."""
    import re as _re
    if not listing_path.exists():
        print(f'  ⚠ Listing page not found: {listing_path} — skipping')
        return
    listing = listing_path.read_text(encoding='utf-8')
    if articles:
        cards = '\n'.join(make_card_fn(*a) for a in articles)
        grid_block = f'        <div class="articles-grid" id="articlesGrid">\n{cards}\n        </div>'
    else:
        empty_msg = 'Primeiro artigo em breve' if lang == 'pt' else 'First article coming soon'
        grid_block = f'        <div class="articles-grid" id="articlesGrid">\n            <div class="articles-empty" style="grid-column:1/-1"><h3>{empty_msg}</h3></div>\n        </div>'
    listing = _re.sub(
        r'<div class="articles-grid"[^>]*>.*?</div>\s*(?=\s*</div>\s*</section>)',
        grid_block + '\n        ', listing, flags=_re.DOTALL)
    listing_path.write_text(listing, encoding='utf-8')
    lang_label = 'pt/artigos.html' if lang == 'pt' else 'en/articles.html'
    print(f'✓ Rebuilt {lang_label} ({len(articles)} artigo(s))')

# ── Seminars builder ─────────────────────────────────────────

def build_seminars():
    import yaml
    if not SEMINARS_YML.exists():
        print('⚠ _content/seminars.yml not found — skipping seminars build')
        return

    data = yaml.safe_load(SEMINARS_YML.read_text(encoding='utf-8')) or {}
    html = SEMINARS_HTML.read_text(encoding='utf-8')

    subtitle = data.get('subtitle', '')
    if subtitle:
        html = _inject(html, 'seminars_subtitle',
            f'<p class="section-lead reveal d2" style="color:var(--jade-pale);max-width:640px;margin:0.75rem auto 0">{subtitle}</p>')

    intro = data.get('intro', '')
    if intro:
        paras = ''.join(f'<p class="reveal d{i+2}">{p.strip()}</p>\n                '
                        for i, p in enumerate(intro.split('\n\n')) if p.strip())
        html = _inject(html, 'seminars_intro_start', '\n                ' + paras)

    seminars = data.get('seminars', [])
    if seminars:
        STATUS_COLOURS = {
            'Registration Open': 'var(--jade)',
            'Announced':         'var(--gold)',
            'Sold Out':          '#dc2626',
            'Completed':         'var(--text-muted)',
            'TBC':               'var(--text-muted)',
        }
        cards = ''
        for s in seminars:
            status   = s.get('status', 'TBC')
            colour   = STATUS_COLOURS.get(status, 'var(--text-muted)')
            date_str = str(s.get('date', 'To be confirmed'))
            audience = ', '.join(s.get('audience', [])) if isinstance(s.get('audience'), list) else str(s.get('audience', ''))
            cards += f'''
<div style="background:var(--white);border:1px solid var(--cream-dark);border-top:3px solid var(--jade);
            border-radius:var(--r-lg);padding:1.75rem;margin-bottom:1.25rem">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.5rem;margin-bottom:1rem">
        <h3 style="font-family:var(--font-serif);font-size:1.3rem;color:var(--jade-dark);margin:0">{s.get('title','')}</h3>
        <span style="font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:{colour};
                     background:rgba(0,0,0,.04);padding:3px 10px;border-radius:20px">{status}</span>
    </div>
    <p style="font-size:14px;color:var(--text-muted);margin:0 0 .4rem">📅 {date_str} &nbsp;·&nbsp; 📍 {s.get('location','')}</p>
    <p style="font-size:14px;color:var(--text-muted);margin:0 0 .75rem">👥 {audience}</p>
    <p style="font-size:14px;color:var(--text-mid);line-height:1.7;margin:0">{s.get('description','')}</p>
</div>'''

        section = f'''
<section style="background:var(--cream);padding:4rem 2rem">
    <div class="container">
        <div class="eyebrow center reveal" style="color:var(--gold)">Upcoming Events</div>
        <h2 class="section-title reveal d1" style="text-align:center">Seminars &amp; Workshops</h2>
        {cards}
    </div>
</section>
'''
        html = _inject(html, 'seminars_upcoming_start', '\n' + section + '\n')

    SEMINARS_HTML.write_text(html, encoding='utf-8')
    print('✓ Rebuilt en/seminars.html')

# ── Page text builder ─────────────────────────────────────────

PAGES_DIR  = ROOT / '_content' / 'pages'
INDEX_HTML = ROOT / 'en' / 'index.html'
ABOUT_HTML = ROOT / 'en' / 'about.html'

def _md_inline(text):
    import re as _re
    text = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = _re.sub(r'\*(.+?)\*',     r'<em>\1</em>', text)
    return text

def build_page_text():
    import yaml
    home_yml = PAGES_DIR / 'home.yml'
    if home_yml.exists():
        data = yaml.safe_load(home_yml.read_text(encoding='utf-8')) or {}
        html = INDEX_HTML.read_text(encoding='utf-8')
        if data.get('hero_sub'):
            html = _inject(html, 'home_hero_sub',
                f'<p class="hero-sub">{_md_inline(data["hero_sub"])}</p>')
        if data.get('cta_lead'):
            html = _inject(html, 'home_cta_lead',
                f'<p class="cta-lead reveal d2">{_md_inline(data["cta_lead"])}</p>')
        INDEX_HTML.write_text(html, encoding='utf-8')
        print('✓ Updated en/index.html (home text)')

    about_yml = PAGES_DIR / 'about.yml'
    if about_yml.exists():
        data = yaml.safe_load(about_yml.read_text(encoding='utf-8')) or {}
        html = ABOUT_HTML.read_text(encoding='utf-8')
        if data.get('short_bio'):
            html = _inject(html, 'about_short_bio',
                f'<p class="section-lead reveal d2">{_md_inline(data["short_bio"])}</p>')
        if data.get('quote'):
            q = data['quote'].strip('"\'')
            html = _inject(html, 'about_quote',
                f'<blockquote class="bio-quote reveal d2">"{q}"</blockquote>')
        ABOUT_HTML.write_text(html, encoding='utf-8')
        print('✓ Updated en/about.html (bio text)')

    cond_yml = PAGES_DIR / 'conditions.yml'
    if cond_yml.exists():
        data  = yaml.safe_load(cond_yml.read_text(encoding='utf-8')) or {}
        cpath = ROOT / 'en' / 'conditions.html'
        html  = cpath.read_text(encoding='utf-8')
        if data.get('lead'):
            html = _inject(html, 'conditions_lead',
                f'<p class="section-lead reveal d2" style="color:var(--jade-pale);margin:0 auto">{_md_inline(data["lead"])}</p>')
        cpath.write_text(html, encoding='utf-8')
        print('✓ Updated en/conditions.html (lead text)')

# ── Newsletter builder ────────────────────────────────────────

NEWSLETTER_TMPL = '''\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
<style>
  body,table,td,a{{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}}
  body{{margin:0;padding:0;background:#F8F5F0;font-family:'Georgia',serif}}
  .wrapper{{background:#F8F5F0;padding:32px 16px}}
  .email-card{{max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(4,52,44,0.10)}}
  .header{{background:#04342C;padding:28px 40px;text-align:center}}
  .header img{{height:140px;width:auto;max-width:100%;display:block;margin:0 auto}}
  .eyebrow{{background:#085041;padding:10px 40px;text-align:center;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#EF9F27;font-family:Georgia,serif}}
  .body{{padding:40px}}
  .article-label{{font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#BA7517;margin:0 0 12px;font-family:Georgia,serif}}
  .article-title{{font-family:Georgia,serif;font-size:28px;font-weight:normal;color:#04342C;line-height:1.25;margin:0 0 20px}}
  .cover-img{{width:100%;max-height:300px;object-fit:cover;border-radius:8px;display:block;margin-bottom:24px}}
  .excerpt{{font-size:16px;color:#2D4A3E;line-height:1.85;margin:0 0 32px}}
  .cta-wrap{{text-align:center;margin:0 0 40px}}
  .cta-btn{{display:inline-block;background:#BA7517;color:#FAEEDA;text-decoration:none;padding:14px 36px;border-radius:8px;font-family:Georgia,serif;font-size:15px;font-weight:normal;letter-spacing:0.02em}}
  .divider{{border:none;border-top:1px solid #EDE9E2;margin:0 0 32px}}
  .about{{background:#E1F5EE;border-radius:8px;padding:24px;margin-bottom:32px}}
  .about p{{font-size:13px;color:#085041;line-height:1.7;margin:0}}
  .about strong{{color:#04342C}}
  .social{{text-align:center;margin-bottom:24px}}
  .social a{{display:inline-block;margin:0 8px;color:#0F6E56;font-size:13px;text-decoration:none}}
  .footer{{background:#04342C;padding:24px 40px;text-align:center}}
  .footer p{{font-size:11px;color:#9FE1CB;margin:4px 0;line-height:1.7}}
  .footer a{{color:#EF9F27;text-decoration:none}}
  .send-hint{{background:#FFF8E7;border:1px solid #EF9F27;border-radius:8px;padding:14px 20px;margin-bottom:24px;font-family:sans-serif;font-size:13px;color:#7A4F00;text-align:center;line-height:1.6}}
  .send-hint strong{{color:#7A4F00}}
  @media print{{.send-hint{{display:none}}}}
</style>
</head>
<body>
<div class="wrapper">
  <div class="send-hint" id="sendHint">
    <strong>📧 To send:</strong> Open Gmail → Compose → Bcc: Newsletter NaturalMed → Subject: <strong>{subject}</strong><br>
    Then click the button below to hide this bar, select all (Cmd+A), copy (Cmd+C) and paste into Gmail (Cmd+V).
    <br><br>
    <button onclick="document.getElementById('sendHint').style.display='none'" style="background:#BA7517;color:#fff;border:none;border-radius:6px;padding:8px 20px;font-size:13px;cursor:pointer;margin-top:4px">
      ✓ Hide this bar — ready to copy
    </button>
  </div>
  <div class="email-card">
    <div class="header">
      <img src="https://www.naturalmed-wellness.com/assets/img/naturalmed-logo-newsletter.png" alt="NaturalMed" onerror="this.style.display='none'">
    </div>
    <div class="eyebrow">Monthly Article · {month_label}</div>
    <div class="body">
      <p class="article-label">{category}</p>
      <h1 class="article-title">{title}</h1>
      {cover_html}
      <p class="excerpt">{excerpt}</p>
      <div class="cta-wrap">
        <a href="{article_url}" class="cta-btn">Read the full article →</a>
      </div>
      <hr class="divider">
      <div class="about">
        <p><strong>Nuno Pestana, BSc TCM</strong> — Traditional Chinese Medicine practitioner
        at NaturalMed in Newtown, Powys. Trained at Chengdu University of TCM, registered
        member of ATCM UK. <a href="https://www.naturalmed-wellness.com/en/about.html" style="color:#085041">Read more about Nuno →</a></p>
      </div>
      <div class="social">
        <a href="https://www.facebook.com/NaturalMedAcupuncture">Facebook</a>
        <a href="https://www.instagram.com/naturalmed_acupuncture">Instagram</a>
        <a href="https://www.naturalmed-wellness.com/en/contact.html">Book Appointment</a>
      </div>
    </div>
    <div class="footer">
      <p>© 2026 NaturalMed · 30 Shortbridge Street, Newtown, Powys SY16 2LN</p>
      <p><a href="https://www.naturalmed-wellness.com/en/privacy.html">Privacy Policy</a>
         &nbsp;·&nbsp;
         <a href="mailto:naturalmed.wellness@gmail.com">naturalmed.wellness@gmail.com</a></p>
      <p style="margin-top:8px;font-size:10px;color:#5DCAA5">
        You are receiving this because you subscribed at naturalmed-wellness.com.
        To unsubscribe reply with "unsubscribe" in the subject line.</p>
    </div>
  </div>
</div>
</body>
</html>
'''

def build_newsletter(articles_en):
    """Generate one newsletter HTML page per EN article."""
    if not articles_en:
        return
    NEWSLETTER_DIR.mkdir(exist_ok=True)
    built = 0
    index_items = []

    for slug_full, meta, pub_date in articles_en:
        out_path    = NEWSLETTER_DIR / f'{slug_full}.html'
        article_url = f'{BASE_URL}/en/articles/{slug_full}.html'
        cover       = meta.get('cover', '')
        cover_url   = absolutise(cover)
        cover_html  = (f'<img class="cover-img" src="{cover_url}" alt="{meta.get("title","")}">'
                       if cover_url else '')
        subject = f'New article from NaturalMed: {meta.get("title","")}'
        html = NEWSLETTER_TMPL.format(
            subject     = subject,
            title       = meta.get('title', ''),
            category    = meta.get('category', 'Traditional Chinese Medicine'),
            month_label = month_label(pub_date, 'en'),
            excerpt     = meta.get('excerpt', ''),
            article_url = article_url,
            cover_html  = cover_html,
        )
        out_path.write_text(html, encoding='utf-8')
        built += 1
        print(f'  ✓ Newsletter: newsletter/{slug_full}.html')
        index_items.append(
            f'<li><a href="{slug_full}.html">{month_label(pub_date, "en")} — {meta.get("title","")}</a></li>'
        )

    # Rebuild newsletter index
    index_path = NEWSLETTER_DIR / 'index.html'
    if index_path.exists():
        import re as _re
        idx_html   = index_path.read_text(encoding='utf-8')
        items_html = '\n    '.join(index_items)
        idx_html   = _re.sub(
            r'<!-- CMS:newsletter_list_start -->.*?<!-- CMS:newsletter_list_end -->',
            f'<!-- CMS:newsletter_list_start -->\n    {items_html}\n    <!-- CMS:newsletter_list_end -->',
            idx_html, flags=_re.DOTALL)
        index_path.write_text(idx_html, encoding='utf-8')

    print(f'✓ Built {built} newsletter(s) in /newsletter/')

# -- /latest redirect (for Instagram bio) ---------------------

LATEST_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="robots" content="noindex, follow">
<meta http-equiv="refresh" content="0; url={url}">
<link rel="canonical" href="{url}">
<title>NaturalMed - latest article</title>
</head>
<body>
<p>Redirecting to the latest article. <a href="{url}">Continue &rarr;</a></p>
<script>window.location.replace("{url}");</script>
</body>
</html>
"""


def build_latest(articles_en):
    """Write /latest/index.html redirecting to the newest EN article."""
    if not articles_en:
        print('  latest: sem artigos EN - ignorado')
        return
    newest = max(articles_en, key=lambda a: a[2])
    url = f'{BASE_URL}/en/articles/{newest[0]}.html'
    out_dir = ROOT / 'latest'
    out_dir.mkdir(exist_ok=True)
    (out_dir / 'index.html').write_text(LATEST_TMPL.format(url=url), encoding='utf-8')
    print(f'\u2713 Built /latest/ -> {newest[0]}.html')


# ── Main ──────────────────────────────────────────────────────

def main():
    import yaml
    import re as _re

    # ── 1. Build EN articles ──────────────────────────────────
    print('\n── Building EN articles ──')
    ARTICLES_DIR_EN.mkdir(parents=True, exist_ok=True)
    articles_en = build_articles(CONTENT_DIR_EN, ARTICLES_DIR_EN, ARTICLE_TEMPLATE_EN, lang='en')

    # ── 2. Build PT artigos ───────────────────────────────────
    print('\n── Building PT artigos ──')
    ARTICLES_DIR_PT.mkdir(parents=True, exist_ok=True)
    articles_pt = build_articles(CONTENT_DIR_PT, ARTICLES_DIR_PT, ARTICLE_TEMPLATE_PT, lang='pt')

    # ── 3. Rebuild EN listing (en/articles.html) ──────────────
    rebuild_listing(ARTICLES_HTML_EN, articles_en, make_card_en, lang='en')

    # ── 4. Rebuild PT listing (pt/artigos.html) ───────────────
    rebuild_listing(ARTICLES_HTML_PT, articles_pt, make_card_pt, lang='pt')

    # ── 5. Rebuild feed.xml (EN only) ────────────────────────
    if FEED_XML.exists():
        feed  = FEED_XML.read_text(encoding='utf-8')
        items = '\n'.join(make_rss_item(*a) for a in articles_en)
        now_rfc = format_datetime(datetime.now(timezone.utc))
        feed = _re.sub(r'<lastBuildDate>.*?</lastBuildDate>',
                       f'<lastBuildDate>{now_rfc}</lastBuildDate>', feed)
        feed = _re.sub(r'(<!-- Articles are added here.*?-->).*?(</channel>)',
                       rf'\1\n{items}\n  \2', feed, flags=_re.DOTALL)
        FEED_XML.write_text(feed, encoding='utf-8')
        print(f'✓ Rebuilt feed.xml ({len(articles_en)} item(s))')

    # ── 6. Build seminars ─────────────────────────────────────
    build_seminars()

    # ── 7. Build page text ────────────────────────────────────
    build_page_text()

    # ── 8. Build newsletters ──────────────────────────────────
    NEWSLETTER_DIR.mkdir(exist_ok=True)
    build_newsletter(articles_en)

    # -- 9. Build /latest redirect ----------------------------
    build_latest(articles_en)


if __name__ == '__main__':
    main()
