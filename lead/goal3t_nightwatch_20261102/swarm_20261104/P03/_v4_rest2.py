# -*- coding: utf-8 -*-
"""V-P03 核验探针 4：push 间接路径 / measure 窗 / 空桩+IAT+格式串 / W10 死代码 / 杂项收尾"""
import sys, struct
from collections import defaultdict, Counter
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
out = []
def P(*a):
    s = " ".join(str(x) for x in a)
    out.append(s); print(s, flush=True)

S = eng.stream
P("[coverage] %.2f%% / %d / %d" % eng.coverage)

def text_call_sites(target):
    tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
    res = []
    i = tb.find(b"\xe8")
    while i >= 0:
        va = eng.TLO + i
        if i + 5 <= len(tb):
            rel = struct.unpack_from("<i", tb, i + 1)[0]
            if va + 5 + rel == target: res.append(va)
        i = tb.find(b"\xe8", i + 1)
    return res

def cstr(va, n=64):
    b = eng.rd(va, n)
    z = b.find(b"\0")
    return b[:z if z >= 0 else n]

# ================= C. push 0xA8ED84 间接路径 =================
P("")
P("===== [C] push 0xA8ED84 间接写路径 =====")
tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
pat = bytes.fromhex("68 84 ed a8 00".replace(" ", ""))
pushes, i = [], tb.find(pat)
while i >= 0:
    pushes.append(eng.TLO + i); i = tb.find(pat, i + 1)
P("[push 0xA8ED84 sites in .text] = %s" % [hex(v) for v in pushes])

for base, end, tag in ((0x67F7E0, 0x67F840, "hostA(0x67F7E0)"), (0x67F9C0, 0x67FA30, "hostB(0x67F9C0)")):
    P("[%s context]" % tag)
    for a, b, m, o in eng.disasm(base, end - base):
        P("    0x%08x  %-18s %s %s" % (a, b, m, o))

hits = eng.disp_hits(0xA8ED84)
SER = [0xA8ED78, 0xA83D4C, 0xA8ED84, 0x89EA40, 0x89EC28, 0x89ECC0, 0xA8E3A8, 0xB07784]
for host_lo, host_hi, tag in ((0x67F7E0, 0x67F9C0, "hostA"), (0x67F9C0, 0x67FD80, "hostB")):
    row = {}
    for g in SER:
        hs = [h for h in eng.disp_hits(g) if host_lo <= h[0] < host_hi]
        row[hex(g)] = "%dW/%dR" % (sum(1 for x in hs if x[1] == "W"), sum(1 for x in hs if x[1] == "R"))
    P("[serial globals in %s] %s" % (tag, row))

# 错误路径 jl
P("[hostA err-path @0x67F9B8 region]")
for a, b, m, o in eng.disasm(0x67F9B0, 0x10):
    P("    0x%08x  %s %s %s" % (a, b, m, o))
P("[hostB err-path @0x67FD11 region]")
for a, b, m, o in eng.disasm(0x67FD08, 0x10):
    P("    0x%08x  %s %s %s" % (a, b, m, o))

# 调用链
P("[callers 0x67F7E0] %s" % [hex(c) for c in text_call_sites(0x67F7E0)])
P("[callers 0x67D300] %s" % [hex(c) for c in text_call_sites(0x67D300)])
P("[callers 0x67F9C0] %s" % [hex(c) for c in text_call_sites(0x67F9C0)])
P("[callers 0x67E730] %s" % [hex(c) for c in text_call_sites(0x67E730)])
# 0x6CF240 调用（hostB 校验）
P("[call 0x6CF240 sites in hostB] %s" % [hex(c) for c in text_call_sites(0x6CF240) if 0x67F9C0 <= c < 0x67FD80])

# hostB 读 [0xA8ED78] 与校验的次序
P("[hostB 0x67F9D0..0x67FA30]")
for a, b, m, o in eng.disasm(0x67F9D0, 0x60):
    P("    0x%08x  %-18s %s %s" % (a, b, m, o))

