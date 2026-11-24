#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44: (a) tight 3x crop of the campaign-menu content region for the
CSF description-area display verdict; (b) inspect the installed CSF for
official description labels (used by the positive-control arm).
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C


def main():
    from PIL import Image
    src = L.OUT / "screen_w44_run_S2_campaign_menu.png"
    im = Image.open(src).convert("RGB")
    # The game renders its 800x600-ish frame into the upper-left of the
    # 1707x960 window; the right/bottom remainder is black (verified by the
    # full 2x crop and the all-black right-half crop).
    c = im.crop((0, 0, 860, 620))
    c = c.resize((c.width * 3, c.height * 3), Image.LANCZOS)
    dst = L.OUT / "crop_w44_campaign_menu_content3x.png"
    c.save(dst)
    print("crop saved", dst, c.size, "bytes", dst.stat().st_size)

    # also save a compact non-black bounding box for the record
    g = im.convert("L")
    bbox = g.point(lambda p: 255 if p > 8 else 0).getbbox()
    print("non-black bbox of full screenshot:", bbox)

    # CSF label inspection (read-only, offline)
    v12 = C.V12 / "ra2forge"
    sys.path.insert(0, str(C.V12))
    from ra2forge import csf as csf_mod
    p = C.GAME / "ra2md.csf"
    data = csf_mod.read_csf(p, strict=True)
    labels = [e["name"] for e in data["labels"]] if isinstance(data, dict) and "labels" in data else None
    if labels is None:
        print("csf data keys:", list(data.keys()) if isinstance(data, dict) else type(data))
    else:
        print("csf num_labels:", len(labels))
        for want in ("DESC:ALL1", "DESC:SOV1", "GUI:SinglePlayer", "RA2F:942506FC"):
            hits = [x for x in labels if x.lower() == want.lower()]
            print("  label", want, "present=", bool(hits), "count=", len(hits))
        for want in ("DESC:ALL1", "DESC:SOV1"):
            for e in data["labels"]:
                if e["name"].lower() == want.lower():
                    print("  value", want, "=", repr(e.get("value"))[:300])
                    break


if __name__ == "__main__":
    main()
