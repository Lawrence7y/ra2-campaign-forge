# -*- coding: utf-8 -*-
"""F8 独立复核探针（复核员 F8-review 专用）。

与被复核探针 _w8_f8.py 的独立性：不导入 ra2tool.Engine，手动解析 PE 头 +
直接用 capstone 5.0.7 线性解码 .text，全部门槛判据自行实现。
零真机、只读 gamemd.exe；结果全部打到 stdout，由 shell 重定向落盘（脚本不写文件）。

复核点：
  R0  SHA256/字节数/ImageBase/段表（含 .detour 特征）
  R1  全文件（全部段）裸 E8/E9 -> 0x5F4B10 / 0x6D2140 上界扫描（补 .detour 漏扫）
  R2  .text 线性解码：call/jmp imm 两目标计数（对 3 / 139 / 0）
  R3  渲染簇 [0x6D8DB0,0x6DA1FC)：1603/0 调用/0 绝对写/19 处 inc-dec 全寄存器/0 内存计数
  R4  宽域 [0x6D3D10,0x6DA200)：内存 inc/dec/add/sub 分类（对 21 全 STACK）
  R5  反例猎杀 A：139 个 IsVisible 调用点，前向 48 条 + 每个 jcc 分支目标 16 条
      内的内存计数操作（补 F8「仅 8 条」窗口 + 不跟分支的缺口）
  R6  反例猎杀 B：全 .text 绝对内存 inc/dec/add/sub 普查（ABS 形态计数器全集）
      + xadd 普查 + 立即数 dword 0x5F4B10/0x6D2140 出现点
  R7  两步虚调度（mov r,[r+0x104] 后紧跟 call/jmp reg）普查
  R8  vtable 槽 65 字节验证（0x7E3458/0x7F5D74/0x7F641C）+ 0x5F4B10 的 .rdata 引用数
  R9  容器寻址复核：0x8A0364/0x8A0370 绝对 vs [reg+disp] 形态普查（攻「绝对 VA」写法）
      + 0xB0CE88/0xB0CE30/0xB0CE34/0x887324 位移普查（对 27/14/14）
  R10 IsVisible 边界常量与视口字段字节复核

运行：python -I -X utf8 _f8rev_probe.py > _f8rev_out.txt 2>&1
"""
import sys, os, struct, hashlib, time
from collections import Counter
import capstone
from capstone.x86 import (X86_OP_MEM, X86_OP_IMM, X86_OP_REG,
                          X86_REG_ESP, X86_REG_EBP)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EXE = "D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe"
OUT = []
def P(*a):
    OUT.append(" ".join(str(x) for x in a))

t0 = time.time()
data = open(EXE, "rb").read()

# ---------------- R0 ----------------
P("=== R0 SELF PROOF ===")
P("R0 RUN_TIMESTAMP", time.strftime("%Y-%m-%d %H:%M:%S"))
P("R0 SHA256", hashlib.sha256(data).hexdigest())
P("R0 BYTES", len(data))

e_lfanew, = struct.unpack_from("<I", data, 0x3C)
assert data[e_lfanew:e_lfanew+4] == b"PE\0\0", "PE sig"
coff = e_lfanew + 4
nsec, = struct.unpack_from("<H", data, coff + 2)
optsize, = struct.unpack_from("<H", data, coff + 16)
opt = coff + 20
magic, = struct.unpack_from("<H", data, opt)
assert magic == 0x10B, "PE32"
IB, = struct.unpack_from("<I", data, opt + 28)
P("R0 IMAGEBASE", hex(IB))
secs = []
so = opt + optsize
for i in range(nsec):
    b = data[so + i*40: so + i*40 + 40]
    name = b[:8].rstrip(b"\0").decode("latin1")
    vsize, vaddr, rawsz, rawptr = struct.unpack_from("<IIII", b, 8)
    chars, = struct.unpack_from("<I", b, 36)
    secs.append((name, IB + vaddr, vsize, rawptr, rawsz, chars))
    P("  SEC %-8s va=%s vsize=%s raw=%s rawsz=%s chars=%s exec=%s" %
      (name, hex(IB+vaddr), hex(vsize), hex(rawptr), hex(rawsz), hex(chars),
       bool(chars & 0x20000000)))

