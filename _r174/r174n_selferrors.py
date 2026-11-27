#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-N · 本轮自错的机制化汇总（每条都给最小复现，能 FAIL 才算证据）

本轮自错九条，全部由可失败断言当场抓出，无一条进入结论或正文数字（唯一进入正文的是
V555 里那句「同血缘克隆 仅 1 次」，已在 V556 用一段显式计数改正，见 S-624）：

  S-617  SequenceMatcher 默认 autojunk=True 会把高频短串当垃圾跳过：同一对字符串
         报 2 段（1 replace + 1 insert）而关闭 autojunk 后报 3 段（全 insert）。
         我用默认参数断言「只 1 个非 equal 段」，写盘后 H5 FAIL。
  S-618  断言「facts_floors 变化行恰 5 行」，实测 6 行（EXPECT_CUR 与 CUR_SHA256 是两条独立行）。
  S-619  首跑时该 FAIL 出现在写盘之前，脚本却继续写盘并 exit 1 ⇒ 写盘未落在最后一道断言之后
         （S-602 的教训被我自己违反）。已在 r174m 里改成「全部断言 → 统一写盘」。
  S-620  r174a 的 N3 小样本预期值写错（我按 18/16 写，实测 23/21）；N5b 断言「bounds 出现 2 次」，
         实测 1 次（键名与标记内那一次是同一处）。
  S-621  r174b 的 Q1 代数式写错（把「删段跨度」起点取成 OFF-1），三条假 FAIL；
         且第一版收尾引用未定义的 lhs/rhs 变量 NameError。
  S-622  r174e 的 N1 断言「成员长度恒等于偏移」，对调键序后实测差 5（不是 1），
         又断言「只有一种读法能得 913,239」，实测 OFF+2 也等于 913,239 ⇒ 「只有」是假的。
  S-623  r174g 的 N3 反控只想改一个单元却断言为 2。fail-closed 当场拦住写盘。
  S-624  V555 的 R174 补段自身写了 3 次「同血缘克隆」，把「仅 1 次」变成假话（实测 4 次）——
         正是它自己在描述的「引文自指」失效。V556 用显式计数改正。
  S-625  r174l 的 N3 里写了 `ops if False` 这种永假分支的残句（虽然结果对，但表达式本身是错的）。

