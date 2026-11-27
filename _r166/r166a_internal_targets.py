#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r166a_internal_targets.py —— F24 bounds 里那 65 条「不是指令起点」的地址到底是什么

R162 待办第 2 条（至今没人做）：bounds 有 65 条地址不在 plain（无 skipdata）起点集里，
R162 的措辞是「65 条全 < 尾界且全部在某条指令内部（位移 1..7）」。

本轮把它改成一组可失败命题，并把两种解释显式分开：
  H-A 「bounds 不是纯起点集，混进了指令内部地址」
  H-B 「那 65 个字节是**线性解码根本解不出的字节**（1 字节重对齐点），skipdata 把它们
       变成 1 字节数据项 ⇒ 它们的起点就进了 bounds」
H-B 的判决性判据：plain 扫描的单字节重对齐点的**地址集合**是否 == bounds − plain 起点集。

另外三条独立量：
  * raw blob（SizeOfRawData）与 VirtualSize blob 两种口径的起点数差，必须是尾填充 0x00 的账；
  * skipdata 起点序列与 bounds 是否逐位相等（R164 已证，本轮复算作反控）；
  * 对每条 65 地址：`disasm` 单字节起点解不出（证明它是洞），以及「从 VA-k 起单解能覆盖 VA 的
    k 集合」是否恰好复现 R162 的 1..7 —— 若复现，则「在某条指令内部」只是**逐地址重解码**
    的产物，不是任何一次线性解码里的事实。

