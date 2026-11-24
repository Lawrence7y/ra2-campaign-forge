# -*- coding: utf-8 -*-
"""§533 probe B -- MainLogicFrame(0x55D360) 全函数 CFG：枚举「帧不推进」的全部出口。

只读 gamemd.exe（sha256 钉死）。零真机、零进程、零写入（除 stdout）。

核心命题：
  CurrentFrame(0xA8ED84) 全镜像唯一定常自增点 = 0x55DE7E/0x55DE81（MainLogicFrame 体内）。
  ⇒ 「帧号冻结」在二进制层面 ⟺ 「MainLogicFrame 从入口走到某个 ret 而未经过 0x55DE7E」。

本探针把这个命题展开成**有限集合**：对每个 ret，判定 INC 是否必然在它之前。
"""
import hashlib
import struct
from collections import defaultdict

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == EXPECT_SHA, "image drift"

e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    nm = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append((nm, IB + va, vsz, rp, rsz))
TEXT = next(s for s in SEC if s[0] == ".text")
TLO, THI = TEXT[1], TEXT[1] + TEXT[4]


def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            off = rp + (va - sva)
            return off if off < rp + rsz else None
    return None


def rd(va, n):
    o = fo(va)
    return raw[o:o + n] if o is not None else b"\0" * n


MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True

FUNC = 0x55D360
INC_RD, INC_PT, INC_WR = 0x55DE73, 0x55DE7E, 0x55DE81
# 函数尾：0x55D371 的 je 指向 0x55DECF；再往下一段 0x55DEE0 是另一个函数头
END_GUESS = 0x55DEE0

text = rd(FUNC, END_GUESS - FUNC)
insns = []
for ins in MD.disasm(text, FUNC):
    insns.append({"va": ins.address, "sz": ins.size, "mn": ins.mnemonic,
                  "op": ins.op_str, "bs": ins.bytes.hex(),
                  "tgt": ins.operands[0].imm if (ins.mnemonic.startswith("j") and ins.operands
                                                 and ins.operands[0].type == 2) else None})
BY = {i["va"]: i for i in insns}
print("E1 window [%08X,%08X) decoded %d insns" % (FUNC, END_GUESS, len(insns)))

# ---- succ edges (intra-function) -------------------------------------------
succ = defaultdict(list)
for k, i in enumerate(insns):
    a, mn, tgt = i["va"], i["mn"], i["tgt"]
    nxt = insns[k + 1]["va"] if k + 1 < len(insns) else None
    if mn.startswith("ret"):
        continue
    if mn == "jmp":
        if tgt is not None and FUNC <= tgt < END_GUESS:
            succ[a].append(tgt)
        continue
    if mn.startswith("j"):
        if tgt is not None and FUNC <= tgt < END_GUESS:
            succ[a].append(tgt)
        if nxt is not None:
            succ[a].append(nxt)
        continue
    if nxt is not None:
        succ[a].append(nxt)

# ---- forward reachability: does every path to P pass through INC? ----------
def reaches_only_via_inc(target):
    """True if removing INC instructions makes target unreachable from FUNC."""
    seen = set()
    work = [FUNC]
    while work:
        a = work.pop()
        if a in seen:
            continue
        seen.add(a)
        for s in succ.get(a, ()):
            if INC_RD <= s <= INC_WR:      # cut the increment straight-line block
                continue
            if s not in seen:
                work.append(s)
    return target not in seen

rets = [i for i in insns if i["mn"].startswith("ret") and i["va"] < END_GUESS]
print("E2 rets in window: %d" % len(rets))
print()
print("%-10s %-16s %-8s %-6s %s" % ("VA", "bytes", "mnem", "op", "INC 必经?"))
print("-" * 78)
no_inc = []
for r in rets:
    via = reaches_only_via_inc(r["va"])
    tag = "YES (帧已推进)" if via else "*** NO  -> 帧号冻结出口 ***"
    if not via:
        no_inc.append(r)
    print("%08X   %-16s %-8s %-6s %s" % (r["va"], r["bs"], r["mn"], r["op"], tag))
print()
print("E3 不经过 INC 即可到达的 ret 数 = %d" % len(no_inc))

# ---- 对每个「冻结出口」回溯守卫链 -----------------------------------------
def back_chain(target, depth=14):
    """collect the branch insns that guard target (reverse BFS on pred)."""
    pred = defaultdict(list)
    for a, ss in succ.items():
        for s in ss:
            pred[s].append(a)
    seen, work, conds = set(), [target], []
    while work and len(seen) < depth * 8:
        a = work.pop()
        if a in seen:
            continue
        seen.add(a)
        i = BY.get(a)
        if i and i["mn"].startswith("j"):
            conds.append((a, i["mn"], i["op"]))
        for p in pred.get(a, ()):
            if p not in seen:
                work.append(p)
    return conds

print()
print("=" * 78)
print("每个『帧号冻结出口』的回溯守卫链")
print("=" * 78)
for r in no_inc:
    print("\n--- ret @ %08X ---" % r["va"])
    for a, mn, op in sorted(back_chain(r["va"])):
        print("   %08X  %-6s %s" % (a, mn, op))

# ---- 特别标出 INC 之前的阻塞性循环 ----------------------------------------
print()
print("=" * 78)
print("★ INC 之前的『阻塞循环』普查（回边落在 INC 之前 = 可能永久不返回）")
print("=" * 78)
for k, i in enumerate(insns):
    a, mn, tgt = i["va"], i["mn"], i["tgt"]
    if mn.startswith("j") and mn != "jmp" and tgt is not None and tgt < a and a < INC_PT:
        # 回边
        body = [x for x in insns if tgt <= x["va"] <= a]
        calls = [x for x in body if x["mn"] == "call"]
        print("回边 %08X -> %08X (loop %d insns, %d calls)" % (a, tgt, len(body), len(calls)))
        for c in calls:
            print("      call %s" % c["op"])
