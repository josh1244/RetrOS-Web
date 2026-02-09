#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.INFO)
import fetcher

sites = [
    'https://example.com',
    'https://httpbin.org/html',
]

print("\n=== Testing Fetcher ===\n")
for site in sites:
    try:
        result = fetcher.fetch_page(site)
        if result.get('status') == 'ok':
            print(f"OK: {site}")
            print(f"    Tags: {result['tag_count']}, Divs: {result['div_count']}")
            print(f"    Title: {result['title']}")
            print(f"    Digest: {result['digest'][:16]}...")
        else:
            print(f"ERROR: {site} - {result.get('error')}")
    except Exception as e:
        print(f"EXCEPTION: {site} - {e}")
    print()
