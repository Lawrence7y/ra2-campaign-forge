# -*- coding: utf-8 -*-
"""R172 L：四件套补记 C16 重钉（170→171 节）与 S-592（反控副本深度错）。

改前状态：§2.177 / §1227 / PC / 看板第 172 轮 均已落盘；本脚本只在各段内**替换一句过期的「未重钉」表述**并追加一条补记。
纪律同前：xb 独占备份 -> 断言旧 sha 与 CR -> 一次性写 -> 回读校验。
"""
import hashlib, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(TIER, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BOARD = os.path.join(TIER, 'STATUS_BOARD.md')
BAK = os.path.join(TIER, 'R17_LEAD_BASELINE')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

# 过期句 -> 新表述（各件里那句「未重钉」必须被就地改口，否则与磁盘相反）
AMEND = [
 (RC, 'R14_COMMON.md', 1081,
  '`GATE_VER` **未升**（仍 R166）。\n',
  '`GATE_VER` **未升**（仍 R166）。\n'
  '**补记（C16 随本节重钉）**：`§2.177` 实测 **6,659 B**（字符 3,810）⇒ 新 floor **3,329**（一半）；`C16_FLOORS` **170 → 171** 条'
  '（新增 id **177**，176 本已在表内）、`C16_FLOORS_SHA256` `141afe44…` → **`84273ed6…`**。实跑 NOTE 逐字 '
  '`171 sections measured (pinned 171), hollow/deficient 0, missing 0, unpinned 0, min margin 20`；`GATE_VER` 仍 `R166`，'
  '`C7_TEXT` / `C14_TEXT` / `FREEZE` 三者一字未动；把 177 的 floor 调大 1、或删掉 177 整行，各得一条会 FAIL 的反控（见七之 S-592）。\n'),
 (LED, 'GOAL_THREE_TARGETS_20261018.md', 337,
  '三段实跑 exit 0 / G1=G2=G3=ok、`GATE_VER` 仍 R166。\n',
  '三段实跑 exit 0 / G1=G2=G3=ok、`GATE_VER` 仍 R166。**C16 随 §2.177 重钉**：实测 **6,659 B** ⇒ floor **3,329**；'
  '`C16_FLOORS` **170 → 171** 条（新增 id **177**）、`C16_FLOORS_SHA256` `141afe44…`→**`84273ed6…`**；NOTE 逐字 171 节 pinned 171 / unpinned 0。\n'),
 (LOCK, 'LEAD_LOCK', 137,
  '本轮**未升** `GATE_VER`、**未改** C16 逐节表（本节落盘后 C16 下界仍需在下一轮按 §2.177 实测量重钉 —— 如实登记为未完成项）。\n',
  '本轮**未升** `GATE_VER`（仍 R166）；**C16 逐节表已随 §2.177 重钉**（见 PC9）。\n'
  '\n'
  'PC9. ✅ **交付六：C16 随 §2.177 重钉（170 → 171 节），以及一条「假反控」自错.** `§2.177` 实测 **6,659 B**（字符 3,810）⇒ 新 floor **3,329**；'
  '`C16_FLOORS` `141afe44…` → **`84273ed6…`**，新增 id **177**（176 本已在表内），原 170 条逐条不变；'
  '`GATE_VER` / `C7_TEXT` / `C14_TEXT` / `FREEZE` 四者一字未动。实跑 NOTE 逐字 `171 sections measured (pinned 171), hollow/deficient 0, missing 0, unpinned 0, min margin 20`。'
  '**S-592（假反控，族谱同 S-457）**：`r172j` 的 N4/N5 把 `check_disc.py` 副本放在 `_r172/` 下 —— 该脚本按**本文件位置反推三层**定 `ROOT`，'
  '放浅一层就反推到 `/home/t628/projects` ⇒ 副本恒以 `FileNotFoundError` 收场，于是「未改副本 exit 0」假 FAIL、'
  '而「floor 调大 1 必 FAIL」是**因为找不到文件才 FAIL**、对该断言毫无判别力。'
  '`r172k` 把副本放到 `lead/next_re_20261117_r14/`（与生产同深度）、先断言三层反推得同一 `ROOT`，再做正反控：'
  '未改副本 exit 0、floor +1 ⇒ FAIL、删掉 177 整行 ⇒ FAIL（理由含 unpinned）、生产副本随后仍 exit 0。**9 断言 0 FAIL**。\n'),
 (BOARD, 'STATUS_BOARD.md', 0,
  '**未取得**：① `coverage.tsv` / `PANEL.md` 仍不可读（全盘 find 0 命中）⇒ F23 四计数与 F35 严格列仍不可重数；② F35 grade 未改；\n'
  '③ C7 三死分支仍各 0 行；④ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑤ `a2_sites` 生成器与 86.19% 原值仍不可重算；\n'
  '⑥ **C16 逐节表本轮未重钉**（§2.177 落盘后下一轮须按实测量重钉，如实登记为未完成项）。\n',
  '**C16 随 §2.177 重钉**：实测 **6,659 B** ⇒ floor **3,329**；`C16_FLOORS` **170 → 171** 条（新增 id **177**）、'
  '`C16_FLOORS_SHA256` `141afe44…`→**`84273ed6…`**；NOTE 逐字 `171 sections measured (pinned 171) … unpinned 0`。\n'
  '**未取得**：① `coverage.tsv` / `PANEL.md` 仍不可读（全盘 find 0 命中）⇒ F23 四计数与 F35 严格列仍不可重数；② F35 grade 未改；'
  '③ C7 三死分支仍各 0 行；④ C11 id 3/4/22/27/28 与 5 处永远通过子项未动；⑤ `a2_sites` 生成器与 86.19% 原值仍不可重算。\n'),
]

for path, name, cr_expect, olD, new in AMEND:
    raw = io.open(path, 'rb').read()
    t = raw.decode('utf-8')
    ck('A0 %s 旧串恰 1 次' % name, t.count(olD) == 1, t.count(olD))
    if t.count(olD) != 1:
        continue
    t2 = t.replace(olD, new, 1)
    bak = os.path.join(BAK, name + '.before_r172_amend.bak')
    with io.open(bak, 'xb') as f: f.write(raw)
    ck('A1 %s 备份独占创建' % name, io.open(bak, 'rb').read() == raw)
    io.open(path, 'wb').write(t2.encode('utf-8'))
    b2 = io.open(path, 'rb').read()
    ck('A2 %s 回读逐字节 == 待写' % name, b2 == t2.encode('utf-8'))
    ck('A3 %s CR 仍 %d' % (name, cr_expect), b2.count(b'\r') == cr_expect, b2.count(b'\r'))
    ck('A4 %s 旧串已消失' % name, olD not in t2)
    print('  %s: %d B -> %d B（%+d）' % (name, len(raw), len(b2), len(b2) - len(raw)))

b = io.open(BOARD, encoding='utf-8').read()
ck('B1 看板行数 %d <= 300 且 < 260（未触发归档）' % b.count('\n'), b.count('\n') < 260, b.count('\n'))
ck('B2 看板第 172 轮段仍恰 1 处', b.count('## 🟢 R17 第 172 轮') == 1)
d = io.open(RC, encoding='utf-8').read()
ck('C1 R14_COMMON §2.177 仍恰 1 处', d.count('\n## 2.177 · R172') == 1)
ck('C2 R14_COMMON 含 84273ed6 恰 1 次（补记）', d.count('84273ed6') == 1, d.count('84273ed6'))
d2 = io.open(LED, encoding='utf-8').read()
ck('C3 台账 §1227 仍恰 1 处 且含 84273ed6', d2.count('\n## §1227 · R172') == 1 and d2.count('84273ed6') == 1)
d3 = io.open(LOCK, encoding='utf-8').read()
ck('C4 LEAD_LOCK PC9 恰 1 处（行首锚定）', len([1 for l in d3.split('\n') if l.startswith('PC9.')]) == 1)
ck('C4b PC · R17 第 172 轮 仍恰 1 处 / PA1 PB1 未误伤',
   len([1 for l in d3.split('\n') if l.startswith('PC · R17 第 172 轮')]) == 1
   and len([1 for l in d3.split('\n') if l.startswith('PA1.')]) == 1
   and len([1 for l in d3.split('\n') if l.startswith('PB1.')]) == 1)

print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
