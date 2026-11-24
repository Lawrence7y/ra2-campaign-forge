# -*- coding: utf-8 -*-
"""把 20 条 exists 升级为内容级校验式；只改 DISC_RECHECK.tsv 第 6 列（索引5）。
   读备份、逐字段替换、写回、回读校验：28 行 / 7 列 / 其余 6 列逐字未变。
"""
import io, os, sys

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LIVE = os.path.join(R14, 'DISC_RECHECK.tsv')
BAK  = os.path.join(R14, 'R17_R90_T2_DISCUP', 'DISC_RECHECK.BEFORE.tsv')

# 纪律号 -> 新校验式（表达式不含字面空格；✓(...) 注释会被 check_disc.py / 本验证器按首空格剥离）
UP = {
 '3':  r'grep=池未加载\(未核验\)\s+0 ✓(L16 未核验=0)',
 '4':  r'grep=节号体例通过\s+15 ✓(L15 节号锚通过=15)',
 '5':  r'grep=复合条目的锚是并集 ✓(L5 F34 行逐字引用)',
 '6':  r'grep=审计把「在锚里」说成「不在锚里」 ✓(L4 F28 行)',
 '7':  r'grep=REFUTED-OVERSTRICT ✓(L7 F21 复核结论)',
 '8':  r'grep=列与列之间没有同步 ✓(L125 第二次犯例结论)',
 '10': r'grep=当不变量用的只有 ✓(L98 不变量清单)',
 '11': r'grep=控制组总判定：\*\*PASS ✓(L19 控制组全通过)',
 '12': r'grep=闭集合声明（纪律\s*12①） ✓(报告头 L3)',
 '13': r'grep=控制组（四个子检查全都要） ✓(checkC3.py L181)',
 '14': r'grep=checkC3_report_FAIL\.md ✓(checkC3.py L264 FAIL 落盘)',
 '15': r'grepcount=所在节分布=3 ✓(L78-80 三方分布)',
 '16': r'grepcount=\*\*相同\*\*=3 ✓(三文件 mtime/字节未变)',
 '17': r'grepcount=out_excl=2 ✓(自身产物目录显式排除)',
 '18': r'grep=12:07.*无产物 ✓(历史时刻无产物)',
 '19': r'grep=逐字节闭合 ✓(漂移分解闭合)',
 '21': r'grep=2×2\s*溯源表 ✓(375/333/384 溯源)',
 '23': r'grep=为什么该在一边 ✓(8 族判据表)',
 '24': r'grep=附注性限定语 ✓(构成性/附注性区分)',
 '25': r'grep=丢\s*re\.I ✓(审计员 flags 丢失)',
}

def read(p):
    return io.open(p, encoding='utf-8', newline='').read()

src = read(BAK)
lines = src.split('\n')
# 末尾空串处理：保留原样
trailing = lines[-1] == ''
body = lines[:-1] if trailing else lines
assert len(body) == 29, '头部+28 数据行，实际 %d' % len(body)
head = body[0]
data = body[1:]
assert len(data) == 28
for l in data:
    assert len(l.split('\t')) == 7, '列数异常: %r' % l[:40]

changed = []
new_data = []
for l in data:
    f = l.split('\t')
    num = f[0]
    if num in UP:
        before = f[5]
        assert before.startswith('exists '), '非 exists: 纪律%s %r' % (num, before)
        f[5] = UP[num]
        changed.append((num, before, f[5]))
    new_data.append('\t'.join(f))

out_lines = [head] + new_data + ([''] if trailing else [])
io.open(LIVE, 'w', encoding='utf-8', newline='').write('\n'.join(out_lines))
print('WROTE', LIVE, 'changed', len(changed))

# ---- 回读校验 ----
rb = read(LIVE)
rl = rb.split('\n')
rtrailing = rl[-1] == ''
rbody = rl[:-1] if rtrailing else rl
assert rtrailing == trailing, '末尾换行状态变了'
assert len(rbody) == 29, '回读行数异常 %d' % len(rbody)
assert rbody[0] == head, '表头变了'
assert len(rbody) - 1 == 28
for i, (old_l, new_l) in enumerate(zip(data, rbody[1:])):
    of, nf = old_l.split('\t'), new_l.split('\t')
    assert len(nf) == 7, '回读列数异常 行%d' % (i+2)
    for c in (0,1,2,3,4,6):
        assert of[c] == nf[c], '非校验式列被改: 行%d 列%d 纪律%s' % (i+2, c, of[0])
    if of[0] in UP:
        assert nf[5] == UP[of[0]], '校验式未按计划写入 纪律%s' % of[0]
    else:
        assert nf[5] == of[5], '未升级行校验式被改 纪律%s' % of[0]
print('READBACK OK: 28 行 / 7 列 / 其余 6 列逐字未变 / 升级 %d 条 / 未升级 %d 条'
      % (len(changed), 28 - len(changed)))
print('UPGRADED_NUMS=' + ','.join(sorted(changed, key=lambda x:int(x[0])) and [c[0] for c in sorted(changed, key=lambda x:int(x[0]))]))
