# -*- coding: utf-8 -*-
"""V-P03 核验探针 1：现场自证 + disp_hits 基线 + 10 写点字节 + 全写点 mnemonic 普查 + 字节计数闭合"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("[sha] prefix =", eng.sha[:16], "(expect 73201cc021497c95)")
print("[text] = [0x%x, 0x%x) size=0x%x" % (eng.TLO, eng.THI, eng.TSZ))

cov = eng.coverage
print("[coverage] %.2f%% / %d insns / resync=%d" % cov)

hits = eng.disp_hits(0xA8ED84)
W = [h for h in hits if h[1] == "W"]
R = [h for h in hits if h[1] == "R"]
print("[disp_hits 0xA8ED84] total=%d W=%d R=%d" % (len(hits), len(W), len(R)))

print("[10 W points with bytes]")
for va, d, mn, ops in sorted(W):
    n = {"89": 6, "a3": 5, "c7": 10}.get(mn and va and __import__("binascii").hexlify(eng.rd(va,1)).decode(), 6)
    b = eng.rd(va, 12).hex()
    print("  0x%08x  %-22s %s %s" % (va, b[:22], mn, ops))

print("[W mnemonic census] (任何 inc/add/sub/or/and/xor 直接内存形式都算推翻)")
from collections import Counter
print(" ", Counter(mn for _, _, mn, _ in W))

print("[anchor bytes]")
print("  0x55DE73:", eng.rd(0x55DE73, 6).hex(), "(expect 8b1584eda800)")
print("  0x55DE7E:", eng.rd(0x55DE7E, 3).hex(), "(expect 42)")
print("  0x55DE81:", eng.rd(0x55DE81, 6).hex(), "(expect 891584eda800)")

# 字节计数闭合：84 ed a8 00 在 .text 的出现次数
tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
pat = bytes.fromhex("84eda800")
cnt, i = 0, tb.find(pat)
locs = []
while i >= 0:
    cnt += 1
    locs.append(eng.TLO + i)
    i = tb.find(pat, i + 1)
print("[byte count] '84eda800' in .text = %d (claim 1009 = 1007 disp + 2 push)" % cnt)

# 差集：哪些字节位置不是 disp_hits 命中点
hit_vas = set(v for v, *_ in hits)
extra = [hex(v) for v in locs if v not in hit_vas]
print("[extra byte locs beyond disp_hits] =", extra)

# [reg+0xA8ED84] 家族（base!=0）——若存在则 1009 闭合会破
fld = eng.disp_hits_field(0xA8ED84)
fld_nonabs = [h for h in fld if h not in hits]
print("[disp_hits_field] total=%d, beyond disp_hits=%d" % (len(fld), len(fld_nonabs)))
for h in fld_nonabs[:10]:
    print("   extra:", h)

# 立即数形态普查：mov reg,0xA8ED84 (B8+r) —— 应为 0
mov_imm = []
for off in range(len(tb) - 5):
    if tb[off] in range(0xB8, 0xC0) and tb[off+1:off+5] == pat:
        mov_imm.append(eng.TLO + off)
print("[mov reg,0xA8ED84 imm forms] =", len(mov_imm), [hex(v) for v in mov_imm[:10]])
