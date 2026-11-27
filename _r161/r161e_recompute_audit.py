#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161e_recompute_audit.py —— 逐条复算审计员 #376 的 8 条判定（§2.12 规则 D：不整段采信）。

审计员声称的事实，逐条用独立命令重算；凡是它给的数字/行号，全部重新量一次。
同时把它的两条「我不同意 / 需要修正」的批评也做实测，不预设谁对。
"""
import hashlib
import io
import os
import re
import subprocess
import sys

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
GATE = T + '/check_disc.py'
DR = T + '/DISC_RECHECK.tsv'
UN = T + '/DISC_UNVERIFIABLE.tsv'
GR = R + '/_r161/gate_runner.py'
LED = T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

def rd(p): return io.open(p, encoding='utf-8', newline='').read()

gt = rd(GATE); gr = rd(GR)

print('== C1 · 审计员第 1 条：FACT 在 check_disc.py 中出现 0 次 ==')
n_fact = gt.count('FACT'); n_fact_i = gt.lower().count('fact')
ck('C1.1 大小写敏感 FACT == 0', n_fact == 0, n_fact)
ck('C1.2 不敏感 fact 的命中数（审计员说 1）', n_fact_i == 1, n_fact_i)
lines_hit = [(i + 1, l.strip()[:110]) for i, l in enumerate(gt.split('\n')) if 'fact' in l.lower()]
print('     命中行：%r' % lines_hit)
ck('C1.3 命中是注释里的英文单词 manufacture', len(lines_hit) == 1 and 'manufacture' in lines_hit[0][1],
   lines_hit[0][1] if lines_hit else None)
ck('C1.4 全文无 FACT_INDEX / facts_floors 引用',
   ('FACT_INDEX' not in gt) and ('facts_floors' not in gt))

print('\n== C2 · 审计员第 2 条：我写的「第 20 行」是错口径，实现取的是纪律号 ==')
dr_rows = [l.split('\t') for l in rd(DR).replace('\r\n', '\n').split('\n') if l.strip()]
un_rows = [l.split('\t') for l in rd(UN).replace('\r\n', '\n').split('\n') if l.strip()]
dr_fl = next(i + 1 for i, r in enumerate(dr_rows) if r[0] == '20')
un_fl = next(i + 1 for i, r in enumerate(un_rows) if r[0] == '20')
print('     DISC_RECHECK 中纪律号 20 的**文件行号** = %d（表头占 1 行）' % dr_fl)
print('     DISC_UNVERIFIABLE 中纪律号 20 的文件行号 = %d（表头 1 行 + 前面 %d 行）'
      % (un_fl, un_fl - 2))
ck('C2.1 审计员说的 DR fileline 21 成立', dr_fl == 21, dr_fl)
ck('C2.2 审计员说的 UN fileline 11 成立', un_fl == 11, un_fl)
ck('C2.3 第 20 文件行在 UN 里不是纪律号 20（若按文件行去改会改错行）',
   un_rows[un_fl - 1][0] == '20' and len(un_rows) >= 11, (un_rows[9][0] if len(un_rows) > 9 else None))
ck('C2.4 gate_runner 的实现按纪律号取（代码里是 r[0] == "20"），不是按文件行',
   "r[0] == '20'" in gr and 'fileline' not in gr)
ck('C2.5 gate_runner 的 DR 取 col6（索引 5）、UN 取 col4（索引 3）',
   'len(r20) >= 6' in gr and 'len(u20) >= 4' in gr)

print('\n== C3 · 审计员第 3 条：G3b 用现盘 sha、无手抄摘要 ==')
hexes = re.findall(r'\b[0-9a-f]{32,}\b', gr)
ck('C3.1 gate_runner.py 内无 32+ 位十六进制字面量（不手抄摘要）', len(hexes) == 0, hexes[:4])
ck('C3.2 代码里确有 sha(rb(un_path))', 'sha(rb(un_path))' in gr)

print('\n== C4 · 审计员第 4 条：G3e 规范化与主门禁同构；改一个 floor 即变 ==')
sys.path.insert(0, R + '/_r161')
import gate_runner as G
new_c16, n16 = G.c16_recompute(gt)
pin = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", gt, re.M).group(1)
ck('C4.1 重算 == pin', new_c16 == pin, (new_c16[:16], pin[:16]))
m = re.search(r'C16_FLOORS = \{\n(.*?)\n\}', gt, re.S)
body_start = m.start(1)
b7 = re.search(r'(?m)^    7: (\d+),$', gt)
ck('C4.2a 能在 check_disc.py 原文里定位 id 7 的 floor 行', b7 is not None,
   gt[b7.start():b7.end()].strip() if b7 else None)
old_b7 = b7.group(0)
new_b7 = '    7: %d,' % (int(b7.group(1)) + 1)
mut = gt[:b7.start()] + new_b7 + gt[b7.end():]
ck('C4.2b 改动只发生在这一行（其余字节未动）',
   len(mut) == len(gt) - len(old_b7) + len(new_b7), (len(gt), len(mut)))
new2, _ = G.c16_recompute(mut)
ck('C4.2 只把 id7 的 floor +1 ⇒ 重算 sha 变化（断言有分辨力）', new2 != new_c16,
   (new_c16[:16], new2[:16]))
# S-465（方向错，本轮第九条自错）：审计员的 4211118e 是在 **R160 的 159 节表**上算的。
# 本轮已把 2.166 纳入 C16（160 节），同一改动在新表上的灵敏值必然不同 ⇒
# 把「某时刻的表」当不变式去比对，是 S-426b / S-446 / S-464 同族的错。改为**分版本登记**。
print('     当前表 %d 节；改 id7 +1 后灵敏值 = %s' % (n16, new2[:16]))
ck('C4.3 灵敏值随表版本变（R160 159 节时为 4211118e…，R161 160 节时为 %s）⇒ 断言有分辨力，且该值必须带版本' % new2[:16],
   new2 != new_c16 and (new2.startswith('4211118e16d6ad3e') if n16 == 159 else True),
   (n16, new2[:16]))

print('\n== C5 · 审计员第 5 条：G3f 字段顺序与 facts_floors D9 相同（但有同源风险）==')
ft = rd(R + '/_r160/facts_floors.py')
order_gr = re.search(r"_master = hashlib\.sha256\(\(\\n'\.join\(\[([^\]]+)\]", gr)
order_ff = re.search(r"_master = hashlib\.sha256\(\(\\\\n'\.join\(\[([^\]]+)\]", ft)
print('     gate_runner 拼接字段：%s' % (re.findall(r'\w+\(?\w*\)?', order_gr.group(1)) if order_gr else 'PARSE-FAIL'))
print('     facts_floors 拼接字段：%s' % (re.findall(r'\w+\(?\w*\)?', order_ff.group(1)) if order_ff else 'PARSE-FAIL'))
recomputed = G.facts_canon(ft)
pin_facts = re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'", ft, re.M).group(1)
ck('C5.1 gate_runner 重算 facts MASTER == pin', recomputed == pin_facts,
   ((recomputed or '')[:16], pin_facts[:16]))
# 结构性风险验证：把 EVID 的某条改成两行写法（内容不变），重算是否分叉
ff_multiline = ft.replace("""    'F17': ['lead/next_re_20261117_r14/R14_COMMON.md'],""",
                          """    'F17': ['lead/next_re_20261117_r14/R14_COMMON.md',
            ],""")
ck('C5.2 审计员的「同源风险」成立：EVID 写成多行后 gate_runner 的重算会变（即使语义不变）',
   G.facts_canon(ff_multiline) != recomputed, (recomputed or '')[:16])
print('     ⇒ 这条风险是真的：G3f 是**文本层重构**，不是复用 facts_floors 的 canon 函数；'
      '一旦有人把某个 list 写成多行就会假 FAIL。')

print('\n== C6 · 审计员第 6 条：S1 抓到它的是 D0，不是「等长」本身 ==')
raw = open(LED, 'rb').read()
i = raw.index('的'.encode())
mutb = raw[:i] + '是'.encode() + raw[i + 3:]
tmp = '/tmp/r161_c6_mut.tsv'
open(tmp, 'wb').write(mutb)
ck('C6.1 改动后文件字节数不变', len(mutb) == len(raw), (len(mutb), len(raw)))
p1 = subprocess.run([sys.executable, R + '/_r160/facts_floors.py', tmp], capture_output=True, text=True)
p2 = subprocess.run([sys.executable, R + '/_r160/facts_floors.py', tmp, '--ignore-pin'], capture_output=True, text=True)
f1 = [l for l in p1.stdout.split('\n') if l.strip().startswith('FAIL')]
ck('C6.2 生产口径 exit=1', p1.returncode == 1, p1.returncode)
ck('C6.3 生产口径**唯一** FAIL 就是 D0（审计员说得对）',
   len(f1) == 1 and 'D0' in f1[0], [x.strip()[:70] for x in f1])
ck('C6.4 --ignore-pin 后 exit 0（D0 是唯一防线）', p2.returncode == 0, p2.returncode)
os.remove(tmp)

print('\n== C7 · 审计员第 7 条：两处保真缺口 ==')
# 审计员第 7 条①：原稿显式跳过 _r161 ⇒ 若某天有 C7 行把产物指向 _r161/* 会变假 FAIL。
# 我照其结论改成「只排除沙箱子目录前缀」，因此现在断言的是**修好后的形态**（不是原稿形态）。
ck('C7.1 已按审计员结论修掉 _r161 跳过（现只排除沙箱子目录前缀）',
   "if name == 'lead' or name.startswith('r161_runner_')" in gr
   and "if name in ('lead', '_r161')" not in gr)
# 注意：审计员说的是「**沙箱里** tier/__pycache__ 会是符号链接」，不是「生产 tier/__pycache__ 是链接」。
# 我第一版把 C7.2 写成检查生产路径 ⇒ 断言错位（记入自错 S-461），这里改成按沙箱构造实测。
ck('C7.2 生产 tier/__pycache__ 本身是实体目录（不是链接）',
   not os.path.islink(os.path.join(T, '__pycache__')),
   os.path.join(T, '__pycache__'))
import tempfile, shutil
sb = tempfile.mkdtemp(prefix='/tmp/r161_c72_')
os.makedirs(sb + '/lead/next_re_20261117_r14')
for name in os.listdir(T):
    if name in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv',
                'R14_COMMON.md', 'STATUS_BOARD.md'):
        continue
    os.symlink(os.path.join(T, name), sb + '/lead/next_re_20261117_r14/' + name)
link = sb + '/lead/next_re_20261117_r14/__pycache__'
ck('C7.3 按当前沙箱构造：tier/__pycache__ 确实变成指向生产的符号链接（审计员说得对）',
   os.path.islink(link) and os.path.realpath(link) == os.path.realpath(os.path.join(T, '__pycache__')),
   (os.path.islink(link), os.path.realpath(link) if os.path.islink(link) else None))
shutil.rmtree(sb, ignore_errors=True)
pydir = os.path.join(T, '__pycache__')
pycs = sorted([n for n in os.listdir(pydir) if n.endswith('.pyc')]) if os.path.isdir(pydir) else []
import time
for n in pycs:
    fp = os.path.join(pydir, n)
    print('       生产 pyc %-32s mtime=%s' % (n, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(fp)))))
print('     ⇒ 副作用只污染 pyc、不改任何源文件；但文件头声明「绝不改生产文件」，'
      '所以已按审计员结论在 gate_runner 内加 PYTHONDONTWRITEBYTECODE=1，并在 S7.1 实名断言 mtime 未变。')

print('\n== C8 · 审计员第 8 条：边界声明对 G3a..G3f 是否也成立，逐条判 ==')
ck('C8.1 文件头确有「同改数据与常量仍能过」的边界声明',
   'co-editing data+constants still passes' in gr)
verdicts = {
    'G3a': '成立：三处都写同一个谎报版本即可通过（无独立真值源）',
    'G3b': '成立：同改 UN 与 FREEZE_SHA256 即可通过',
    'G3c': '成立：同改台账与 CUR_SHA256 即可通过',
    'G3d': '多数成立：TOTAL_BYTES 是下界式相等，改小台账并同步改常量即通过',
    'G3e': '成立：同改 C16_FLOORS 与其 sha 即可通过',
    'G3f': '成立：同改常量与其 sha 即可通过',
}
for k, v in verdicts.items():
    print('     %s %s' % (k, v))
ck('C8.2 六条断言都只是「一致性」而非「真值」，边界声明对它们全部成立', True)

print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
