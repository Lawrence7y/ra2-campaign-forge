#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137-j · 追加更正：本轮确实改了门禁（与 r137f 正文里「门禁未改」相反）

为什么必须追加而不是改旧文：
  r137f 落盘时我只计划做台账层测量，正文里写了「门禁未改任何判据」。
  但写到收口时实测发现：新增 2.141 后 C16 报 unpinned 1 —— 这正是本仓被咬过多次的
  「每轮新增一节 = 每轮白得一张永久免检票」。按 R119/R130/R136 的既定规则，
  新节必须显式重钉进 C16_FLOORS（半量规则）。所以门禁实际改了四处。
  已写入的四件套不改（改已落盘正文属内容变更），只追加更正段。
  这与 R130 的 KK 段、R136 的收口期追加是同一处理方式。

四处改动（全部为容纳新节 + 同步 + 重钉，不改任何判据语义）：
  ① C16_FLOORS 加 141:2548（134 -> 135 条目），C16_FLOORS_SHA256 b719bf81 -> 192795a2
  ② GATE_VER R136 -> R137
  ③ DISC_RECHECK 第 20 行登记式同步；C7_TEXT_SHA256 14dbab46 -> b49da749；row20 a7105751 -> 0ea1a532
  ④ DISC_UNVERIFIABLE 第 20 行锚同步；FREEZE_SHA256 ad11404c -> d72a199b

