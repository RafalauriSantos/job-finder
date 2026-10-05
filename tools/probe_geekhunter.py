#!/usr/bin/env python3
"""Read-only probe for public GeekHunter job pages.

This intentionally does not create a collector or persist jobs. It answers
whether a public page exposes enough fields for a future adapter.
"""
import argparse
import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

import requests


def probe(url):
    response = requests.get(url, headers={'User-Agent': 'WorkHunter public probe/1.0'},
                            timeout=20, allow_redirects=True)
    html = response.text
    title = ''
    match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
    if match:
        title = re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', match.group(1)))).strip()
    descriptions = re.findall(r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']+)', html, re.I)
    json_ld = []
    for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
        try:
            json_ld.append(json.loads(unescape(raw.strip())))
        except json.JSONDecodeError:
            pass
    # Limit signal checks to the page's metadata/body rather than the full
    # application shell, which contains filter labels such as "Remoto".
    visible_text = ' '.join(descriptions) + ' ' + re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.I | re.S)
    return {
        'requested_url': url,
        'final_url': response.url,
        'http_status': response.status_code,
        'content_bytes': len(response.content),
        'title': title,
        'description_meta_available': bool(descriptions),
        'description_meta_chars': max((len(x) for x in descriptions), default=0),
        'json_ld_blocks': len(json_ld),
        'jobposting_json_ld': any((item.get('@type') == 'JobPosting') for item in json_ld if isinstance(item, dict)),
        'signals': {
            'remote': bool(re.search(r'\b(remoto|remote|home office)\b', visible_text, re.I)),
            'salary': bool(re.search(r'R\$|sal[aá]rio|remunera', visible_text, re.I)),
            'requirements': bool(re.search(r'experi[eê]ncia obrigat|requisito|responsabilidade', visible_text, re.I)),
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args(argv)
    print(json.dumps(probe(args.url), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
