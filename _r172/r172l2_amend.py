# -*- coding: utf-8 -*-
"""R172 L2：补记四件套（C16 重钉 + S-592）；L1 因两处锚串不唯一/带换行而成假 FAIL（S-593），本脚本用长锚。

S-593（本轮第五条自错）：L1 的 R14_COMMON 锚串「GATE_VER **未升**（仍 R166）。\\n」在 §2.176 与本轮 §2.177 各 1 次 ⇒
断言「恰 1 次」假 FAIL；看板锚串自带换行，而磁盘上 ③④⑤⑥ 全在同一行 ⇒ 计数 0、同样假 FAIL。
→ 口径订正：**长锚不够，必须是「唯一锚」**；两处均改为含本轮独有字样的长串。
"""
import hashlib, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(TIER, 'R14_COMMON.md')
BOARD = os.path.join(TIER, 'STATUS_BOARD.md')
BAK = os.path.join(TIER, 'R17_LEAD_BASELINE')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

# ---- R14_COMMON ----
RC_OLD = ('`facts_floors` **exit 0**（D0 `988a9567` / D8 121,010 / D9 `ce436f7a`）、`gate_runner` **G1=G2=G3=ok**。`GATE_VER` **未升**（仍 R166）。\n')
RC_NEW = ('`facts_floors` **exit 0**（D0 `988a9567` / D8 121,010 / D9 `ce436f7a`）、`gate_runner` **G1=G2=G3=ok**。`GATE_VER` **未升**（仍 R166）。\n'
 '**补记（C16 随本节重钉）**：`§2.177` 实测 **6,659 B**（字符 3,810）⇒ 新 floor **3,329**（一半）；`C16_FLOORS` **170 → 171** 条'
 '（新增 id **177**，176 本已在表内）、`C16_FLOORS_SHA256` `141afe44…` → **`84273ed6…`**。实跑 NOTE 逐字 '
 '`171 sections measured (pinned 171), hollow/deficient 0, missing 0, unpinned 0, min margin 20`；`GATE_VER` 仍 `R166`，'
 '`C7_TEXT` / `C14_TEXT` / `FREEZE` 三者一字未动。**反控是真反控**：把 177 的 floor 调大 1 必 FAIL、删掉 177 整行必 FAIL'
 '（理由含 unpinned）、未改副本 exit 0 —— 三条都由放在**与生产同深度**的副本跑出（见 S-592）。\n')

raw = io.open(RC, 'rb').read(); t = raw.decode('utf-8')
ck('A0 R14_COMMON 唯一长锚恰 1 次', t.count(RC_OLD) == 1, t.count(RC_OLD))
if t.count(RC_OLD) == 1:
    t2 = t.replace(RC_OLD, RC_NEW, 1)
    bak = os.path.join(BAK, 'R14_COMMON.md.before_r172_amend.bak')
    with io.open(bak, 'xb') as f: f.write(raw)
    ck('A1 R14_COMMON 备份独占创建', io.open(bak, 'rb').read() == raw)
    io.open(RC, 'wb').write(t2.encode('utf-8'))
    b2 = io.open(RC, 'rb').read()
    ck('A2 R14_COMMON 回读逐字节 == 待写 / CR 仍 1081', b2 == t2.encode('utf-8') and b2.count(b'\r') == 1081,
       b2.count(b'\r'))
    ck('A3 R14_COMMON 含 84273ed6 恰 1 次', t2.count('84273ed6') == 1, t2.count('84273ed6'))
    print('  R14_COMMON.md: %d B -> %d B（%+d）' % (len(raw), len(b2), len(b2) - len(raw)))

# ---- 看板 ----
B_OLD = '⑤ `a2_sites` 生成器与 86.19% 原值仍不可重算；⑥ **C16 逐节表本轮未重钉**（§2.177 落盘后下一轮须按实测量重钉，如实登记为未完成项）。\n'
B_NEW = ('⑤ `a2_sites` 生成器与 86.19% 原值仍不可重算。\n\n'
 '**C16 随 §2.177 重钉**：实测 **6,659 B** ⇒ floor **3,329**；`C16_FLOORS` **170 → 171** 条（新增 id **177**）、'
 '`C16_FLOORS_SHA256` `141afe44…`→**`84273ed6…`**；NOTE 逐字 `171 sections measured (pinned 171) … unpinned 0`。'
 '反控三条（floor +1 / 删行 / 未改副本）由**与生产同深度**的副本跑出，见 S-592。\n')
rawb = io.open(BOARD, 'rb').read(); tb = rawb.decode('utf-8')
ck('B0 看板唯一锚恰 1 次', tb.count(B_OLD) == 1, tb.count(B_OLD))
if tb.count(B_OLD) == 1:
    tb2 = tb.replace(B_OLD, B_NEW, 1)
    bakb = os.path.join(BAK, 'STATUS_BOARD.md.before_r172_amend.bak')
    with io.open(bakb, 'xb') as f: f.write(rawb)
    ck('B1 看板备份独占创建', io.open(bakb, 'rb').read() == rawb)
    io.open(BOARD, 'wb').write(tb2.encode('utf-8'))
    b3 = io.open(BOARD, 'rb').read()
    ck('B2 看板回读逐字节 == 待写 / CR 仍 0', b3 == tb2.encode('utf-8') and b3.count(b'\r') == 0)
    ck('B3 看板含 84273ed6 恰 1 次', tb2.count('84273ed6') == 1, tb2.count('84273ed6'))
    print('  STATUS_BOARD.md: %d B -> %d B（%+d）' % (len(rawb), len(b3), len(b3) - len(rawb)))
    print('  看板行数 =', b3.count(b'\n'))

# ---- 交叉一致性 ----
r = io.open(RC, encoding='utf-8').read()
bb = io.open(BOARD, encoding='utf-8').read()
L = io.open(os.path.join(ROOT, 'lead', 'LEAD_LOCK'), encoding='utf-8').read()
G = io.open(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), encoding='utf-8').read()
ck('C1 四件套都含新 C16 常量 84273ed6', all(x.count('84273ed6') >= 1 for x in (r, bb, L, G)),
   [x.count('84273ed6') for x in (r, bb, L, G)])
ck('C2 四件套都含新 floor 3329', all('3,329' in x or '3329' in x for x in (r, bb, L, G)))
ck('C3 「本轮未重钉」这句过期表述在四件套里全消失',
   all('本轮未重钉' not in x for x in (r, bb, L, G)))
ck('C4 旧 C16 常量 141afe44 仍作为「旧值」被引用恰 1 次/件（可追溯）',
   all(x.count('141afe44') == 1 for x in (r, bb, L, G)), [x.count('141afe44') for x in (r, bb, L, G)])
ck('C5 看板 < 260 行（未触发归档）', bb.count('\n') < 260, bb.count('\n'))
ck('C6 §2.177 / §1227 / PC 段 / 第 172 轮段 各仍恰 1 处',
   r.count('\n## 2.177 · R172') == 1 and G.count('\n## §1227 · R172') == 1
   and len([1 for x in L.split('\n') if x.startswith('PC · R17 第 172 轮')]) == 1
   and bb.count('## 🟢 R17 第 172 轮') == 1)
ck('C7 S-592 在 LEAD_LOCK 与看板各 1 次（自错可追溯）', L.count('S-592') >= 1 and bb.count('S-592') >= 1)

print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
