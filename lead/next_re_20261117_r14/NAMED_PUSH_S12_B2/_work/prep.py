# -*- coding: utf-8 -*-
"""材料自校验 + 主虚表钉死（本批跨 4 类）。COL 在 .rdata，TD 在 .data —— 必须跨段 va_read。"""
import hashlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

print("=== 材料 ===")
h = hashlib.sha256(open(EXE, "rb").read()).hexdigest().upper()
EXP = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
print("sha256 =", h, "MATCH =", h == EXP)
print("ImageBase = %08X  .text=[%08X,%08X)" % (IB, TEXT_LO, TEXT_HI))
for nm, v0, vs, d in SECS:
    print("  %-8s %08X +%X" % (nm, v0, vs))
print("atlas funcs =", len(ATLAS))

# ---- 全镜像扫描：COL (sig==0, td 指向 .?AV 名串) ----
cols = {}
for nm, v0, vs, data in SECS:
    if nm != ".rdata":
        continue
    for off in range(0, len(data) - 0x18, 4):
        va = v0 + off
        if u32(va) != 0:
            continue
        td = u32(va + 0xC)
        if not td or va_sec(td) is None:
            continue
        name = read_cstr(td + 8, 200)
        if not name.startswith(".?AV"):
            continue
        cols.setdefault(name, []).append(dict(col=va, td=td))

TARGETS = ("BuildingClass", "BuildingTypeClass", "CaptureManagerClass", "FactoryClass")
print("\n=== 目标类的全部 COL / vtable base ===")
for nm in sorted(cols):
    if not any(k in nm for k in TARGETS):
        continue
    if "Vector" in nm:
        continue
    print("\n-- %s" % nm)
    for ci in cols[nm]:
        col = ci["col"]
        vbs = []
        for v_sec, v0, vs, data in SECS:
            if v_sec != ".rdata":
                continue
            for off in range(0, len(data) - 8, 4):
                va2 = v0 + off
                if u32(va2) != col:
                    continue
                vb = va2 + 4
                p0 = u32(vb)
                if p0 and in_text(p0):
                    vbs.append((vb, p0))
        for vb, p0 in vbs:
            n = 0
            while n < 900:
                p = u32(vb + 4 * n)
                if not p or not in_text(p):
                    break
                n += 1
            print("   COL %08X TD %08X  vt %08X  slot0 %08X  nslots %d"
                  % (col, ci["td"], vb, p0, n))
