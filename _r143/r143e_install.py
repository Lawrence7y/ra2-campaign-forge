#!/usr/bin/env python3
"""R143 E：C1 的第二形态（寄存器搬运装表）与「已知装表点」定点复核。

目的：把「对象偏移 0 处写虚表指针」的覆盖率从 imm 立即数形态（838/1218）补到寄存器形态，
并逐字节复核台账里已登记的装表点（例如 0x4E6CFD 装 0x7E9EE4）。

形态：
  F1 imm 形态   mov dword ptr [rX+0], imm==vt
  F2 reg 形态   mov r1, imm==vt (或 lea r1,[vt]) 之后 <=6 条指令内 mov dword ptr [rX+0], r1
                （中间若 r1 被改写或遇到 call 则作废；遇到写内存或其它寄存器不影响）
  F3 仅 imm/仅 reg 都不算覆盖，两者并集才算

反控：
  G1 用伪虚表集合（等势随机 .data dword，seed=143）重算 F1+F2 覆盖数，必须塌到个位数百分比。
  G2 把「偏移 0」换成 4，覆盖数必须大幅下降。
  G3 目标寄存器必须不是 esp/ebp（排除栈上临时变量伪装成对象）。
"""
import struct, json, subprocess, re, collections, random, hashlib, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

P = 'ra2bench/gamemd.exe'
data = open(P, 'rb').read(); N = len(data)
pe = pefile.PE(P, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
T = [s for s in secs if s[0] == '.text'][0]
TEXT_RAW = T[3]; TEXT_RSZ = T[4]

def va2off(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs):
            d = va - lo
            return raw + d if d < rs else None
    return None

def rd(va, l):
    o = va2off(va)
    if o is None or o + l > N: return None
    return data[o:o + l]

def dw(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]

def sec_of(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs): return nm
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32)
GEN = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi')

def sweep():
    off = TEXT_RAW; end = TEXT_RAW + TEXT_RSZ
    while off < end:
        chunk = data[off:min(off + 65536, end)]
        base = IB + (T[1] + (off - TEXT_RAW))
        consumed = 0
        for a, sz, mn, op in md.disasm_lite(chunk, base):
            if a - base + sz > len(chunk): break
            consumed = a - base + sz
            yield a, sz, mn, re.sub(r'\s*([+,*])\s*', r'\1', op or '')
        off += consumed if consumed else 1

# ---- VTS ----
pat = re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
TDs = {}
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        for m in pat.finditer(data[raw:raw + rs]):
            s = IB + ava + m.start()
            if dw(s - 8) is not None and dw(s - 4) == 0 and sec_of(dw(s - 8)) in ('.data', '.rdata'):
                TDs[s - 8] = m.group()
tdset = set(TDs)
COL = set()
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in tdset:
                c = IB + ava + i * 4 - 12
                if dw(c) == 0 and dw(c + 12) == v and dw(c + 16) != 0:
                    COL.add(c)
VTS = set()
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in COL:
                vt = IB + ava + i * 4 + 4
                if dw(vt - 4) == v:
                    VTS.add(vt)

RE_STORE = re.compile(r'^dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\](?:,([^,]+))?$')
RE_IMM = re.compile(r'^(0x[0-9a-f]+|\d+)$')
RE_LOADIMM = re.compile(r'^([a-z0-9]+),(0x[0-9a-f]+|\d+)$')
RE_LEAABS = re.compile(r'^([a-z0-9]+),\[(0x[0-9a-f]+)\]$')

def disp_of(s):
    if s is None: return 0
    return int(s[3:], 16) if s.startswith('+0x') else -int(s[1:])