# ================= D. measure 窗 =================
P("")
P("===== [D] measure 窗 dispatcher 0x48CCC0 =====")
P("[0x48CCC0..0x48CEC0]")
for a, b, m, o in eng.disasm(0x48CCC0, 0x200):
    P("    0x%08x  %-18s %s %s" % (a, b, m, o))
P("[fps string @0x81D514] %r" % cstr(0x81D514))
P("[fps string @0x81D53C] %r" % cstr(0x81D53C))
P("[fps string @0x81D55C] %r" % cstr(0x81D55C))

hits = eng.disp_hits(0xA8ED84)
P("[0x55CFD0 head]")
for a, b, m, o in eng.disasm(0x55CFD0, 0x20):
    P("    0x%08x  %-18s %s %s" % (a, b, m, o))
P("[0x55CFD0 func 0xA8ED84 hits] %s" %
  [(hex(a), d, m) for a, d, m, _ in hits if 0x55CFD0 <= a < 0x55D360])

# 四旗标写者
for f in (0xA83D49, 0xA8ECD0, 0x8B41C0, 0xA83D48):
    hs = eng.disp_hits(f)
    ws = [h for h in hs if h[1] == "W"]
    P("[flag 0x%x] refs=%d W=%d %s" % (f, len(hs), len(ws), [(hex(a), m, o) for a, d, m, o in ws]))

# 0x55CFD0 四变体块
P("[0x55CFD0 four blocks]")
for blk in (0x55D123, 0x55D1B1, 0x55D219, 0x55D25C):
    P("  block @0x%x:" % blk)
    for a, b, m, o in eng.disasm(blk - 0x10, 0x30):
        P("    0x%08x  %-18s %s %s" % (a, b, m, o))

# 转换触发函数 → 加载器调用
for fn in (0x685670, 0x685DC0, 0x6863E0, 0x686570):
    cs_ = [c for c in text_call_sites(0x683AB0) if fn <= c < fn + 0x400]
    P("[0x%x -> call 0x683AB0 sites] %s" % (fn, [hex(c) for c in cs_]))
P("[Disconnect_Gracefully search]")
b85 = eng.raw.find(b"Disconnect_Gracefully")
P("   file off=%s" % hex(b85) if b85 >= 0 else "   not found")
# 0x685670/0x685DC0/0x6863E0 被谁调
for fn in (0x685670, 0x685DC0, 0x6863E0, 0x686570):
    P("[callers of 0x%x] %s" % (fn, [hex(c) for c in text_call_sites(fn)]))

# ================= E. 空桩 + IAT + 格式串 =================
P("")
P("===== [E] 空桩 / IAT / 格式串 =====")
P("[0x4068E0] %s" % eng.rd(0x4068E0, 16).hex())
P("[0x4068F0] %s" % eng.rd(0x4068F0, 4).hex())
P("[0x6B8B10] %s" % eng.rd(0x6B8B10, 16).hex())
for va in (0x7E11F0, 0x7E1530, 0x7E14A4):
    P("[IAT 0x%x] = %s" % (va, eng.resolve_iat(va)))
P("[u32 0x7E4C30] = 0x%x  sec=%s" % (eng.u32(0x7E4C30), "see map"))
for nm, sva, vsz, rp, rsz in eng.SEC:
    if sva <= 0x7E4C30 < sva + vsz:
        P("   0x7E4C30 in section %s [0x%x,0x%x)" % (nm, sva, sva + vsz))
P("[u32 0xA8E2E4] = %d" % eng.u32(0xA8E2E4))
h2 = eng.disp_hits(0xA8E2E4)
P("[0xA8E2E4 hits] total=%d W=%d %s" % (len(h2), sum(1 for x in h2 if x[1]=="W"), [(hex(a),d,m) for a,d,m,_ in h2]))

hitsB = eng.disp_hits(0xA8B24C)
wsB = [h for h in hitsB if h[1] == "W"]
P("[0xA8B24C] refs=%d W=%d" % (len(hitsB), len(wsB)))
for a, d, m, o in wsB:
    # 读出 mov dword [0xA8B24C], imm 的立即数
    bts = eng.rd(a, 10)
    imm = None
    if bts[:2] == b"\xc7\x05":
        imm = struct.unpack_from("<I", bts, 6)[0]
    P("   W 0x%08x %s %s imm=%s" % (a, m, o, hex(imm) if imm is not None else "?"))

