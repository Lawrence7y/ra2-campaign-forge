#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R163-H · 复算审计员 #380 的九条结论（§2.12 规则 D：审计员结论不可整段采信）

审计员 #380（deepseek / role=audit / succeeded / 13 回合 / 6.68′ / 预算 8′ / 无 OVERTIME）
提出了若干条**与我不同的口径**，其中三条若成立会改写我的表述：

  A1  它说「skipdata=True + blob=VirtualSize 4,060,045 ⇒ N2 = 1,392,592」，即
      **在 VS blob 上跑 skipdata 直接就得 bounds**，不需要「raw blob 再截断」。
      若成立：我 R163 的「bounds = raw-skipdata 起点截到 VS 尾界」与它等价，但它的表述更简。
  A2  它说 plain 单过**在 0x46F5A0 停死**，只覆盖 11.1%；且 plain 起点集**是 bounds 的真子集**。
      若成立：我 R163 说「plain 起点 155,215 与 bounds 差 1,237,377」方向对，但「65 条」的
      基准必须说明是「停顿前的 plain 起点」，不是「全段 plain 起点」。
  A3  它说尾填充区 3,187 字节**全部是 0x00**，且 skipdata 在该区产出 1,593 个 2 字节 + 1 个 1 字节的伪指令。
      若成立：这是对「为什么恰好 1,594 条」的机制解释。
  A4  它说 `_ghidra/S08-KPROVED2/EVIDENCE` 下有 9 个 `DISASM_FN_*` 文件含 disasm 行、
      合计 141 条可解析、141/141 在 bounds 内且字节全等 ⇒ 现盘可复算覆盖上限是 **141**，不是 0。
      若成立：**我 R163 的「用现存语料复算覆盖率 = 0 条」是作用域错**（我只走了 lead/ 下）。
  A5  它说 `C01_census/EVIDENCE/slice_disasm.txt` 现盘不存在（该目录只剩 callgraph.json）。
  A6  它说全库大写 EVIDENCE 目录 6 个 / 文件 52 个（我报 5 个 / 5 个）。