严禁 detail=True 全段；只对 65 条命中地址单独取 detail。
"""
import bisect
import io
import json
import os
import sys
from collections import Counter

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
BOUNDS = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r166/r166a_internal_targets.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:600]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:300]) if detail else ''))


# ---------------------------------------------------------------- 0 基线
print('== 0 段表基线 ==')
data = io.open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.decode().rstrip('\x00') == '.text'][0]
RAW, RSZ, VA, VSZ = t.PointerToRawData, t.SizeOfRawData, t.VirtualAddress, t.Misc_VirtualSize
LO = IB + VA
TAIL = LO + VSZ
print('  .text raw=%d rsz=%d vsz=%d lo=%#x tail=%#x' % (RAW, RSZ, VSZ, LO, TAIL))
ck('B0 gamemd.exe == 4,825,360 B', len(data) == 4825360, len(data))
ck('B1 .text (raw 4096 / rsz 4,063,232 / vsz 4,060,045)',
   (RAW, RSZ, VSZ) == (4096, 4063232, 4060045), (RAW, RSZ, VSZ))

J = json.load(io.open(BOUNDS, encoding='utf-8'))
bounds = [int(x, 16) for x in J['bounds']]
bS = set(bounds)
ck('B2 bounds 1,392,592 条', len(bounds) == 1392592, len(bounds))
ck('B3 bounds 严格递增（单列、无重复）',
   all(bounds[i] < bounds[i + 1] for i in range(len(bounds) - 1)), len(bounds))

VS_BLOB = data[RAW:RAW + VSZ]
RAW_BLOB = data[RAW:RAW + RSZ]


# ---------------------------------------------------------------- 通用：线性扫描（记录重对齐点）
def linear_scan(blob, md):
    """64KB 分块 + 1 字节重对齐；返回 (starts, sizes, resync_sites)。"""
    starts = []
    sizes = []
    resync = []
    pos = 0
    n = len(blob)
    while pos < n:
        base = LO + pos
        seg = blob[pos:pos + 65536]
        consumed = 0
        for a, sz, mn, op in md.disasm_lite(seg, base):
            if a - base + sz > len(seg):
                break
            starts.append(a)
            sizes.append(sz)
            consumed = a - base + sz
        if consumed:
            pos += consumed
        else:
            resync.append(base)
            pos += 1
    return starts, sizes, resync


# ---------------------------------------------------------------- 1 plain（无 skipdata，VirtualSize）
print('\n== 1 plain 扫描：VirtualSize blob，记录单字节重对齐点 ==')
md = Cs(CS_ARCH_X86, CS_MODE_32)
pstarts, psz, resync = linear_scan(VS_BLOB, md)
pS = set(pstarts)
print('  起点 %d ; 首 %#x 末 %#x ; 重对齐点 %d' % (len(pstarts), pstarts[0], pstarts[-1], len(resync)))
ck('C0 plain 起点 == 1,392,527', len(pstarts) == 1392527, len(pstarts))
ck('C1 plain 起点严格递增', all(pstarts[i] < pstarts[i + 1] for i in range(len(pstarts) - 1)),
   len(pstarts))
ck('C2 重对齐点条数 == 65', len(resync) == 65, len(resync))

# ---------------------------------------------------------------- 2 65 条内部地址
print('\n== 2 bounds − plain 起点集 ==')
internal = [v for v in bounds if v not in pS]
print('  条数 %d' % len(internal))
ck('D0 bounds 中不在 plain 起点集的条数 == 65', len(internal) == 65, len(internal))
ck('D1 该集合 == plain 扫描的单字节重对齐点集合（H-B 判决性判据）',
   sorted(internal) == sorted(resync),
   'only_in_bounds=%d only_in_resync=%d'
   % (len(set(internal) - set(resync)), len(set(resync) - set(internal))))
ck('D2 全部 < VirtualSize 尾界（不在尾填充区）', all(v < TAIL for v in internal), TAIL)
print('  首尾 %#x .. %#x' % (internal[0], internal[-1]))

# ---------------------------------------------------------------- 3 逐条字节与「洞」性质
print('\n== 3 逐条：该字节在 1 字节对齐处能否解出 / 是否有某个 k=1..7 使 VA-k 起能覆盖它 ==')
md_det = Cs(CS_ARCH_X86, CS_MODE_32)
rows = []
cover_k = Counter()
for va in internal:
    off = va - LO
    b = VS_BLOB[off]
    # (a) 从 VA 自身起解：应解不出（这就是重对齐点的定义）
    self_dec = list(md_det.disasm(VS_BLOB[off:off + 16], va))
    self_ok = len(self_dec) > 0
    # (b) 是否有 k 使 VA-k 起的单条指令覆盖 VA
    ks = []
    for k in range(1, 8):
        if off - k < 0:
            continue
        ds = list(md_det.disasm(VS_BLOB[off - k:off - k + 16], va - k))
        if ds and ds[0].size > k:
            ks.append(k)
    for k in ks:
        cover_k[k] += 1
    # (c) 前一条 plain 指令（线性解码里的前驱）与后一条
    i = bisect.bisect_left(pstarts, va)
    prev = pstarts[i - 1] if i > 0 else None
    nxt = pstarts[i] if i < len(pstarts) else None
    rows.append({'va': va, 'byte': b, 'self_decodable': self_ok,
                 'covering_ks': ks, 'prev_start': prev, 'next_start': nxt,
                 'gap_prev': (va - prev) if prev is not None else None})
    print('   %#010x byte=%02x self_dec=%s covering_k=%s prev=%#x(+%d) next=%#x'
          % (va, b, 'Y' if self_ok else 'N', ks, prev or 0, (va - prev) if prev is not None else -1,
             nxt or 0))

ck('E0 65 条全部**不能**从自身起解出指令（即都是解码洞，不是某条指令的起点）',
   all(not r['self_decodable'] for r in rows), sum(1 for r in rows if r['self_decodable']))
print('  字节值分布 %s' % {hex(k): v for k, v in sorted(Counter(r['byte'] for r in rows).items())})
print('  covering_k 分布 %s （有覆盖者 %d / 65）'
      % (dict(sorted(cover_k.items())), sum(1 for r in rows if r['covering_ks'])))
print('  gap_prev（相对前一条 plain 起点）分布 %s'
      % dict(sorted(Counter(r['gap_prev'] for r in rows).items())))
ck('E1 字节值不是单一值（如实记录分布，不预设它是填充）',
   len(Counter(r['byte'] for r in rows)) > 1,
   len(Counter(r['byte'] for r in rows)))
ck('E2 存在覆盖且全部 k 落 1..5（R162/R163 写的「位移 1..7」在本口径下上界应为 5）',
   all(all(1 <= k <= 5 for k in r['covering_ks']) for r in rows),
   sorted(cover_k))
ck('E3 反控：把「被覆盖」判据放宽到 k<=16 也不会有 k>5 的新命中（上界是真的）',
   all(not list(md_det.disasm(VS_BLOB[(r['va'] - LO) - k:(r['va'] - LO) - k + 32], r['va'] - k)) or
       list(md_det.disasm(VS_BLOB[(r['va'] - LO) - k:(r['va'] - LO) - k + 32],
                          r['va'] - k))[0].size <= k
       for r in rows for k in (6, 7, 8, 12, 16)),
   'checked k in {6,7,8,12,16}')
ck('E4 有 17 条连 k<=5 也覆盖不到（它们只在线性解码序列的缝隙里，不在任何重解指令内部）',
   sum(1 for r in rows if not r['covering_ks']) == 17,
   sum(1 for r in rows if not r['covering_ks']))

# ---------------------------------------------------------------- 4 raw vs VirtualSize 口径差
print('\n== 4 raw blob 口径（解释 R162 的 1,394,120）==')
md2 = Cs(CS_ARCH_X86, CS_MODE_32)
rstarts, rsz_list, rresync = linear_scan(RAW_BLOB, md2)
print('  raw 起点 %d ; 重对齐点 %d' % (len(rstarts), len(rresync)))
ck('F0 raw 起点 == 1,394,120（R162 / R143 同值）', len(rstarts) == 1394120, len(rstarts))
ck('F1 raw 起点 − VirtualSize 起点 == 1,593（尾填充 0x00 的账）',
   len(rstarts) - len(pstarts) == 1593, len(rstarts) - len(pstarts))
tail_zero = sum(1 for b in data[RAW + VSZ:RAW + RSZ] if b == 0)
print('  尾填充字节 %d ; 其中 0x00 %d' % (RSZ - VSZ, tail_zero))
ck('F2 尾填充长度 3,187 B 且全 0x00', (RSZ - VSZ) == 3187 and tail_zero == 3187,
   (RSZ - VSZ, tail_zero))
ck('F3 1,593 × 2 + 1 == 3,187（skipdata 逐字节 vs plain 两字节 NOP 的口径差）',
   1593 * 2 + 1 == 3187)
rawset_diff = [a for a in rstarts if a not in pS]
ck('F4 raw 多出的起点全部 ≥ VirtualSize 尾界', all(a >= TAIL for a in rawset_diff),
   len(rawset_diff))

# ---------------------------------------------------------------- 5 skipdata 复算（反控）
print('\n== 5 反控：skipdata 口径（分块）与 bounds 的关系 ==')
# 说明（S-527）：skipdata 的**整段一次扫**在 4 MB 上要跑 6 分钟以上（本轮实测被 timeout 掐断），
# 故整段逐位相等这一条由独立脚本 _r166/r166c_skipdata_whole.py 承担（长跑、后台）。
# 本脚本只跑分块版，并如实记录它的**块边界伪起点**：分块版会多出若干条，本轮实测多 114 条。
md3 = Cs(CS_ARCH_X86, CS_MODE_32)
md3.skipdata = True
sstarts, ssz, sresync = linear_scan(VS_BLOB, md3)
print('  skipdata 分块口径起点 %d（重对齐点 %d）' % (len(sstarts), len(sresync)))
sset = set(sstarts)
extra = [a for a in sstarts if a not in bS]
missing = [a for a in bounds if a not in sset]
print('  分块口径多出（块边界伪起点）%d 条 ; 缺 %d 条' % (len(extra), len(missing)))
ck('G0 分块 skipdata 起点 = 1,392,706（与整段口径 1,392,592 差 114，记录两数）',
   len(sstarts) == 1392706, (len(sstarts), len(bounds)))
ck('G1 分块口径既不包含 bounds 也不被 bounds 包含：既多 188 条又缺 74 条 '
   '⇒ 分块不可用于「skipdata == bounds」这条判据（R164 的整段一次扫才是该判据的合法口径）',
   len(extra) == 188 and len(missing) == 74, (len(extra), len(missing)))
ck('G2 反控：把分块版当成整段版会造出 188 + 74 = 262 条假差 —— 这正是不能用它的理由',
   len(extra) + len(missing) == 262, len(extra) + len(missing))
ck('G3 反控：bounds ∩ plain 起点集 == 1,392,527 且 + 65 == 1,392,592（判据有分辨力）',
   len([v for v in bounds if v in pS]) == 1392527 and 1392527 + 65 == 1392592,
   len([v for v in bounds if v in pS]))
ck('G4 65 条在分块 skipdata 起点集里全部存在（= 它们是真起点，不是线性解码起点）',
   all(v in sset for v in internal), sum(1 for v in internal if v in sset))

# ---------------------------------------------------------------- 6 落盘
json.dump({'section': {'raw': RAW, 'rsz': RSZ, 'vsz': VSZ, 'lo': LO, 'tail': TAIL},
           'plain_starts': len(pstarts), 'plain_resync': len(resync),
           'raw_starts': len(rstarts), 'skip_starts': len(sstarts),
           'bounds': len(bounds), 'internal': len(internal),
           'internal_eq_resync': sorted(internal) == sorted(resync),
           'cover_k_hist': {str(k): v for k, v in sorted(cover_k.items())},
           'byte_hist': {hex(k): v for k, v in sorted(Counter(r['byte'] for r in rows).items())},
           'rows': [dict((k, (hex(v) if isinstance(v, int) else v)) for k, v in r.items())
                    for r in rows],
           'asserts': RES, 'fail': FAIL},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n== 结论 ==')
print('  断言 %d 条，FAIL %d' % (len(RES), FAIL))
print('  产物 %s' % OUT)
sys.exit(1 if FAIL else 0)
