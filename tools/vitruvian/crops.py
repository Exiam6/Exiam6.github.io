import re, os
S = os.path.dirname(os.path.abspath(__file__))
svg = open(S + '/master.svg').read()
inner = re.sub(r'^<svg[^>]*>', '', svg, count=1).rsplit('</svg>', 1)[0]
KEYS = ("hd", "hn", "ft", "ch")
css = '.vm-geom{opacity:.55}.l-deep{opacity:.6}.l-shade{opacity:.7}.l-halo{fill:none;stroke:#fff;stroke-width:2.6;stroke-linejoin:round}.part{display:none}'
css += ''.join('.%s-%s{display:var(--%s%s,none)}' % (k, v, k, v) for k in KEYS for v in "OABCDE")
crops = {"hd": ("420 118 160 190", 240), "hn": ("95 118 250 235", 300), "ft": ("150 796 490 134", 560), "ch": ("390 280 220 220", 260)}
cells = []
for key, (vb, w) in crops.items():
    for v in ("OABCDE" if key == "hd" else "OABC"):
        x, y, cw, ch = map(float, vb.split()); h = int(w*ch/cw)
        cells.append('<div style="width:%dpx"><div style="font:13px sans-serif;color:#333">%s-%s</div><svg viewBox="%s" style="--%s%s:inline;width:%dpx;height:%dpx;color:#8a6a4f;display:block;background:#fff"><use href="#fig" width="1000" height="1000"/></svg></div>' % (w, key, v, vb, key, v, w, h))
html = '<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#eee;font-family:sans-serif}.g{display:flex;flex-wrap:wrap;gap:10px;padding:10px;align-items:flex-start}%s</style></head><body><svg width="0" height="0" style="position:absolute"><symbol id="fig" viewBox="0 0 1000 1000">%s</symbol></svg><div class="g">%s</div></body></html>' % (css, inner, "\n".join(cells))
open(S + '/crops.html', 'w').write(html)
print("ok")
