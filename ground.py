#!/usr/bin/env python3
"""
ground.py — produce Playwright browser observations for one page.
These observations are the ONLY thing that differs between the static
and grounded judge packets. Outputs a JSON of per-criterion ground facts.

Usage: python3 ground.py pages/clean/base-01/index.html
"""
import sys, json, pathlib
from playwright.sync_api import sync_playwright

path = pathlib.Path(sys.argv[1])
html_uri = path.resolve().as_uri()

MOBILE = {"width": 390, "height": 844}  # iPhone-ish first screen

def observe(page):
    facts = {}

    # C1 mechanical: viewport meta present (DOM-level fact)
    facts["C1_viewport_meta"] = page.locator("meta[name=viewport]").count() > 0

    # C4 hybrid: is testimonial/trust content actually VISIBLE?
    # find likely testimonial/trust blocks, report rendered visibility + box size
    c4 = []
    for sel in ["[class*=testimonial]", "[class*=review]", "[class*=trust]",
                "[class*=press]", "[class*=badge]"]:
        loc = page.locator(sel)
        for i in range(loc.count()):
            el = loc.nth(i)
            box = el.bounding_box()
            c4.append({
                "selector": sel,
                "in_dom": True,
                "visible": el.is_visible(),
                "box_area": (box["width"] * box["height"]) if box else 0,
            })
    facts["C4_trust_content"] = c4 if c4 else "no testimonial/trust block matched"

    # C6 hybrid: is the primary CTA visible in the MOBILE first screen?
    cta = page.locator("a,button").filter(
        has_text=__import__("re").compile(
            r"(get|start|book|visit|shop|sign|buy|try|contact)", 2))
    c6 = []
    for i in range(min(cta.count(), 5)):
        el = cta.nth(i)
        box = el.bounding_box()
        c6.append({
            "text": (el.inner_text() or "").strip()[:40],
            "visible": el.is_visible(),
            "top": box["y"] if box else None,
            "in_first_screen": (box["y"] < MOBILE["height"]) if box else False,
        })
    facts["C6_cta_mobile"] = c6 if c6 else "no CTA-like element matched"

    return facts

with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport=MOBILE)
    pg.goto(html_uri)
    result = observe(pg)
    browser.close()

print(json.dumps(result, indent=2))
