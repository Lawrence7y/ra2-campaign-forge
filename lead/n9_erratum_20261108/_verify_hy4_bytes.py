# -*- coding: utf-8 -*-
# _verify_hy4_bytes.py — 独立复核②：不依赖 capstone 的原始字节扫描 + call 目标复算 + 全仓检索
# 零真机 / 零采样 / 纯磁盘只读。写域: lead/n9_erratum_20261108/，前缀 _verify_
import struct, os, hashlib

ROOT = r"D:\Project\ra2-campaign-forge"
def P(rel): return os.path.join(ROOT, rel.replace("/", os.sep))

data = open(P("ra2youli/gamemd.exe"), "rb").read()
e = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, e+6)[0]
optsize = struct.unpack_from("<H", data, e+20)[0]
imagebase = struct.unpack_from("<I", data, e+24+28)[0]
sec0 = e + 24 + optsize
secs = []
for i in range(nsec):
    o = sec0 + 40*i
    name = data[o:o+8].rstrip(b"\0").decode("ascii","replace")
    vsz, va, rsz, raw = struct.unpack_from("<IIII", data, o+8)
    secs.append((name, va, vsz, rsz, raw))

def va2off(va):
    rva = va - imagebase
    for nm, sva, vsz, rsz, raw in secs:
        if sva <= rva < sva + max(vsz, rsz, 1):
            d = rva - sva
            return (raw + d) if d < rsz else None
    return None

def off2va(off):
    for nm, sva, vsz, rsz, raw in secs:
        if raw <= off < raw + rsz:
            return imagebase + sva + (off - raw)
    return None

# ---- 1. 原始字节扫描：所有对 [0xB0CD48] 的 disp32 引用 ----
print("== 原始字节扫描：4 字节序列 48 CD B0 00（= disp32 0x00B0CD48）的所有出现 ==")
pat = b"\x48\xCD\xB0\x00"
pos = 0
hits = []
while True:
    i = data.find(pat, pos)
    if i < 0: break
    hits.append(i)
    pos = i + 1
print("全文件命中数 =", len(hits))
for off in hits:
    va = off2va(off)
    # 指令起点 = disp32 起点 - 2（ModRM+opcode）或 -1（仅 opcode 情形另判）
    op2 = data[off-2:off] if off >= 2 else b""
    op1 = data[off-1:off] if off >= 1 else b""
    inst_va = va - 2 if va is not None else None
    tag = ""
    if op2 == b"\xDC\x0D": tag = "fmul qword [disp32]  (DC 0D = fmul st(0),qword)"
    elif op2 == b"\xDD\x1D": tag = "fstp qword [disp32]  (DD 1D = fstp qword)"
    elif op2 == b"\xDC\x05": tag = "fadd qword [disp32]"
    elif op2 == b"\xDD\x05": tag = "fld  qword [disp32]"
    else: tag = "前置2字节=%s 前置1字节=%s" % (op2.hex(), op1.hex())
    print("  off=0x%06X VA=0x%08X 指令VA=0x%08X pre2=%s -> %s"
          % (off, va if va else 0, inst_va if inst_va else 0, op2.hex(), tag))

# ---- 2. 与 _sc_scan_out.txt:73-84 的 12 条清单对照 ----
print("\n== 与存档 12 条清单对照 ==")
scanL = open(P("lead/spec_static_closure_20261108/_sc_scan_out.txt"), "r", encoding="utf-8").read().splitlines()
archived = []
for i in range(72, 84):  # 1-based 73..84
    L = scanL[i]
    archived.append(L.strip())
    print("  _scan:%d | %s" % (i+1, L.strip()))
print("存档条数 =", len(archived))

# ---- 3. 唯一写者编码 + call 0x4CACB0 目标复算 ----
print("\n== 写者 0x6D1BDD 与 call 目标复算 ==")
o = va2off(0x006D1BDD)
print("  0x6D1BDD off=0x%X bytes=%s" % (o, data[o:o+6].hex()))
o2 = va2off(0x006D1BCF)
rel = struct.unpack_from("<i", data, o2+1)[0]
tgt = (0x006D1BCF + 5 + rel) & 0xFFFFFFFF
print("  0x006D1BCF E8 rel32=0x%08X (%d) -> target=0x%08X  %s"
      % (rel & 0xFFFFFFFF, rel, tgt, "OK(=0x4CACB0)" if tgt == 0x004CACB0 else "MISMATCH"))

# ---- 4. lead 域 *.md 检索（与勘误 downstreamImpact 作用域一致；全仓 walk 因 >120s 已放弃，改用 lead 有界版）----
print("\n== lead 域 *.md 检索 ==")
keys = ["静态 u64 窗口读", "均静态可闭", "B0CD48"]
res = {k: [] for k in keys}
for dp, dns, fns in os.walk(P("lead")):
    for fn in fns:
        if not fn.lower().endswith(".md"): continue
        full = os.path.join(dp, fn)
        rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
        try: lines = open(full, "r", encoding="utf-8", errors="replace").read().splitlines()
        except Exception: continue
        for i, L in enumerate(lines, 1):
            for k in keys:
                if k in L: res[k].append((rel, i, L.strip()[:160]))
for k in keys:
    print("-- KEY %r 全仓命中 %d 行 --" % (k, len(res[k])))
    files = sorted(set(r for r,_,_ in res[k]))
    for f in files:
        cnt = sum(1 for r,_,_ in res[k] if r == f)
        print("   %3d 行  %s" % (cnt, f))