def va2off(va):
    for nm, v, vsz, rp, rs, ch in secs:
        if v <= va < v + rs:
            return rp + (va - v)
    return None

# ---------------- R1 whole-file E8/E9 ----------------
P("")
P("=== R1 WHOLE-FILE raw E8/E9 -> targets (all sections incl .detour/.rsrc/.data) ===")
TGT = {0x5F4B10: "DrawIfVisible", 0x6D2140: "IsVisible"}
hits = {t: [] for t in TGT}
for nm, va, vsz, rp, rs, ch in secs:
    if rs == 0:
        continue
    blob = data[rp:rp+rs]
    for i in range(len(blob) - 5):
        b0 = blob[i]
        if b0 == 0xE8 or b0 == 0xE9:
            rel, = struct.unpack_from("<i", blob, i+1)
            t = va + i + 5 + rel
            if t in TGT:
                hits[t].append((nm, hex(va+i), "E8" if b0 == 0xE8 else "E9"))
for t in (0x5F4B10, 0x6D2140):
    P("R1 %s: %d %s" % (TGT[t], len(hits[t]), hits[t]))

# ---------------- R2 linear sweep of .text ----------------
P("")
P("=== R2 OWN LINEAR SWEEP .text (capstone %s, detail on) ===" % capstone.__version__)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
TLO = next(s[1] for s in secs if s[0] == ".text")
TSZ = next(s[4] for s in secs if s[0] == ".text")
TB = next(s[3] for s in secs if s[0] == ".text")
tb = data[TB:TB+TSZ]
stream = []
cur = 0
fails = 0
while cur < len(tb):
    got = list(md.disasm(tb[cur:cur+15], TLO + cur))
    if got:
        stream.extend(got)
        last = got[-1]
        cur = (last.address - TLO) + last.size
    else:
        fails += 1
        cur += 1
P("R2 INSNS", len(stream), "resync_steps", fails, "elapsed %.1fs" % (time.time()-t0))
idx = {i.address: k for k, i in enumerate(stream)}

def call_imm(i):
    if i.mnemonic in ("call", "jmp") and i.operands and i.operands[0].type == X86_OP_IMM:
        return i.operands[0].imm
    return None

def mem_class(m):
    if m.base == 0 and m.index == 0:
        return "ABS"
    if m.base == X86_REG_ESP:
        return "STACK"
    if m.base == X86_REG_EBP:
        return "EBP"
    return "REG+DISP"

def mem_counter_flags(i):
    """(mnem, op_str, class) if inc/dec/add/sub with mem FIRST operand."""
    if i.mnemonic in ("inc", "dec", "add", "sub") and i.operands:
        op = i.operands[0]
        if op.type == X86_OP_MEM:
            return (i.mnemonic, i.op_str, mem_class(op.mem))
    return None

DRAWHIV, ISVIS = 0x5F4B10, 0x6D2140

dc  = [i.address for i in stream if i.mnemonic == "call" and call_imm(i) == DRAWHIV]
jc  = [i.address for i in stream if i.mnemonic == "jmp" and call_imm(i) == DRAWHIV]
dvi = [i.address for i in stream if i.mnemonic == "call" and call_imm(i) == ISVIS]
jvi = [i.address for i in stream if i.mnemonic == "jmp" and call_imm(i) == ISVIS]
P("R2 CALL DrawIfVisible", len(dc), [hex(a) for a in dc])
P("R2 JMP  DrawIfVisible", len(jc), [hex(a) for a in jc])
P("R2 CALL IsVisible", len(dvi), "first", hex(dvi[0]) if dvi else None,
  "last", hex(dvi[-1]) if dvi else None)