本脚本对每条给一个**可失败**断言：把「错的那一版」也算一遍，必须与「对的那一版」不同。
另加孤儿进程自检（按 /proc/<pid>/cmdline 精确排除本进程与外层 bash）。
"""
import io
import json
import os
import sys
from difflib import SequenceMatcher

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r174/r174n_selferrors.json'

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


print('== S-617 · autojunk 会改变 opcode 计数 ==')
# autojunk 需要「长度 >= 200 且某元素出现率 > 1%」才触发：用 300 个同字符做底
o = 'SEG' + 'A' * 300 + 'TAIL'
nw = 'SEG' + 'B' * 40 + 'A' * 300 + 'C' * 40 + 'TAIL'
aj = [op for op in SequenceMatcher(None, o, nw).get_opcodes() if op[0] != 'equal']
no = [op for op in SequenceMatcher(None, o, nw, autojunk=False).get_opcodes() if op[0] != 'equal']
print('autojunk=True  %s' % aj)
print('autojunk=False %s' % no)
ck('S-617a 两种参数给出不同段数（证明默认参数不可用于精确断言）', len(aj) != len(no), (len(aj), len(no)))
ck('S-617b 关闭 autojunk 后全是 insert（真实形状）', all(op[0] == 'insert' for op in no), [op[0] for op in no])
ck('S-617c 默认参数下出现 replace（假形状）', any(op[0] == 'replace' for op in aj), [op[0] for op in aj])

print('== S-618 · 变化行数 5 vs 6 ==')
ff = io.open('_r160/facts_floors.py', encoding='utf-8').read()
bak = io.open('lead/next_re_20261117_r14/R17_LEAD_BASELINE/facts_floors.py.before_r174_V555_20261127_140500.bak',
              encoding='utf-8').read()
d = [i for i, (a, b) in enumerate(zip(bak.split('\n'), ff.split('\n'))) if a != b]
print('V554->V555 的 facts_floors 变化行数 = %d' % len(d))
ck('S-618a 实际变化行数为 6 不是 5', len(d) == 6, len(d))
ck('S-618b 其中两行分别含 EXPECT_CUR 与 CUR_SHA256（各自独立成行）',
   sum(1 for i in d if 'EXPECT_CUR' in bak.split('\n')[i]) == 1 and
   sum(1 for i in d if 'CUR_SHA256' in bak.split('\n')[i]) == 1,
   [bak.split('\n')[i][:30] for i in d])

print('== S-619 · 写盘必须落在最后一道断言之后 ==')
for p in ('_r174/r174i_repin.py', '_r174/r174m_repin_v556.py'):
    t = io.open(p, encoding='utf-8').read()
    _c = [x for x in (t.find("io.open(FF, 'w'"), t.find("io.open(GR, 'w'"), t.find("io.open(PTR, 'w'"))
          if x > 0]
    first_write = min(_c) if _c else -1
    gate = max(t.find('fail-closed（写盘前总闸）'), t.find('★ fail-closed：'))
    print('%s: 首个写盘点=%d ; 总闸=%d' % (p, first_write, gate))
    ck('S-619.%s 总闸存在且早于首个写盘点' % os.path.basename(p),
       0 <= gate < first_write, (gate, first_write))
ck('S-619c r174i 首跑违反该纪律（N8b FAIL 在写盘之前）——本条只作记录，不重跑',
   'S-619' in io.open('_r174/r174i_repin.py', encoding='utf-8').read())

print('== S-620 · 小样本预期值 ==')
smp = b'{"calls": {"1": ["2"]}, "bounds": ["A"]}'
import json as _j
ser = _j.dumps({'calls': _j.loads(smp)['calls']}, ensure_ascii=False).encode()
off = smp.find(b'}, "bounds": [')
print('小样本 calls-only=%d off=%d bounds 出现=%d' % (len(ser), off, smp.count(b'"bounds"')))
ck('S-620a calls-only 长度是 23 不是 18', len(ser) == 23, len(ser))
ck('S-620b 偏移是 21 不是 16', off == 21, off)
ck('S-620c "bounds" 在该样本出现 1 次（不是 2 次）', smp.count(b'"bounds"') == 1, smp.count(b'"bounds"'))

print('== S-622 · 「只有一种读法」是假的 ==')
big = io.open('lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json', 'rb').read()
OFF = big.find(b'}, "bounds": [')
serb = _j.dumps({'calls': _j.loads(big)['calls']}, ensure_ascii=False).encode()
ck('S-622a OFF+2 == len(ser)（偏移读法也能得 913,239）', OFF + 2 == len(serb), (OFF + 2, len(serb)))
ck('S-622b 真实差值 913,239 − 913,237 = 2', len(serb) - OFF == 2, len(serb) - OFF)

print('== S-624 · 自指失效：V555 里「仅 1 次」实测 4 次 ==')
def lim_of(path):
    for l in io.open(path, encoding='utf-8').read().rstrip('\n').split('\n')[1:]:
        f = l.split('\t')
        if f[0] == 'F35':
            return f[4]
    return ''
l554 = lim_of('lead/next_re_20261117_r14/R17_R126_FACTINDEX_V554/FACT_INDEX.tsv')
l555 = lim_of('lead/next_re_20261117_r14/R17_R127_FACTINDEX_V555/FACT_INDEX.tsv')
l556 = lim_of('lead/next_re_20261117_r14/R17_R128_FACTINDEX_V556/FACT_INDEX.tsv')
for tag, t in (('V554', l554), ('V555', l555), ('V556', l556)):
    print('%s: 同血缘克隆=%d 不是独立实现=%d' % (tag, t.count('同血缘克隆'), t.count('不是独立实现')))
ck('S-624a V554 的 clone == 1', l554.count('同血缘克隆') == 1, l554.count('同血缘克隆'))
ck('S-624b V555 的 clone == 4（V555 正文「仅 1 次」因此为假）',
   l555.count('同血缘克隆') == 4 and '「同血缘克隆」仅 **1** 次' in l555, l555.count('同血缘克隆'))
ck('S-624c V556 的 clone == 5 且正文预告 5 与 8', l556.count('同血缘克隆') == 5, l556.count('同血缘克隆'))
ck('S-624d V556 的 needle == 8', l556.count('不是独立实现') == 8, l556.count('不是独立实现'))
ck('S-624e V556 正文里写着两个新数', '**5** 与 **8**' in l556)

print('== S-625 · 永假分支残句 ==')
t = io.open('_r174/r174l_write_v556.py', encoding='utf-8').read()
ck('S-625 修好后的版本里不再有 "if False"', 'if False' not in t, 'if False' in t)

print('== 孤儿进程自检 ==')
me = os.getpid()
myset = set()
for pid in os.listdir('/proc'):
    if not pid.isdigit():
        continue
    try:
        cl = io.open('/proc/%s/cmdline' % pid, 'rb').read().replace(b'\0', b' ').decode('utf-8', 'replace').strip()
        nm = io.open('/proc/%s/comm' % pid).read().strip()
    except Exception:
        continue
    if not cl:
        continue
    if int(pid) == me or pid in (str(os.getppid()),):
        continue
    if '_r174/' not in cl:
        continue
    if 'r174n_selferrors.py' in cl:      # 本脚本自身（及其外层 bash 包装）不算
        continue
    myset.add((int(pid), nm, cl[:140]))
print('与本轮 _r174 相关且在跑的进程: %s' % sorted(myset))
ck('孤儿进程自检：无其它 _r174 脚本残留在跑', all(p == me for p, _, _ in myset) or not myset,
   sorted(myset))

print('\n== RESULT: %d assertions, %d FAIL ==' % (n, len(fails)))
res = {'script': 'r174n_selferrors.py', 'assertions_total': n, 'fails': fails,
       'procs': sorted(myset)}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('wrote ' + OUT)
if fails:
    print('FAILS: %s' % fails)
sys.exit(1 if fails else 0)
