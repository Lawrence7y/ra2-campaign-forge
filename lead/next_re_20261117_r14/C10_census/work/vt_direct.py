#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C10 虚表槽直指、atlas 未收录的真入口数（R14-R1 追加数）。

定义：vtable 槽直接指向地址 X，X ∈ [LO,HI)（本片地址范围），且 owner(X)==None
（X 不在任何 atlas 函数区间内 ⇒ atlas 未收录）。虚表槽天然指向函数入口，
再以「首指令可解码 + 非数据」确认是真入口（不倒退到指令内部）。

双通道（互不依赖对方判定产物）：
  通道 A：rtti_independent.json（自写 struct PE + .rdata COL→TD 恢复，真实槽数）
  通道 B：pefile 重新解析 .rdata，独立重做 COL/TD→vtable 槽，算同一集合
两通道各自算集，最后比对（一致/差异分别列出）。
输出 EVIDENCE/vt_direct_entries.tsv + work/vt_direct.json
"""
import os, json, struct, bisect, re
import pefile
import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C10_census")
WORK = os.path.join(CARD, "work")
EVID = os.path.join(CARD, "EVIDENCE")
EXE = os.path.join(ROOT, "ra2youli\\gamemd.exe")
LO, HI = 0x773500, 0x7E038D

# atlas 函数区间（仅用于 owner 判定）
lines = open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8", errors="replace").read().splitlines()
hdr = lines[0].split("\t")
rows = []
for ln in lines[1:]:
    if not ln.strip(): continue
    r = dict(zip(hdr, ln.split("\t")))
    rows.append((int(r["entry"], 16), int(r["size"])))
rows.sort()
starts = [a for a, _ in rows]; sizes = dict(rows)
atlas_entries = set(starts)
def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + sizes[starts[i]] else None

# ---------- 通道 A：读 rtti_independent.json ----------
ri = json.load(open(os.path.join(WORK, "rtti_independent.json"), encoding="utf-8"))
slots_A = set()
for v in ri["vtables"]:
    for s in v["slots_list"]:
        slots_A.add(int(s, 16))

# ---------- 通道 B：pefile 独立重做 RTTI 恢复 ----------
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
sec_by = {}
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    sec_by[nm] = s

def sec_range(nm):
    s = sec_by[nm]
    va = IB + s.VirtualAddress
    return va, s.SizeOfRawData, s.PointerToRawData, s.Misc_VirtualSize

def make_u32():
    data = pe.__data__
    def u32(va):
        for nm in (".rdata", ".data"):
            va0, rawsz, ptr, vsz = sec_range(nm)
            if va0 <= va and va + 4 <= va0 + max(rawsz, vsz):
                off = ptr + (va - va0)
                return struct.unpack_from("<I", data, off)[0]
        raise ValueError("no bytes")
    return u32
u32 = make_u32()

TEXT_LO = IB + sec_by[".text"].VirtualAddress
TEXT_HI = TEXT_LO + sec_by[".text"].SizeOfRawData

# TypeDescriptor
tds = {}
for nm in (".rdata", ".data"):
    va0, rawsz, ptr, vsz = sec_range(nm)
    buf = pe.__data__[ptr:ptr+rawsz]
    for m in re.finditer(rb"\.\?A[VU]", buf):
        i = m.start()
        if i < 8: continue
        z = buf.find(b"\x00", i)
        if z < 0: continue
        tds[va0 + i - 8] = True
tdset = set(tds)
# COL
cols = set()
for nm in (".rdata", ".data"):
    va0, rawsz, ptr, vsz = sec_range(nm)
    buf = pe.__data__[ptr:ptr+rawsz]
    for off in range(0, len(buf)-20, 4):
        ptd = struct.unpack_from("<I", buf, off+12)[0]
        if ptd in tdset:
            pcd = struct.unpack_from("<I", buf, off+16)[0]
            if 0x400000 <= pcd < 0x900000:
                cols.add(va0 + off)
# vtable pos + slots
slots_B = set()
for nm in (".rdata", ".data"):
    va0, rawsz, ptr, vsz = sec_range(nm)
    buf = pe.__data__[ptr:ptr+rawsz]
    for off in range(0, len(buf)-4, 4):
        v = struct.unpack_from("<I", buf, off)[0]
        if v in cols:
            vt = va0 + off + 4
            n = 0
            while n < 512:
                try: p = u32(vt + 4*n)
                except ValueError: break
                if TEXT_LO <= p < TEXT_HI: n += 1
                else: break
            for i in range(n):
                slots_B.add(u32(vt + 4*i))

# ---------- 交集/并集 + 本片洞判定 ----------
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True; md.detail = False
def first_ok(va):
    """首指令可解码且像入口（非 emms/fld/fstp/st( ) 这类数据误指）。"""
    for nm in (".text",):
        va0, rawsz, ptr, vsz = sec_range(nm)
        if va0 <= va < va0 + max(rawsz, vsz):
            off = ptr + (va - va0)
            d = pe.__data__[off:off+16]
            il = [ins for ins in md.disasm(d, va) if ins.id != 0]
            if not il: return False, ""
            first = "%s %s" % (il[0].mnemonic, il[0].op_str)
            bad = ("fld ", "fstp ", "fxch ", "emms", "mov byte ptr", "mov word ptr")
            ok = not any(first.startswith(b) for b in bad)
            return ok, first
    return False, ""

def in_slice_hole(slots):
    out = []
    for x in sorted(slots):
        if not (LO <= x < HI): continue
        if x in atlas_entries: continue
        if owner(x) is not None: continue   # 只取洞中（真正 atlas 未收录）
        ok, first = first_ok(x)
        out.append((x, ok, first))
    return out

A = in_slice_hole(slots_A)
B = in_slice_hole(slots_B)
setA = set(x for x, ok, f in A if ok)
setB = set(x for x, ok, f in B if ok)

# 输出
rows_out = []
for x, ok, first in A:
    rows_out.append((x, "A" if x in setA else "", "B" if x in setB else "", ok, first,
                     ",".join("%08X" % s for s in sorted(slots_A.__and__({x})) )))
with open(os.path.join(EVID, "vt_direct_entries.tsv"), "w", encoding="utf-8") as f:
    f.write("target\tin_chanA\tin_chanB\tfirst_ok\tfirst_insn\tn_vt_slots_pointing\n")
    for x, ca, cb, ok, first, _ in rows_out:
        # 数该目标被多少 vtable 槽指向（通道A）
        cnt = sum(1 for v in ri["vtables"] for s in v["slots_list"] if int(s,16) == x)
        f.write("%08X\t%s\t%s\t%d\t%s\t%d\n" % (x, ca, cb, ok, first.replace("\t"," "), cnt))

json.dump(dict(lo=hex(LO), hi=hex(HI),
               n_slots_A=len(slots_A), n_slots_B=len(slots_B),
               slots_agree=(slots_A == slots_B),
               n_in_slice_hole_A=len(A), n_in_slice_hole_B=len(B),
               n_true_entry_A=len(setA), n_true_entry_B=len(setB),
               union_true=len(setA | setB), inter_true=len(setA & setB),
               entries=[dict(target=hex(x), first=first, first_ok=ok,
                             in_A=(x in setA), in_B=(x in setB)) for x, ok, first in A]),
          open(os.path.join(WORK, "vt_direct.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("slots_A=%d slots_B=%d agree=%s" % (len(slots_A), len(slots_B), slots_A == slots_B))
print("in-slice-hole A=%d B=%d" % (len(A), len(B)))
print("vtable直指未收录真入口 A=%d B=%d union=%d inter=%d" % (len(setA), len(setB), len(setA|setB), len(setA&setB)))
for x, ok, first in A:
    print("  %08X ok=%d A=%d B=%d %s" % (x, ok, x in setA, x in setB, first))
