# -*- coding: utf-8 -*-
"""S13-PUSH 环②/环④ 见证辅助：基于 recore，扫描 vtable 槽 / RTTI / direct callers / ctor-vs-atexit 安装点。
复用 S15S16_3B2/witness.py 的方法，但独立实现；遵守 ㉓（活 vptr 必须是构造器写的，atexit 析构器表不算）。
"""
import os, sys, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone.x86 import *

# 全镜像 section 表（含 raw data），按 VA
_SECS = []
for s in R._pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    va = R.IB + s.VirtualAddress
    sz = max(s.Misc_VirtualSize, s.SizeOfRawData)
    _SECS.append((nm, va, sz, s.get_data()[:sz]))

def va_in(va):
    for nm, v0, sz, data in _SECS:
        if v0 <= va < v0 + sz:
            return nm
    return None

def va_read(va, n):
    for nm, v0, sz, data in _SECS:
        if v0 <= va < v0 + sz:
            off = va - v0
            return data[off:off + n]
    return b""

def u32(va):
    b = va_read(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None

def read_cstr(va, maxn=200):
    out = bytearray()
    for i in range(maxn):
        b = va_read(va + i, 1)
        if not b or b[0] == 0:
            break
        out += b
    return out.decode("latin1", "replace")

def parse_col(col_va):
    if not col_va or not va_in(col_va):
        return None
    sig = u32(col_va)
    td = u32(col_va + 0xC)
    chd = u32(col_va + 0x10)
    return {"col": col_va, "sig": sig, "td": td, "chd": chd}

def parse_td(td_va):
    if not td_va or not va_in(td_va):
        return None
    name_va = td_va + 8
    return {"td": td_va, "name_va": name_va, "name": read_cstr(name_va, 200)}

def find_dword_refs(target):
    """全镜像(跳过 .text) 中 dword==target 的 VA（vtable 槽候选）。"""
    needle = struct.pack("<I", target)
    refs = []
    for nm, v0, sz, data in _SECS:
        if nm == ".text":
            continue
        start = 0
        while True:
            i = data.find(needle, start)
            if i < 0:
                break
            refs.append((v0 + i, nm))
            start = i + 1
    return refs

def resolve_slot(refva):
    """给定槽 VA，回扫 k=0..40 找 COL(sig=0, TD 名 .?AV)，返回 vtable_base/slot_off/RTTI。"""
    best = None
    for k in range(0, 41):
        vb = refva - 4 * k
        c = u32(vb - 4)
        if not c:
            continue
        ci = parse_col(c)
        if not ci or ci["sig"] != 0:
            continue
        tdi = parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            best = {"vtable_base": vb, "slot_off": 4 * k, "col": ci["col"],
                    "td": tdi["td"], "name_va": tdi["name_va"], "rtti_name": tdi["name"]}
            break
    return best

# --- .text 原始字节扫描 ---
TEXT_DATA = R.TEXT_DATA
TEXT_VA = R.TEXT_VA

def find_direct_calls(target):
    calls = []
    for off in range(0, len(TEXT_DATA) - 5):
        if TEXT_DATA[off] != 0xE8:
            continue
        rel = struct.unpack_from("<i", TEXT_DATA, off + 1)[0]
        dest = (TEXT_VA + off + 5 + rel) & 0xFFFFFFFF
        if dest == target:
            calls.append(TEXT_VA + off)
    return calls

def find_vtable_writes(vtable_addr):
    """找 .text 中把 vtable_addr 作为立即数写入的站点。
       imm 出现在 off；往前辨认指令形式：
         C7 05 <disp32> <imm32>  => off-6=C7, off-5=05, global=u32(off-4)   (全局 vptr 写)
         C7 <modrm> <imm32>      => off-2=C7, modrm=off-1                   (对象/栈 vptr 写)
         B8+r <imm32>            => off-1 in B8..BF                        (vt 指针载入寄存器)
       返回 dict。"""
    writes = {"global": [], "regdisp": [], "imm_load": []}
    for off in range(6, len(TEXT_DATA) - 4):
        imm = struct.unpack_from("<I", TEXT_DATA, off)[0]
        if imm != vtable_addr:
            continue
        va = TEXT_VA + off
        if TEXT_DATA[off-6] == 0xC7 and TEXT_DATA[off-5] == 0x05:  # C7 05 disp32 imm32
            absv = struct.unpack_from("<I", TEXT_DATA, off-4)[0]
            writes["global"].append({"write_va": (TEXT_VA + off-6) & 0xFFFFFFFF, "global": absv})
        elif TEXT_DATA[off-2] == 0xC7:  # C7 r/m32 imm32
            writes["regdisp"].append((TEXT_VA + off-2) & 0xFFFFFFFF)
        if 0xB8 <= TEXT_DATA[off-1] <= 0xBF:
            writes["imm_load"].append((TEXT_VA + off-1) & 0xFFFFFFFF)
    return writes

ATEXIT_VA = 0x7C978A

def is_atexit_registered(func_va, window=0x60):
    """构造器 vs 析构器 ㉓：若 func_va 作为 push imm 出现在某 call 0x7C978A 之前 window 内 => atexit 析构器。"""
    # 找 push <func_va>  (68 imm32)
    needle = b"\x68" + struct.pack("<I", func_va)
    start = 0
    sites = []
    for s in R._pe.sections:
        pass
    for nm, v0, sz, data in _SECS:
        if nm != ".text":
            continue
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0:
                break
            pushva = v0 + i
            # 之后 window 内是否 call 0x7C978A (E8 rel32)
            for j in range(i + 5, min(i + 5 + window, len(data) - 5)):
                if data[j] == 0xE8:
                    rel = struct.unpack_from("<i", data, j + 1)[0]
                    if (v0 + j + 5 + rel) & 0xFFFFFFFF == ATEXIT_VA:
                        sites.append((pushva, v0 + j))
                        break
            st = i + 1
    return sites

def find_containing_atlas_func(va):
    """给定 .text 地址，找覆盖它的最小 atlas 函数入口（用于判定写点所在函数是否为 atexit-dtor）。"""
    best = None
    for e, info in R.ATLAS.items():
        ea = int(e, 16)
        if ea <= va < ea + info["size"]:
            if best is None or ea > best[0]:
                best = (ea, e, info["size"])
    return best

def witness_entry(entry_hex):
    ea = int(entry_hex, 16)
    refs = find_dword_refs(ea)
    slots = []
    for refva, sec in refs:
        si = resolve_slot(refva)
        if not si:
            slots.append({"slot_va": "%08X" % refva, "section": sec, "rtti": None})
            continue
        w = find_vtable_writes(si["vtable_base"])
        # 判定每个 global 写点所在函数是否 atexit-dtor
        for g in w["global"]:
            g["in_func"] = find_containing_atlas_func(g["write_va"])
            g["atexit"] = bool(is_atexit_registered(g["in_func"][0])) if g["in_func"] else False
        # regdisp 写点（对象/栈构造期 install）也判定所在函数
        for rw in w["regdisp"]:
            f = find_containing_atlas_func(rw)
            if f:
                g = {"write_va": "%08X" % rw, "global": None,
                     "in_func": f, "atexit": bool(is_atexit_registered(f[0]))}
                w["global"].append(g)
        slots.append({
            "slot_va": "%08X" % refva, "section": sec,
            "vtable_base": "%08X" % si["vtable_base"], "slot_off": si["slot_off"],
            "col": "%08X" % si["col"], "td": "%08X" % si["td"],
            "name_va": "%08X" % si["name_va"], "rtti_name": si["rtti_name"],
            "global_writes": w["global"], "imm_loads": ["%08X" % x for x in w["imm_load"]],
        })
    direct = find_direct_calls(ea)
    return {"entry": entry_hex, "direct_callers": ["%08X" % x for x in direct], "slots": slots}

if __name__ == "__main__":
    # self-check on a known S15 slot with vtable
    r = witness_entry("00727240")
    print(json.dumps(r, ensure_ascii=False, indent=1)[:2000])
