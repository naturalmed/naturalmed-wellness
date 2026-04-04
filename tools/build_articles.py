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

def _inject(html, marker, new_content):
    """Replace content between <!-- CMS:marker --> and <!-- /CMS:marker -->."""
    start = f'<!-- CMS:{marker} -->'
    end   = f'<!-- /CMS:{marker} -->'
    if start not in html:
        return html  # marker not found, skip silently
    before = html[:html.index(start) + len(start)]
    after  = html[html.index(end):]
    return before + new_content + after


def build_seminars():
    if not SEMINARS_YML.exists():
        print('⚠ _content/seminars.yml not found — skipping seminars build')
        return

    data = _yaml_mod.safe_load(SEMINARS_YML.read_text(encoding='utf-8')) or {}
    html = SEMINARS_HTML.read_text(encoding='utf-8')

    # ── Subtitle ────────────────────────────────────────────────
    subtitle = data.get('subtitle', '')
    if subtitle:
        html = _inject(html, 'seminars_subtitle',
            f'<p class="section-lead reveal d2" style="color:var(--jade-pale);max-width:640px;margin:0.75rem auto 0">{subtitle}</p>')

    # ── Intro paragraphs ────────────────────────────────────────
    intro = data.get('intro', '')
    if intro:
        paras = ''.join(f'<p class="reveal d{i+2}">{p.strip()}</p>\n                ' 
                        for i, p in enumerate(intro.split('\n\n')) if p.strip())
        html = _inject(html, 'seminars_intro_start', '\n                ' + paras)

    # ── Upcoming seminars list ──────────────────────────────────
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
            status      = s.get('status', 'TBC')
            colour      = STATUS_COLOURS.get(status, 'var(--text-muted)')
            date_str    = str(s.get('date', 'To be confirmed'))
            audience    = ', '.join(s.get('audience', [])) if isinstance(s.get('audience'), list) else str(s.get('audience', ''))
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
        html = _inject(html, 'seminars_upcoming_start',
            '\n' + section + '\n')

    SEMINARS_HTML.write_text(html, encoding='utf-8')
    print('✓ Rebuilt en/seminars.html')


# ═══════════════════════════════════════════════════════════════
# PAGE TEXT BUILD
# ═══════════════════════════════════════════════════════════════

PAGES_DIR   = ROOT / '_content' / 'pages'
INDEX_HTML  = ROOT / 'en' / 'index.html'
ABOUT_HTML  = ROOT / 'en' / 'about.html'


def _md_inline(text):
    """Convert **bold** and *italic* in short text snippets."""
    import re as _re
    text = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = _re.sub(r'\*(.+?)\*',     r'<em>\1</em>', text)
    return text


def build_page_text():
    # ── Home ────────────────────────────────────────────────────
    home_yml = PAGES_DIR / 'home.yml'
    if home_yml.exists():
        data = _yaml_mod.safe_load(home_yml.read_text(encoding='utf-8')) or {}
        html = INDEX_HTML.read_text(encoding='utf-8')
        if data.get('hero_sub'):
            html = _inject(html, 'home_hero_sub',
                f'<p class="hero-sub">{_md_inline(data["hero_sub"])}</p>')
        if data.get('cta_lead'):
            html = _inject(html, 'home_cta_lead',
                f'<p class="cta-lead reveal d2">{_md_inline(data["cta_lead"])}</p>')
        INDEX_HTML.write_text(html, encoding='utf-8')
        print('✓ Updated en/index.html (home text)')

    # ── About ───────────────────────────────────────────────────
    about_yml = PAGES_DIR / 'about.yml'
    if about_yml.exists():
        data = _yaml_mod.safe_load(about_yml.read_text(encoding='utf-8')) or {}
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

    # ── Conditions ──────────────────────────────────────────────
    cond_yml = PAGES_DIR / 'conditions.yml'
    if cond_yml.exists():
        data  = _yaml_mod.safe_load(cond_yml.read_text(encoding='utf-8')) or {}
        cpath = ROOT / 'en' / 'conditions.html'
        html  = cpath.read_text(encoding='utf-8')
        if data.get('lead'):
            html = _inject(html, 'conditions_lead',
                f'<p class="section-lead reveal d2" style="color:var(--jade-pale);margin:0 auto">{_md_inline(data["lead"])}</p>')
        cpath.write_text(html, encoding='utf-8')
        print('✓ Updated en/conditions.html (lead text)')


# ── Patch main() to call the new builders ───────────────────────

NEWSLETTER_DIR  = ROOT / 'newsletter'

