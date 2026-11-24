# -*- coding: utf-8 -*-
"""F7 独立复核探针（reviews/_f7rev_probe.py）· 只读
用法: python -I -X utf8 _f7rev_probe.py > _f7rev_out.txt 2>&1
铁律: 零真机 / 零注入 / 只读 gamemd.exe 磁盘镜像；唯一写域 = W8_STATIC_LOCATE/reviews/
复核点:
  A  SHA256+字节数（独立 hashlib，不经 ra2tool）
  B  RAW 全文件 LE-dword 扫描：0x6F8DF0/0x6FB010/四包装 —— 找 imm/vtable 旁路通道（反例狩猎）
  C  RAW E8/E9 扫描（.text）：GT/0x6FB010/0x6ECCE0/0x736CA0 直调直跳上界
  D  流内 imm32 扫描：0x6F8DF0/0x6FB010 与 [A8EC00,A8ED00) 邻域地址物化（间接通道反例狩猎）
  E  重同步解码流单遍普查：call/jmp 到目标；call [reg+0x3C4]/[reg+0x424] 计数；
     0xA8EC34 访存；GT 体/包装绝对写；inc/add [abs] 全景；disp==0x1150 写点
  F  关键反汇编：0x6FB010 头、0x6F8DF0 头、GT 尾边界、%14 门全字节、
     0x666E09/0x666E1A 构造器立即数、0x7E27F8 常量、0x740B10 边界、0x740BE0 区、
     0x736640 v[265] 宿主、0x50B730 头、0x714160 PipWrap 绑定
  G  u32 虚表槽（含补跑声称的 0x7F5ECC）
  H  0x4F8F87 %8 门与 0x4F8E1E..0x4F8E28 字节上下文（0x4F8E24 可解码性）
"""
import sys, time, struct, hashlib
from collections import defaultdict

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
SWARM = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104"

def P(*a):
    try:
        print(" ".join(str(x) for x in a), flush=True)
    except Exception:
        pass

def D(eng, va, n, title):
    P("-- disasm %08x (%s) --" % (va, title))
    for a, b, m, o in eng.disasm(va, n):
        P("  %08x  %-20s %s %s" % (a, b, m, o))

# ---------- A. independent SHA256 ----------
t0 = time.time()
blob = open(EXE, "rb").read()
P("== A. INDEPENDENT SELF-CERT ==")
P("SHA256(indep hashlib) =", hashlib.sha256(blob).hexdigest())
P("FILE_BYTES =", len(blob))

sys.path.insert(0, SWARM)
from ra2tool import Engine
eng = Engine()
P("IMAGE_BASE =", hex(eng.IB))
P("sections:", [(nm, hex(sv), hex(rsz)) for nm, sv, vsz, rp, rsz in eng.SEC])

def sec_of(va):
    for nm, sv, vsz, rp, rsz in eng.SEC:
        if sv <= va < sv + vsz:
            return nm
    return "<hdr/other>"

# ---------- B. whole-FILE LE dword scan ----------
P()
P("== B. WHOLE-FILE LE-DWORD SCAN (imm/vtable bypass hunt) ==")
TARGETS = {
    0x006F8DF0: "Greatest_Threat",
    0x006FB010: "fn_6FB010(UpdateReload)",
    0x00445F00: "BLDG_v241_wrap",
    0x004D9920: "FOOT_v241_wrap",
    0x00743190: "UNIT_v241_wrap",
    0x0051E140: "INF_v241_wrap",
    0x00736CA0: "UNIT_v265_wrap",
}
for tgt, nm in sorted(TARGETS.items()):
    pat = struct.pack("<I", tgt)
    hits = []
    i = blob.find(pat)
    while i >= 0:
        # file offset -> VA (per section, raw ptr mapping)
        va = None
        for snm, sv, vsz, rp, rsz in eng.SEC:
            if rp <= i < rp + rsz:
                va = sv + (i - rp)
                break
        hits.append((i, va))
        i = blob.find(pat, i + 1)
    P("DWORD %08x (%s): %d hits" % (tgt, nm, len(hits)))
    for off, va in hits:
        if va is None:
            P("   file_off=%08x VA=<not-mapped>" % off)
        else:
            P("   file_off=%08x VA=%08x sec=%s" % (off, va, sec_of(va)))

# ---------- C. RAW E8/E9 in .text ----------
P()
P("== C. RAW E8/E9 SCAN in .text ==")
tb = blob[eng.TB:eng.TB + eng.TSZ]
TLO = eng.TLO
def raw_rel(opc, target):
    hits = []; i = 0
    while True:
        i = tb.find(bytes([opc]), i)
        if i < 0:
            break
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        if TLO + i + 5 + rel == target:
            hits.append(TLO + i)
        i += 1
    return hits