P("R2 JMP  IsVisible", len(jvi), [hex(a) for a in jvi])
P("R2 DIRECT_SITES_MATCH_F8", sorted(dc) == [0x422C8E, 0x73B132, 0x749B5B],
  "| ISVIS_COUNT_MATCH_139", len(dvi) == 139)

# ---------------- R3 render cluster ----------------
P("")
P("=== R3 RENDER CLUSTER [0x6D8DB0,0x6DA1FC) ===")
R_LO, R_HI = 0x6D8DB0, 0x6DA1FC
rin = [i for i in stream if R_LO <= i.address < R_HI]
P("R3 INSNS", len(rin), "(F8 claim 1603)")
P("R3 CALL_DRAWHIV", sum(1 for i in rin if i.mnemonic == "call" and call_imm(i) == DRAWHIV))
P("R3 JMP_DRAWHIV", sum(1 for i in rin if i.mnemonic == "jmp" and call_imm(i) == 0x5F4B10))
gw = []
for i in rin:
    for op in i.operands:
        if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 \
                and (op.access & capstone.CS_AC_WRITE):
            gw = gw + [(hex(i.address), i.mnemonic, i.op_str, op.size)]
P("R3 ABS_GLOBAL_WRITES", len(gw))
for t in gw:
    P("   ", t)
indec = [(hex(i.address), i.mnemonic, i.op_str) for i in rin if i.mnemonic in ("inc", "dec")]
P("R3 INC_DEC_TOTAL", len(indec), "(F8 claim 19)")
for t in indec:
    P("   ", t)
mc = [(hex(i.address),) + mem_counter_flags(i) for i in rin if mem_counter_flags(i)]
P("R3 MEM_INC_DEC_ADD_SUB(any-mem)", len(mc))
for t in mc:
    P("   ", t)
mw = []
for i in rin:
    for op in i.operands:
        if op.type == X86_OP_MEM and (op.access & capstone.CS_AC_WRITE):
            mw = mw + [(hex(i.address), i.mnemonic, i.op_str, mem_class(op.mem))]
mw_nonstack = [t for t in mw if t[3] != "STACK"]
P("R3 ALL_MEM_WRITES", len(mw), "non-STACK", len(mw_nonstack))
for t in mw_nonstack:
    P("   ", t)

# ---------------- R4 wide region ----------------
P("")
P("=== R4 WIDE SCAN [0x6D3D10,0x6DA200) ===")
wide = [i for i in stream if 0x6D3D10 <= i.address < 0x6DA200]
wl = [(hex(i.address),) + mem_counter_flags(i) for i in wide if mem_counter_flags(i)]
P("R4 INSNS", len(wide), "(F8 claim 7933)", "MEM_COUNTER_OPS", len(wl), "(F8 claim 21)")
cls = Counter(t[3] for t in wl)
P("R4 CLASS_DIST", dict(cls))
for t in wl:
    P("   ", t)

# ---------------- R5 counterexample hunt at call sites ----------------
P("")
P("=== R5 COUNTEREXAMPLE HUNT: 139 IsVisible sites, forward 48 insns + jcc targets 16 insns ===")
CONDC = ("ja","jae","jb","jbe","jc","je","jg","jge","jl","jle","jo","jp","jpe","jpo",
         "js","jz","jne","jno","jns","jnp","loop","loope","loopne","jecxz")
def decode_at(va, n=16):
    off = va2off(va)
    if off is None:
        return []
    return list(md.disasm(data[off:off+15*n], va))[:n]

def flags_in(seq):
    out = []
    for j, i in enumerate(seq):
        f = mem_counter_flags(i)
        if f:
            out.append((j, hex(i.address), i.mnemonic, i.op_str, f[2]))
    return out

