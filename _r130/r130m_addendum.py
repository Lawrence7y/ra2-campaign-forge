#!/usr/bin/env python3
# R130 r130m: append the closing-gate addendum to the four artifacts.
# Preconditions asserted against post-r130i state. LF-only; CR profiles preserved.
import hashlib
import io
import os
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BOARD = os.path.join(R14, 'STATUS_BOARD.md')
COMMON = os.path.join(R14, 'R14_COMMON.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
LEDGER = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')

BOARD_TXT = u'''
### 十二 · 收口期追加（如实记，不改上文）

本轮确实改动了门禁，共三处，全部带反控、方向都是收紧。

其一，新增的 2.134 必须入 C16_FLOORS。写完 2.134 后门禁当场报 unpinned 1 ——这正是本仓反复被咬过的「新增一节就白得一张永久免检票」。按半量规则重钉：实测正文 1882 B，取 941，表条目 127 -> 128，摘要 d7d41af110a692d8 -> 9bc92f2c05c797ef。重钉后 pinned 128 / unpinned 0 / hollow 0 / missing 0。

其二，C16 重钉后的反控 11/11（r130k）：正控 exit 0 且含 pinned 128 与 unpinned 0；把 2.134 正文清空 exit 1 并报 (134, 9, 941)；只把 134 的下界从 941 改 900、不改摘要 exit 1 命中 TAMPERED；把 134 从表里删掉 exit 1。两次恢复后三方 sha 均回基线。

其三，GATE_VER 由 R129 升到 R130 并同步 DISC_RECHECK 第 20 行登记式（C10 门自检要求二者一致，而本轮确实动了 check_disc.py）。终态 check_disc.py exit 0、C10 显示 ok(R130)。

另记一条事故於未发：r130k 第一版的恢复块写成「读一个不存在的回退文件并写入」——若真的走到那条分支，会把 R14_COMMON.md 覆写成空。修法是先把两份正本字节读进内存，finally 只能从内存恢复，不让恢复依赖磁盘状态。该块在改好前一次崩溃中实际跑过，两个文件 sha 均回基线（gate 67a74da6 / common 1f81179e），证明这一版是对的；但错版本身记作 S-203。

看板终态 134 行（未超 300），归档 CR 仍 2952，看板 CR 仍 0。
'''

COMMON_TXT = u'''
六、门禁收口（R130）：新增的 2.134 必须入 C16_FLOORS，否则「新增一节」就白得一张永久免检票。写完当场报 unpinned 1 即为此。按半量规则重钉：实测正文 1882 B 取 941，条目 127->128，摘要 d7d41af110a692d8 -> 9bc92f2c05c797ef。反控 11/11，含「清空 2.134 正文 -> exit 1 报 (134,9,941)」与「只改下界不改摘要 -> TAMPERED」。GATE_VER 同步 R129 -> R130 并改登记行，终态 ok(R130)。

七、事故未发一条（S-203）：恢复块不得依赖磁盘状态。r130k 初版把「读回退文件再写入」当恢复手段，若命中会把 R14_COMMON.md 写成空。改为先把正本字节读进内存、finally 只从内存恢复。改好后一次崩溃中该块实际执行，两文件 sha 均回基线。
'''

LOCK_TXT = u'''
KK. 收口期追加（如实记，不改上文）：本轮改门禁三处，全带反控、方向收紧。其一新增 2.134 必须入 C16_FLOORS —— 写完当场报 unpinned 1，正是本仓被咬过的「新增一节即白得永久免检票」。按半量规则重钉：实测 1882 B 取 941，条目 127 -> 128，摘要 d7d41af1 -> 9bc92f2c。重钉后 pinned 128 / unpinned 0 / hollow 0 / missing 0 / min margin 941。其二反控 r130k 11/11：清空 2.134 正文 exit 1 报 (134, 9, 941)；只改下界 941->900 不改摘要 exit 1 命中 TAMPERED；删掉 134 条目 exit 1；两次恢复后 sha 回基线。其三 GATE_VER R129 -> R130 并同步第 20 行登记式，终态 exit 0、C10 ok(R130)。另记 S-203（事故未发）：r130k 初版恢复块写成「读一个不存在的回退文件并写入」，命中即把 R14_COMMON.md 写成空；改为先读进内存、finally 只从内存恢复。该块在改好后一次崩溃中实际执行，两文件 sha 均回基线，反证修法正确。看板终态 134 行。
'''

LEDGER_TXT = u'''
R130 收口期补记（承 §1184）：本轮改门禁三处，均带反控。新增 2.134 入 C16_FLOORS（实测 1882 B 取 941，条目 127->128，摘要 d7d41af1 -> 9bc92f2c，重钉后 unpinned 0）；r130k 反控 11/11（清空正文 -> (134,9,941) FAIL、只改下界不改摘要 -> TAMPERED、删条目 -> FAIL、恢复后 sha 回基线）；GATE_VER R129 -> R130 同步登记行，终态 ok(R130)。
另：S-203 事故未发 —— 恢复块若依赖磁盘回退文件，会把 R14_COMMON.md 写成空；改为内存持有正本字节。此条应作为「写盘脚本的恢复路径」这一类错误的范例留档。
'''

EXP = {BOARD: 0, COMMON: 1081, LOCK: 137, LEDGER: 337}


def precheck():
    ok = True
    for p, cr in EXP.items():
        b = io.open(p, 'rb').read()
        if b.count(b'\r') != cr:
            print('PRECHECK FAIL CR', os.path.basename(p), b.count(b'\r'), '!=', cr)
            ok = False
        if '收口期追加（如实记，不改上文）' in b.decode('utf-8', 'replace'):
            # board-only marker from THIS round; R129 used the same phrase, so guard on
            # the round-specific token instead
            pass
        if 'S-203' in b.decode('utf-8', 'replace'):
            print('PRECHECK FAIL: S-203 already present in', os.path.basename(p))
            ok = False
    return ok


def app(p, txt, want_cr):
    before = io.open(p, 'rb').read()
    assert before.count(b'\r') == want_cr
    assert '\r' not in txt, 'CR in text'
    with io.open(p, 'ab') as f:
        f.write(txt.encode('utf-8'))
    after = io.open(p, 'rb').read()
    assert after.count(b'\r') == want_cr
    assert after.startswith(before)
    return after


def main():
    if not precheck():
        print('ABORT')
        return 1
    for p, t, cr in ((BOARD, BOARD_TXT, 0), (COMMON, COMMON_TXT, 1081),
                     (LOCK, LOCK_TXT, 137), (LEDGER, LEDGER_TXT, 337)):
        b = app(p, t, cr)
        print('appended', os.path.basename(p), 'CR', b.count(b'\r'),
              'LF', b.count(b'\n'), 'sha', hashlib.sha256(b).hexdigest()[:16])
    return 0


if __name__ == '__main__':
    sys.exit(main())
