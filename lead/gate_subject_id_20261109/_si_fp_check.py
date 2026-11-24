# -*- coding: utf-8 -*-
"""_si_fp_check.py — 主体识别诊断：复核编排方 8 件指纹 + ORPHAN 句实证（只读）。"""
import hashlib
import time
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge")
OUTD = ROOT / "lead/gate_subject_id_20261109"
FP = {
    "lead/counterpart_fix_20261109/COUNTERPART_FIX.md": ("e291f5a8f8b2c303b31e7f06989233e122460d9838817271fa425cae066ff416", 32830),
    "lead/counterpart_fix_20261109/_cf_counterpart_vs_tighten_20261109.md": ("9878bb7ec170599dd8d74eacfa0a7be0806294d91d8be994a456ad6ed864ddb4", 32840),
    "lead/strict_exposure_20261109/STRICT_EXPOSURE.md": ("3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8", 23798),
    "lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md": ("f320a80110806e6b57281988085d40776b43e719123db29cdb6564fe68c6c545", 24897),
    "lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md": ("823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c", 30536),
    "lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md": ("ec0fb8ec47cfb71be5b28bc8a76f9152a6cbd377e741e7be1902a0958fbba154", 42172),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}


def sha256_file(p):
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


lines = []
t0 = time.perf_counter()
ok_all = True
for rel, (wsha, wn) in FP.items():
    p = ROOT / rel
    sha, n = sha256_file(p)
    ok = (sha == wsha) and (n == wn)
    ok_all = ok_all and ok
    lines.append("%-72s sha=%s bytes=%d shaMatch=%s bytesMatch=%s => %s" % (
        rel, sha, n, sha == wsha, n == wn, "OK" if ok else "MISMATCH"))

cf = ROOT / "lead/counterpart_fix_20261109/COUNTERPART_FIX.md"
mid = ROOT / "lead/counterpart_fix_20261109/_cf_counterpart_vs_tighten_20261109.md"


def orphan_report(p):
    txt = p.read_text(encoding="utf-8", errors="replace")
    hits = []
    i = 0
    while True:
        i = txt.find("ORPHAN", i)
        if i < 0:
            break
        hits.append(txt[max(0, i - 70): i + 90].replace("\n", "⏎"))
        i += 6
    has_full = "变 ORPHAN 不等于问题解决" in txt
    return {"orphanCount": len(hits), "hasFullSentence": has_full,
            "contexts": hits, "chars": len(txt)}


r1 = orphan_report(cf)
r2 = orphan_report(mid)
elapsed = round(time.perf_counter() - t0, 3)

out = []
out.append("== 编排方指纹复核（8 件，hashlib.sha256 实算） ==")
out += lines
out.append("")
out.append("== ORPHAN 句实证（counterpart_fix_20261109 域内两件） ==")
out.append("主件 COUNTERPART_FIX.md：ORPHAN 出现 %d 次；全句「变 ORPHAN 不等于问题解决」存在=%s；字符数=%d"
           % (r1["orphanCount"], r1["hasFullSentence"], r1["chars"]))
for c in r1["contexts"]:
    out.append("  主件ctx: …%s…" % c)
out.append("中间稿 _cf_counterpart_vs_tighten_20261109.md：ORPHAN 出现 %d 次；全句存在=%s；字符数=%d"
           % (r2["orphanCount"], r2["hasFullSentence"], r2["chars"]))
for c in r2["contexts"]:
    out.append("  中稿ctx: …%s…" % c)
out.append("字节数差 = %d - %d = %d" % (32840, 32830, 32840 - 32830))
out.append("elapsedSec=%s" % elapsed)
out.append("ALL_FINGERPRINTS_OK=%s" % ok_all)

text = "\n".join(out)
(OUTD / "_si_fp_out.txt").write_text(text, encoding="utf-8")
print(text)
