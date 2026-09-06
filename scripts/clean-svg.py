#!/usr/bin/env python3
"""Prepare an upstream Branding SVG for the web.

The Branding repo ships Inkscape working files: ~14 KB each, most of it editor
metadata. This strips that, drops the millimetre width/height so CSS controls
size, and optionally rewrites one path's fill.

The wordmark rewrite is the interesting part. Upstream ships two horizontal
logos that are byte-identical except the wordmark path's fill (#280b0b for light
backgrounds, #ffffff for dark). Setting that one path to currentColor reproduces
both from a single asset, so the wordmark follows the theme and the tri-colour
mark stays fixed.

    scripts/clean-svg.py in.svg out.svg [--fill-index=N:VALUE] [--replace=OLD:NEW]
"""

import re
import sys
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
DROP_NS = ("sodipodi", "inkscape", "rdf", "cc", "dc", "ns1")


def clean(src: str, dst: str, fills: dict[int, str], swaps: dict[str, str]) -> None:
    ET.register_namespace("", SVG)
    raw = open(src).read()
    for old, new in swaps.items():
        raw = raw.replace(old, new)

    root = ET.fromstring(raw)

    # Drop editor-only elements.
    for parent in root.iter():
        for child in list(parent):
            tag = child.tag
            if tag.startswith("{") and not tag.startswith(f"{{{SVG}}}"):
                parent.remove(child)
            elif tag.split("}")[-1] in ("metadata", "namedview"):
                parent.remove(child)

    # Drop editor-only attributes.
    for el in root.iter():
        for attr in list(el.attrib):
            if attr.startswith("{") and not attr.startswith(f"{{{SVG}}}"):
                del el.attrib[attr]

    # Millimetre width/height fight CSS sizing; the viewBox is what matters.
    root.attrib.pop("width", None)
    root.attrib.pop("height", None)

    # Rewrite the nominated paths' fills.
    paths = [el for el in root.iter() if el.tag == f"{{{SVG}}}path"]
    for idx, value in fills.items():
        style = paths[idx].get("style", "")
        if re.search(r"fill:\s*[^;]+", style):
            style = re.sub(r"fill:\s*[^;]+", f"fill:{value}", style, count=1)
        else:
            style = (style + ";" if style else "") + f"fill:{value}"

        if value == "currentColor":
            # Inkscape leaves `color:#000000` on text-converted-to-path elements.
            # currentColor resolves against the element's OWN color property, so
            # that declaration pins the wordmark to black and it never inherits
            # the theme. Strip it, along with the font-* properties that mean
            # nothing on a path.
            style = re.sub(r"(^|;)\s*color\s*:[^;]*", r"\1", style)
            style = re.sub(r"(^|;)\s*(font|-inkscape-font)[a-z-]*\s*:[^;]*", r"\1", style)
            style = re.sub(r";{2,}", ";", style).strip(";")

        paths[idx].set("style", style)

    # A strict style-src blocks inline style attributes, which would leave every
    # path in the logo unfilled and the mark invisible. SVG presentation
    # attributes (fill=, opacity=) are not subject to style-src, so carry the
    # handful of properties that matter across and drop the editor leftovers.
    KEEP = ("fill", "fill-opacity", "fill-rule", "stroke", "stroke-width",
            "stroke-opacity", "stroke-linejoin", "stroke-linecap", "opacity")
    for el in root.iter():
        style = el.get("style")
        if not style:
            continue
        for decl in style.split(";"):
            if ":" not in decl:
                continue
            prop, _, val = decl.partition(":")
            prop, val = prop.strip(), val.strip()
            if prop in KEEP and val and not el.get(prop):
                el.set(prop, val)
        del el.attrib["style"]

    out = ET.tostring(root, encoding="unicode")
    out = re.sub(r"\n\s*\n", "\n", out).strip() + "\n"
    open(dst, "w").write(out)

    print(f"  {src} -> {dst}   {len(raw)} -> {len(out)} bytes   {len(paths)} paths")


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    fills: dict[int, str] = {}
    swaps: dict[str, str] = {}
    for arg in sys.argv[3:]:
        if arg.startswith("--fill-index="):
            i, v = arg.split("=", 1)[1].split(":", 1)
            fills[int(i)] = v
        elif arg.startswith("--replace="):
            o, n = arg.split("=", 1)[1].split(":", 1)
            swaps[o] = n
    clean(src, dst, fills, swaps)
    return 0


if __name__ == "__main__":
    sys.exit(main())
