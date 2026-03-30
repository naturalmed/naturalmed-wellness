#!/usr/bin/env python3
"""
NaturalMed — add-article.py
============================
Run this script each time you publish a new article.
It updates feed.xml with a new RSS item and prints
the card HTML you paste into en/articles.html.

Usage:
    python3 tools/add-article.py

Then follow the prompts.
"""

import re, sys, textwrap
from datetime import datetime, timezone
from pathlib import Path
from email.utils import format_datetime

ROOT = Path(__file__).parent.parent          # project root
FEED = ROOT / 'feed.xml'
BASE_URL = 'https://www.naturalmed-wellness.com'

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text

def ask(prompt, default=None):
    suffix = f' [{default}]' if default else ''
    val = input(f'{prompt}{suffix}: ').strip()
    return val or default or ''

def main():
    print('\n══════════════════════════════════════')
    print(' NaturalMed — Publish New Article')
    print('══════════════════════════════════════\n')

    # ── Gather metadata ────────────────────────────────────────
    title    = ask('Article title')
    category = ask('Category (e.g. Acupuncture, Herbal Medicine, Qi Theory)')
    excerpt  = ask('Excerpt / lead paragraph (2–3 sentences for RSS and newsletter)')
    date_str = ask('Publish date (YYYY-MM-DD)', datetime.now().strftime('%Y-%m-%d'))
    read_min = ask('Estimated reading time in minutes', '8')

    try:
        pub_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError:
        print('✗ Invalid date format. Use YYYY-MM-DD.')
        sys.exit(1)

    month_label = pub_date.strftime('%B %Y')          # e.g. "April 2026"
    ym          = pub_date.strftime('%Y-%m')           # e.g. "2026-04"
    slug        = f'{ym}-{slugify(title)}'             # e.g. "2026-04-acupuncture-and-pain"
    filename    = f'{slug}.html'
    rel_path    = f'en/articles/{filename}'
    abs_url     = f'{BASE_URL}/{rel_path}'
    cover_url   = f'{BASE_URL}/assets/img/articles/{slug}-cover.jpg'
    rfc_date    = format_datetime(pub_date)

    # ── Build RSS <item> ───────────────────────────────────────
    item = f'''
    <item>
      <title>{title}</title>
      <link>{abs_url}</link>
      <guid isPermaLink="true">{abs_url}</guid>
      <pubDate>{rfc_date}</pubDate>
      <dc:creator>Nuno Pestana</dc:creator>
      <category>{category}</category>
      <description><![CDATA[{excerpt}]]></description>
      <content:encoded><![CDATA[
        <p>{excerpt}</p>
        <p><a href="{abs_url}">Read the full article →</a></p>
      ]]></content:encoded>
    </item>'''

    # ── Update feed.xml ────────────────────────────────────────
    feed_text = FEED.read_text(encoding='utf-8')

    # Update lastBuildDate
    feed_text = re.sub(
        r'<lastBuildDate>.*?</lastBuildDate>',
        f'<lastBuildDate>{rfc_date}</lastBuildDate>',
        feed_text
    )

    # Insert new item before the closing comment / </channel>
    marker = '    <!-- Articles are added here'
    if marker in feed_text:
        feed_text = feed_text.replace(marker, item + '\n' + marker)
    else:
        feed_text = feed_text.replace('  </channel>', item + '\n  </channel>')

    FEED.write_text(feed_text, encoding='utf-8')
    print(f'\n✓ feed.xml updated — item added: {title}')

    # ── Create article file from template ─────────────────────
    template_path = ROOT / 'en' / 'articles' / 'article-template.html'
    article_path  = ROOT / 'en' / 'articles' / filename

    if template_path.exists():
        tpl = template_path.read_text(encoding='utf-8')
        tpl = tpl.replace('ARTICLE TITLE GOES HERE', title)
        tpl = tpl.replace('ARTICLE TITLE', title)
        tpl = tpl.replace('SHORT DESCRIPTION (150 chars max — appears in Google and in the RSS feed excerpt).', excerpt[:150])
        tpl = tpl.replace('SHORT DESCRIPTION', excerpt[:150])
        tpl = tpl.replace('Acupuncture · April 2026', f'{category} · {month_label}')
        tpl = tpl.replace('April 2026', month_label)
        tpl = tpl.replace('8 min read', f'{read_min} min read')
        tpl = tpl.replace('YYYY-MM-DDT00:00:00+00:00', pub_date.strftime('%Y-%m-%dT00:00:00+00:00'))
        tpl = tpl.replace('YYYY-MM-slug', slug)
        tpl = tpl.replace('LEAD PARAGRAPH — Write a compelling one-paragraph introduction that hooks the reader. This will also be used as the excerpt in the RSS feed and in the newsletter email. Keep it to 2–3 sentences.', excerpt)
        article_path.write_text(tpl, encoding='utf-8')
        print(f'✓ Article file created: {rel_path}')
    else:
        print(f'⚠  Template not found at {template_path} — article file not created.')

    # ── Print card HTML ────────────────────────────────────────
    card = textwrap.dedent(f'''
        <!-- Article: {title} ({month_label}) -->
        <article class="article-card reveal">
            <a href="articles/{filename}">
                <img class="article-card-img"
                     src="../assets/img/articles/{slug}-cover.jpg"
                     alt="{title}"
                     onerror="this.outerHTML='<div class=\\'article-card-img-placeholder\\'><svg width=\\'48\\' height=\\'48\\' fill=\\'none\\' stroke=\\'var(--jade)\\' stroke-width=\\'1.5\\' viewBox=\\'0 0 24 24\\'><path d=\\'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5\\'/></svg></div>'">
            </a>
            <div class="article-card-body">
                <div class="article-tag">{category} · {month_label}</div>
                <h2 class="article-card-title">
                    <a href="articles/{filename}" style="color:inherit;text-decoration:none">
                        {title}
                    </a>
                </h2>
                <p class="article-card-excerpt">
                    {excerpt}
                </p>
                <div class="article-card-meta">
                    <span class="article-card-date">
                        <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
                        {month_label}
                    </span>
                    <a href="articles/{filename}" class="read-more">
                        Read article
                        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                    </a>
                </div>
            </div>
        </article>''')

    print('\n══════════════════════════════════════')
    print(' Paste this card into en/articles.html')
    print(' (inside <div class="articles-grid">)')
    print(' REMOVE the empty-state div first.')
    print('══════════════════════════════════════')
    print(card)

    print('\n══════════════════════════════════════')
    print(' Next steps:')
    print(f' 1. Open en/articles/{filename} and write your article')
    print(f' 2. Add a cover image: assets/img/articles/{slug}-cover.jpg')
    print(' 3. Paste the card HTML above into en/articles.html')
    print(' 4. git add . && git commit -m "Article: ' + title + '" && git push')
    print(' 5. Mailchimp RSS campaign will detect the update and send the newsletter')
    print('══════════════════════════════════════\n')

if __name__ == '__main__':
    main()