NEWSLETTER_TMPL = '''\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
<style>
  /* Reset */
  body,table,td,a{{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}}
  body{{margin:0;padding:0;background:#F8F5F0;font-family:'Georgia',serif}}
  
  .wrapper{{background:#F8F5F0;padding:32px 16px}}
  .email-card{{max-width:600px;margin:0 auto;background:#ffffff;
               border-radius:12px;overflow:hidden;
               box-shadow:0 4px 24px rgba(4,52,44,0.10)}}

  /* Header */
  .header{{background:#04342C;padding:28px 40px;text-align:center}}
  .header img{{height:48px;width:48px;border-radius:50%;
               border:2px solid rgba(93,202,165,0.4)}}
  .header-name{{font-family:Georgia,serif;font-size:22px;font-weight:normal;
                color:#E1F5EE;margin:10px 0 2px;letter-spacing:0.03em}}
  .header-tagline{{font-size:12px;color:#9FE1CB;letter-spacing:0.12em;
                   text-transform:uppercase;margin:0}}

  /* Eyebrow */
  .eyebrow{{background:#085041;padding:10px 40px;text-align:center;
            font-size:11px;letter-spacing:0.18em;text-transform:uppercase;
            color:#EF9F27;font-family:Georgia,serif}}

  /* Body */
  .body{{padding:40px}}
  .article-label{{font-size:11px;letter-spacing:0.18em;text-transform:uppercase;
                  color:#BA7517;margin:0 0 12px;font-family:Georgia,serif}}
  .article-title{{font-family:Georgia,serif;font-size:28px;font-weight:normal;
                  color:#04342C;line-height:1.25;margin:0 0 20px}}
  .cover-img{{width:100%;max-height:300px;object-fit:cover;
              border-radius:8px;display:block;margin-bottom:24px}}
  .excerpt{{font-size:16px;color:#2D4A3E;line-height:1.85;margin:0 0 32px}}
  
  /* CTA button */
  .cta-wrap{{text-align:center;margin:0 0 40px}}
  .cta-btn{{display:inline-block;background:#BA7517;color:#FAEEDA;
            text-decoration:none;padding:14px 36px;border-radius:8px;
            font-family:Georgia,serif;font-size:15px;font-weight:normal;
            letter-spacing:0.02em}}

  /* Divider */
  .divider{{border:none;border-top:1px solid #EDE9E2;margin:0 0 32px}}

  /* About */
  .about{{background:#E1F5EE;border-radius:8px;padding:24px;margin-bottom:32px}}
  .about p{{font-size:13px;color:#085041;line-height:1.7;margin:0}}
  .about strong{{color:#04342C}}

  /* Social */
  .social{{text-align:center;margin-bottom:24px}}
  .social a{{display:inline-block;margin:0 8px;color:#0F6E56;
             font-size:13px;text-decoration:none}}

  /* Footer */
  .footer{{background:#04342C;padding:24px 40px;text-align:center}}
  .footer p{{font-size:11px;color:#9FE1CB;margin:4px 0;line-height:1.7}}
  .footer a{{color:#EF9F27;text-decoration:none}}

  /* Print/send hint bar */
  .send-hint{{background:#FFF8E7;border:1px solid #EF9F27;border-radius:8px;
              padding:14px 20px;margin-bottom:24px;font-family:sans-serif;
              font-size:13px;color:#7A4F00;text-align:center;
              line-height:1.6}}
  .send-hint strong{{color:#7A4F00}}

  @media print{{.send-hint{{display:none}}}}
</style>
</head>
<body>
<div class="wrapper">

  <!-- Admin send hint (hidden when printing) -->
  <div class="send-hint">
    <strong>📧 To send:</strong> In Gmail, click <em>Compose</em> → drag this file into the message body → set To: your subscribers group → Subject: <strong>{subject}</strong>
  </div>

  <div class="email-card">

    <!-- Header -->
    <div class="header">
      <img src="https://www.naturalmed-wellness.com/assets/img/naturalmed-logo.png"
           alt="NaturalMed" onerror="this.style.display='none'">
      <p class="header-name">NaturalMed</p>
      <p class="header-tagline">Traditional Chinese Medicine · Mid-Wales, UK</p>
    </div>

    <!-- Eyebrow -->
    <div class="eyebrow">Monthly Article · {month_label}</div>

    <!-- Body -->
    <div class="body">
      <p class="article-label">{category}</p>
      <h1 class="article-title">{title}</h1>

      {cover_html}

      <p class="excerpt">{excerpt}</p>

      <div class="cta-wrap">
        <a href="{article_url}" class="cta-btn">Read the full article →</a>
      </div>

      <hr class="divider">

      <!-- About box -->
      <div class="about">
        <p><strong>Nuno Pestana, BSc TCM</strong> — Traditional Chinese Medicine practitioner
        at NaturalMed in Newtown, Powys. Trained at Chengdu University of TCM, registered
        member of ATCM UK. <a href="https://www.naturalmed-wellness.com/en/about.html"
        style="color:#085041">Read more about Nuno →</a></p>
      </div>

      <!-- Social -->
      <div class="social">
        <a href="https://www.facebook.com/NaturalMedAcupuncture">Facebook</a>
        <a href="https://www.instagram.com/naturalmed_acupuncture">Instagram</a>
        <a href="https://www.naturalmed-wellness.com/en/contact.html">Book Appointment</a>
      </div>
    </div>

    <!-- Footer -->
    <div class="footer">
      <p>© 2026 NaturalMed · 30 Shortbridge Street, Newtown, Powys SY16 2LN</p>
      <p><a href="https://www.naturalmed-wellness.com/en/privacy.html">Privacy Policy</a>
         &nbsp;·&nbsp;
         <a href="mailto:naturalmed.wellness@gmail.com">naturalmed.wellness@gmail.com</a></p>
      <p style="margin-top:8px;font-size:10px;color:#5DCAA5">
        You are receiving this because you subscribed at naturalmed-wellness.com.
        To unsubscribe reply with "unsubscribe" in the subject line.</p>
    </div>

  </div><!-- /.email-card -->
</div><!-- /.wrapper -->
</body>
</html>
'''


