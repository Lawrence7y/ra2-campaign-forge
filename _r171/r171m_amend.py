# -*- coding: utf-8 -*-
"""R171 M：把 C16 重钉（169->170 节，随 §2.176）补进四件套——四件套正文写作时 C16 尚未重钉。

纪律：只**追加**补记段，不改已写正文的任何字节；CR 五项保持。
"""
import hashlib, io, json, os, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
RC = os.path.join(TIER, 'R14_COMMON.md')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
EXPECT = {RC: 1081, LED: 337, LOCK: 137, BRD: 0}
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

pre = {p: io.open(p, 'rb').read() for p in EXPECT}
for p, want in EXPECT.items():
    ck('P0 %s CR == %d' % (os.path.basename(p), want), pre[p].count(b'\r\n') == want, pre[p].count(b'\r\n'))

AMEND = {
 RC: "\n**补记（C16 随本节重钉）**：`§2.176` 实测 **5,554 B**（字符 3,265）⇒ 新 floor **2,777**（一半）；`C16_FLOORS` 表 **169 → 170** 条（新增 id **176**，因 170..175 早已在表内）、`C16_FLOORS_SHA256` `bb7fe832…` → **`141afe4431a71eb5…`**。**反控**：旧表复算命中旧常量（硬闸，未命中不写盘）；原 **169** 条 floor 逐条不变；`GATE_VER` 仍 `R166`、`C7_TEXT_SHA256` / `C14_TEXT_SHA256` / `FREEZE_SHA256` 三者一字未动（`_r171/r171l` 20 断言中 17 PASS，3 条为我的行差/文案断言口径错，见 S-585）。复跑 NOTE 逐字 `170 sections measured (pinned 170), hollow/deficient 0, missing 0, unpinned 0, min margin 20`；反向控：把 id 176 的 floor 调大 1 必 FAIL。**S-585**：`r171k` 首版判「FAIL 0」用裸子串，命中 NOTE 里的 `can never FAIL` ⇒ 假 FAIL；改判**行首** FAIL。\n",
 LED: "\n**六 · C16 随本节重钉（169 → 170 节）.** `§2.176` 实测 **5,554 B** ⇒ floor **2,777**；`C16_FLOORS` **169 → 170** 条（新增 **id 176**；170..175 本已在表内）、`C16_FLOORS_SHA256` `bb7fe832`→**`141afe4431a71eb5`**。反控：旧表命中旧常量作硬闸、原 169 条逐条不变、`GATE_VER`/`C7_TEXT`/`C14_TEXT`/`FREEZE` 一字未动；NOTE 逐字 `170 sections measured (pinned 170) … unpinned 0`；id 176 floor +1 必 FAIL。\n",
 LOCK: "\nPB13. 📌 **交付十：C16 随 §2.176 重钉（169 → 170 节），以及三条口径型自错.** `§2.176` 实测 **5,554 B**（字符 3,265）⇒ 新 floor **2,777**；`C16_FLOORS` **169 → 170** 条、`C16_FLOORS_SHA256` `bb7fe832`→**`141afe4431a71eb5`**。**反控五条**：旧表复算命中旧常量（硬闸，未命中不写盘）、原 169 条逐条不变、`GATE_VER` 仍 `R166`、`C7_TEXT_SHA256`/`C14_TEXT_SHA256`/`FREEZE_SHA256` 一字未动、把 id 176 floor 调大 1 必 FAIL。复跑 NOTE 逐字 `170 sections measured (pinned 170), hollow/deficient 0, missing 0, unpinned 0, min margin 20`。**S-585**：`r171k` 判「check_disc FAIL 0」用**裸子串** `'FAIL' not in out`，而 NOTE 里有 `can never FAIL` ⇒ 假 FAIL；改判**行首** FAIL（与 `PA12` S-577「计数型断言必须钉锚点」同族）。**S-586**：`r171l` 先按「新节 id = 170」写，实测 **170..175 早已在 C16_FLOORS 表内**，真正缺的是 **176**；断言 `max(tbl)==169` 当场 FAIL 并**阻止写盘**（fail-closed 生效）。**S-587**：`r171l` 首版 `new[176]=floor` 少了 `new=dict(tbl)` ⇒ NameError；以及行差断言用「逐行 zip 比较」，插入一行导致后面全部错位、报 **219 行变化**，实际 SequenceMatcher 只报 **1 insert + 1 replace**。\n",
 BRD: "\n**C16 随本节重钉（169 → 170 节）**：`§2.176` 实测 **5,554 B** ⇒ floor **2,777**；`C16_FLOORS` **169 → 170** 条（新增 **id 176**，170..175 本已在表内）、`C16_FLOORS_SHA256` `bb7fe832…` → **`141afe4431a71eb5…`**。反控：旧表命中旧常量作硬闸、原 169 条逐条不变、`GATE_VER` 仍 `R166`、`C7_TEXT`/`C14_TEXT`/`FREEZE` 一字未动、id 176 floor +1 必 FAIL；NOTE 逐字 `170 sections measured (pinned 170), hollow/deficient 0, missing 0, unpinned 0, min margin 20`。**S-585**：`r171k` 首版用裸子串判 `FAIL 0`，命中 NOTE 的 `can never FAIL` ⇒ 假 FAIL，改判行首。**自错本轮共 S-579..S-587 九条**。\n",
}
for p in EXPECT:
    b = os.path.join(BASE, '%s.before_r171amend_%s.bak' % (os.path.basename(p), TS))
    with io.open(b, 'xb') as f:
        f.write(pre[p])
    ck('P1 备份独占 %s' % os.path.basename(b), io.open(b, 'rb').read() == pre[p])

for p, add in AMEND.items():
    old = pre[p]
    io.open(p, 'wb').write(old + add.encode('utf-8'))
    raw = io.open(p, 'rb').read()
    ck('W %s CR 仍 %d' % (os.path.basename(p), EXPECT[p]), raw.count(b'\r\n') == EXPECT[p], raw.count(b'\r\n'))
    ck('W %s 追加后以前缀形式保留原文' % os.path.basename(p), raw.startswith(old))

# 看板仍 <= 300 行
ck('W 看板行数 <= 300', io.open(BRD, 'rb').read().count(b'\n') <= 300, io.open(BRD, 'rb').read().count(b'\n'))
print('\n  看板 %d 行' % io.open(BRD, 'rb').read().count(b'\n'))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
