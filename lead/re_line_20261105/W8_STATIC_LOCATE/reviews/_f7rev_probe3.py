# -*- coding: utf-8 -*-
"""F7 独立复核探针 #3（reviews/_f7rev_probe3.py）· 只读
  N  GT 深度-1 直接被调者普查 × 全局绝对写交集（「累加器藏在被调者」反例狩猎）
  O  0x736664（v[265] 派发宿主）可达性：EB rel8 / 流内 jmp / 启发式函数起点 E8 扫描
  P  0x6739A4/0x6739BF（mov/fstp [esi+0x1150]）上下文与函数归属
  Q  v+0x27C（接收 push 0xA8EC30 的虚方法）五个已知虚表落点反汇编
  R  0x709820 全文件 dword 引用（F7 诚实账第 6 条：0x7E2640 未归属）
用法: python -I -X utf8 _f7rev_probe3.py > _f7rev3_out.txt 2>&1
"""
import sys, time, struct, bisect
from collections import defaultdict

SWARM = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104"

def P(*a):
    try:
        print(" ".join(str(x) for x in a), flush=True)
    except Exception:
        pass

def D(eng, va, n, title):
    P("-- disasm %08x (%s) --" % (va, title))
    got = eng.disasm(va, n)
    if not got:
        P("  (empty decode)")
    for a, b, m, o in got:
        P("  %08x  %-20s %s %s" % (a, b, m, o))

t0 = time.time()
blob = open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb").read()
sys.path.insert(0, SWARM)
from ra2tool import Engine
eng = Engine()
stream = eng.stream
addrs = [i.address for i in stream]
by = eng.by()
P("stream insns=%d (%.1fs)" % (len(stream), time.time() - t0))

GTLO, GTHI = 0x6F8DF0, 0x6F9DB0
P()
P("== N. GT depth-1 callees x global abs writes ==")
callees = defaultdict(list)
for ins in stream[bisect.bisect_left(addrs, GTLO):bisect.bisect_left(addrs, GTHI)]:
    try:
        ops = ins.operands
    except Exception:
        continue
    if ins.mnemonic in ("call", "jmp") and ops and ops[0].type == 2:
        t = ops[0].imm
        if not (GTLO <= t < GTHI):
            callees[t].append((ins.address, ins.mnemonic, ins.bytes.hex()))
P("external direct call/jmp targets from GT body: %d" % len(callees))
for t in sorted(callees):
    P("  -> %08x  sites=%s" % (t, [(hex(a), mn) for a, mn, _ in callees[t]]))

# abs-disp writes per callee window [T, T+0x600)
P()
for t in sorted(callees):
    k1 = bisect.bisect_left(addrs, t); k2 = bisect.bisect_left(addrs, t + 0x600)
    ws = []
    for ins in stream[k1:k2]:
        try:
            ops = ins.operands
        except Exception:
            continue
        if ins.mnemonic in ("call", "jmp"):
            continue
        for op in ops:
            if op.type == 3:
                m = op.mem
                if m.base == 0 and m.index == 0 and (op.access & 2) and 0xA80000 <= m.disp < 0xB00000:
                    ws.append((ins.address, m.disp, ins.mnemonic, ins.op_str))
    if ws:
        P("CALLEE %08x global-abs-writes: %s" % (t, [(hex(a), hex(d), mn) for a, d, mn, _ in ws]))

P()
P("== O. 0x736664 reachability ==")
tb = blob[eng.TB:eng.TB + eng.TSZ]; TLO = eng.TLO
def raw_rel8(opc, target):
    hits = []; i = 0
    while True:
        i = tb.find(bytes([opc]), i)
        if i < 0:
            break
        rel = tb[i + 1]
        if rel >= 0x80:
            rel -= 0x100
        if TLO + i + 2 + rel == target:
            hits.append(TLO + i)
        i += 1
    return hits
def raw_rel32(opc, target):
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
P("RAW_E8 -> 0x736664: %s" % [hex(x) for x in raw_rel32(0xE8, 0x736664)])
P("RAW_E9 -> 0x736664: %s" % [hex(x) for x in raw_rel32(0xE9, 0x736664)])
P("RAW_EB -> 0x736664: %s" % [hex(x) for x in raw_rel8(0xEB, 0x736664)])
# any stream jmp with imm target 0x736664
k1 = bisect.bisect_left(addrs, 0x736600); k2 = bisect.bisect_left(addrs, 0x7366C0)
P("stream in [0x736600,0x7366C0):")
for ins in stream[k1:k2]:
    P("   %08x %-18s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

P()
P("== P. 0x6739A4 / 0x6739BF ([esi+0x1150]) context ==")
D(eng, 0x673960, 0xA0, "fstp [esi+0x1150] region")
# heuristic function start
k = bisect.bisect_left(addrs, 0x6739BF) - 1
while k >= 0 and addrs[k] >= 0x6739BF - 0x3000:
    mn = by[addrs[k]].mnemonic
    if mn == "int3" or mn.startswith("ret"):
        P("heuristic fstart for 0x6739BF: %08x (boundary ins %08x %s)" % (addrs[k + 1], addrs[k], mn))
        fs = addrs[k + 1]
        break
    k -= 1
P("RAW_E8 -> %s: %s" % (hex(fs), [hex(x) for x in raw_rel32(0xE8, fs)]))
P("RAW_E9 -> %s: %s" % (hex(fs), [hex(x) for x in raw_rel32(0xE9, fs)]))

P()
P("== Q. vtable+0x27C slot targets (receivers of push 0xA8EC30) ==")
seen = set()
for base, nm in ((0x7F4960, "Techno"), (0x7F5C70, "Unit"), (0x7E8C94, "Foot"),
                 (0x7EB058, "Infantry"), (0x7E3EBC, "Building")):
    va = base + 0x27C
    v = eng.u32(va)
    P("u32(%08x) [%s vslot159] = %08x" % (va, nm, v))
    if v not in seen:
        seen.add(v)
for v in sorted(seen):
    D(eng, v, 0x60, "v+0x27C target %08x" % v)

P()
P("== R. 0x709820 whole-file dword refs ==")
pat = struct.pack("<I", 0x709820)
i = blob.find(pat); hits = []
while i >= 0:
    va = None
    for snm, sv, vsz, rp, rsz in eng.SEC:
        if rp <= i < rp + rsz:
            va = sv + (i - rp); break
    hits.append((i, va)); i = blob.find(pat, i + 1)
for off, va in hits:
    P("   file_off=%08x VA=%s sec=%s" % (off, hex(va) if va else "<none>",
      next((nm for nm, sv, vsz, rp, rsz in eng.SEC if va and sv <= va < sv + vsz), "?")))

P()
P("### F7-REVIEW PROBE3 end %.1fs" % (time.time() - t0))