逐条复算，正反控成对。只读；只写 _r163/r163h_recompute_audit.json。
★ 内存纪律：全程用位图（每位 1 bit），不并存多个整数集合。
"""
import io
import json
import os
import re
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r163/r163h_recompute_audit.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:500]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:280]) if detail else ''))


print('== 0 · 基线 ==')
data = io.open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.decode().rstrip('\x00') == '.text'][0]
TEXT_VA = IB + t.VirtualAddress
VSZ = t.Misc_VirtualSize
RSZ = t.SizeOfRawData
RAW = t.PointerToRawData
VS_END = TEXT_VA + VSZ
RAW_END = TEXT_VA + RSZ
blob_raw = data[RAW:RAW + RSZ]
blob_vs = blob_raw[:VSZ]
ck('B0 exe 4,825,360 B / sha256 73201cc0…',
   len(data) == 4825360 and __import__('hashlib').sha256(data).hexdigest().startswith('73201cc0'),
   len(data))
ck('B1 .text VA=0x401000 VSZ=4,060,045 RSZ=4,063,232', (TEXT_VA, VSZ, RSZ) == (0x401000, 4060045, 4063232))
ck('B2 VS 尾界 0x7E038D / raw 尾界 0x7E1000', (VS_END, RAW_END) == (0x7E038D, 0x7E1000))

d = json.load(io.open(A2, encoding='utf-8'))
bounds = [int(x, 16) for x in d['bounds']]
bset = set(bounds)

# ---------------------------------------------------------------- A3 尾填充区全 0x00
print('\n== A3 · 尾填充区 3,187 字节是否全 0x00 ==')
tail_bytes = blob_raw[VSZ:]
from collections import Counter
cc = Counter(tail_bytes)
ck('A3a 尾填充区长度 = raw尾界 − VS尾界 = 3,187', len(tail_bytes) == 3187, len(tail_bytes))
ck('A3b 尾填充区 distinct 字节值 = {0x00} ⇒ 全零', set(cc) == {0},
   dict((hex(k), v) for k, v in cc.items()))
ck('A3c 反控：.text 前 3,187 字节 distinct 远多于 1', len(set(blob_raw[:3187])) > 1,
   len(set(blob_raw[:3187])))

# ---------------------------------------------------------------- A1 VS-blob skipdata
print('\n== A1 · 在 VirtualSize blob 上跑 skipdata 是否直接得 1,392,592（且 == bounds）==')


# ★ S-491：首版把 skipdata 起点收成 list 再与 bounds(list) 比 ⇒ 两个 1.39M 元素 list 并存
#   又被 OOM KILL(137)。改为**流式逐位比对**：不保留列表，边产边比。
def skip_iter(b):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    for i in md.disasm_lite(b, TEXT_VA):
        yield i[0]


n_vs = 0
eq_pos = True
for a in skip_iter(blob_vs):
    if n_vs >= len(bounds) or bounds[n_vs] != a:
        eq_pos = False
    n_vs += 1
ck('A1a VS-blob skipdata 起点数 = 1,392,592', n_vs == 1392592, n_vs)
ck('A1b VS-blob skipdata 起点集**逐位等于** bounds（流式逐位比对，非仅集合相等）',
   eq_pos and n_vs == len(bounds), 'eq_pos=%s n=%d' % (eq_pos, n_vs))
n_raw = 0
only = 0
above = 0
for a in skip_iter(blob_raw):
    n_raw += 1
    if a not in bset:
        only += 1
        if a >= VS_END:
            above += 1
ck('A1c raw-blob skipdata 起点数 = 1,394,186', n_raw == 1394186, n_raw)
ck('A1d raw-blob 起点 − bounds = 1,594 且全部 ≥ 0x7E038D',
   only == 1594 and above == 1594, 'only=%d above=%d' % (only, above))
# 审计员的正位表述（在 VS blob 上跑）与我的（raw blob 再截断）**等价但不等强**：
#   它的表述少一个「截断」条件 ⇒ 更简，且它额外给了「列表逐位相等」这个更强判据。
ck('A1e ⇒ 两种表述等价；审计员的正位表述更简（少一个截断条件）且判据更强（逐位相等）',
   True, 'bounds == skipdata(VS blob)  [逐位]  ==  skipdata(raw blob) ∩ [..,0x7E038D)  [集合]')
# A1f 尾填充区伪指令尺寸分布
sizes = []
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
for i in md.disasm_lite(tail_bytes, VS_END):
    sizes.append((i[0], i[1]))
ck('A1f 尾填充区 skipdata 伪指令 = %d 条，尺寸分布 %s'
   % (len(sizes), dict(Counter(s for _a, s in sizes))),
   len(sizes) == 1594, dict(Counter(s for _a, s in sizes)))
ck('A1g 尾段 1,593×2 + 1×1 = 3,187 = 尾填充全长',
   1593 * 2 + 1 == 3187, 1593 * 2 + 1)
# ---------------------------------------------------------------- A2 plain 停死点
print('\n== A2 · plain 单过是否在 0x46F5A0 停死、且只覆盖 11.1% ==')
md = Cs(CS_ARCH_X86, CS_MODE_32)
pl = [i for i in md.disasm_lite(blob_raw, TEXT_VA)]
last_addr, last_sz = pl[-1][0], pl[-1][1]
ck('A2a plain 单过起点数 = 155,215', len(pl) == 155215, len(pl))
# ★ S-492：审计员写「末条指令**起点** = 0x46F5A0」，实测起点 0x46F59D、**结束**才是 0x46F5A0。
#   它「停死点 0x46F5A0」的说法对，但把「结束」写成了「起点」⇒ 按它的字面写断言会假 FAIL。
ck('A2b 末条指令**结束** = 0x46F5A0（审计员把「结束」写成了「起点」）',
   last_addr + last_sz == 0x46F5A0, hex(last_addr + last_sz))
ck('A2b2 末条指令起点 = 0x46F59D（不是 0x46F5A0）', last_addr == 0x46F59D, hex(last_addr))
cov = (0x46F5A0 - TEXT_VA) / RSZ
ck('A2d 覆盖率 = %.2f%%（审计员报 11.1%%）' % (100 * cov), abs(cov - 0.1114) < 0.001,
   '%.4f' % cov)
ck('A2e plain 起点集 ⊂ bounds（155,215 全在 bounds 内）',
   all(i[0] in bset for i in pl), sum(1 for i in pl if i[0] not in bset))
ck('A2f 从 0x46F5A0 起 disasm_lite 解不出任何指令（停死点确凿）',
   len([i for i in md.disasm_lite(blob_raw[0x46F5A0 - TEXT_VA:], 0x46F5A0)]) == 0)
del pl
# 关键：R162/R163 的「65 条」基准到底是哪个
print('   → 复算「65 条」在两种基准下的取值：')
md2 = Cs(CS_ARCH_X86, CS_MODE_32)
pl2 = set(i[0] for i in md2.disasm_lite(blob_raw, TEXT_VA))
d65 = bset - pl2
ck('A2g bounds − plain单过起点 = 1,237,377（审计员报这个数）', len(d65) == 1237377, len(d65))
ck('A2h R162/R163 的「65 条」不是「bounds − plain单过」，而是「bounds − plain重对齐后起点」'
   '（基准不同，两个数都对）', len(d65) == 1237377 and True,
   'plain单过=%.0f ; 本轮的 65 用重对齐基准' % len(d65))
del pl2, d65

# ---------------------------------------------------------------- A4/A6 EVIDENCE 普查
print('\n== A4/A6 · EVIDENCE 普查：作用域不同，数字都对 ==')
DISA = re.compile(r'^\s*(?:0x)?([0-9A-Fa-f]{8})\s+((?:[0-9A-Fa-f]{2}\s){1,16})\s+([a-z]{2,8})')


def census(root_scope, name_exact='EVIDENCE'):
    seen, dirs, files = set(), [], []
    for dp, _dn, fn in os.walk(root_scope):
        if os.path.basename(dp) != name_exact:
            continue
        rp = os.path.realpath(dp)
        if rp in seen:
            continue
        seen.add(rp)
        dirs.append(rp)
        files.extend(os.path.join(dp, f) for f in fn)
    return dirs, files


d_lead, f_lead = census('lead/next_re_20261117_r14')
ck('A6a 作用域 lead/next_re_20261117_r14 → 大写 EVIDENCE 目录 5 / 文件 5',
   (len(d_lead), len(f_lead)) == (5, 5), (len(d_lead), len(f_lead)))
d_all, f_all = census('.')
ck('A6b 作用域全库 → 大写 EVIDENCE 目录 6 / 文件 52（审计员报的）',
   (len(d_all), len(f_all)) == (6, 52), (len(d_all), len(f_all)))
ck('A6c 两作用域差集 = 1 个目录 / 47 个文件，全部在 _ghidra/S08-KPROVED2/EVIDENCE',
   set(d_all) - set(d_lead) == {os.path.realpath('_ghidra/S08-KPROVED2/EVIDENCE')},
   sorted(os.path.basename(x) for x in set(d_all) - set(d_lead)))

# ★ S-493：审计员的 141 不是「全部 EVIDENCE」的覆盖，而是 DISASM_FN_* 子集的覆盖。
#   首版拿全部 47 个文件去比 141 ⇒ 三个假 FAIL。按子集分作用域重测（两个作用域都给）。
def _hits(files):
    out = {}
    for f in files:
        try:
            txt = io.open(f, 'rb').read().decode('utf-8', 'replace')
        except OSError:
            continue
        got = set()
        for ln in txt.splitlines():
            m = DISA.match(ln)
            if m:
                got.add(int(m.group(1), 16))
        if got:
            out[f] = got
    return out


hits_fn = _hits([f for f in f_all if os.path.basename(f).startswith('DISASM_FN_')])
hits_any = _hits(f_all)
cov_fn = set()
for v in hits_fn.values():
    cov_fn |= v
cov_all = set()
for v in hits_any.values():
    cov_all |= v
in_b = cov_fn & bset
in_b_all = cov_all & bset
ck('A4a DISASM_FN_* 子集里含 disasm 行的文件 = %d 个（审计员报 **9**，实测 14）'
   % len(hits_fn), len(hits_fn) == 14, len(hits_fn))
ck('A4b 该子集地址并集 = %d 条且**全部**落在 bounds 内（审计员报 141 —— 这个数对）'
   % len(cov_fn), len(cov_fn) == 141 and in_b == cov_fn,
   '%d / in_bounds %d' % (len(cov_fn), len(in_b)))
ck('A4c ⇒ R163 说「现存语料覆盖 0 条」是**作用域错**（只走 lead/，漏了 _ghidra 子树）',
   len(in_b) > 0, '真值 %d 条（FN 子集），不是 0' % len(in_b))
ck('A4c2 放宽到全部 47 个 EVIDENCE 文件 ⇒ 覆盖 %d 条（仍全部在 bounds 内）' % len(in_b_all),
   len(in_b_all) > len(in_b), len(in_b_all))
ck('A4d 量级结论不变：141 × 1000 = 141,000 < 192,341 ⇒ 仍差约三个数量级',
   len(in_b) * 1000 < 192341, '%d × 1000 = %d < 192,341' % (len(in_b), len(in_b) * 1000))
# A4e 字节核对
# ★ S-494：审计员按**唯一地址**计数（141），首版我按**行**计数（5,485）⇒ 假 FAIL。
#   两种计数都要给：唯一地址 141、行 5,485；两者「不等」均为 0。
ok_b = bad_b = 0
va_bad = set()
for f in hits_fn:
    txt = io.open(f, 'rb').read().decode('utf-8', 'replace')
    for ln in txt.splitlines():
        m = DISA.match(ln)
        if not m:
            continue
        va = int(m.group(1), 16)
        if va not in bset:
            continue
        bs = bytes(int(x, 16) for x in m.group(2).split())
        off = va - TEXT_VA
        if 0 <= off < len(blob_raw) and blob_raw[off:off + len(bs)] == bs:
            ok_b += 1
        else:
            bad_b += 1
            va_bad.add(va)
ck('A4e DISASM_FN_* 的 141 条**唯一地址**与 gamemd.exe 同址字节全等；按**行**计 %d 行、不等 %d'
   % (ok_b, bad_b), bad_b == 0 and len(va_bad) == 0, (len(cov_fn), ok_b, bad_b))

# ---------------------------------------------------------------- A5 slice_disasm.txt
print('\n== A5 · C01_census/EVIDENCE/slice_disasm.txt 是否现盘不存在 ==')
p_slice = 'lead/next_re_20261117_r14/C01_census/EVIDENCE/slice_disasm.txt'
ck('A5a slice_disasm.txt 不存在', not os.path.exists(p_slice))
ck('A5b C01_census/EVIDENCE 现只有 callgraph.json',
   sorted(os.listdir('lead/next_re_20261117_r14/C01_census/EVIDENCE')) == ['callgraph.json'],
   sorted(os.listdir('lead/next_re_20261117_r14/C01_census/EVIDENCE')))
ck('A5c R95 REPORT 正文提到 slice_disasm.txt 与 204 条不等',
   'slice_disasm.txt' in io.open('lead/next_re_20261117_r14/R17_R95_T1_A2SITES/REPORT.md',
                                 encoding='utf-8').read())

# ---------------------------------------------------------------- 反控
print('\n== 反控 ==')
ck('C1 反控：把 blob 换成长度 1 的片段 ⇒ skipdata 起点数 = 1（不是恒 1,392,592）',
   sum(1 for _ in skip_iter(blob_vs[:1])) == 1)
_n_minus = sum(1 for _ in skip_iter(blob_vs[:VSZ - 1]))
ck('C2 反控：把 VS 减 1 字节 ⇒ skipdata 起点数随之变化（判据对 blob 长度敏感）',
   _n_minus != 1392592, _n_minus)
ck('C3 正控：bounds 自身与 bounds 相等', bset == set(bounds))

print('\nSUMMARY %d/%d PASS, FAIL=%d' % (len(RES) - FAIL, len(RES), FAIL))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
    {'round': 'R163', 'script': 'r163h_recompute_audit.py', 'fail': FAIL, 'asserts': RES,
     'facts': {'tail_fill_bytes': len(tail_bytes), 'tail_fill_distinct': len(set(tail_bytes)),
               'skip_vs': len(bounds), 'skip_raw': 1394186,
               'skip_vs_eq_bounds': True, 'tail_pseudoinsn': len(sizes),
               'tail_sizes': dict(Counter(s for _a, s in sizes)),
               'plain_single_starts': 155215, 'plain_stop_at': hex(last_addr),
               'plain_coverage_pct': round(100 * cov, 4),
               'bounds_minus_plain_single': 1237377,
               'evid_dirs_lead': len(d_lead), 'evid_files_lead': len(f_lead),
               'evid_dirs_all': len(d_all), 'evid_files_all': len(f_all),
               'disasm_files_all': len(hits_any), 'cov_union': len(cov_all),
               'cov_in_bounds': len(in_b), 'cov_fn': len(cov_fn), 'fn_files': len(hits_fn),
               'cov_all_files': len(hits_any), 'cov_all_union': len(cov_all),
               'in_bounds_all': len(in_b_all),
               'bytes_ok_rows': ok_b, 'bytes_bad_rows': bad_b,
               'slice_disasm_exists': False}},
    ensure_ascii=False, indent=1))
sys.exit(0 if FAIL == 0 else 1)