def build_newsletter(articles):
    """Generate one newsletter HTML page per article (most recent only if new)."""
    if not articles:
        return

    NEWSLETTER_DIR.mkdir(exist_ok=True)

    # Build a newsletter for each article that doesn't have one yet
    built = 0
    index_items = []

    for slug_full, meta, pub_date in articles:
        out_path = NEWSLETTER_DIR / f'{slug_full}.html'
        article_url = f'{BASE_URL}/en/articles/{slug_full}.html'
        cover = meta.get('cover', '')
        cover_html = (f'<img class="cover-img" src="{cover}" alt="{meta.get("title","")}">'
                      if cover else '')

        subject = f'New article from NaturalMed: {meta.get("title","")}'
        html = NEWSLETTER_TMPL.format(
            subject      = subject,
            title        = meta.get('title', ''),
            category     = meta.get('category', 'Traditional Chinese Medicine'),
            month_label  = month_label(pub_date),
            excerpt      = meta.get('excerpt', ''),
            article_url  = article_url,
            cover_html   = cover_html,
        )
        out_path.write_text(html, encoding='utf-8')
        built += 1
        print(f'  ✓ Newsletter: newsletter/{slug_full}.html')

        # Collect for index
        index_items.append(
            f'<li><a href="{slug_full}.html">{month_label(pub_date)} — {meta.get("title","")}</a></li>'
        )

    # Rebuild newsletter index
    index_path = NEWSLETTER_DIR / 'index.html'
    if index_path.exists():
        idx_html = index_path.read_text(encoding='utf-8')
        items_html = '\n    '.join(index_items)
        idx_html = re.sub(
            r'<!-- CMS:newsletter_list_start -->.*?<!-- CMS:newsletter_list_end -->',
            f'<!-- CMS:newsletter_list_start -->\n    {items_html}\n    <!-- CMS:newsletter_list_end -->',
            idx_html, flags=re.DOTALL
        )
        index_path.write_text(idx_html, encoding='utf-8')

    print(f'✓ Built {built} newsletter(s) in /newsletter/')


# ── Single main entry point ──────────────────────────────────────

def main():
    import yaml  # pyyaml — required for seminars and page text

    # ── 1. Build articles + listing + RSS ──
    md_files = sorted(__import__('glob').glob(str(CONTENT_DIR / '*.md')), reverse=True)
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
        cover_img = (f'<img class="article-cover" src="{cover}" alt="{meta.get("title","")}">' if cover else '')

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

    # ── 2. Rebuild articles.html listing ──
    listing = ARTICLES_HTML.read_text(encoding='utf-8')
    if articles:
        cards = '\n'.join(make_card(*a) for a in articles)
        grid_block = f'''        <div class="articles-grid" id="articlesGrid">\n{cards}\n        </div>'''
    else:
        grid_block = '''        <div class="articles-grid" id="articlesGrid">\n            <div class="articles-empty" style="grid-column:1/-1"><h3>First article coming soon</h3></div>\n        </div>'''
    import re as _re
    listing = _re.sub(
        r'<div class="articles-grid"[^>]*>.*?</div>\s*(?=\s*</div>\s*</section>)',
        grid_block + '\n        ', listing, flags=_re.DOTALL)
    ARTICLES_HTML.write_text(listing, encoding='utf-8')
    print(f'✓ Rebuilt en/articles.html ({len(articles)} article(s))')

    # ── 3. Rebuild feed.xml ──
    from email.utils import format_datetime
    from datetime import timezone
    feed = FEED_XML.read_text(encoding='utf-8')
    items = '\n'.join(make_rss_item(*a) for a in articles)
    now_rfc = format_datetime(datetime.now(timezone.utc))
    feed = _re.sub(r'<lastBuildDate>.*?</lastBuildDate>', f'<lastBuildDate>{now_rfc}</lastBuildDate>', feed)
    feed = _re.sub(r'(<!-- Articles are added here.*?-->).*?(</channel>)', rf'\1\n{items}\n  \2', feed, flags=_re.DOTALL)
    FEED_XML.write_text(feed, encoding='utf-8')
    print(f'✓ Rebuilt feed.xml ({len(articles)} item(s))')

    # ── 4. Build seminars ──
    build_seminars()

    # ── 5. Build page text ──
    build_page_text()

    # ── 6. Build newsletters ──
    NEWSLETTER_DIR.mkdir(exist_ok=True)
    build_newsletter(articles)


if __name__ == '__main__':
    main()
