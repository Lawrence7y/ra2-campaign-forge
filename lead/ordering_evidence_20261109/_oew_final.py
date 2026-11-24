# -*- coding: utf-8 -*-
"""_oew_final.py -- 交付前自检：六节、必现要素、绑定行严格格式、8 件指纹、纪律。
Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oew_final.py"
"""
from __future__ import annotations
import hashlib, json, re, subprocess
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "ordering_evidence_20261109"
doc = WD / "ORDERING_EVIDENCE.md"
text = doc.read_text(encoding="utf-8")
O: dict = {}
O["doc_bytes"] = doc.stat().st_size
O["doc_sha256"] = hashlib.sha256(doc.read_bytes()).hexdigest()

# 六节
secs = re.findall(r"^## (\d) (.+)$", text, re.M)
O["sections"] = secs
O["six_sections_in_order"] = [int(n) for n, _ in secs] == [1, 2, 3, 4, 5, 6]

# 必现要素
req = ["mtime", "ctime", "atime", "324 秒", "可用", "可写", "内容因果链",
       "commit-then-reveal", "带外见证", "三重相等", "巧合概率", "适用范围", "未验"]
O["required_elements"] = {k: (k in text) for k in req}
O["all_required_present"] = all(O["required_elements"].values())

# 绑定行：严格格式 + 无不合格式 token
STRICT = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$", re.M)
hits = STRICT.findall(text)
O["binding"] = {"n_strict_hits": len(hits), "hashes": [h for h, _ in hits],
                "byte_numbers": [int(b) for _, b in hits]}
TOKEN = re.compile(r"被核对象 SHA256\s*=")
all_lines = [l for l in text.splitlines() if TOKEN.search(l)]
O["binding"]["n_token_lines"] = len(all_lines)
O["binding"]["n_nonconforming"] = sum(1 for l in all_lines if not STRICT.fullmatch(l))
O["binding"]["all_conforming"] = O["binding"]["n_nonconforming"] == 0
# 首行对象绑定行须等于磁盘 seal
seal_p = ROOT / "lead/cert_realcheck_20261109/_cr_seal.json"
sb = seal_p.read_bytes()
seal_h, seal_n = hashlib.sha256(sb).hexdigest(), len(sb)
first = STRICT.search(text)
O["binding"]["object_line_equals_disk_seal"] = (first is not None and first.group(1) == seal_h and int(first.group(2)) == seal_n)
# 9 行基线绑定行全等
baseline = [
    ("5af2b304a71ec4c13bea14d1034ef0de12d306a62f769a41bec3891c6392cc5f", 45423),
    ("09548c9ad258270fc7dbf80150437e868e45c6b8f5220214cbfd8aa20b1ec6d7", 9590),
    ("e49151caef129b8925fcb02bcd23c36060cd411102e05350bad7839b8d769657", 1126),
    ("5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542),
    ("63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
    ("2e539d392b0aca54cb8cd2c83bd20e1d87ba9ce5cbc8f15ea5ea279ef0b86574", 5376),
    ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    ("2cd2b39d32fb510b4d0eca96bd27befc96dcb8c963b8a46e27a0040f5a607969", 45567),
]
O["binding"]["baseline_9_lines_all_present"] = all((h, n) in [(x, int(y)) for x, y in hits] for h, n in baseline)

# 8 件指纹收尾 + 只读域
ORCH = {
    "lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md": ("5af2b304a71ec4c13bea14d1034ef0de12d306a62f769a41bec3891c6392cc5f", 45423),
    "lead/seal_chronology_20261109/_sc_probe_out.json": ("09548c9ad258270fc7dbf80150437e868e45c6b8f5220214cbfd8aa20b1ec6d7", 9590),
    "lead/seal_chronology_20261109/_sc_ctime.py": ("e49151caef129b8925fcb02bcd23c36060cd411102e05350bad7839b8d769657", 1126),
    "lead/oracle_spec_20261109/_os_ORACLE_SPEC.md": ("5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542),
    "lead/cert_realcheck_20261109/_cr_seal.json": ("63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
    "lead/cert_realcheck_20261109/_cr_build_seal.py": ("2e539d392b0aca54cb8cd2c83bd20e1d87ba9ce5cbc8f15ea5ea279ef0b86574", 5376),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
final = {}
for rel, (eh, en) in ORCH.items():
    b = (ROOT / rel).read_bytes()
    final[rel] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b),
                  "unchanged": hashlib.sha256(b).hexdigest() == eh and len(b) == en}
O["READONLY_ALL_UNCHANGED"] = all(v["unchanged"] for v in final.values())
O["final"] = final

# 写域文件清单 + 无新 seal + 无签名 sidecar + git
O["write_domain_files"] = sorted(p.name for p in WD.iterdir() if p.is_file())
O["n_new_seal_json"] = len([p for p in WD.iterdir() if p.is_file() and "seal" in p.name.lower() and p.suffix == ".json"])
O["oew_files_only_new"] = sorted(p.name for p in WD.iterdir() if p.is_file() and p.name.startswith("_oew_") or p.name == "ORDERING_EVIDENCE.md")

def run(cmd):
    r = subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    return {"rc": r.returncode, "out": (r.stdout or "").strip()[:400], "err": (r.stderr or "").strip()[:300]}
O["git_head"] = run('git log -1 --format="%H %cI"')
O["git_status_wd"] = run('git status --porcelain -- lead/ordering_evidence_20261109/')

out = WD / "_oew_final_out.json"
out.write_text(json.dumps(O, ensure_ascii=False, indent=2), encoding="utf-8")
print("WROTE", out.name, out.stat().st_size)
print("DOC", O["doc_sha256"], O["doc_bytes"])
print("SIX_SECTIONS_IN_ORDER =", O["six_sections_in_order"], O["sections"])
print("ALL_REQUIRED_PRESENT =", O["all_required_present"])
print("MISSING =", [k for k, v in O["required_elements"].items() if not v])
print("BINDING =", O["binding"])
print("READONLY_ALL_UNCHANGED =", O["READONLY_ALL_UNCHANGED"])
print("N_NEW_SEAL_JSON =", O["n_new_seal_json"])
print("OE_NEW_FILES =", O["oew_files_only_new"])
print("GIT_HEAD =", O["git_head"]["out"])
print("GIT_STATUS_WD =", O["git_status_wd"]["out"])