total_flags = []
n_jcc = 0
n_tgt = 0
for a in dvi:
    k = idx[a]
    fwd = stream[k+1: k+49]
    for f in flags_in(fwd):
        total_flags.append(("FWD", hex(a)) + f)
    for i in fwd:
        if i.mnemonic in CONDC and i.operands and i.operands[0].type == X86_OP_IMM:
            tgt = i.operands[0].imm
            n_jcc += 1
            tseq = decode_at(tgt, 16)
            n_tgt += len(tseq)
            for f in flags_in(tseq):
                total_flags.append(("TGTFROM", hex(a), hex(tgt)) + f)
P("R5 SITES", len(dvi), "JCC_EXAMINED", n_jcc, "TARGET_INSNS", n_tgt)
P("R5 MEM_COUNTER_FLAGS(fwd+targets)", len(total_flags))
for t in total_flags:
    P("   ", t)
SITES5 = [0x43E6B7, 0x43E788, 0x6D909E, 0x6D916C, 0x6D93FA, 0x6D98E9, 0x6D9A21]
fl5 = []
n_jcc5 = 0
for a in SITES5 + dc:
    k = idx.get(a)
    if k is None:
        continue
    fwd = stream[k+1: k+41]
    for f in flags_in(fwd):
        fl5.append(("FWD", hex(a)) + f)
    for i in fwd:
        if i.mnemonic in CONDC and i.operands and i.operands[0].type == X86_OP_IMM:
            tgt = i.operands[0].imm
            n_jcc5 += 1
            for f in flags_in(decode_at(tgt, 16)):
                fl5.append(("TGTFROM", hex(a), hex(tgt)) + f)
P("R5 VIRTUAL+DIRECT SITES", len(SITES5)+len(dc), "JCC", n_jcc5, "FLAGS", len(fl5))
for t in fl5:
    P("   ", t)

# ---------------- R6 ABS counter census + xadd + dword immediates ----------------
P("")
P("=== R6 WHOLE-.TEXT ABS-mem inc/dec/add/sub census + xadd + dword immediates ===")
abs_cnt = []
xadd = []
for i in stream:
    f = mem_counter_flags(i)
    if f and f[2] == "ABS":
        abs_cnt.append((hex(i.address), i.mnemonic, i.op_str))
    if i.mnemonic == "xadd":
        xadd.append((hex(i.address), i.op_str))
P("R6 ABS_COUNTER_OPS_TOTAL", len(abs_cnt))
for t in abs_cnt:
    P("   ", t)
P("R6 XADD_TOTAL", len(xadd))
for t in xadd:
    P("   ", t)
for pat, name in ((struct.pack("<I", DRAWHIV), "0x5F4B10"),
                  (struct.pack("<I", ISVIS), "0x6D2140")):
    occ = []
    off = 0
    while True:
        off = data.find(pat, off)
        if off < 0:
            break
        va = None
        for nm, v, vsz, rp, rs, ch in secs:
            if rp <= off < rp + rs:
                va = v + (off - rp)
                break
        occ.append(hex(va) if va is not None else "rawoff:" + hex(off))
        off += 1
    P("R6 DWORD_PATTERN %s occurrences=%d" % (name, len(occ)), occ[:40])

# ---------------- R7 two-step dispatch ----------------
P("")
P("=== R7 TWO-STEP DISPATCH mov r32,[r32+0x104] then call/jmp reg ===")
n2 = 0
hits2 = []
for k, i in enumerate(stream):
    if i.mnemonic != "mov" or len(i.operands) != 2:
        continue
    dst, src = i.operands
    if (src.type == X86_OP_MEM and src.mem.disp == 0x104 and src.mem.base != 0
            and src.mem.index == 0 and dst.type == X86_OP_REG):
        n2 += 1
        for j in stream[k+1: k+9]:
            if j.mnemonic in ("call", "jmp") and j.operands and j.operands[0].type == X86_OP_REG:
                hits2.append((hex(i.address), i.op_str, "->", hex(j.address), j.mnemonic, j.op_str))