hitsC = eng.disp_hits(0xB07784)
wsC = [h for h in hitsC if h[1] == "W"]
P("[0xB07784] refs=%d W=%d %s" % (len(hitsC), len(wsC), [(hex(a), m, o) for a, d, m, o in wsC]))

hitsD = eng.disp_hits(0x89E3A0)
wsD = [h for h in hitsD if h[1] == "W"]
P("[0x89E3A0] refs=%d W=%d %s" % (len(hitsD), len(wsD), [(hex(a), m, o) for a, d, m, o in wsD]))

for va in (0x82CC04, 0x82CBF4, 0x82C9A4, 0x831A60, 0x83DA88, 0x82C1BC, 0x84C540, 0x820C54):
    P("[str 0x%x] %r" % (va, cstr(va, 48)))

# 0x4790E0 行为
P("[0x4790E0 head]")
for a, b, m, o in eng.disasm(0x4790E0, 0x40):
    P("    0x%08x  %-18s %s %s" % (a, b, m, o))

# ================= F. W10 死代码 =================
P("")
P("===== [F] W10 宿主 0x7970D0 死代码复核 =====")
refs = []
for off, va in file_dword_search(0x7970D0):
    refs.append((hex(off), hex(va)))
P("[file-wide dword 0x7970D0 occurrences] %d %s" % (len(refs), refs[:20]))
# E8/E9/0F8x 入边
tbx = eng.raw[eng.TB: eng.TB + eng.TSZ]
ins_edges = []
for i in range(len(tbx) - 6):
    va = eng.TLO + i
    if tbx[i] == 0xE8 and i + 5 <= len(tbx):
        rel = struct.unpack_from("<i", tbx, i + 1)[0]
        if 0x7970D0 <= va + 5 + rel < 0x7975AC: ins_edges.append((hex(va), "E8"))
    if tbx[i] == 0xE9 and i + 5 <= len(tbx):
        rel = struct.unpack_from("<i", tbx, i + 1)[0]
        if 0x7970D0 <= va + 5 + rel < 0x7975AC: ins_edges.append((hex(va), "E9"))
    if tbx[i] == 0x0F and i + 6 <= len(tbx) and 0x80 <= tbx[i+1] <= 0x8F:
        rel = struct.unpack_from("<i", tbx, i + 2)[0]
        if 0x7970D0 <= va + 6 + rel < 0x7975AC: ins_edges.append((hex(va), "0F8x"))
P("[static in-edges (E8/E9/0F8x) into [0x7970D0,0x7975AC)] from .text] = %d %s" % (len(ins_edges), ins_edges[:10]))
# 相对 jmp 短跳 EB/0F8x 已含 0F8x；短跳 EB cb
short_edges = []
for i in range(len(tbx) - 2):
    va = eng.TLO + i
    if tbx[i] == 0xEB:
        rel = struct.unpack_from("<b", tbx, i + 1)[0]
        if 0x7970D0 <= va + 2 + rel < 0x7975AC: short_edges.append(hex(va))
P("[EB short-jmp into range] = %d %s" % (len(short_edges), short_edges[:10]))
# W10 宿主内跳转表
P("[W10 host jump-table refs]")
hitsJT = eng.disp_hits_field(0x7975AC) + eng.disp_hits_field(0x7975C4)
P("   %s" % [(hex(a), d, m, o) for a, d, m, o in hitsJT])
P("[jmp [reg*4+imm] inside host] %s" %
  [(hex(i.address), i.mnemonic, i.op_str) for i in S if 0x7970D0 <= i.address < 0x7975AC and i.mnemonic == "jmp" and "[" in i.op_str])
P("[W10 host head] %s" % eng.rd(0x7970D0, 8).hex())
P("[W10 host rets] %s" % [hex(i.address) for i in S if 0x7970D0 <= i.address < 0x7975AC and i.mnemonic.startswith("ret")])

