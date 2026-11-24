#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W40 · extra diagnostic variants (D: bad magic; E: override a visible label).

These are ADDITIONAL experiments that separate the two boundaries W29 conflated:
  D = 4-byte bad-magic loose CSF  -> does 0x734799 / 0x6BD85A actually fire?
  E = full clone with ONE official *visible* label's value replaced by our text
      -> does the loose CSF actually change what the UI RENDERS?

They do NOT replace test A/B; they sharpen the boundary verdict.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r02"
W40 = RUN / "W40_csf_live"
OUT = W40 / "out"
V10 = RUN / "W30_csf_capability" / "ra2forge_patched_v10"
sys.path.insert(0, str(V10))
from ra2forge import csf as C  # noqa: E402

OFFICIAL = OUT / "official_ra2md.csf"
MARK = "W40_CSF_LIVE_OK_20261113"
CANDIDATE_LABELS = ["GUI:SinglePlayer", "GUI:ExitGame", "GUI:Options",
                    "GUI:MainMenu", "GUI:Network", "GUI:WWOnline",
                    "GUI:MoviesAndCredits"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    oc = C.read_csf(OFFICIAL, strict=True)
    r = {"official_num_labels": oc.num_labels,
         "candidate_labels": {n: oc.get(n) for n in CANDIDATE_LABELS}}
    chosen = next((n for n in CANDIDATE_LABELS if oc.get(n) is not None), None)
    r["chosen_label"] = chosen
    if chosen is None:
        raise RuntimeError("no known visible label in official CSF")

    # D: deliberately broken magic (W29 §4 experiment A, verbatim: 4 bytes XXXX)
    pD = OUT / "ra2md.csf.badmagic"
    pD.write_bytes(b"XXXX")
    r["variant_D"] = {"path": str(pD), "bytes": 4, "content": b"XXXX".hex(),
                      "sha256": sha(pD), "magic_ok": False}

    # E: full clone, replace one VISIBLE official label's value with our marker
    pE = OUT / "ra2md.csf.override"
    shutil.copyfile(OFFICIAL, pE)
    res = C.append_or_set_label(pE, chosen, MARK, verify=True)
    ec = C.read_csf(pE, strict=True)
    r["variant_E"] = {
        "path": str(pE), "label": chosen, "text": MARK,
        "set_result": res, "size": pE.stat().st_size, "sha256": sha(pE),
        "num_labels": ec.num_labels, "num_strings": ec.num_strings,
        "readback_text_matches": ec.get(chosen) == MARK,
        "official_label_count_unchanged": ec.num_labels == oc.num_labels,
        "only_one_value_changed": [
            (a.name, a.values[0].text) == (b.name, b.values[0].text)
            for a, b in zip(oc.labels, ec.labels)
        ].count(False),
    }
    # byte-compare: exactly one label's payload differs
    r["variant_E"]["overwrite_not_append"] = (ec.num_labels == oc.num_labels == 5211)
    (OUT / "csf_extra_variants.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8")
    print(json.dumps(r, ensure_ascii=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
