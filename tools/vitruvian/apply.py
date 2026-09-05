#!/usr/bin/env python3
"""Splice a chosen combination of parts into index.html.

    python3 tools/vitruvian/apply.py hd=E hn=C ft=O ch=B
"""
import sys, os, re, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import parts
choice = dict(a.split("=") for a in sys.argv[1:]) or {"hd": "E", "hn": "C", "ft": "O", "ch": "B"}
svg = parts.build()
# keep only the chosen part groups, and turn them into plain groups
def keep(m):
    cls = m.group(1)
    key, var = cls.split("-")
    return m.group(0) if choice.get(key) == var else ""
svg = re.sub(r'<g class="part ([a-z]+-[A-Z])">.*?</g>\n</g>', lambda m: keep(m), svg, flags=re.S)
svg = re.sub(r'<g class="part ([a-z]+-[A-Z])">', lambda m: '<g class="vm-part" data-part="%s">' % m.group(1), svg)
svg = svg.replace('<svg viewBox', '<svg class="rm-fig__svg" viewBox', 1)
idx = os.path.join(HERE, "..", "..", "index.html")
html = open(idx).read()
pat = re.compile(r'<svg class="rm-fig__svg".*?</svg>', re.S)
assert len(pat.findall(html)) == 1
html = pat.sub(lambda m: svg, html)
open(idx, "w").write(html)
print("applied", choice, "svg bytes", len(svg))
