# -*- coding: utf-8 -*-
"""B2 ④ 使用见证：主虚表构造期安装点（含 atexit 排查 / 是否构造器）+ 真实虚派发站点。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "rows_b2.json"), encoding="utf-8"))
r12 = {r["entry"]: r for r in json.load(open(os.path.join(HERE, "rings12.json"), encoding="utf-8"))}

MAIN = {
    "BuildingClass": dict(vt=0x007E3EBC, col=0x007FC360, n=322),
    "BuildingTypeClass": dict(vt=0x007E4570, col=0x007FC618, n=49),
    "CaptureManagerClass": dict(vt=0x007E4B40, col=0x007FCB60, n=24),
    "FactoryClass": dict(vt=0x007E88D0, col=0x00800610, n=24),
}


def func_bounds(va):
    """atlas 覆盖 va 的函数 (entry, size)。"""
    return atlas_covering(va)


def ret_shape(entry, size):
    """函数尾部形态：是否 'mov eax,<this>; ret n'（构造器特征）。"""
    body = disasm(entry, size)
    tail = [i for i in body if i.id and i.mnemonic.startswith("ret")]
    out = dict(last_insns=["%s %s" % (i.mnemonic, i.op_str) for i in body[-6:]],
               first_insns=["%s %s" % (i.mnemonic, i.op_str) for i in body[:6]],
               nret=len(tail))
    if len(body) >= 2:
        a, b = body[-2], body[-1]
        out["ret_mov_eax"] = (a.mnemonic == "mov" and a.op_str.startswith("eax,")
                              and b.mnemonic.startswith("ret"))
        if out["ret_mov_eax"]:
            out["eax_src"] = a.op_str
    return out


# ---- 1) 安装点详查 ----
print("=== 安装点详查（是否构造器 / atexit） ===")
INSTALL = {}
for cls, M in MAIN.items():
    sites = find_vtable_imm_sites(M["vt"])
    lst = []
    for s in sites["c7_rm"]:
        wva = s["write_va"]
        fb = func_bounds(wva)
        rec = dict(write_va=hx(wva))
        if fb:
            ent, ehex, size = fb
            rec.update(in_func=hx(ent), func_size=size)
            rec.update(ret_shape(ent, size))
            ax = is_atexit_registered(ent)
            rec["atexit"] = ax
        ins = disasm(wva, 10)
        rec["insn"] = "%s %s" % (ins[0].mnemonic, ins[0].op_str) if ins else "?"
        rec["bytes"] = va_read(wva, ins[0].size).hex(" ") if ins else ""
        lst.append(rec)
        print("\n %-20s vt %08X @%s  %s   bytes=%s" % (cls, M["vt"], rec["write_va"], rec["insn"], rec["bytes"]))
        print("     in_func=%s size=%s atexit=%s" % (rec.get("in_func"), rec.get("func_size"), rec.get("atexit")))
        print("     head: %s" % (rec.get("first_insns"),))
        print("     tail: %s  ret_mov_eax=%s" % (rec.get("last_insns"), rec.get("ret_mov_eax")))
    INSTALL[cls] = lst

# ---- 2) 真实虚派发站点：call dword ptr [reg + 4*slot] ----
print("\n\n=== 真实虚派发站点扫描（call [reg+4*slot]） ===")
# 建索引：disp -> 站点
disp_map = {}
for off in range(0, len(TEXT_DATA) - 8):
    b0 = TEXT_DATA[off]
    # FF /2 = call r/m32
    if b0 != 0xFF:
        continue
    m = TEXT_DATA[off + 1]
    # modrm: mod!=3, reg==2
    if (m >> 3) & 7 != 2 or (m >> 6) == 3:
        continue
    mod = m >> 6
    rm = m & 7
    disp = None
    ln = 0
    if mod == 1:
        disp = struct.unpack_from("<b", TEXT_DATA, off + 2)[0]
        ln = 3
    elif mod == 2:
        disp = struct.unpack_from("<i", TEXT_DATA, off + 2)[0]
        ln = 6
    if disp is None:
        continue
    disp_map.setdefault(disp, []).append((TEXT_VA + off, rm, ln))
print("disp buckets:", len(disp_map))

for r in rows:
    e = r["entry"]
    slot = r12[e]["ring2"].get("slot_index")
    cls = r12[e]["cls_hint"]
    if slot is None:
        print("\n## %s no slot" % e)
        continue
    d = slot * 4
    hits = disp_map.get(d, [])
    print("\n## %s %s  slot#%d disp=0x%X  派发站点 %d 处" % (e, r["name"], slot, d, len(hits)))
    for va, rm, ln in hits[:12]:
        ins = disasm(va, 8)
        fb = func_bounds(va)
        print("    %08X %-30s in_func=%s" % (va, ("%s %s" % (ins[0].mnemonic, ins[0].op_str)) if ins else "?",
                                             hx(fb[0]) if fb else None))

# ---- 3) direct callers ----
print("\n\n=== direct callers ===")
for r in rows:
    ev = int(r["entry"], 16)
    cs = find_direct_calls(ev)
    print(" %s %-30s direct_callers=%d %s" % (r["entry"], r["name"], len(cs),
                                              [hx(c) for c in cs[:8]]))

json.dump(dict(install=INSTALL), open(os.path.join(HERE, "ring4.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n-> ring4.json")
