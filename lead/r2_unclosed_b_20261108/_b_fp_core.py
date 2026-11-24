# -*- coding: utf-8 -*-
"""崩点2 补证①：三相关件 + 周边被核件 hashlib 实算 SHA256/字节数 + 尾串归属判定。
只读；输出写本写域 _b_fp_core_out.txt。路径全部为常量，含显式包含校验。"""
import hashlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
WD = LEAD / "r2_unclosed_b_20261108"
OUT = WD / "_b_fp_core_out.txt"

R2D = LEAD / "dtrigger_round2_20261107"
CMP = LEAD / "dtrigger_compare_20261107"
R3V = LEAD / "criteria_r3_verify_20261108"

FILES = [
    R2D / "_dB_anchor_recompute.py",
    R2D / "_dB_anchor_recompute_out.txt",
    R2D / "_dB_anchor_recompute_data.json",
    R2D / "_verify_B_out.txt",
    R2D / "CRITERIA_ROUND2.md",
    R3V / "R2_BREAKPOINTS_CLOSURE.md",
    CMP / "CRITERIA_COMPARE.md",
    CMP / "_dtrigger_metrics.py",
    CMP / "_dtrigger_probe_out.txt",
    CMP / "_dtrigger_supplement_out.txt",
]
# 编排方提供的实跑指纹（比对确认读到同一份文件）
ORCH = {
    "_dB_anchor_recompute.py": ("44b10371cdc258e7db5c232f53d9d64dfdf4f34cb084115d0bb8c7a05a5a382b", 27324),
    "_dB_anchor_recompute_out.txt": ("3e9588ce1def2ebc5b9ad77a3ce242b47bcada4ae1ab1bc4ea606775edd40807", 14479),
    "_verify_B_out.txt": ("4ee6a6b78d80a336c3431a6f71d9f5a77fec93ef65b7a4c642a49b669368c107", 7229),
    "_dB_anchor_recompute_data.json": ("8fb149f21e9b41d7c808e8f8c2e1cb35ca62b881ebe65bfba7029b6f95763794", 42910),
    "R2_BREAKPOINTS_CLOSURE.md": ("bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde", 22351),
    "CRITERIA_COMPARE.md": ("4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726", 48343),
}
TAILS = {
    "claim_script_tail(20位)=26f3fb61829756dfeecf": "26f3fb61829756dfeecf",
    "claim_out_tail(11位)=b6f95763794": "b6f95763794",
}

def in_scope(p: Path) -> bool:
    try:
        rp = p.resolve()
    except OSError:
        return False
    if ".." in str(rp):
        return False
    return rp.is_relative_to(WD) or rp.is_relative_to(LEAD) or rp.is_relative_to(ROOT)

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

lines = []
digests = {}
for p in FILES:
    if not (p.exists() and in_scope(p)):
        lines.append(f"MISSING_OR_OUT_OF_SCOPE  {p}")
        continue
    d = sha256_file(p)
    n = p.stat().st_size
    digests[p.name] = (d, n)
    tag = ""
    if p.name in ORCH:
        od, on = ORCH[p.name]
        tag = f"  [vs编排方: sha={'MATCH' if d == od else 'MISMATCH'} bytes={'MATCH' if n == on else 'MISMATCH'}]"
    lines.append(f"SHA256 {d}  bytes {n:>7}  {p.relative_to(ROOT)}{tag}")

lines.append("")
lines.append("【尾串归属判定（对 _dB_ 三相关件）】")
for tname, t in TAILS.items():
    for name in ("_dB_anchor_recompute.py", "_dB_anchor_recompute_out.txt", "_dB_anchor_recompute_data.json"):
        d, n = digests[name]
        pos = d.find(t)
        if pos < 0:
            lines.append(f"  {tname} -> in {name}: False")
        else:
            lines.append(f"  {tname} -> in {name}: True  pos={pos}  尾{len(t)}位(endswith)={d.endswith(t)}  digest共64位")

lines.append("")
lines.append("【被核绑定汇总（本轮 hashlib 实算）】")
for name in ORCH:
    d, n = digests[name]
    lines.append(f"  {name}: SHA256 = {d}，字节数 = {n}")

txt = "\n".join(lines) + "\n"
assert OUT.is_relative_to(WD)
OUT.write_text(txt, encoding="utf-8")
print(txt)