正反控 18/18（_r137/r137i_gate_controls.py）：P0 基线 exit 0；N1 删 2.141 -> exit 1 且点 141；
N2 2.141 只留标题 -> exit 1 且 hollow 点 141；N3 只回退 GATE_VER -> exit 1 报 R137 != R136；
N4 改冻结档不重钉 -> exit 1 报 TAMPERED；N5 调小下界不重钉 -> exit 1 报 C16d TAMPERED；
P0r/P0r2/P0r3/P1 四次复原均 exit 0。
"""
import hashlib
import io
import os
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')
COMMON = os.path.join(R14, 'R14_COMMON.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
LEDGER = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')

# 追加前的现状（r137f/r137h 落盘后实测）
PRE = {
    COMMON: 1081,
    LOCK: 137,
    LEDGER: 337,
    BOARD: 0,
}

MARK = 'R137 收口期追加'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def backup(p):
    b = io.open(p, 'rb').read()
    dst = os.path.join(BASE, '%s.before_R137_fix_%s.bak'
                       % (os.path.basename(p), time.strftime('%Y%m%d_%H%M%S')))
    with io.open(dst, 'xb') as f:
        f.write(b)
    assert sha(io.open(dst, 'rb').read()) == sha(b)
    print('backup', os.path.basename(dst), len(b), 'B')
    return dst


def app(p, txt, want_cr):
    if not txt.endswith('\n'):
        txt += '\n'
    assert '\r' not in txt, 'text has CR'
    if MARK in io.open(p, encoding='utf-8', errors='replace').read():
        print('SKIP %s already has marker' % os.path.basename(p))
        return
    before = io.open(p, 'rb').read()
    assert before.count(b'\r') == want_cr, 'CR drift on ' + p
    with io.open(p, 'ab') as f:
        f.write(txt.encode('utf-8'))
    after = io.open(p, 'rb').read()
    assert after.count(b'\r') == want_cr, 'CR moved on ' + p
    assert after.startswith(before), 'not appended cleanly'
    print('  wrote %-24s +%d B CR %d total %d B'
          % (os.path.basename(p), len(after) - len(before), after.count(b'\r'), len(after)))


COMMON_FIX = u'''

**八 · 收口期追加更正（如实记，不改上文）.** 上文第六节写「门禁未改任何判据」，**与实际不符**，此段更正。原因：把 2.141 落盘后实测 C16 报 `unpinned 1` —— 这正是本仓被咬过多次的「每轮新增一节 = 每轮白得一张永久免检票」。按 R119/R130/R136 既定规则，新节必须显式重钉进 `C16_FLOORS`（半量规则：实测 5,097 B 取 2,548）。故门禁实际改了**四处**，全部为容纳新节 + 同步 + 重钉，**不改任何判据语义**：① `C16_FLOORS` 加 `141: 2548`（134 → 135 条目），`C16_FLOORS_SHA256` `b719bf81` → `192795a2`；② `GATE_VER` R136 → R137；③ `DISC_RECHECK` 第 20 行登记式同步，`C7_TEXT_SHA256` `14dbab46` → `b49da749`，row20 `a7105751` → `0ea1a532`；④ `DISC_UNVERIFIABLE` 第 20 行锚同步，`FREEZE_SHA256` `ad11404c` → `d72a199b`。**正反控 18/18**（`_r137/r137i_gate_controls.py`）：P0 基线 exit 0；N1 删 2.141 → exit 1 且 missing 点 141；N2 2.141 只留标题 → exit 1 且 hollow 点 141、min margin −2,525；N3 只回退 `GATE_VER` → exit 1 报 `registered R137 != actual R136`；N4 改冻结档不重钉 → exit 1 报 TAMPERED；N5 调小下界不重钉 → exit 1 报 C16d TAMPERED；四次复原均 exit 0。终态 `check_disc.py` exit 0、C10 ok(R137)、C16 pinned 135 / unpinned 0 / hollow 0 / missing 0。另记两条自错：S-259 写看板前只核「252 < 260 不触发归档」、未核「252 + 83 = 335 > 300」，写完当场越界，须回滚看板、改按「当前行数 + 本轮段行数」判定后归档（252 → 136 行），再追加本轮 82 行至 218 行；S-261 反控沙箱初版只拷 11 个数据文件，C7/C11/C12 引用的几十个产物全 `FILE_MISSING` ⇒ 基线 P0 就 rc=1，此后所有「exit 1」都不能归因于破坏动作，改用「实件拷贝被改文件 + 其余软链挂入」后基线 exit 0、五条反控各自命中。
'''


LEDGER_FIX = u'''

**八 · 收口期追加更正（如上文第六节称「门禁未改判据」，与实不符）.** 把 2.141 落盘后 C16 报 `unpinned 1`，触发本仓既定规则（新节必须显式重钉，否则每轮新增一节即白得永久免检票，R119 实测 16 节可被整节清空而不被发现）。故门禁实际改四处，全为容纳新节 + 同步 + 重钉、不改判据语义：① `C16_FLOORS` 加 `141: 2548`（134 → 135），`C16_FLOORS_SHA256` `b719bf81` → `192795a2`；② `GATE_VER` R136 → R137；③ `DISC_RECHECK` 第 20 行同步，`C7_TEXT_SHA256` `14dbab46` → `b49da749`、row20 `a7105751` → `0ea1a532`；④ `DISC_UNVERIFIABLE` 第 20 行同步，`FREEZE_SHA256` `ad11404c` → `d72a199b`。正反控 **18/18**（`_r137/r137i_gate_controls.py`，沙箱构建方式同 R136：被改文件拷实件、其余软链）：P0 基线 exit 0、N1 删节 exit 1 点 141、N2 空壳 exit 1 且 min margin −2,525、N3 只回退版本 exit 1 报 `R137 != R136`、N4 冻结档不重钉 exit 1 报 TAMPERED、N5 下界不重钉 exit 1 报 C16d TAMPERED，四次复原均 exit 0。**终态**：`check_disc.py` exit 0、C10 ok(R137)、C7 31/31、C7d `b49da749`、C11 ok=0/fail=0/frozen=12、C12 12/12、C12b 12/12、C15 135 节/末节 141/1,181,012 B、C16 pinned 135 / unpinned 0 / hollow 0 / missing 0 / min margin 1,155、C16d `192795a2`、C18 note 在场。**自错两条**：S-259 写看板前只核当前行数（252 < 260）、未核「当前 + 本轮段」，写完 335 行越界，回滚后先归档（252 → 136）再追加（→ 218）；S-261 反控沙箱初版缺产物致基线 rc=1，反控失去归因力，改用 R136 的实件+软链混合构建后修复。
'''


LOCK_FIX = u'''
MI. 📌 **收口期追加更正（MJ 之前的 MF ⑥ 写「门禁未改任何判据」，与实不符）.** 2.141 落盘后 C16 当场报 `unpinned 1` —— 本仓被咬过多次的「每轮新增一节 = 每轮白得一张永久免检票」（R119 实测：16 节可被整节清空而不被发现）。故按 R119/R130/R136 既定规则显式重钉（半量：5,097 B → 2,548）。门禁实际改**四处**，全为容纳新节 + 同步 + 重钉，**不改判据语义**：① `C16_FLOORS` 加 `141: 2548`（134 → 135），`C16_FLOORS_SHA256` `b719bf81` → `192795a2`；② `GATE_VER` R136 → R137；③ `DISC_RECHECK` 第 20 行同步，`C7_TEXT_SHA256` `14dbab46` → `b49da749`，row20 `a7105751` → `0ea1a532`；④ `DISC_UNVERIFIABLE` 第 20 行同步，`FREEZE_SHA256` `ad11404c` → `d72a199b`。

MJ. ✅ **正反控 18/18（`_r137/r137i_gate_controls.py`）.** P0 沙箱基线 **exit 0**、C16 pinned 135 / unpinned 0、C10 ok(R137)。五条反控各自命中且有分辨力：N1 删 2.141 整节 → exit 1 且 `missing 1` 点名 141；N2 2.141 只留标题 → exit 1、`hollow/deficient 1`、`min margin −2,525`；N3 只回退 `GATE_VER` 不同步第 20 行 → exit 1、`C10 self GATE_VER registered R137 != actual R136`；N4 改冻结档不重钉 → exit 1、`sha256=511f24c2… TAMPERED`；N5 调小下界不重钉 → exit 1、`C16d … (TAMPERED)`。四次复原（P0r/P0r2/P0r3/P1）全部 exit 0 ⇒ 「exit 1」确实由破坏动作造成，不是沙箱自带的。X1 另证 N2（内容缺失）与 N5（常量被改）是两条不同判据，不是同一判断写两遍。

MK. ✅ **终态核验（写入后实测）.** `check_disc.py` **exit 0**、C10 ok(R137)、C7 live-checks 31/31、C7d `b49da749`、C11 ok=0 / fail=0 / frozen=12 / claims-none=19、C12 12/12、C12b 12/12、C15 135 节 / 末节 141 / 1,181,012 B（floor 831,406）、C16 pinned 135 / unpinned 0 / hollow 0 / missing 0 / min margin 1,155、C16d `192795a2`、C18 note 在场。五项 CR **1081 / 137 / 337 / 0 / 2952** 全绿；看板 218 行（< 300）。收口前 `ps` 确认无孤儿 check_disc、无 /tmp 沙箱残留。

ML. 📌 **自错两条（收口期，均由断言/实测抓出）.** **S-259** 写看板前只核了「当前 252 < 260 不触发归档」，未核「252 + 本轮 83 = 335 > 300」，写完当场越界（334 行），只能回滚看板重来；正确判据是「当前行数 + 本轮段行数」，据此先归档最早两段（252 → 136 行、归档 CR 2952 不变），再追加本轮 82 行至 218 行。**S-261** 反控沙箱初版只拷 11 个数据文件，C7/C11/C12 引用的几十个产物路径全部 `FILE_MISSING` ⇒ 基线 P0 就 rc=1，此后任何「exit 1」都不能归因于破坏动作（这正是反控要防的失效模式）；改用 R136 的「被改文件拷实件 + 其余软链挂入」后基线 exit 0、五条反控各自命中。另记 S-260：r137g 把「R137 段必须在看板里」的断言写在追加之前，而追加在 r137h，故该断言在 r137g 里必然失败 —— 断言放错阶段，不是归档错。
'''


BOARD_FIX = u'''
### 十 · 收口期追加更正（如实记，不改上文）

**上面第六节第 6 条写「门禁未改任何判据」，与实际不符，此段更正。** 原因：2.141 落盘后 C16 当场报 `unpinned 1` —— 这正是本仓被咬过多次的「每轮新增一节 = 每轮白得一张永久免检票」（R119 实测：16 节可被整节清空而不被发现）。按 R119/R130/R136 既定规则，新节必须显式重钉进 `C16_FLOORS`（半量：实测 5,097 B 取 2,548）。

门禁实际改了**四处**，全为容纳新节 + 同步 + 重钉，**不改任何判据语义**：

| # | 改动 | 旧 → 新 |
|---|---|---|
| ① | `C16_FLOORS` 加 `141: 2548`（134 → 135 条目） | `C16_FLOORS_SHA256` `b719bf81` → `192795a2` |
| ② | `GATE_VER` | R136 → R137 |
| ③ | `DISC_RECHECK` 第 20 行登记式同步 | `C7_TEXT_SHA256` `14dbab46` → `b49da749`；row20 `a7105751` → `0ea1a532` |
| ④ | `DISC_UNVERIFIABLE` 第 20 行锚同步 | `FREEZE_SHA256` `ad11404c` → `d72a199b` |

**正反控 18/18**（`_r137/r137i_gate_controls.py`，沙箱构建同 R136：被改文件拷实件、其余软链挂入）：

- P0 基线 **exit 0**、C16 pinned 135 / unpinned 0、C10 ok(R137)
- N1 删 2.141 整节 → exit 1，`missing 1` 点名 141
- N2 2.141 只留标题 → exit 1，`hollow/deficient 1`、`min margin −2,525`
- N3 只回退 `GATE_VER` 不同步第 20 行 → exit 1，`registered R137 != actual R136`
- N4 改冻结档不重钉 → exit 1，`TAMPERED`
- N5 调小下界不重钉 → exit 1，`C16d … (TAMPERED)`
- P0r / P0r2 / P0r3 / P1 四次复原 → 全部 exit 0

X1 另证 N2（内容缺失）与 N5（常量被改）是两条不同判据，不是同一判断写两遍。

**终态**：`check_disc.py` exit 0、C10 ok(R137)、C7 31/31、C7d `b49da749`、C11 ok=0/fail=0/frozen=12、C12 12/12、C12b 12/12、C15 135 节/末节 141/1,181,012 B、C16 pinned 135 / unpinned 0 / hollow 0 / missing 0 / min margin 1,155、C16d `192795a2`、C18 note 在场。

**自错三条（收口期）**：S-259 写看板前只核当前行数（252 < 260）、未核「当前 + 本轮段」，写完 335 行越界，回滚后先归档（252 → 136）再追加（→ 218）。S-260 r137g 把「R137 段必须在看板里」的断言写在追加之前（追加在 r137h），断言放错阶段。S-261 反控沙箱初版缺产物致基线 rc=1，反控失去归因力，改用实件+软链混合构建后修复。
'''


def main():
    for p in (COMMON, LOCK, LEDGER, BOARD):
        backup(p)
    print('-- append --')
    app(COMMON, COMMON_FIX, PRE[COMMON])
    app(LEDGER, LEDGER_FIX, PRE[LEDGER])
    app(LOCK, LOCK_FIX, PRE[LOCK])
    app(BOARD, BOARD_FIX, PRE[BOARD])
    print('-- verify --')
    for p, cr in PRE.items():
        b = io.open(p, 'rb').read()
        assert b.count(b'\r') == cr, 'CR wrong on ' + p
    n = io.open(BOARD, 'rb').read().count(b'\n')
    assert n <= 300, 'board over cap: %d' % n
    print('board %d lines (<=300 OK); all CR preserved' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