# ================= H. MLF 尾部旗标链字节级对齐复核 =================
P("")
P("===== [H] MLF 尾部 0x55DE40..0x55DE75 原始字节与两种对齐 =====")
raw = eng.rd(0x55DE40, 0x38)
P("[raw 0x55DE40..0x55DE78] %s" % raw.hex())
P("[stream-boundary disasm (engine sync)]")
for a, b, m, o in eng.disasm(0x55DE40, 0x38):
    P("    0x%08x  %-20s %s %s" % (a, b, m, o))
P("[alt alignment: start 0x55DE5F]")
for a, b, m, o in eng.disasm(0x55DE5F, 0x1A):
    P("    0x%08x  %-20s %s %s" % (a, b, m, o))
# 引擎流里 0x55DE40..0x55DE60 的边界
P("[engine stream instructions 0x55DE00..0x55DE60]")
for i in S:
    if 0x55DE00 <= i.address < 0x55DE60:
        P("    0x%08x  %-16s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
# 四旗标在 MLF 内的 R 命中（含 jne 0x55DEC8 邻接检查）
hits = eng.disp_hits(0xA8ED84)
for f in (0xA83D49, 0xA8ECD0, 0x8B41C0, 0xA83D48):
    hs = [(hex(a), m, o) for a, d, m, o in eng.disp_hits(f) if 0x55D360 <= a < 0x55DEE0]
    P("[flag 0x%x in MLF] %s" % (f, hs))
# jne 0x55DEC8 的全部来源
P("[all jumps to 0x55DEC8 in .text]")
tb2 = eng.raw[eng.TB: eng.TB + eng.TSZ]
for i in range(len(tb2) - 2):
    va = eng.TLO + i
    if tb2[i] in (0xEB, 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F):
        rel = struct.unpack_from("<b", tb2, i + 1)[0]
        if va + 2 + rel == 0x55DEC8: P("    short 0x%08x (op %02x)" % (va, tb2[i]))
    if tb2[i] == 0x0F and i + 6 <= len(tb2) and 0x80 <= tb2[i+1] <= 0x8F:
        rel = struct.unpack_from("<i", tb2, i + 2)[0]
        if va + 6 + rel == 0x55DEC8: P("    near 0x%08x (0f8x)" % va)

# ================= I. 0xA8ED84 全文件 dword 普查（.text 之外） =================
P("")
P("===== [I] 0xA8ED84 地址值的全文件出现（指针表别名风险） =====")
patv = struct.pack("<I", 0xA8ED84)
occ, i2 = [], eng.raw.find(patv)
while i2 >= 0:
    occ.append(i2); i2 = eng.raw.find(patv, i2 + 1)
def fo_of(off):
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if rp <= off < rp + rsz:
            return nm, sva + (off - rp)
    return "?", 0
tblo, tbhi = eng.TB, eng.TB + eng.TSZ
outside = []
for off in occ:
    nm, va = fo_of(off)
    if nm == ".text" and tblo <= off < tbhi:
        continue
    outside.append((hex(off), nm, hex(va)))
P("[file-wide 0xA8ED84 occurrences] total=%d ; outside .text=%d" % (len(occ), len(outside)))
for o in outside[:20]:
    P("   %s" % (o,))

# ================= G. 杂项 =================
P("")
P("===== [G] 杂项 =====")
hitsF = eng.disp_hits(0xA8ED80)
P("[focus 0xA8ED80] refs=%d W=%s" % (len(hitsF), [(hex(a), m, o) for a, d, m, o in hitsF if d == "W"]))
hitsG = eng.disp_hits(0xA8B230)
P("[GameLogic 0xA8B230] refs=%d W=%s" % (len(hitsG), [(hex(a), m, o) for a, d, m, o in hitsG if d == "W"]))
# init 内 [0xA8B24C]=2 与 INGAME
P("[init 0x52D9C0..0x52DA20]")
for a, b, m, o in eng.disasm(0x52D9C0, 0x60):
    P("    0x%08x  %-18s %s %s" % (a, b, m, o))

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/P03/_v4_out_partCDEFG.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("PARTCDEFG SAVED")