def scan(vtset, want_disp=0):
    f1 = []          # (va, base, vt)
    f2 = []          # (va, base, vt, move_va)
    pend = {}        # reg -> (imm, va, first_seen_index)
    idx = 0
    for a, sz, mn, op in sweep():
        idx += 1
        # 过期处理：超过 6 条指令的 pending 作废（用 idx - first_seen > 6）
        for r in list(pend):
            if idx - pend[r][2] > 6:
                del pend[r]
        if not op: continue
        ms = RE_STORE.match(op)
        if ms and mn in ('mov', 'movl'):
            base, ds, tgt = ms.group(1), disp_of(ms.group(2)), ms.group(3)
            if tgt is not None:
                if RE_IMM.match(tgt):
                    iv = (int(tgt, 16) if tgt.startswith('0x') else int(tgt)) & 0xFFFFFFFF
                    if iv in vtset and base in GEN and ds == want_disp:
                        f1.append((a, base, iv))
                elif tgt in GEN and base in GEN and ds == want_disp:
                    p = pend.get(tgt)
                    if p and p[0] in vtset:
                        f2.append((a, base, p[0], p[1]))
            if tgt in GEN and not (base in GEN and ds == want_disp):
                pass
            continue
        ml = RE_LOADIMM.match(op)
        if ml and mn == 'mov' and ml.group(1) in GEN:
            iv = (int(ml.group(2), 16) if ml.group(2).startswith('0x') else int(ml.group(2))) & 0xFFFFFFFF
            pend[ml.group(1)] = (iv, a, idx)
            continue
        le = RE_LEAABS.match(op)
        if le and mn == 'lea' and le.group(1) in GEN:
            iv = int(le.group(2), 16) & 0xFFFFFFFF
            pend[le.group(1)] = (iv, a, idx)
            continue
        # 其它写该寄存器的形态：让 pending 失效
        if op and mn != 'cmp' and mn != 'test':
            dst = op.partition(',')[0]
            if dst in pend:
                del pend[dst]
        if mn == 'call':
            for r in ('eax', 'ecx', 'edx'):
                pend.pop(r, None)
    return f1, f2

f1, f2 = scan(VTS, 0)
cov1 = {s[2] for s in f1}
cov2 = {s[2] for s in f2}
covU = cov1 | cov2
# 反控
f1_4, f2_4 = scan(VTS, 4)
random.seed(143)
pool = []
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(struct.unpack_from('<I', blob, i * 4)[0])
FAKE = set(random.sample(pool, len(VTS)))
gf1, gf2 = scan(FAKE, 0)
gU = {s[2] for s in gf1} | {s[2] for s in gf2}

# ---- 定点字节复核：台账已登记的装表点 ----
KNOWN = {
    '0x4E6CFD': (0x7E9EE4, 'DynamicVectorClass<HouseClass*> 容器 ctor 装表（台账 GOAL §28363 登记）'),
    '0x7B8850': (0x7F7B2C, 'WWMouseClass ctor 装表（台账 GOAL §31929 登记）'),
    '0x7E3EBC': (None, 'BuildingClass 主 vtable 地址本身（供参考）'),
    '0x7F4960': (None, 'TechnoClass 主 vtable 地址本身（供参考）'),
}
spot = {}
for k, (vt, note) in KNOWN.items():
    va = int(k, 16)
    b = rd(va, 16)
    txt = None
    if b is not None:
        seq = list(md.disasm_lite(b, va))
        txt = ' | '.join('%s %s' % (mn, re.sub(r'\s*([+,*])\s*', r'\1', op)) for a, sz, mn, op in seq[:4])
    spot[k] = {'note': note, 'bytes': b.hex() if b else None, 'disasm': txt,
               'expect_vt': hex(vt) if vt else None,
               'is_F1': any(hex(s[0]) == k.lower() for s in f1),
               'is_F2': any(hex(s[0]) == k.lower() for s in f2)}

res = {
 'exe_sha256': hashlib.sha256(data).hexdigest(),
 'exe_bytes': N,
 'vt_distinct': len(VTS), 'td': len(TDs), 'col': len(COL),
 'F1_sites': len(f1), 'F1_distinct_vt': len(cov1), 'F1_coverage': round(len(cov1) / len(VTS), 4),
 'F2_sites': len(f2), 'F2_distinct_vt': len(cov2), 'F2_coverage': round(len(cov2) / len(VTS), 4),
 'UNION_distinct_vt': len(covU), 'UNION_coverage': round(len(covU) / len(VTS), 4),
 'F1_base_regs': dict(collections.Counter(s[1] for s in f1)),
 'F2_base_regs': dict(collections.Counter(s[1] for s in f2)),
 'uncovered_n': len(VTS - covU),
 'N_disp4_distinct': len({s[2] for s in f1_4} | {s[2] for s in f2_4}),
 'N_disp4_coverage': round(len({s[2] for s in f1_4} | {s[2] for s in f2_4}) / len(VTS), 4),
 'G_fake_distinct': len(gU), 'G_fake_coverage': round(len(gU) / len(FAKE), 4),
 'G_fake_sites': len(gf1) + len(gf2),
 'spot': spot,
}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143e_install.json', 'w'), ensure_ascii=False, indent=1)
json.dump({'f1_head': [[hex(a), b, hex(v)] for a, b, v in f1[:40]],
           'f2_head': [[hex(a), b, hex(v), hex(m)] for a, b, v, m in f2[:40]],
           'uncovered_head': [hex(v) for v in sorted(VTS - covU)[:40]]},
          open('_r143/r143e_samples.json', 'w'), ensure_ascii=False, indent=1)
