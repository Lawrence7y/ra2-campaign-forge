# -*- coding: utf-8 -*-
"""④ 使用见证索引：
 - 全 .text 扫一遍，索引 (a) call/jmp dword ptr [reg(+index*scale)+disp]
   (b) mov dword ptr [mem], imm32   (c) mov reg, imm32
 - 每行：找 vtable 安装点（非 atexit 析构器），找与 slot_off 匹配的派发点，
   并判定「安装点所在函数 == 派发点所在函数」的强同函数链。
输出 _work/ring4.json + ring4.txt
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
from capstone import *
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
AN = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))

TEXT = R.TEXT_DATA
TV = R.TEXT_VA
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

dispatches = []   # (addr, mnem, base_reg_name, disp, index_reg)
imm_stores = []   # (addr, imm, memdesc)
imm_loads = []    # (addr, imm, reg_name)
insns_all = []    # (addr, id, mnem, op_str) 供 containment / 上下文

t0 = None
n = 0
for ins in md.disasm(TEXT, TV):
    n += 1
    if ins.id == 0:          # skipdata
        continue
    ops = ins.operands
    if ins.id in (X86_INS_CALL, X86_INS_JMP) and ops and ops[0].type == X86_OP_MEM:
        m = ops[0].mem
        base = ins.reg_name(m.base) if m.base != X86_REG_INVALID else None
        idx = ins.reg_name(m.index) if m.index != X86_REG_INVALID else None
        dispatches.append({"va": ins.address, "mnem": ins.mnemonic, "base": base,
                           "index": idx, "scale": m.scale, "disp": m.disp})
    elif ins.id == X86_INS_MOV and len(ops) == 2 and ops[1].type == X86_OP_IMM \
            and ops[0].type == X86_OP_MEM:
        m = ops[0].mem
        base = ins.reg_name(m.base) if m.base != X86_REG_INVALID else None
        imm_stores.append({"va": ins.address, "imm": ops[1].imm & 0xFFFFFFFF,
                           "disp": m.disp, "base": base})
    elif ins.id == X86_INS_MOV and len(ops) == 2 and ops[1].type == X86_OP_IMM \
            and ops[0].type == X86_OP_REG:
        imm_loads.append({"va": ins.address, "imm": ops[1].imm & 0xFFFFFFFF,
                          "reg": ins.reg_name(ops[0].reg)})
    insns_all.append((ins.address, ins.id, ins.mnemonic, ins.op_str))
print("scanned insns:", n, "dispatches:", len(dispatches), "imm_stores:", len(imm_stores),
      "imm_loads:", len(imm_loads))

def containing_func(va):
    best = None
    for e, info in R.ATLAS.items():
        ea = int(e, 16)
        if ea <= va < ea + info["size"]:
            if best is None or ea > best[0]:
                best = (ea, e, info["size"])
    return best

# 函数起点集合，用于更快 containment（按大小建列表）
FUNCS = sorted((int(k, 16), k, v["size"]) for k, v in R.ATLAS.items())
import bisect
_fstarts = [f[0] for f in FUNCS]
def func_of(va):
    i = bisect.bisect_right(_fstarts, va) - 1
    while i >= 0:
        s, k, sz = FUNCS[i]
        if s <= va < s + sz:
            return (s, k, sz)
        if s + sz <= va and i > 0 and FUNCS[i-1][0] + FUNCS[i-1][2] <= va:
            # 往回退一步以免跨越空洞太远
            i -= 1
            continue
        break
    return None

ATEXIT_CACHE = {}
def atexit_of(func_start):
    if func_start not in ATEXIT_CACHE:
        ATEXIT_CACHE[func_start] = bool(C2.is_atexit_registered(func_start))
    return ATEXIT_CACHE[func_start]

out = {}
for rec in AN:
    entry = rec["entry"]
    vt_info = None
    for s in rec["ring2_slots"]:
        if s.get("rtti_name"):
            vt_info = s
            break
    if not vt_info:
        out[entry] = {"ok": False, "why": "no rtti slot"}
        continue
    V = int(vt_info["vtable_base"], 16)
    O = vt_info["slot_off"]
    stores = [s for s in imm_stores if s["imm"] == V]
    install = []
    for s in stores:
        f = func_of(s["va"])
        install.append({"va": "%08X" % s["va"], "in_func": f[1] if f else None,
                        "atexit": atexit_of(f[0]) if f else None,
                        "mem": ("[%s+0x%x]" % (s["base"], s["disp"])) if s["base"] else ("[0x%x]" % s["disp"])})
    loads = [{"va": "%08X" % x["va"], "reg": x["reg"]} for x in imm_loads if x["imm"] == V]
    # 派发点：disp == slot_off 且 index 空
    disps = [d for d in dispatches if d["disp"] == O and not d["index"]]
    disp_fns = {}
    for d in disps:
        f = func_of(d["va"])
        disp_fns.setdefault(f[1] if f else None, []).append("%08X" % d["va"])
    # 强链：安装函数 与 派发函数 相同
    inst_fns = {i["in_func"] for i in install if i["in_func"] and i["atexit"] is False}
    strong = {k: v for k, v in disp_fns.items() if k in inst_fns}
    out[entry] = {
        "vtable": "%08X" % V, "slot_off": O,
        "installs": install, "imm_loads": loads,
        "n_dispatch_sites_total": len(disps),
        "dispatch_total": len(disps),
        "strong_same_func": strong,
        "install_fns": sorted(x for x in inst_fns if x),
        "direct": rec["ring4_direct"],
    }

json.dump(out, open(os.path.join(WORK, "ring4.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

with open(os.path.join(WORK, "ring4.txt"), "w", encoding="utf-8") as f:
    for e, v in out.items():
        f.write("ROW %s vt=%s slot_off=%d direct=%s\n" % (e, v.get("vtable"), v.get("slot_off", -1), v.get("direct")))
        for i in v.get("installs", []):
            f.write("   install %s %s in_func=%s atexit=%s\n" % (i["va"], i["mem"], i["in_func"], i["atexit"]))
        for l in v.get("imm_loads", []):
            f.write("   imm_load %s reg=%s\n" % (l["va"], l["reg"]))
        f.write("   dispatch(disp=slot_off) total=%s strong_same_func=%s\n" % (
            v.get("n_dispatch_sites_total"), v.get("strong_same_func")))
print("-> ring4.json / ring4.txt")