for tgt, nm in ((0x6F8DF0, "Greatest_Threat"), (0x6FB010, "fn_6FB010"),
                (0x6ECCE0, "pct14-host"), (0x736CA0, "UNIT_v265_wrap"),
                (0x445F00, "BLDG_v241_wrap"), (0x4D9920, "FOOT_v241_wrap")):
    P("RAW_E8 -> %08x (%s): %s" % (tgt, nm, [hex(x) for x in raw_rel(0xE8, tgt)]))
    P("RAW_E9 -> %08x (%s): %s" % (tgt, nm, [hex(x) for x in raw_rel(0xE9, tgt)]))

# ---------- D+E. single-pass stream census ----------
P()
P("== D/E. STREAM CENSUS (resynced linear decode) ==")
GTLO, GTHI = 0x6F8DF0, 0x6F9DB0
CALLTG = {0x6F8DF0, 0x6FB010, 0x6ECCE0, 0x736CA0, 0x445F00, 0x4D9920}
vt3c4 = []; vt424 = []
cmap = defaultdict(list); jmap = defaultdict(list)
abs_hits_ec34 = []
nbhd_writes = []          # abs-disp writes with disp in [A8EC00, A8ED00)
rmw_abs = defaultdict(list)  # inc/add/sub/or with abs mem disp & write access
w1150 = []
imm_fn = defaultdict(list)   # imm32 == function addresses
imm_nbhd = []                # imm32 in [A8EC00, A8ED00)
abs_writes = []
t3 = time.time()
stream = eng.stream
P("stream insns=%d" % len(stream))
for ins in stream:
    try:
        ops = ins.operands
    except Exception:
        continue
    mn = ins.mnemonic; a = ins.address
    if mn in ("call", "jmp") and ops and ops[0].type == 2:
        t = ops[0].imm
        if t in CALLTG:
            (cmap if mn == "call" else jmap)[t].append((a, ins.bytes.hex()))
    if mn == "call" and ops and ops[0].type == 3:
        s = ins.op_str
        if "+ 0x3c4]" in s:
            vt3c4.append(a)
        elif "+ 0x424]" in s:
            vt424.append(a)
    for op in ops:
        if op.type == 2:
            if op.imm in TARGETS:
                imm_fn[op.imm].append((a, mn, ins.op_str, ins.bytes.hex()))
            elif 0xA8EC00 <= op.imm < 0xA8ED00:
                imm_nbhd.append((a, mn, ins.op_str, hex(op.imm)))
        elif op.type == 3:
            m = op.mem
            if m.base == 0 and m.index == 0:
                d = m.disp; w = bool(op.access & 2)
                if d == 0xA8EC34:
                    abs_hits_ec34.append((a, "W" if w else "R", mn, ins.op_str, ins.bytes.hex()))
                if 0xA8EC00 <= d < 0xA8ED00 and w:
                    nbhd_writes.append((a, d, mn, ins.op_str, ins.bytes.hex()))
                if w:
                    abs_writes.append((a, d, mn))
                    if mn in ("inc", "add", "sub", "or", "xor"):
                        rmw_abs[d].append((a, mn, ins.op_str))
                if d == 0x1150 and w:
                    w1150.append((a, mn, ins.op_str, ins.bytes.hex()))
P("census pass done %.1fs" % (time.time() - t3))

P()
P("-- E1. imm32 materialization of function addresses (indirect-call channel hunt) --")
for t in sorted(imm_fn):
    P("IMM %08x count=%d: %s" % (t, len(imm_fn[t]), [(hex(a), mn, ops) for a, mn, ops, _ in imm_fn[t]]))
P("IMM in [A8EC00,A8ED00) count=%d" % len(imm_nbhd))
for a, mn, ops, iv in imm_nbhd[:40]:
    P("   %08x %s %s imm=%s" % (a, mn, ops, iv))

P()
P("-- E2. stream call/jmp to targets --")
for t in sorted(CALLTG):
    P("STREAM_CALL %08x: %s" % (t, [(hex(s), b) for s, b in cmap.get(t, ())]))
    P("STREAM_JMP  %08x: %s" % (t, [(hex(s), b) for s, b in jmap.get(t, ())]))

P()
P("-- E3. virtual dispatch sites --")
P("call [reg+0x3C4] count=%d: %s" % (len(vt3c4), [hex(x) for x in vt3c4]))
P("call [reg+0x424] count=%d: %s" % (len(vt424), [hex(x) for x in vt424]))

