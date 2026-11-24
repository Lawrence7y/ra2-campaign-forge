"""S9 · 8 个「大段连续 code-pointer」命中的来源定位：找该区段的真实表基准与被引用形式，
并逐字节看目标前后（判断 case 标签 vs 真入口）。"""
import json
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import EVIDENCE, HERE, Image, new_md
import s3_channels as s3

img = s3.img
md = s3.md

meas = pickle.load(open(os.path.join(HERE, "measure.pkl"), "rb"))
rows = meas["rows"]
t1 = [r["va"] for r in rows if r["tier"] == "T1"]
chan = pickle.load(open(os.path.join(HERE, "channels.pkl"), "rb"))

# 1) 该区段的所有 index 引用 / push imm 引用
code = img.read(img.text_start, img.text["raw_size"])
REG_LO, REG_HI = 0x86E000, 0x875000
refs = []
for insn in md.disasm(code, img.text_start):
    if insn.address >= img.text_end:
        break
    if insn.id == 0:
        continue
    for op in insn.operands:
        v = None
        if op.type == 3 and op.mem.index != 0:
            v = op.mem.disp & 0xFFFFFFFF
        elif op.type == 2 and insn.mnemonic in ("push", "mov", "lea", "cmp"):
            v = op.imm & 0xFFFFFFFF
        if v is not None and REG_LO <= v < REG_HI:
            refs.append((insn.address, insn.mnemonic, v, insn.op_str))

print("refs into [0x86E000,0x875000):", len(refs))
for r in refs[:25]:
    print("   %08X  %-5s 0x%08X  %s" % r)

# 2) 每个一档行的 16B 前文 / 64B 正文
print("\n--- context per tier1 row ---")
for va in t1:
    print("== %08X ==" % va)
    print("   prev32:", img.bytes_hex(va - 32, 32))
    print("   here48:", img.bytes_hex(va, 48))
    d = s3.chan_d(va)
    print("   d1=%d pad=%d d2=%s" % (int(d["d1"]), d["pad"], d["d2_why"]))
    # 前驱指令
    pr = s3.insn_ending_at(va)
    if pr:
        for insn in md.disasm(img.read(pr[0], pr[1]), pr[0]):
            print("   prev insn: %08X %-22s %s" % (insn.address, insn.mnemonic, insn.op_str))

out = dict(refs=[(f"{a:08X}", m, f"{v:08X}", s) for a, m, v, s in refs],
           region="0086E000-00875000", tier1=[f"{v:08X}" for v in t1])
with open(os.path.join(EVIDENCE, "s9_region_refs.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
