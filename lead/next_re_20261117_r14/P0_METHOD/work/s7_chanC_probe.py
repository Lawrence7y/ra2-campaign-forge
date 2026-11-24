"""S7 · 通道 C 的精化：区分「函数指针表」与「switch 跳表」。

动机（本卡核心诊断）：9 个 C 命中所在的 .data 区段是**等距目标序列**
（如 0x4A16CE/0x4A1957/0x4A1BDF，步长 ≈0x288，且多数**不是 16B 对齐**）——
这是 switch 跳表（case 标签）而不是函数指针数组。若不区分，一档会把**函数体内标签**
判成函数入口（正是 ADJ4/ADJ5 的同型错误）。

判别法（全 .text 扫一遍，收集两类引用）：
  REF_INDEX_JMP : `jmp dword ptr [<base> + reg*4]` / `call dword ptr [<base> + reg*4]` 里的 base
                  ⇒ 该 base 是**跳表**：其项是 case 标签，不是函数入口
  REF_PUSH_IMM  : `push <imm32>` 且 imm32 落在 .data/.rdata ⇒ _initterm 式的表边界传参
  REF_MOV_INDEX : `mov reg, [<base> + reg*4]` ⇒ 跳表读取（间接派发）
"""
import bisect
import json
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import EVIDENCE, HERE, Image, new_md

img = Image()
md = new_md()

with open(os.path.join(HERE, "index.pkl"), "rb") as f:
    idx = pickle.load(f)

DATA_LO, DATA_HI = 0x812000, 0xB79BE4
RD_LO, RD_HI = 0x7E1000, 0x811074
tbl_lo, tbl_hi = DATA_LO, DATA_HI

code = img.read(img.text_start, img.text["raw_size"])
jmp_index = {}      # base -> [site...]
call_index = {}
mov_index = {}
push_imm = {}       # imm -> [site...]

for insn in md.disasm(code, img.text_start):
    if insn.address >= img.text_end:
        break
    if insn.id == 0:
        continue
    mn = insn.mnemonic
    for op in insn.operands:
        # X86_OP_MEM == 3
        if op.type == 3 and op.mem.index != 0:
            disp = op.mem.disp & 0xFFFFFFFF
            if tbl_lo <= disp < tbl_hi or RD_LO <= disp < RD_HI:
                if mn == "jmp":
                    jmp_index.setdefault(disp, []).append(insn.address)
                elif mn == "call":
                    call_index.setdefault(disp, []).append(insn.address)
                else:
                    mov_index.setdefault(disp, []).append(insn.address)
        elif op.type == 2 and mn == "push":  # X86_OP_IMM
            v = op.imm & 0xFFFFFFFF
            if DATA_LO <= v < DATA_HI or RD_LO <= v < RD_HI:
                push_imm.setdefault(v, []).append(insn.address)

print("jmp-indexed bases:", len(jmp_index), " call-indexed:", len(call_index),
      " mov-indexed:", len(mov_index), " push-imm bases:", len(push_imm))

# ---- 对 9 个 C 命中：回溯所属表起点并分类 ----
chan = pickle.load(open(os.path.join(HERE, "channels.pkl"), "rb"))
meas = pickle.load(open(os.path.join(HERE, "measure.pkl"), "rb"))
rows = meas["rows"]
t1 = [r["va"] for r in rows if r["tier"] == "T1"]


def table_span(slot_va):
    """从 slot 出发向两侧扩展到「连续 .text 指针」段的最大区间（允许夹杂非指针，取 ±32 dword 窗口内连续段）。"""
    lo = slot_va
    while lo - 4 >= tbl_lo and img.in_text(img.u32(lo - 4) or 0):
        lo -= 4
    hi = slot_va
    while hi + 4 < tbl_hi and img.in_text(img.u32(hi + 4) or 0):
        hi += 4
    return lo, hi


def classify(base):
    tags = []
    if base in jmp_index:
        tags.append(("INDEX_JMP", jmp_index[base]))
    if base in call_index:
        tags.append(("INDEX_CALL", call_index[base]))
    if base in mov_index:
        tags.append(("INDEX_MOV", mov_index[base]))
    if base in push_imm:
        tags.append(("PUSH_IMM", push_imm[base]))
    return tags


out = {"c_hits": [], "initterm_control": []}
for va in t1:
    slots = chan["c_data_ptrs"].get(va, [])
    for slot in slots:
        lo, hi = table_span(slot)
        tags = classify(lo)
        # 尝试窗口内的所有 4B 对齐基址（表起点可能不是 lo）
        if not tags:
            for b in range(lo, hi + 1, 4):
                tags = classify(b)
                if tags:
                    lo = b
                    break
        entries = [img.u32(q) for q in range(lo, min(hi, lo + 64 * 4) + 1, 4)]
        out["c_hits"].append(dict(
            target=f"{va:08X}", slot=f"{slot:08X}", table=[f"{lo:08X}", f"{hi:08X}"],
            n_entries=len(entries),
            entry_aligned=sum(1 for e in entries if e and e % 16 == 0),
            refs=[(t, [f"{s:08X}" for s in sites[:4]]) for t, sites in tags],
            entries_sample=[f"{e:08X}" for e in entries[:10]],
        ))

# 对照：_initterm 主表（0x812000..0x815DA4）应判为 PUSH_IMM
for base in (0x812000, 0x815DA8, 0x815DBC):
    out["initterm_control"].append(dict(base=f"{base:08X}", refs=classify(base)))

# 统计：所有被 index-jmp 引用的表（跳表）里，有多少地址落在本池
jmp_tbl_targets = set()
for base, sites in jmp_index.items():
    # 表长度未知，按紧随的连续 .text 指针段取
    q = base
    n = 0
    while True:
        w = img.u32(q + n * 4)
        if w is None or not img.in_text(w) or n > 2000:
            break
        jmp_tbl_targets.add(w)
        n += 1
pool = set(r["va"] for r in rows)
out["jump_table_targets_total"] = len(jmp_tbl_targets)
out["pool_in_jump_tables"] = sorted(f"{v:08X}" for v in (pool & jmp_tbl_targets))
out["tier1_in_jump_tables"] = sorted(f"{v:08X}" for v in (set(t1) & jmp_tbl_targets))
out["rand_in_jump_tables"] = sum(1 for r in meas["rand"] if r["va"] in jmp_tbl_targets)

with open(os.path.join(EVIDENCE, "s7_chanC_probe.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

for c in out["c_hits"]:
    print(f"{c['target']} slot {c['slot']} table {c['table']} n={c['n_entries']} "
          f"aligned={c['entry_aligned']} refs={c['refs']}")
print("initterm control:", out["initterm_control"])
print("pool in jump-table targets:", len(out["pool_in_jump_tables"]),
      "of which tier1:", out["tier1_in_jump_tables"])
print("random in jump-table targets:", out["rand_in_jump_tables"], "/1000")