P()
P("-- E4. [0xA8EC34] accesses --")
P("count=%d" % len(abs_hits_ec34))
for a, rw, mn, ops, bh in abs_hits_ec34:
    P("   %08x %s %s %s [%s]" % (a, rw, mn, ops, bh))

P()
P("-- E5. abs-disp WRITES disp in [A8EC00,A8ED00) --")
P("count=%d" % len(nbhd_writes))
for a, d, mn, ops, bh in nbhd_writes:
    P("   %08x disp=%08x %s %s [%s]" % (a, d, mn, ops, bh))

P()
P("-- E6. inc/add/sub/or/xor with abs mem disp & write access (RMW accumulator universe) --")
for d in sorted(rmw_abs):
    P("disp %08x n=%d: %s" % (d, len(rmw_abs[d]), [(hex(a), mn) for a, mn, _ in rmw_abs[d]][:12]))

P()
P("-- E7. writes with disp==0x1150 (Rules+0x1150) --")
P("count=%d" % len(w1150))
for a, mn, ops, bh in w1150:
    P("   %08x %s %s [%s]" % (a, mn, ops, bh))

# ---------- F. fixed disasms ----------
P()
P("== F. FIXED DISASMS ==")
D(eng, 0x6FB010, 0x28, "0x6FB010 head (UpdateReload?)")
P()
D(eng, 0x6F8DF0, 0x24, "Greatest_Threat head (RMW)")
P()
D(eng, 0x6F9D90, 0x40, "GT tail boundary (census window check)")
P()
D(eng, 0x6ECD40, 0x30, "pct14 gate bytes")
P()
D(eng, 0x6ECDF0, 0x30, "pct14 dispatch tail (push 1 -> call)")
P()
# constructor immediates: raw reads + double assembly
b1 = eng.rd(0x666E09, 10); b2 = eng.rd(0x666E1A, 10)
P("raw@0x666E09 = %s" % b1.hex())
P("raw@0x666E1A = %s" % b2.hex())
lo = struct.unpack_from("<I", b1, 6)[0]; hi = struct.unpack_from("<I", b2, 6)[0]
dval = struct.unpack("<d", struct.pack("<II", lo, hi))[0]
P("Rules+0x1150 default double = lo=%08x hi=%08x -> %.6g" % (lo, hi, dval))
c9 = eng.rd(0x7E27F8, 8)
P("raw@0x7E27F8 = %s -> %.6g" % (c9.hex(), struct.unpack("<d", c9)[0]))
P("int(%.4f * %.1f) = %d ; round = %d" % (dval, struct.unpack("<d", c9)[0],
  int(dval * struct.unpack("<d", c9)[0]), round(dval * struct.unpack("<d", c9)[0])))
P()
D(eng, 0x740B10, 0x50, "fn_740B10 full (v151?) + boundary to next fn")
P()
D(eng, 0x740BD0, 0x50, "and-ecx,7 region context (0x740BED attribution)")
P()
D(eng, 0x736640, 0x60, "v[265] dispatch host 0x736664")
P()
D(eng, 0x50B730, 0x50, "0x50B730 head (owner predicate)")
P()
D(eng, 0x714160, 0x48, "PipWrap binding region 0x714180")

# ---------- G. u32 slots ----------
P()
P("== G. U32 VTABLE SLOTS ==")
for va, nm in ((0x7F4D24, "Techno v241"), (0x7F4D84, "Techno v265"),
               (0x7F6094, "Unit v265"), (0x7F5ECC, "Unit v151 (claimed 0x740B10)"),
               (0x7F6034, "Unit v241"), (0x7E9058, "Foot v241"),
               (0x7EB41C, "Infantry v241"), (0x7E4280, "Building v241"),
               (0x7F5D94, "Unit v73"), (0x7EB17C, "Infantry v73"), (0x7E8DB8, "Foot v73")):
    P("u32(%08x) = %08x   ; %s" % (va, eng.u32(va), nm))

# ---------- H. mod-8 gate bytes & 0x4F8E24 context ----------
P()
P("== H. MOD8 GATE + 0x4F8E24 DECODABILITY ==")
P("raw 0x4F8F87..0x4F8F9C =", eng.rd(0x4F8F87, 0x15).hex())
P("raw 0x4F8E1E..0x4F8E2C =", eng.rd(0x4F8E1E, 0xE).hex())
D(eng, 0x4F8E21, 0x10, "aligned decode at 0x4F8E21 (0x4F8E24 inside?)")

P()
P("### F7-REVIEW PROBE end %.1fs" % (time.time() - t0))
