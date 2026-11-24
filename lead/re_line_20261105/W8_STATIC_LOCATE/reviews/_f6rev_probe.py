# -*- coding: utf-8 -*-
"""F6 独立复核探针（复核员 F6 专用）。只读 gamemd.exe；结果全部打到 stdout，
由 shell 重定向落盘（脚本自身不做任何落盘动作）。

与被复核探针 _w8_f6.py 的差别：本探针自带 PE 解析与重同步线性解码（不复用
ra2tool.Engine 的缓存流），查询集合独立设计，含反例狩猎（邻域交叉核对）。
运行：python -I -X utf8 _f6rev_probe.py > _f6rev_probe_out.txt 2>&1
"""
import hashlib, struct, time, bisect, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
_buf = []
def P(*a):
    _buf.append(" ".join(str(x) for x in a))

t0 = time.time()
raw = open(EXE, "rb").read()
P("SHA256 %s" % hashlib.sha256(raw).hexdigest())
P("SIZE %d" % len(raw))

# ---- 自带 PE 解析（独立于 ra2tool）----
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    nm = raw[tab + i*40: tab+i*40+8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i*40 + 8)
    SEC.append((nm, IB + va, vsz, rp, rsz))
P("IMAGEBASE 0x%X" % IB)
TLO, THI, TB, TSZ = next((s[1], s[1]+s[4], s[3], s[4]) for s in SEC if s[0] == ".text")

def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            o = rp + (va - sva)
            return o if o < rp + rsz else None
    return None
def rd(va, n):
    o = fo(va)
    return raw[o:o+n] if o is not None else b"\x00"*n
def u32(va):
    return struct.unpack_from("<I", rd(va, 4), 0)[0]
def s32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v

# ---- 自带重同步 linear-sweep（G-23 纪律：逐址+1 恢复，防静默截断）----
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True
tb = raw[TB:TB+TSZ]
insns = []
cur, fails = TLO, 0
while cur < THI:
    got = list(md.disasm(tb[cur-TLO: cur-TLO+15], cur))
    if not got:
        cur += 1; fails += 1; continue
    insns.append(got[0]); cur += got[0].size
P("MY DECODE: insns=%d resync=%d cov=%.4f%%" %
  (len(insns), fails, 100.0*sum(i.size for i in insns)/TSZ))

# ---- 单趟普查：绝对全局命中 / 字段命中 / 直接调用表 ----
ABS_SET = {0x887324, 0xB0CE28, 0xB0CE2C, 0xB0CE30, 0xB0CE34, 0x886FA0,
           0x887308, 0x88730C, 0xB0CD60, 0xB0CD64, 0xB0CD68, 0xA8ED6B, 0x8A0094}
FIELD_SET = {0xB0, 0xB4, 0xD64, 0xD68, 0xD74, 0xD78, 0xD80, 0xD84, 0xD88,
             0xD8C, 0xD7D}
abs_hits = {k: [] for k in ABS_SET}
fld_hits = {k: [] for k in FIELD_SET}
CALLS = {}
for ins in insns:
    try:
        ops = ins.operands
    except Exception:
        continue
    if ins.mnemonic == "call" and ops and ops[0].type == 2:
        CALLS.setdefault(ops[0].imm, []).append(ins.address)
    for op in ops:
        if op.type != 3:
            continue
        if op.mem.base == 0 and op.mem.index == 0 and op.mem.disp in ABS_SET:
            abs_hits[op.mem.disp].append(
                (ins.address, "W" if (op.access & 2) else "R", ins.mnemonic, ins.op_str))
        if op.mem.disp in FIELD_SET:
            fld_hits[op.mem.disp].append(
                (ins.address, "W" if (op.access & 2) else "R", ins.mnemonic, ins.op_str))

ref_887324 = sorted(h[0] for h in abs_hits[0x887324])
def near_887324(a, win=3000):
    i = bisect.bisect_left(ref_887324, a - win)
    return i < len(ref_887324) and ref_887324[i] <= a + win

