# -*- coding: utf-8 -*-
"""§533 probe H -- 带审计重同步的全段扫描（修 probe6/7 的假零命中）。

背景（当场自查）：probe6/probe7 用 `for ins in MD.disasm(b, TLO)` 做全镜像扫描。
capstone 的 disasm 迭代器**在第一个不可解码字节处静默停止**（本仓 G-23 已登记），
于是在 .text 前段某处断掉 ⇒ 后面 0x55D7D4 等站点全部看不见 ⇒ 「0 处写点」是假零。

本件用**逐址 +1 重同步**（同 _crev_engine / text_sweep 口径）重做，并打印覆盖率自证。
只读 gamemd.exe。零真机、零写入（除 stdout）。
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
TB = TEXT[3]


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

# ---- resync linear decode (audit: count of failures) ------------------------
text_bytes = raw[TB: TB + TEXT[4]]
stream = []
cur = TLO
fails = 0
while cur < THI:
    ins = list(MD.disasm(text_bytes[cur - TLO: cur - TLO + 15], cur))
    if not ins:
        cur += 1
        fails += 1
        continue
    q = ins[0]
    stream.append(q)
    cur += q.size
print("E1 resync decode: %d insns, %d resync steps (>=1 byte skipped)" % (len(stream), fails))
print("E1b covered bytes: %.2f%% of .text" % (
    100.0 * sum(i.size for i in stream) / TEXT[4]))

# ---- 索引：所有「绝对地址 disp」访存 --------------------------------------
WATCH = {0xA8B230: "GameLogic ptr(global)", 0xA8B238: "GameMode",
         0xA8ED80: "Focus/fastflag", 0xA8ED84: "CurrentFrame",
         0xA8E9A0: "InGame flag"}
by_disp = defaultdict(list)
for ins in stream:
    try:
        ops = ins.operands
    except Exception:
        continue
    for op in ops:
        if op.type == 3 and op.mem.index == 0 and getattr(op, "access", 0) is not None:
            d = op.mem.disp
            if d in WATCH and op.mem.base == 0:
                w = bool(op.access & 2)
                by_disp[d].append((ins.address, "W" if w else "R",
                                   ins.mnemonic, ins.op_str))
                break

print()
print("=" * 78)
print("T1 关键全局的绝对访存普查（重同步全段）")
print("=" * 78)
for d, name in WATCH.items():
    v = by_disp.get(d, [])
    ws = [x for x in v if x[1] == "W"]
    print("  %08X %-22s 总 %4d  读 %4d  写 %3d" % (d, name, len(v), len(v) - len(ws), len(ws)))

print()
print("=" * 78)
print("T2 [0xA8B230] 的全部写入点")
print("=" * 78)
for a, m, mn, op in by_disp.get(0xA8B230, []):
    if m == "W":
        print("   W %08X  %-8s %s" % (a, mn, op))

print()
print("=" * 78)
print("T3 [0xA8ED80] 的全部写入点（焦点旗标）")
print("=" * 78)
for a, m, mn, op in by_disp.get(0xA8ED80, []):
    if m == "W":
        print("   W %08X  %-8s %s" % (a, mn, op))

print()
print("=" * 78)
print("T4 [0xA8ED84] CurrentFrame 的全部写入点")
print("=" * 78)
for a, m, mn, op in by_disp.get(0xA8ED84, []):
    if m == "W":
        print("   W %08X  %-8s %s" % (a, mn, op))

# ---- [+0x62C] 家族（base 任意） -------------------------------------------
print()
print("=" * 78)
print("T5 [+0x62C] 家族（任意基址）读/写点")
print("=" * 78)
for disp in (0x61C, 0x620, 0x624, 0x628, 0x62C, 0x630):
    hits = []
    for ins in stream:
        try:
            ops = ins.operands
        except Exception:
            continue
        for op in ops:
            if op.type == 3 and op.mem.disp == disp:
                hits.append((ins.address, "W" if (op.access & 2) else "R",
                             ins.mnemonic, ins.op_str))
                break
    print("  +0x%03X : %d 处   (W=%d R=%d)" % (
        disp, len(hits), sum(1 for h in hits if h[1] == "W"),
        sum(1 for h in hits if h[1] == "R")))
    if disp == 0x62C:
        for h in hits:
            print("      %s %08X  %-8s %s" % h)
