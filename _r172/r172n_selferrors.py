# -*- coding: utf-8 -*-
"""R172 N：把 S-592..S-595 补进 LEAD_LOCK 与看板的自错句（行数不增，避免触发看板归档）。"""
import hashlib, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BOARD = os.path.join(TIER, 'STATUS_BOARD.md')
BAK = os.path.join(TIER, 'R17_LEAD_BASELINE')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

LOCK_OLD = ('**9 断言 0 FAIL**。\n')
LOCK_NEW = ('**9 断言 0 FAIL**。**S-593**：`r172l` 的补记锚串取「GATE_VER **未升**（仍 R166）。\\n」，'
 '该串在 §2.176 与本轮 §2.177 各 1 次 ⇒ 断言「恰 1 次」假 FAIL；看板那条锚串自带换行而磁盘上 ③④⑤⑥ 全在同一行 ⇒ 计数 0、同样假 FAIL；'
 '改用含本轮独有字样的长锚后 15/15 通过（`r172l2`）。**S-594**：`r172l` 的 C4 断言「四件套的旧常量 141afe44 各恰 1 次」，'
 '而 R171 段的 `bb7fe832…→141afe4431a71eb5…` 也是这个前缀 ⇒ 每件 2 次、假 FAIL；订正为**段级作用域**'
 '（只在 §2.177 段内数，`r172m` T1/T2 通过）。**S-595**：`r172m` F4 把 `dict` 的键数 55 当成「54 数据行不符」、'
 'F8 用 `startswith(F)` 把表头键也拉进 grade 比 ⇒ 两条假 FAIL；改为显式判 `fact_id` 键与逐 fid 的 grade 后通过。'
 '**S-588..S-595 共 8 条，全部由可失败断言当场抓出，无一条进入结论或正文数字**；其中 S-593 与 S-594 是同一族：'
 '**「计数型断言没钉锚点 / 没钉作用域」**（与 R171 S-577、R170 PA12 同族，第三次复发）。\n')

BOARD_OLD = ('S-591 分句切分连错两版（千分位逗号 / 括注内标点被当界），两版都判 2/10。\n')
BOARD_NEW = ('S-591 分句切分连错两版（千分位逗号 / 括注内标点被当界），两版都判 2/10；'
 '**S-592** C16 反控副本放在 `_r172/` 下、`check_disc` 按本文件位置反推三层 ⇒ 副本恒 FileNotFoundError，'
 '「floor +1 必 FAIL」成了假反控，改放同深度目录后 9 断言通过；**S-593** 补记锚串在 §2.176 与 §2.177 各 1 次 ⇒ 假 FAIL；'
 '**S-594** 把 R171 段的同一前缀算进本轮常量计数 ⇒ 假 FAIL，改段级作用域；'
 '**S-595** 把 dict 键数 55 当数据行数、grade 比较拉进表头 ⇒ 两条假 FAIL。**共 S-588..S-595 八条，无一条进结论**。\n')

for path, name, old, new, cr in ((LOCK, 'LEAD_LOCK', LOCK_OLD, LOCK_NEW, 137),
                                 (BOARD, 'STATUS_BOARD.md', BOARD_OLD, BOARD_NEW, 0)):
    raw = io.open(path, 'rb').read(); t = raw.decode('utf-8')
    ck('N0 %s 锚串恰 1 次' % name, t.count(old) == 1, t.count(old))
    if t.count(old) != 1: continue
    t2 = t.replace(old, new, 1)
    bak = os.path.join(BAK, name + '.before_r172_selferrors.bak')
    with io.open(bak, 'xb') as f: f.write(raw)
    ck('N1 %s 备份独占创建' % name, io.open(bak, 'rb').read() == raw)
    io.open(path, 'wb').write(t2.encode('utf-8'))
    b2 = io.open(path, 'rb').read()
    ck('N2 %s 回读逐字节 == 待写 / CR 仍 %d' % (name, cr), b2 == t2.encode('utf-8') and b2.count(b'\r') == cr, b2.count(b'\r'))
    ck('N3 %s 行数未增（避免触发看板归档）' % name,
       b2.count(b'\n') == raw.count(b'\n'), (raw.count(b'\n'), b2.count(b'\n')))
    print('  %s: %d B -> %d B / 行数 %d' % (name, len(raw), len(b2), b2.count(b'\n')))

b = io.open(BOARD, encoding='utf-8').read()
ck('X1 看板仍 < 260 行', b.count('\n') < 260, b.count('\n'))
ck('X2 看板第 172 轮段仍恰 1 处', b.count('## 🟢 R17 第 172 轮') == 1)
l = io.open(LOCK, encoding='utf-8').read()
ck('X3 LEAD_LOCK S-588..S-595 全在', all(('S-%d' % k) in l for k in range(588, 596)))
ck('X4 LEAD_LOCK PC · R17 第 172 轮 仍恰 1 处',
   len([1 for x in l.split('\n') if x.startswith('PC · R17 第 172 轮')]) == 1)

print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