def dump(lo, hi):
    for ins in insns:
        if lo <= ins.address < hi:
            P("%08X  %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
def callers(f):
    return [hex(c) for c in CALLS.get(f, [])]
TAC = (0x6D1C00, 0x6DC500)

# ---- [B] vtable / RTTI ----
P("=" * 78); P("[B] Tactical vtable 0x7F4348 + RTTI")
slots = [u32(0x7F4348 + 4*i) for i in range(31)]
P("slots0-30: %s" % " ".join("%d=0x%08X" % (i, v) for i, v in enumerate(slots)))
P("vtable[5]=0x%08X vtable[8]=0x%08X vtable[23]=0x%08X" % (slots[5], slots[8], slots[23]))
def rtti_name(vt):
    col = u32(vt - 4)
    if not (col & 0x80000000) or col >= 0x900000:
        return None
    td = u32(col + 0x0C)
    b = rd(td + 8, 64)
    return (hex(col), b.split(b"\x00")[0].decode("latin1", "replace"))
P("RTTI vtable 0x7F4348: %s" % (rtti_name(0x7F4348),))
P("RTTI vtable 0x7E85D4: %s" % (rtti_name(0x7E85D4),))

# ---- [C] ctor 全体 ----
P("=" * 78); P("[C] ctor 0x6D1C20 to 0x6D1E30 full")
dump(0x6D1C20, 0x6D1E30)

# ---- [D] 创建点现场 ----
P("=" * 78); P("[D] ctor callers=%s" % callers(0x6D1C20))
for lo, hi, tag in ((0x52C68C, 0x52C6C8, "0x52C694 ctx"), (0x599D78, 0x599D94, "0x599D80 ctx"),
                    (0x6853B0, 0x6853C0, "0x6853B4 ctx"), (0x6875F8, 0x687644, "0x687617 ctx"),
                    (0x6BF846, 0x6BF858, "0x6BF84F ctx")):
    P("-- %s" % tag); dump(lo, hi)

# ---- [E] 0x887324 命中普查 ----
P("=" * 78)
hh = abs_hits[0x887324]
P("REFS 0x887324 total=%d W=%d" % (len(hh), len([h for h in hh if h[1] == "W"])))
for va, rw, mn, ops in hh:
    if rw == "W":
        P("  %08X %s %s %s" % (va, rw, mn, ops))

# ---- [F] 逐帧派发 ----
P("=" * 78); P("[F] MainLogicFrame dispatch site")
dump(0x55D83C, 0x55D84E)
P("0x55D847 inside MainLogicFrame [0x55D360, 0x55DEE0): %s" % (0x55D360 <= 0x55D847 < 0x55DEE0))
P("-- all call [reg+0x5C] sites + whether 0x887324 appears within prior 16B")
for ins in insns:
    if ins.mnemonic != "call":
        continue
    try:
        ops = ins.operands
    except Exception:
        continue
    for op in ops:
        if op.type == 3 and op.mem.disp == 0x5C:
            i = bisect.bisect_left(ref_887324, ins.address + 16 - 16)
            hit = i < len(ref_887324) and ref_887324[i] < ins.address
            P("  %08X call %s  887324_near=%s" % (ins.address, ins.op_str, hit))

# ---- [G] 写者 0x6D8B30 全体 + 除法数值模拟 ----
P("=" * 78); P("[G] writer 0x6D8B30 FULL")
dump(0x6D8B30, 0x6D8C58)
P("callers of 0x6D8B30: %s" % callers(0x6D8B30))
P("callers of 0x5AFB80: n=%d %s" % (len(CALLS.get(0x5AFB80, [])), callers(0x5AFB80)[:12]))
def msvc_div(n, shift, plus):
    prod = s32(0x88888889) * n          # imul
    edx = s32(prod >> 32)               # 高32位（算术）
    edx = s32(edx + n)                  # add edx, n（32位回卷）
    edx = edx >> shift                  # sar
    mask = (edx & 0xFFFFFFFF) >> 31     # shr ecx,0x1F
    return edx + mask + plus            # lea [edx+ecx+plus]
P("-- numeric sim: D88=width/60+2, D8C=height/15+4 ?")
bad = 0
for w, h in ((320,240),(512,384),(10,10),(640,480),(800,600),(1024,768),(1152,864),
             (1280,1024),(1600,1200),(1920,1080),(2048,1536)):
    x, y = msvc_div(w, 5, 2), msvc_div(h, 3, 4)
    ok = (x == w // 60 + 2) and (y == h // 15 + 4)
    bad += (not ok)
    P("   w=%4d h=%4d -> D88=%3d (exp %3d) D8C=%3d (exp %3d) %s"
      % (w, h, x, w//60+2, y, h//15+4, "OK" if ok else "MISMATCH"))
P("SIM mismatches=%d" % bad)

# ---- [H] 读方 ----
P("=" * 78); P("[H1] 0x6D8AE0 cell-containment full")
dump(0x6D8AE0, 0x6D8B26)
P("[H2] IsVisible 0x6D2140 prologue/reads/bounds")
dump(0x6D2140, 0x6D2160)
dump(0x6D21F0, 0x6D2274)
cc = CALLS.get(0x6D2140, [])
P("direct callers of 0x6D2140: %d" % len(cc))
P("  first10: %s" % [hex(a) for a in cc[:10]])
P("  in-Tactical-family: %d" % len([a for a in cc if TAC[0] <= a < TAC[1]]))
P("-- chain head 0x5F4B40 to 0x5F4B70")
dump(0x5F4B40, 0x5F4B70)

# ---- [I] AI 0x6D2540 ----
P("=" * 78); P("[I] AI 0x6D2540 key parts")
dump(0x6D2540, 0x6D2570)
dump(0x6D2650, 0x6D2690)
dump(0x6D2750, 0x6D2790)
P("callers of 0x6D2540 (E8): %s" % callers(0x6D2540))

# ---- [J] 字段普查 + 反例狩猎 ----
P("=" * 78); P("[J] field census (my own single pass) + counterexample hunt")
for off in (0xB0, 0xB4, 0xD64, 0xD68, 0xD74, 0xD78, 0xD80, 0xD84, 0xD88, 0xD8C, 0xD7D):
    hs = fld_hits[off]
    ws = [h for h in hs if h[1] == "W"]
    tac = [h for h in ws if TAC[0] <= h[0] < TAC[1]]
    P("field +0x%-4X R=%4d W=%4d TacW=%d -> %s"
      % (off, len(hs)-len(ws), len(ws), len(tac), [hex(h[0]) for h in tac]))
    out = [h for h in ws if not (TAC[0] <= h[0] < TAC[1])]
    susp = [(hex(h[0]), h[3]) for h in out if near_887324(h[0])]
    P("   nonTacW=%d  with_887324_within_3000B: %s" % (len(out), susp if susp else "none"))
P("-- 6 suspects in Tactical domain: verify [esp] stack-slot claim")
for a in (0x6D744B, 0x6DB7D9, 0x6D42E2, 0x6D434B, 0x6D7460, 0x6DB7E9):
    dump(a - 6, a + 7)

# ---- [K] 全局普查 ----
P("=" * 78); P("[K] globals census")
for g in (0xB0CE28, 0xB0CE2C, 0xB0CE30, 0xB0CE34, 0xB0CD60, 0xB0CD64, 0xB0CD68,
          0x886FA0, 0x887308, 0x88730C, 0xA8ED6B, 0x8A0094):
    hh2 = abs_hits[g]
    ws2 = [(hex(v), m, o) for v, rw, m, o in hh2 if rw == "W"]
    P("0x%08X refs=%3d W=%2d  %s" % (g, len(hh2), len(ws2), ws2))
P("-- 0x6D1A40 to 0x6D1A58 (zero-init of 0xB0CE28-34)"); dump(0x6D1A40, 0x6D1A58)
P("-- ctx of 0x886FA0 writer 0x40DA2C"); dump(0x40DA10, 0x40DA40)
P("-- ctx of 0x886FA0 writer 0x4A8987"); dump(0x4A8970, 0x4A89C4)
P("callers of 0x6D5F60: %s" % callers(0x6D5F60)
  )
P("callers of 0x6D6070: n=%d" % len(CALLS.get(0x6D6070, [])))
P("callers of 0x6D8640: n=%d %s" % (len(CALLS.get(0x6D8640, [])),
   [hex(a) for a in CALLS.get(0x6D8640, [])]))
P("callers of 0x6DC470: %s" % callers(0x6DC470))
P("-- dtor 0x6DC470 to 0x6DC4A8"); dump(0x6DC470, 0x6DC4A8)

# ---- [L] Bink 排除复核 ----
P("=" * 78); P("[L] Bink 0x432750 to 0x432A60 exclusion recheck")
bad_ref = [hex(h[0]) for h in abs_hits[0x887324] if 0x432750 <= h[0] < 0x432A60]
bad_cal = [hex(a) for a in CALLS.get(0x6D2140, []) + CALLS.get(0x6D8B30, [])
           if 0x432750 <= a < 0x432A60]
P("refs 0x887324 in fn: %s ; calls IsVisible/0x6D8B30 in fn: %s" % (bad_ref, bad_cal))
P("callers of 0x432750: %s" % callers(0x432750))
P("-- host of other caller 0x4326B3"); dump(0x432690, 0x4326C4)
P("-- 4-dword RECT write site"); dump(0x432A16, 0x432A50)
P("-- tail"); dump(0x432A50, 0x432A62)

# ---- [M] DSurface ctor ----
P("=" * 78); P("[M] DSurface ctor 0x4BA5A0")
dump(0x4BA5A0, 0x4BA5DC)
dump(0x4BA640, 0x4BA6A0)
vtw = [hex(i.address) for i in insns
       if i.mnemonic == "mov" and len(i.bytes) >= 10
       and i.bytes[0:3] in (b"\xc7\x06", b"\xc7\x46", b"\xc7\x40", b"\xc7\x43", b"\xc7\x47")
       and i.bytes[-4:] == struct.pack("<I", 0x7E85D4)]
P("mov [reg],0x7E85D4 sites: %s" % vtw)

# ---- [P] 0x54AD70 to 0x54AE00（+0xD80 家族间接读登记点）----
P("=" * 78); P("[P] 0x54AD70 to 0x54AE00")
dump(0x54AD70, 0x54AE00)

# ---- [Q] 同步链 ----
P("=" * 78); P("[Q] sync chain 0x6D5F60 to 0x6D5FFA"); dump(0x6D5F60, 0x6D5FFA)
P("-- jump tail 0x6D613F to 0x6D616C"); dump(0x6D613F, 0x6D616C)
P("-- vtable[5] body tail 0x6DBDBB to 0x6DBDF0"); dump(0x6DBDBB, 0x6DBDF0)

P("=" * 78)
P("ELAPSED %.1fs" % (time.time() - t0))
sys.stdout.write("\n".join(_buf) + "\n")