P("R7 MOV_SLOT65_TOTAL", n2, "FOLLOWED_BY_CALL/JMP_REG", len(hits2))
for t in hits2:
    P("   ", t)

# ---------------- R8 vtable slot bytes ----------------
P("")
P("=== R8 VTABLE SLOT-65 BYTES ===")
for va, want in ((0x7E3458, 0x422C70), (0x7F5D74, 0x73B0B0), (0x7F641C, 0x749B20)):
    off = va2off(va)
    val, = struct.unpack_from("<I", data, off)
    P("R8 u32[%s] = %s expected %s match=%s" % (hex(va), hex(val), hex(want), val == want))
refs = []
off = 0
while True:
    off = data.find(struct.pack("<I", DRAWHIV), off)
    if off < 0:
        break
    for nm, v, vsz, rp, rs, ch in secs:
        if rp <= off < rp + rs:
            refs.append((nm, hex(v + (off - rp))))
            break
    off += 1
P("R8 REFS_OF_0x5F4B10", len(refs), refs)

# ---------------- R9 container & proxy disp census ----------------
P("")
P("=== R9 DISP CENSUS: container/proxy globals, ABS vs [reg+disp] ===")
for T, label in ((0x8A0364, "Items?"), (0x8A0370, "Count?"), (0x886FA8, "container-base-ptr"),
                 (0xB0CE88, "dirtyRectCount"), (0xB0CE30, "screenW"), (0xB0CE34, "screenH"),
                 (0x887324, "TacticalPtr")):
    abs_hits, rd_hits = [], []
    for i in stream:
        for op in i.operands:
            if op.type != X86_OP_MEM:
                continue
            m = op.mem
            if m.disp != T:
                continue
            acc = "W" if (op.access & capstone.CS_AC_WRITE) else "R"
            if m.base == 0 and m.index == 0:
                abs_hits.append((hex(i.address), i.mnemonic, i.op_str, acc))
            else:
                rd_hits.append((hex(i.address), i.mnemonic, i.op_str, acc))
    P("R9 %-18s ABS=%d  REGDISP=%d" % (label, len(abs_hits), len(rd_hits)))
    for t in abs_hits:
        P("     ABS ", t)
    for t in rd_hits[:24]:
        P("     RD  ", t)
    if len(rd_hits) > 24:
        P("     ... %d more" % (len(rd_hits) - 24))
loads = [(hex(i.address), i.op_str) for i in stream
         if i.mnemonic == "mov" and len(i.operands) == 2
         and i.operands[0].type == X86_OP_REG and i.operands[1].type == X86_OP_MEM
         and i.operands[1].mem.base == 0 and i.operands[1].mem.disp == 0x886FA8]
P("R9 LOADS [0x886FA8]", len(loads), loads[:12])
first = next((i for i in stream if any(
    op.type == X86_OP_MEM and op.mem.disp in (0x8A0364, 0x8A0370) and op.mem.base != 0
    for op in i.operands)), None)
if first is not None:
    k = idx[first.address]
    P("R9 CONTEXT before first [reg+0x8a03xx] hit %s:" % hex(first.address))
    for i in stream[max(0, k-12): k+1]:
        P("     %s %s %s" % (hex(i.address), i.mnemonic, i.op_str))

# ---------------- R10 IsVisible boundary bytes ----------------
P("")
P("=== R10 ISVIS BOUNDARY / VIEWPORT BYTES ===")
for va, n, tag in ((0x6D21FD, 0x20, "viewport reads + in/out store"),
                   (0x6D2223, 0x50, "boundary compares")):
    P("--- %s ---" % tag)
    for i in decode_at(va, 40):
        if i.address >= va + n:
            break
        P("   %s %s %s %s" % (hex(i.address), i.bytes.hex(), i.mnemonic, i.op_str))

P("")
P("=== DONE elapsed %.1fs ===" % (time.time() - t0))
print("\n".join(OUT))
