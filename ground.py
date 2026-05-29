#!/usr/bin/env python3
"""
ground.py — Playwright browser observations for one page.
Day 2 v2: occlusion detection samples multiple points on each CTA's bounding
box (top edge, bottom edge, corners) so that PARTIAL occlusion (e.g. sticky
header covering only the top half of a button) is correctly detected.
"""
import sys, json, pathlib
from playwright.sync_api import sync_playwright

path = pathlib.Path(sys.argv[1])
html_uri = path.resolve().as_uri()
MOBILE = {"width": 390, "height": 844}

ANCESTOR_CLIP_JS = """
(el) => {
  const reasons = [];
  let cur = el;
  while (cur && cur !== document.body) {
    const cs = getComputedStyle(cur);
    const rect = cur.getBoundingClientRect();
    if (cs.display === 'none') reasons.push('ancestor display:none');
    if (cs.visibility === 'hidden') reasons.push('ancestor visibility:hidden');
    if (parseFloat(cs.opacity) === 0) reasons.push('ancestor opacity:0');
    if (cs.transform && cs.transform.includes('matrix(0')) reasons.push('ancestor transform:scale(0)');
    if (cs.overflow !== 'visible' && (cur.clientHeight === 0 || cur.clientWidth === 0))
      reasons.push('ancestor 0-size with overflow:hidden');
    if (cs.overflow === 'hidden' && rect.height > 0) {
      const childRect = el.getBoundingClientRect();
      const ancRect = cur.getBoundingClientRect();
      if (childRect.bottom > ancRect.bottom + 1 || childRect.top < ancRect.top - 1)
        reasons.push('child clipped by ancestor overflow:hidden');
    }
    cur = cur.parentElement;
  }
  return reasons;
}
"""

def observe(page):
    facts = {}
    facts["C1_viewport_meta"] = page.locator("meta[name=viewport]").count() > 0

    c4 = []
    for sel in ["[class*=testimonial]", "[class*=review]", "[class*=trust]",
                "[class*=press]", "[class*=badge]"]:
        loc = page.locator(sel)
        for i in range(loc.count()):
            el = loc.nth(i)
            box = el.bounding_box()
            handle = el.element_handle()
            clip_reasons = page.evaluate(ANCESTOR_CLIP_JS, handle) if handle else []
            self_visible = el.is_visible()
            user_visible = self_visible and not clip_reasons
            contrast_info = page.evaluate("""(el) => {
                const cs = getComputedStyle(el);
                return {color: cs.color, background: cs.backgroundColor};
            }""", handle) if handle else {}
            c4.append({
                "selector": sel, "in_dom": True,
                "selector_visible": self_visible, "user_visible": user_visible,
                "clip_reasons": clip_reasons,
                "box_area": (box["width"] * box["height"]) if box else 0,
                "style": contrast_info,
            })
    facts["C4_trust_content"] = c4 if c4 else "no testimonial/trust block matched"

    c5 = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('[onclick]').forEach(el => {
            const code = el.getAttribute('onclick') || '';
            const looks_dead = !/(display|hidden|toggle|classList|style\\.|innerHTML)/i.test(code);
            if (looks_dead) out.push({tag: el.tagName, onclick: code.slice(0, 80)});
        });
        const clipped = [];
        document.querySelectorAll('*').forEach(el => {
            const cs = getComputedStyle(el);
            if (cs.maxHeight && cs.maxHeight !== 'none' &&
                cs.overflow === 'hidden' && el.scrollHeight > el.clientHeight + 4) {
                clipped.push({tag: el.tagName, class: el.className,
                              scrollHeight: el.scrollHeight, clientHeight: el.clientHeight,
                              hidden_content_px: el.scrollHeight - el.clientHeight});
            }
        });
        const empty = [];
        document.querySelectorAll('[class*=credential],[class*=field],[class*=item]').forEach(el => {
            if (el.children.length === 0 && !el.textContent.trim()) {
                empty.push({tag: el.tagName, class: el.className});
            }
        });
        return {dead_onclicks: out, max_height_clipped: clipped, empty_structural_divs: empty};
    }""")
    facts["C5_affordance_and_claims"] = c5

    # C6: now with multi-point occlusion sampling (detects partial occlusion).
    c6 = page.evaluate(f"""() => {{
        const ctas = [...document.querySelectorAll('a,button')]
            .filter(el => /get|start|book|visit|shop|sign|buy|try|contact/i.test(el.innerText || ''));
        return ctas.slice(0, 5).map(el => {{
            const r = el.getBoundingClientRect();
            // Sample 9 points across the bounding box: 4 corners, 4 edge midpoints, 1 center.
            const inset = 2;  // pull 2px inside the edges to avoid floating-point misses
            const pts = [
                [r.left + inset,         r.top + inset],            // top-left
                [r.left + r.width/2,     r.top + inset],            // top-center
                [r.right - inset,        r.top + inset],            // top-right
                [r.left + inset,         r.top + r.height/2],       // mid-left
                [r.left + r.width/2,     r.top + r.height/2],       // center
                [r.right - inset,        r.top + r.height/2],       // mid-right
                [r.left + inset,         r.bottom - inset],         // bottom-left
                [r.left + r.width/2,     r.bottom - inset],         // bottom-center
                [r.right - inset,        r.bottom - inset],         // bottom-right
            ];
            const occluders = new Set();
            let occluded_points = 0;
            for (const [x, y] of pts) {{
                const top_el = document.elementFromPoint(x, y);
                if (top_el && top_el !== el && !el.contains(top_el)) {{
                    occluded_points++;
                    occluders.add(top_el.tagName + '.' + (top_el.className || '').toString().slice(0, 30));
                }}
            }}
            return {{
                text: (el.innerText || '').trim().slice(0, 40),
                top: r.top,
                left: r.left,
                right: r.right,
                in_first_screen: r.top >= 0 && r.top < {MOBILE['height']},
                horizontally_off_viewport: r.left >= {MOBILE['width']} || r.right <= 0,
                occluded_points: occluded_points,
                fully_occluded: occluded_points === 9,
                partially_occluded: occluded_points > 0 && occluded_points < 9,
                occluders: [...occluders],
            }};
        }});
    }}""")
    facts["C6_cta_mobile"] = c6 if c6 else "no CTA-like element matched"

    broken_imgs = page.evaluate("""() => {
        return [...document.querySelectorAll('img')].filter(img => {
            return img.complete && img.naturalWidth === 0;
        }).map(img => ({src: img.src, alt: img.alt}));
    }""")
    facts["broken_images"] = broken_imgs

    return facts

with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport=MOBILE)
    pg.goto(html_uri)
    pg.wait_for_load_state("networkidle", timeout=5000)
    result = observe(pg)
    browser.close()

print(json.dumps(result, indent=2))
