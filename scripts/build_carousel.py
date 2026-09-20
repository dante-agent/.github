#!/usr/bin/env python3
"""docs/*.png -> docs/carousel.svg (auto-advancing, CSS-animated).

GitHub strips <style>/style= from README HTML, but never looks inside an SVG
loaded via <img>, so the animation has to live in the SVG file. That same
sandbox blocks external refs, hence the base64 payloads.

    python3 scripts/build_carousel.py
"""
import base64, io, pathlib
from PIL import Image

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"
SLIDES = ["Dante-thumbnail-ko", "Dante-recommend", "Dante-recommend-2",
          "Dante-explorer", "Dante-onboarding"]
W, H = 1200, 642          # canvas; every slide is padded/scaled to this ratio
SECS = 4                  # per slide
FADE = 0.6                # crossfade
QUALITY = 68


def load(name):
    """Scale to WxH, padding with the image's own corner colour when the
    source aspect ratio differs (the thumbnail is 3:2, the rest are ~1.87:1)."""
    im = Image.open(DOCS / f"{name}.png").convert("RGB")
    if abs(im.width / im.height - W / H) > 0.01:
        target_w = round(im.height * W / H)
        canvas = Image.new("RGB", (target_w, im.height), im.getpixel((0, 0)))
        canvas.paste(im, ((target_w - im.width) // 2, 0))
        im = canvas
    im = im.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=QUALITY, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# One extra slot re-shows slide 1 at the end, so the loop back to the base
# layer is a crossfade instead of a jump cut.
slots = len(SLIDES) + 1
cycle = slots * SECS
fade_pct = FADE / cycle * 100

layers, css = [], []
for i, name in enumerate(SLIDES):
    tag = (f'<image id="s0" href="data:image/jpeg;base64,{load(name)}"'
           f' x="0" y="0" width="{W}" height="{H}"/>')
    layers.append(tag if i == 0 else tag.replace('id="s0" ', f'class="f{i}" '))
layers.append(f'<use class="f{len(SLIDES)}" href="#s0"/>')   # loop-closing copy

for i in range(1, slots):
    start = i * SECS / cycle * 100
    css.append(f".f{i}{{opacity:0;animation:k{i} {cycle}s linear infinite}}"
               f"@keyframes k{i}{{0%,{start - fade_pct:.2f}%{{opacity:0}}"
               f"{start:.2f}%,100%{{opacity:1}}}}")

svg = (f'<svg xmlns="http://www.w3.org/2000/svg"'
       f' viewBox="0 0 {W} {H}" width="{W}" height="{H}"><title>Dante</title>'
       f'<style>{"".join(css)}</style>{"".join(layers)}</svg>')

out = DOCS / "carousel.svg"
out.write_text(svg)
print(f"{out.relative_to(DOCS.parent)}  {len(svg) / 1024:.0f} KB  {cycle}s cycle")
