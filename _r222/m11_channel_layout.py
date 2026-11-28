# -*- coding: utf-8 -*-
"""R222 m11：0x7c62ac 的三份副本按「声道」而非「位宽」划分（修正 m8 的初步定性）。

命题：
  P1 copy1 只用 ch1 字段（+0x10 计数 / +0x14 预测器 / +0x1c nibble 缓存 / +0x1e 当前 nibble / +0x20 step / +0x22 index）。
  P2 copy3 只用 ch2 字段（+0x24 计数 / +0x2c delta / +0x30 缓存 / +0x32 nibble / +0x34 step / +0x36 index）。
  P3 两套字段基址相差 0x14（+0x10 vs +0x24、+0x1c vs +0x30、+0x20 vs +0x34、+0x22 vs +0x36），
     唯独 delta 累加器不对称（ch1 用 +0x18、ch2 用 +0x2c，差 0x14）。
  P4 0x7c6270 初始化两套完整状态（8 个字段），0x7c6730 只初始化两套的「index + predictor」四个字段
     （+0x22/+0x14 与 +0x36/+0x28）—— 与两声道布局自洽。
反控：
  R1 若 copy3 是「位宽分支」而不是 ch2，则它不应出现 +0x2c/+0x30/+0x32/+0x34/+0x36 这些只被它使用的字段。
  R2 若 ch2 基址与 ch1 相同（单套状态），则 copy1 与 copy3 的字段集应相交 —— 实测是否相交。
"""
import sys, re, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
fails = []


def ck(n, c, d=''):
    if not c:
        fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))


def dis(lo, hi):
    o = P.r2o(lo)
    b = P.RAW[o:o + (hi - lo)]
    return [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in md.disasm(b, lo)]


def fields(lo, hi):
    c = collections.Counter()
    for a, b, mn, op in dis(lo, hi):
        for m in re.finditer(r'\[ebx \+ (0x[0-9a-f]+)\]', op):
            c[m.group(1)] += 1
    return c


COPIES = [('copy1', 0x7c62ea, 0x7c63e8), ('copy2', 0x7c63ea, 0x7c6509), ('copy3', 0x7c6509, 0x7c6609)]
F = {nm: fields(lo, hi) for nm, lo, hi in COPIES}
for nm in F:
    print('%-6s %s' % (nm, dict(sorted(F[nm].items(), key=lambda kv: int(kv[0], 16)))))

# 0x38 是共享的格式字段（16/8 位判定），不属于任一声道；比较时统一排除
FMT = {'0x38'}
CH1 = {'0x10', '0x14', '0x18', '0x1c', '0x1e', '0x20', '0x22'}
CH2 = {'0x24', '0x28', '0x2c', '0x30', '0x32', '0x34', '0x36'}
ck('P1 copy1 只用 ch1 字段（+0x38 格式字段除外）', set(F['copy1']) - FMT <= CH1, sorted(set(F['copy1']) - FMT - CH1))
ck('P2 copy3 只用 ch2 字段（+0x38 格式字段除外）', set(F['copy3']) - FMT <= CH2, sorted(set(F['copy3']) - FMT - CH2))
ck('R2 反控：copy1 与 copy3 的状态字段集不相交（只共享 +0x38）',
   (set(F['copy1']) & set(F['copy3'])) == FMT, sorted(set(F['copy1']) & set(F['copy3'])))
pairs = [('0x10', '0x24'), ('0x14', '0x28'), ('0x1c', '0x30'), ('0x1e', '0x32'), ('0x20', '0x34'), ('0x22', '0x36')]
ck('P3 六对字段基址差恒为 0x14', all(int(b, 16) - int(a, 16) == 0x14 for a, b in pairs),
   [(a, b, int(b, 16) - int(a, 16)) for a, b in pairs])
ck('P3b delta 累加器 ch1=+0x18 / ch2=+0x2c 差 0x14', 0x2c - 0x18 == 0x14 and '0x18' in F['copy1'] and '0x2c' in F['copy3'],
   ('0x18' in F['copy1'], '0x2c' in F['copy3']))
ck('P4 0x7c6270 初始化 8 个字段（两套完整状态）',
   len([1 for a, b, mn, op in dis(0x7c6270, 0x7c62ac)
        if mn == 'mov' and op.startswith(('word ptr [eax', 'dword ptr [eax'))]) == 8)
init1 = []
for a, b, mn, op in dis(0x7c6730, 0x7c6752):
    m = re.match(r'(word|dword) ptr \[eax \+ (0x[0-9a-f]+)\], (.+)$', op)
    if mn == 'mov' and m:
        init1.append((m.group(2), m.group(3)))
ck('P4b 0x7c6730 初始化的四字段 = +0x22/+0x14（ch1 index/pred）+ +0x36/+0x28（ch2 index/pred）',
   {f for f, v in init1} == {'0x22', '0x14', '0x36', '0x28'}, init1)
# copy2 的字段集与位宽分支
ck('P5 copy2 仍用 ch1 字段（+0x10/+0x18/+0x1c/+0x1e/+0x20/+0x22），它是 ch1 的立体声交错路径',
   set(F['copy2']) - FMT <= CH1, sorted(set(F['copy2']) - FMT - CH1))
c2 = [(hex(a), op) for a, b, mn, op in dis(0x7c63ea, 0x7c6509)
      if mn == 'cmp' and op == 'word ptr [ebx + 0x38], 0x10']
c3 = [(hex(a), op) for a, b, mn, op in dis(0x7c6509, 0x7c6609)
      if mn == 'cmp' and op == 'word ptr [ebx + 0x38], 0x10']
ck('P6 copy2 内 16 位判定 2 次、copy3 内 1 次（各自内联，非共享）', len(c2) == 2 and len(c3) == 1, (c2, c3))
# 反控 R1
ck('R1 反控：ch2 专属字段（+0x2c/+0x30/+0x32/+0x34/+0x36）在 copy1/copy2 中出现 0 次',
   not any(f in F['copy1'] or f in F['copy2'] for f in ('0x2c', '0x30', '0x32', '0x34', '0x36')),
   {'copy1': sorted(F['copy1']), 'copy2': sorted(F['copy2'])})

print()
print('FAIL 数 =', len(fails), fails)
if fails:
    raise SystemExit(1)
