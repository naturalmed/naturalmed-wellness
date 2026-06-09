#!/usr/bin/env python3
"""Adiciona canonical + hreflang a todas as páginas do naturalmed-wellness."""
import os

DOMAIN = "https://www.naturalmed-wellness.com"

PAIRS = {
    "en/index.html":    "pt/index.html",
    "en/about.html":    "pt/sobre.html",
    "en/articles.html": "pt/artigos.html",
    "en/articles/2026-04-acupuncture-and-chronic-pain.html":  "pt/artigos/2026-04-acupunctura-e-dor-cronica.html",
    "en/articles/2026-05-insomnia-and-chinese-medicine.html": "pt/artigos/2026-05-insonia-e-medicina-chinesa.html",
    "en/articles/2026-06-neck-pain-tcm-treatment.html":       "pt/artigos/2026-06-dor-no-pescoco-tratamento-mtc.html",
    "en/conditions.html": "pt/condicoes.html",
    "en/contact.html":    "pt/contacto.html",
    "en/privacy.html":    "pt/privacidade.html",
    "en/seminars.html":   "pt/seminarios.html",
    "en/services.html":   "pt/servicos.html",
}
REVERSE = {v: k for k, v in PAIRS.items()}
ALL = list(PAIRS.keys()) + list(REVERSE.keys())

for fp in ALL:
    if not os.path.exists(fp):
        print(f"SKIP (not found): {fp}")
        continue
    src = open(fp, encoding='utf-8').read()
    if 'rel="canonical"' in src:
        print(f"SKIP (já tem): {fp}")
        continue
    if fp.startswith('en/'):
        en_fp, pt_fp = fp, PAIRS[fp]
    else:
        pt_fp, en_fp = fp, REVERSE[fp]
    block = (
        f'    <link rel="canonical" href="{DOMAIN}/{fp}">\n'
        f'    <link rel="alternate" hreflang="en" href="{DOMAIN}/{en_fp}">\n'
        f'    <link rel="alternate" hreflang="pt" href="{DOMAIN}/{pt_fp}">\n'
        f'    <link rel="alternate" hreflang="x-default" href="{DOMAIN}/{en_fp}">'
    )
    open(fp, 'w', encoding='utf-8').write(src.replace('</head>', block + '\n</head>', 1))
    print(f"OK: {fp}")

# root index.html
root = open('index.html', encoding='utf-8').read()
if 'rel="canonical"' not in root:
    block = (
        f'    <link rel="canonical" href="{DOMAIN}/">\n'
        f'    <link rel="alternate" hreflang="x-default" href="{DOMAIN}/">\n'
        f'    <link rel="alternate" hreflang="en" href="{DOMAIN}/en/index.html">\n'
        f'    <link rel="alternate" hreflang="pt" href="{DOMAIN}/pt/index.html">'
    )
    open('index.html', 'w', encoding='utf-8').write(root.replace('</head>', block + '\n</head>', 1))
    print("OK: index.html (raiz)")
