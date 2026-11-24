"""S11 · 两个「孤例」命中的表类型核验（决定一档可用行数）。

004A20F0/004E7C20/0052D620/006E4080/006E62E0/006E80F0/007E0000 已被 S10 判为跳表项。
剩下：
  006CA7B0  slot 008421CC  —— {desc_ptr, fn_ptr} 成对表：00842238/006CA6A0, 0084222C/006CA730,
                              00842220/006CA7B0，三个 code slot 全 d1=1 pad≥8
  007D6830  slot 0087C4AC  —— {fn, rdata_ptr, data_ptr} 三元组：007D6AA2/007F97B8/0087C370,
                              007D6830/007F97AC/0087C370, 007D6624/007F97A4
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import COVERAGE, EVIDENCE, load_lines, norm_addr
import s3_channels as s3

img = s3.img
cov = set()
for ln in load_lines(COVERAGE)[1:]:
    if ln.strip():
        cov.add(int(norm_addr(ln.split("\t")[0]), 16))

chan = __import__("pickle").load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "channels.pkl"), "rb"))
B = chan["B"]


def desc(va):
    d = s3.chan_d(va)
    return dict(va=f"{va:08X}", d1=d["d1"], pad=d["pad"], d2=d["d2_why"],
                in_cov=va in cov, in_vt=va in B,
                bytes=img.bytes_hex(va, 24))


def str_at(va, n=40):
    b = img.read(va, n)
    if not b:
        return None
    e = b.find(b"\x00")
    s = b[:e] if e > 0 else b
    return "".join(chr(c) if 32 <= c < 127 else "." for c in s)


out = {}
# 表 A：{desc, fn} 成对表
rowsA = [0x8421BC, 0x8421C4, 0x8421CC]
out["tableA"] = []
for q in rowsA:
    fn = img.u32(q)
    dp = img.u32(q - 4)
    out["tableA"].append(dict(slot=f"{q:08X}", desc_ptr=f"{dp:08X}",
                              desc_str=str_at(dp), **desc(fn)))
# 表 B：{fn, rdata, data} 三元组
out["tableB"] = []
for q in (0x87C4A0, 0x87C4AC, 0x87C4B8):
    fn = img.u32(q)
    out["tableB"].append(dict(slot=f"{q:08X}", p2=f"{img.u32(q+4):08X}", p3=f"{img.u32(q+8):08X}",
                              **desc(fn)))
for t in (0x7F97B8, 0x7F97AC):
    out.setdefault("tableB_aux", []).append(dict(ptr=f"{t:08X}", str=str_at(t)))

with open(os.path.join(EVIDENCE, "s11_lone_cases.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
