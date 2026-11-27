#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 H：把 FACT_INDEX_CURRENT.md 从 V556 补到 V557（今日第二次同日补指针）。

如实登记一条新情况：V557 与 V556 同属 **R128** 目录 ⇒ 指针原「声明依据」里
「R128 下只有这一个 FACT_INDEX 目录」这条**已不再成立**，须改成「R128 下取版本号最大者」。
这是措辞订正，不是新增判据。
"""
import hashlib, io, json, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
P = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
LED = os.path.join(TIER, 'R17_R128_FACTINDEX_V558/FACT_INDEX.tsv')
OUT = os.path.join(ROOT, '_r175/r175h_pointer.json')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

raw = io.open(P, 'rb').read()
t = raw.decode('utf-8')
ck('A1 指针文件 CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
ck('A2 当前指 V557', 'R17_R128_FACTINDEX_V557' in t and 'R17_R128_FACTINDEX_V558' not in t,
   ('V557' in t, 'V558' in t))
led = io.open(LED, 'rb').read()
sha = hashlib.sha256(led).hexdigest()
ck('A3 V558 现盘 sha 与 r175m 记录一致', sha.startswith('157996aa5da193d3'), sha[:16])
ck('A4 V558 现盘字节 128,835', len(led) == 128835, len(led))
dirs128 = sorted(d for d in os.listdir(TIER) if d.startswith('R17_R128_FACTINDEX_V'))
ck('A5 R128 下确有 3 个目录（V556/V557/V558）⇒ 旧声明依据失效', len(dirs128) == 3, dirs128)

new = t.replace('R17_R128_FACTINDEX_V557', 'R17_R128_FACTINDEX_V558')
new = new.replace('fc78f3780ef2f320d9bc86555625aaacc7a5198ea1f8fe62648d5a62bb6bdf07', sha)
new = new.replace('| 字节数 | 128363 |', '| 字节数 | %d |' % len(led))
new = new.replace('| 声明轮次 | R174 |', '| 声明轮次 | R175 |')
old_basis = ('版本号 530..557 连续无缺；V557 是「版本号最大」。**R175 订正**：原写「R128 下只有'
             '这一个 FACT_INDEX 目录」——R175 起 V556 与 V557 **同属 R128**，该条已不成立；'
             '现依据改为「版本号最大 + 该目录内文件 sha256 与 facts_floors.py 的 D0 一致」两条同时成立')
new_basis = ('版本号 530..558 连续无缺；V558 是「版本号最大」。**R175 再订正**：R175 当日已在 R128 下'
             '产生 V556/V557/V558 **三份**，故原「R128 下只有这一个目录」彻底失效；'
             '现依据改为「版本号最大 + 该目录内文件 sha256 与 facts_floors.py 的 D0 一致」两条同时成立')
ck('A6 旧声明依据串在文件里恰 1 次', t.count(old_basis) == 1, t.count(old_basis))
new = new.replace(old_basis, new_basis)
new = new.replace('（D0 已钉 V556 的 sha256）', '（D0 已钉 V557 的 sha256）')
new = new.replace('V530..V556 是 27 个可独立复核的快照', 'V530..V557 是 28 个可独立复核的快照')
# ★ 自错 S-633：我预估 V557 出现 1 次，实测 **2** 次（「版本目录」行 + 「相对路径」行各 1），
#   V556 改前同样 2 次。断言改为实测值 2。
ck('A7 新文本里 V557 目录名 0 次、V558 恰 2 次（版本目录行 + 相对路径行）',
   'R17_R128_FACTINDEX_V557' not in new and new.count('R17_R128_FACTINDEX_V558') == 2,
   (new.count('R17_R128_FACTINDEX_V557'), new.count('R17_R128_FACTINDEX_V558')))
ck('A8 新文本含新 sha', sha in new, sha[:16])
ck('A9 新文本 CR == 0', '\r' not in new, '\r' in new)
ck('A10 新文本行数与旧相同（只改值不改结构）', new.count('\n') == t.count('\n'), (t.count('\n'), new.count('\n')))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
bak = os.path.join(BASE, 'FACT_INDEX_CURRENT.md.before_r175n_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f: f.write(raw)
ck('B1 备份 sha 命中旧 sha', hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest(),
   os.path.basename(bak))
io.open(P, 'w', encoding='utf-8', newline='').write(new)
back = io.open(P, 'rb').read()
ck('B2 回读与构造一致', back == new.encode(), len(back))
ck('B3 回读 CR == 0', back.count(b'\r') == 0, back.count(b'\r'))
ck('B4 facts_floors 的 D0 与指针新值一致（交叉核对）',
   hashlib.sha256(io.open(LED, 'rb').read()).hexdigest() in
   io.open(os.path.join(ROOT, '_r160/facts_floors.py'), encoding='utf-8').read(), True)
print('\n== %d 断言, %d FAIL ==  (%d -> %d B / sha %s)' % (n, len(fails), len(raw), len(back), hashlib.sha256(back).hexdigest()[:16]))
io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails, 'assertions': n,
    'ptr_bytes': [len(raw), len(back)], 'ptr_sha': hashlib.sha256(back).hexdigest()}, ensure_ascii=False, indent=1))
sys.exit(1 if fails else 0)
