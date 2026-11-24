# -*- coding: utf-8 -*-
"""④ 使用见证取证（B2）：
对每行取 ② 已钉住的 (vt, slot_off)，在 .text 中找 `mov dword ptr [...], vt` 的安装点，
判定所在函数、是否 atexit 析构注册（排除），并标出是否落在本 entry 体内（行内不算见证）。
另外列出 vt[slot] == entry 的自证，供交叉核对。
"""
import os, sys, json, struct, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
from capstone import *
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
REFS = json.load(open(os.path.join(WORK, "refs.json"), encoding="utf-8"))
ROWS = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))}

FUNCS = sorted((int(k, 16), k, v["size"]) for k, v in R.ATLAS.items())
_fstarts = [f[0] for f in FUNCS]

def func_of(va):
    i = bisect.bisect_right(_fstarts, va) - 1
    while i >= 0:
        s, k, sz = FUNCS[i]
        if s <= va < s + sz:
            return (s, k, sz)
        i -= 1
        if i >= 0 and FUNCS[i][0] + FUNCS[i][2] <= va and FUNCS[i][0] < va - 0x2000:
            break
    return None

def all_imm_stores(vt):
    """返回 [(va, op_str, dest_desc)]：.text 中立即数 == vt 的写法（C7 ... 与 B8.. imm 载入）。"""
    T, B = R.TEXT_DATA, R.TEXT_VA
    res = []
    needle = struct.pack("<I", vt)
    st = 0
    offs = []
    while True:
        i = T.find(needle, st)
        if i < 0:
            break
        offs.append(i)
        st = i + 1
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
    for off in offs:
        va = B + off
        is_store = False
        if off >= 6 and T[off-6] == 0xC7 and T[off-5] == 0x05:
            is_store = True
        elif off >= 2 and T[off-2] == 0xC7:
            is_store = True
        if not is_store:
            continue
        # 用 capstone 反汇编该指令取准确形式
        start = va - 6 if (off >= 6 and T[off-6] == 0xC7 and T[off-5] == 0x05) else va - 2
        insns = list(md.disasm(R.read_va(start, 12), start))
        if not insns:
            continue
        ins = insns[0]
        if ins.mnemonic != "mov" or ins.address != start:
            continue
        if len(ins.operands) != 2 or ins.operands[0].type != X86_OP_MEM or ins.operands[1].type != X86_OP_IMM:
            continue
        if (ins.operands[1].imm & 0xFFFFFFFF) != vt:
            continue
        res.append((ins.address, ins.op_str, ins.bytes.hex()))
    return res

out = {}
for e, v in REFS.items():
    slots = [s for s in v["slots"] if s.get("resolved") and ".?AV" in (s["resolved"]["rtti"] or "")]
    if not slots:
        out[e] = {"ok": False, "why": "no rtti slot"}
        continue
    s = slots[0]
    vt = int(s["resolved"]["vtable"], 16)
    off = s["resolved"]["slot_off"]
    ea = int(e, 16)
    size = R.ATLAS.get(e, {}).get("size") or 0
    stores = []
    for va, op, by in all_imm_stores(vt):
        f = func_of(va)
        in_self = (ea <= va < ea + size)
        atex = False
        if f:
            atex = bool(C2.is_atexit_registered(f[0]))
        stores.append({"va": "%08X" % va, "op": op, "bytes": by,
                       "in_func": f[1] if f else None, "atexit": atex,
                       "in_self": in_self})
    # vt[slot] == entry?
    slot_val = C2.u32(vt + off)
    out[e] = {"vt": "%08X" % vt, "slot_off": off, "slot_no": off // 4,
              "rtti": s["resolved"]["rtti"],
              "slot_points_to_entry": (slot_val == ea), "slot_value": "%08X" % (slot_val or 0),
              "stores": stores,
              "n_outside_alive": len([x for x in stores if not x["in_self"] and x["atexit"] is False])}

json.dump(out, open(os.path.join(WORK, "ring4.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
lines = []
for e, v in out.items():
    if not v.get("vt"):
        lines.append("ROW %s  ④ N/A (%s)" % (e, v.get("why")))
        continue
    lines.append("ROW %s  vt=%s slot#%d(%s)  vt[slot]==entry? %s  行外活安装点=%d" % (
        e, v["vt"], v["slot_no"], v["rtti"], v["slot_points_to_entry"], v["n_outside_alive"]))
    for st in v["stores"]:
        lines.append("    store %s %-40s bytes=%s in_func=%s atexit=%s in_self=%s" % (
            st["va"], st["op"], st["bytes"], st["in_func"], st["atexit"], st["in_self"]))
txt = "\n".join(lines)
open(os.path.join(WORK, "ring4.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
