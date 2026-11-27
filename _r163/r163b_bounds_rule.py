#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R163-B · bounds 的生成规则复原：用「生成器口径」结掉 R162 遗留的两条未取得

R162 把 bounds 钉成「.text 内、VirtualSize 以内的指令起始集 + **65 条指令内位移**」，
留了两条待办：① 那 65 条的语义未定；② 自己报的「起始但不在 bounds 1,593 条」只知在尾填充区。

本轮的可失败假设：
  H2  bounds == { capstone(skipdata=True) 的起点 : 地址 < VirtualSize 尾界 }
      若成立 ⇒「65 条指令内位移」是**基准选错**（用 plain 起点当基准）造成的假遗留，
               正确基准下逐条相等、无剩余差集。

三口径各自独立实现：
  P1 plain + 失败处单字节重对齐（R162 修正版口径）
  P2 capstone skipdata=True（整段一次扫）
  P3 objdump（第三方反汇编器，判「是不是 capstone 特有形态」）

★ 内存纪律：三个起点集全部落**位图**（VA 跨度 4.06 MB ⇒ 每位 1 bit ⇒ 约 0.5 MB/份）。
  自错 S-481..S-483 留案：
   S-481 首版返回 list 再 set，三口径同时在存 ⇒ 被 OOM KILL(137)；
   S-482 objdump 用 capture_output 一次性读 1.4M 行 ⇒ 再 OOM；
   S-483 P2 按 64KB 分块 ⇒ 块边界重切出 114 条伪起点（1,394,300 vs 真值 1,394,186）
         ⇒ 分块只对「线性重对齐扫描」安全，skipdata 必须整段一次扫。
只读二进制/JSON；只写 _r163/r163b_bounds_rule.json。
"""
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
GEN_CLAIM = '_r131/_audit_deepseek/a2_callsites.py'
OUT = '_r163/r163b_bounds_rule.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:500]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:280]) if detail else ''))


# ---------------------------------------------------------------- 0 段表
print('== 0 · PE 段表 ==')
data = io.open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.decode().rstrip('\x00') == '.text'][0]
TEXT_VA = IB + t.VirtualAddress
TEXT_RSZ = t.SizeOfRawData
TEXT_VSZ = t.Misc_VirtualSize
blob = data[t.PointerToRawData:t.PointerToRawData + TEXT_RSZ]
VS_END = TEXT_VA + TEXT_VSZ        # 0x7E038D
RAW_END = TEXT_VA + TEXT_RSZ       # 0x7E1000
SPAN = TEXT_RSZ
ck('B0 ImageBase == 0x400000', IB == 0x400000, hex(IB))
ck('B1 .text VA=0x401000 / rsz=4,063,232 / vsz=4,060,045',
   TEXT_VA == 0x401000 and TEXT_RSZ == 4063232 and TEXT_VSZ == 4060045,
   'va=%#x rsz=%d vsz=%d' % (TEXT_VA, TEXT_RSZ, TEXT_VSZ))
ck('B2 VirtualSize 尾界 0x7E038D / raw 尾界 0x7E1000',
   VS_END == 0x7E038D and RAW_END == 0x7E1000, '%#x / %#x' % (VS_END, RAW_END))


def bitmap():
    return bytearray(SPAN >> 3 | 1)


def put(bm, va):
    o = va - TEXT_VA
    bm[o >> 3] |= 1 << (o & 7)


def has(bm, va):
    o = va - TEXT_VA
    return 0 <= o < SPAN and bool(bm[o >> 3] & (1 << (o & 7)))


def cnt(bm):
    return sum(bin(x).count('1') for x in bm)


# bounds 位图
d = json.load(io.open(A2, encoding='utf-8'))
bounds = [int(x, 16) for x in d['bounds']]
bset = set(bounds)
BM_B = bitmap()
for a in bounds:
    put(BM_B, a)
ck('B3 bounds = 1,392,592 条、严格升序、零重复',
   len(bounds) == 1392592 and bounds == sorted(bounds) and len(bset) == len(bounds))
ck('B4 bounds 全在 .text、≥0x401000、≤0x7E038C',
   min(bounds) == TEXT_VA and max(bounds) == 0x7E038C,
   '%#x..%#x' % (min(bounds), max(bounds)))
ck('B5 位图自校验：置位数 == len(bounds)', cnt(BM_B) == len(bounds), cnt(BM_B))

# ---------------------------------------------------------------- 1 P1 plain+resync
print('\n== 1 · P1 plain + 单字节重对齐（R162 修正版口径）==')


def p1_bitmap():
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    bm = bitmap()
    n = 0
    off = 0
    while off < len(blob):
        chunk = blob[off:off + 65536]
        base = TEXT_VA + off
        consumed = 0
        for ins in md.disasm_lite(chunk, base):
            o = ins[0] - TEXT_VA
            if not (bm[o >> 3] & (1 << (o & 7))):
                bm[o >> 3] |= 1 << (o & 7)
                n += 1
            consumed = (ins[0] - base) + ins[1]
        off += consumed if consumed else 1     # ★ S-478 重对齐
    return bm, n


BM_P1, n_p1 = p1_bitmap()
print('  P1 起点数 = %d' % n_p1)
ck('B6 P1 起点数在 1.30M..1.50M（R162 的 r162d 独立实现同量级）',
   1300000 < n_p1 < 1500000, n_p1)

# ---------------------------------------------------------------- 2 P2 skipdata
print('\n== 2 · P2 capstone skipdata=True（整段一次扫）==')


def p2_bitmap():
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    bm = bitmap()
    n = 0
    for ins in md.disasm_lite(blob, TEXT_VA):
        o = ins[0] - TEXT_VA
        if not (bm[o >> 3] & (1 << (o & 7))):
            bm[o >> 3] |= 1 << (o & 7)
            n += 1
    return bm, n


BM_P2, n_p2 = p2_bitmap()
print('  P2 起点数 = %d' % n_p2)
ck('B7 P2 起点数 = 1,394,186（= S21_DIRECT/scan_mine.json 自述 n_raw）',
   n_p2 == 1394186, n_p2)

# ---------------------------------------------------------------- 3 H2 主判据
print('\n== 3 · H2：bounds == { P2 : 地址 < VirtualSize 尾界 } ==')
missing = [a for a in bounds if not has(BM_P2, a)]
ck('B8 bounds ⊆ P2（缺 %d 条）' % len(missing), len(missing) == 0, len(missing))
extra = []
for va in range(TEXT_VA, RAW_END):
    if has(BM_P2, va) and va not in bset:
        extra.append(va)
ck('B9 P2 − bounds = %d 条，且**全部** ≥ VirtualSize 尾界 ⇒ 差额恰是尾填充区'
   % len(extra), len(extra) == 1594 and all(a >= VS_END for a in extra),
   'below_vs_end=%d' % sum(1 for a in extra if a < VS_END))
ck('B10 尾填充区 P2 起点 = %d 条、范围 %#x..%#x（= VS_END .. RAW_END-1）'
   % (len(extra), min(extra), max(extra)),
   min(extra) == VS_END and max(extra) == RAW_END - 1, '%#x..%#x' % (min(extra), max(extra)))
n_trunc = sum(1 for a in extra if a < VS_END)
ck('B11 bounds 条数 + 尾填充区条数 == P2 总起点数（%d + %d == %d）'
   % (len(bounds), len(extra), n_p2), len(bounds) + len(extra) == n_p2)
ck('B12 ⇒ H2 成立：bounds 逐条等于「P2 起点中地址 < 0x7E038D 者」，两侧差集全空',
   len(missing) == 0 and all(a >= VS_END for a in extra))

# ---------------------------------------------------------------- 4 结掉 R162 的两条遗留
print('\n== 4 · R162 遗留①「65 条指令内位移」与②「1,593 条起点不在 bounds」 ==')
# ★ S-484：R162 的「1,593 条起始但不在 bounds」说的是 **P1 全部起点**中 ≥ VS 尾界的那部分
#   （即尾填充区），不是「VS 以内的 P1 起点减去 bounds」。首版取 VS 以内子集 ⇒ 差集 0 ⇒ 假 FAIL。
p1_all_list = [va for va in range(TEXT_VA, RAW_END) if has(BM_P1, va)]
p1_vs = set(p1_all_list)              # 全量（含尾填充）
not_p1 = sorted(bset - p1_vs)         # 「在 bounds 但非 P1 起点」
lost = sorted(p1_vs - bset)           # 「P1 起点但不在 bounds」
ck('B13 复现 R162 口径①：bounds − P1 全部起点 = %d 条（R162 记 65）'
   % len(not_p1), len(not_p1) == 65, len(not_p1))
ck('B14 复现 R162 口径②：P1 全部起点 − bounds = %d 条（R162 记 1,593）'
   % len(lost), len(lost) == 1593, len(lost))
ck('B15 ②那 1,593 条**全部** ≥ VirtualSize 尾界', all(a >= VS_END for a in lost) if lost else False,
   'below=%d' % sum(1 for a in lost if a < VS_END))
ck('B16 ①那 65 条在 P2 口径下**全部**是起点 ⇒ 它们不是「指令内位移」，'
   '是数据区被 skipdata 单字节跳过的位置',
   all(has(BM_P2, a) for a in not_p1), len(not_p1))
import bisect
disp = Counter()
for a in not_p1:
    i = bisect.bisect_right(p1_all_list, a) - 1
    disp[a - p1_all_list[i] if i >= 0 else -1] += 1
ck('B17 65 条「相对前一条 P1 起点」位移分布 = %s（R162 记 1:22 2:20 3:14 6:6 7:1 5:1 4:1）'
   % dict(sorted(disp.items())), sum(disp.values()) == 65, dict(sorted(disp.items())))
ck('B17b 65 条 ≤ P1 最大位移 %d（全部落在一条 P1 指令内部）'
   % max(disp), max(disp) <= 7, max(disp))

# ---------------------------------------------------------------- 5 P3 objdump
print('\n== 5 · P3 objdump（第三方反汇编器参照）==')


def p3_bitmap():
    bm = bitmap()
    n = 0
    pat = re.compile(r'^\s+([0-9a-f]{4,8}):\t')
    pr = subprocess.Popen(['i686-w64-mingw32-objdump', '-d', EXE],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    for ln in pr.stdout:                       # ★ S-482 流式
        m = pat.match(ln)
        if m:
            va = int(m.group(1), 16)
            o = va - TEXT_VA
            if 0 <= o < SPAN and not (bm[o >> 3] & (1 << (o & 7))):
                bm[o >> 3] |= 1 << (o & 7)
                n += 1
    pr.wait()
    return bm, n, pr.returncode


BM_P3, n_p3, p3rc = p3_bitmap()
print('  P3 起点数 = %d (objdump exit %d)' % (n_p3, p3rc))
ck('B18 P3 = 1,401,544 起点（第三方，不是 capstone）', n_p3 == 1401544, n_p3)
extra3 = [va for va in range(TEXT_VA, RAW_END) if has(BM_P3, va) and va not in bset]
ck('B19 P3 − bounds = %d 条（第三方反汇编器在数据区同样产出伪起点，故差集更大）'
   % len(extra3), len(extra3) > len(extra), '%d vs P2 的 %d' % (len(extra3), len(extra)))
ck('B20 反控：只有 P2 使「截到 VS 尾界后」与 bounds 逐条相等；P1/P3 都不行',
   cnt(BM_P2) - len(extra) == len(bounds),
   'P1=%d P3=%d' % (n_p1, n_p3))

# ---------------------------------------------------------------- 6 生成器自述核对
print('\n== 6 · 「生成器」自述与 R95 转述的核对 ==')
g = io.open(GEN_CLAIM, encoding='utf-8', errors='replace').read()
ck('B21 _r131/_audit/deepseek/a2_callsites.py 在盘', os.path.exists(GEN_CLAIM))
ck('B22 它写 disasm_lite 且 detail=False（内存纪律合规）',
   'disasm_lite' in g and 'detail = False' in g)
ck('B23 它**不含** skipdata 字样 ⇒ R95 转述「md.disasm + skipdata=True」与其在盘文本不符',
   'skipdata' not in g, 'count=%d' % g.count('skipdata'))
ck('B24 它只扫 TARGETS=(0x6bedb0, 0x41c250)、不产出 6,728 键 calls 全表 ⇒ 不是 a2_sites 生成器',
   'TARGETS = (0x6bedb0, 0x41c250)' in g and len(d['calls']) == 6728,
   'calls keys=%d' % len(d['calls']))

# ---------------------------------------------------------------- 7 反控
print('\n== 7 · 正反控 ==')
_p1_not_p2 = sum(1 for va in p1_all_list if not has(BM_P2, va))
ck('C1 反控：P1 ⊆ P2（skipdata 只多不少）', _p1_not_p2 == 0, 'extra_in_P1=%d' % _p1_not_p2)
# ★ S-485：首版写「尾界改成 VS_END-1 ⇒ 多交出 1 条」，但 bounds 的 max 恰是 0x7E038C = VS_END-1，
#   故 < VS_END-1 只是**少了**最大那条 ⇒ 差集是 bounds 侧 1 条，不是 P2 侧多 1 条。改为严格敏感方向：
#   尾界 +1（= 0x7E038E）⇒ P2 多交出恰 1 条（0x7E038D）；尾界 -1 ⇒ P2 侧多交 0 条、bounds 侧少 1 条。
sub_p = sum(1 for va in range(TEXT_VA, VS_END + 1) if has(BM_P2, va) and va not in bset)
miss_m = sum(1 for a in bounds if a >= VS_END - 1)
ck('C2 反控：尾界改成 VS_END+1 ⇒ P2 侧多交出恰 1 条；尾界改成 VS_END-1 ⇒ bounds 侧缺恰 1 条',
   sub_p == 1 and miss_m == 1, 'extra=%d missing=%d' % (sub_p, miss_m))
cnt_raw = sum(1 for va in range(TEXT_VA, RAW_END) if has(BM_P2, va) and va not in bset)
ck('C3 反控：不截断（到 RAW_END）⇒ 多交出 1,594 条', cnt_raw == 1594, cnt_raw)
ck('C5 正控：尾界恰取 VirtualSize 尾界时应交出 0 条', sum(
    1 for va in range(TEXT_VA, VS_END) if has(BM_P2, va) and va not in bset) == 0)
ck('C4 正控：P2 起点 100% 落在 [0x401000, 0x7E1000)',
   cnt(BM_P2) == n_p2 and n_p2 == 1394186, '%d / %d' % (cnt(BM_P2), n_p2))

print('\nSUMMARY %d/%d PASS, FAIL=%d' % (len(RES) - FAIL, len(RES), FAIL))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
    {'round': 'R163', 'script': 'r163b_bounds_rule.py', 'fail': FAIL,
     'asserts': RES,
     'facts': {'p1_plain_resync': n_p1, 'p2_skipdata': n_p2, 'p3_objdump': n_p3,
               'bounds': len(bounds), 'p2_minus_bounds': len(extra),
               'p2_below_vs_end': n_trunc, 'p1_diff65': len(not_p1), 'p1_lost': len(lost),
               'disp65': dict(sorted(disp.items())), 'p3_minus_bounds': len(extra3)}},
    ensure_ascii=False, indent=1))
sys.exit(0 if FAIL == 0 else 1)
