#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137-i · 门禁四处改动的正反控（沙箱，不碰真实文件）

本轮改了 check_disc.py 与两张表共四处，全部是「容纳新节 + 同步 + 重钉」，
不改任何判据语义：
  ① C16_FLOORS 加 141:2548（134 -> 135 条目），C16_FLOORS_SHA256 b719bf81 -> 192795a2
  ② GATE_VER R136 -> R137
  ③ DISC_RECHECK 第 20 行登记式同步，C7_TEXT_SHA256 14dbab46 -> b49da749，row20 a7105751 -> 0ea1a532
  ④ DISC_UNVERIFIABLE 第 20 行锚同步，FREEZE_SHA256 ad11404c -> d72a199b

控法：在沙箱里复制 ROOT 的三段式结构（lead/ + R14/ + 两份表 + check_disc.py），
对副本做定点破坏，跑副本的门禁，看它是否 exit 1 且报出预期项。
真实文件全程只读。

反控清单：
  P0 基线：未破坏 -> exit 0
  N1 把 2.141 整节删掉 -> exit 1，C16 报 missing 141
  N2 把 2.141 正文清空（只留标题）-> exit 1，C16 报 hollow，且点名 141
  N3 只回退 GATE_VER（不改第 20 行）-> exit 1，C10 报不一致
  N4 改冻结档第 4 列但不重钉 FREEZE_SHA256 -> exit 1，报 TAMPERED
  N5 把某节下界调小但不重钉 C16_FLOORS_SHA256 -> exit 1，报 C16d TAMPERED
  P1 复原 -> exit 0
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14REL = 'lead/next_re_20261117_r14'
FILES = ['check_disc.py', 'recheck_verify.py', 'R14_COMMON.md',
         'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv', 'DISC_ESTABLISH.tsv',
         'DISC_NS_MAP.tsv', 'STATUS_BOARD.md', 'BOARD_ARCHIVE.md', 'COMPACT_STATE.md']

RES = []
FAIL = 0


def chk(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:400]})
    print(('PASS ' if ok else 'FAIL ') + name + ('  :: ' + str(detail)[:260] if detail else ''))


def build_sandbox():
    """三段式最小 ROOT：lead/ + R14/ + 关键文件 + LEAD_LOCK/台账（部分判据要读）。"""
    sb = tempfile.mkdtemp(prefix='r137sbx_')
    r14 = os.path.join(sb, R14REL)
    os.makedirs(r14, exist_ok=True)
    for fn in FILES:
        src = os.path.join(ROOT, R14REL, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(r14, fn))
    # check_disc.py 里 ROOT 的推导依赖层级：lead/next_re_.../  的上两级
    for rel in ('lead/LEAD_LOCK', 'lead/GOAL_THREE_TARGETS_20261018.md'):
        src = os.path.join(ROOT, rel)
        if os.path.exists(src):
            dst = os.path.join(sb, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    return sb, r14


def run_gate(r14):
    p = subprocess.run([sys.executable, 'check_disc.py'], cwd=r14,
                       capture_output=True, text=True, timeout=280)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def main():
    sb, r14 = build_sandbox()
    try:
        # ---- P0 基线 ----
        rc, out = run_gate(r14)
        chk('P0 sandbox baseline exit 0', rc == 0, 'rc=%d' % rc)
        chk('P0b baseline reports C16 pinned 135 / unpinned 0',
            'pinned 135' in out and 'unpinned 0' in out,
            [l for l in out.splitlines() if 'C16 per-section' in l][:1])
        chk('P0c baseline C10 ok(R137)', 'ok(R137)' in out,
            [l for l in out.splitlines() if 'C10' in l][:1])

        common = os.path.join(r14, 'R14_COMMON.md')
        base_common = io.open(common, 'rb').read()
        base_gate = io.open(os.path.join(r14, 'check_disc.py'), 'rb').read()
        base_freeze = io.open(os.path.join(r14, 'DISC_UNVERIFIABLE.tsv'), 'rb').read()

        # ---- N1 删整节 2.141 ----
        txt = base_common.decode('utf-8')
        i = txt.index('## 2.141')
        txt2 = txt[:i]
        io.open(common, 'w', encoding='utf-8', newline='').write(txt2)
        rc, out = run_gate(r14)
        chk('N1 delete section 2.141 -> exit 1', rc == 1, 'rc=%d' % rc)
        chk('N1b names 141 as missing', '141' in out and ('gone' in out or 'missing' in out),
            [l for l in out.splitlines() if 'missing' in l or 'gone' in l][:1])

        # ---- N2 2.141 只留标题 ----
        io.open(common, 'w', encoding='utf-8', newline='').write(txt[:i] + '## 2.141 R137：空壳\n')
        rc, out = run_gate(r14)
        chk('N2 hollow 2.141 -> exit 1', rc == 1, 'rc=%d' % rc)
        hol = [l for l in out.splitlines() if 'hollow' in l]
        chk('N2b hollow line names (141, ...)', any('141' in l for l in hol), hol[:1])

        # 复原正文
        io.open(common, 'wb').write(base_common)
        rc, out = run_gate(r14)
        chk('P0r restore 2.141 -> exit 0', rc == 0, 'rc=%d' % rc)

        # ---- N3 只回退 GATE_VER ----
        g = base_gate.decode('utf-8').replace("GATE_VER = 'R137'", "GATE_VER = 'R136'", 1)
        io.open(os.path.join(r14, 'check_disc.py'), 'w', encoding='utf-8').write(g)
        rc, out = run_gate(r14)
        chk('N3 revert GATE_VER only -> exit 1', rc == 1, 'rc=%d' % rc)
        chk('N3b C10 reports mismatch (registered != actual)',
            'C10' in out and ('R136' in out or 'R137' in out),
            [l for l in out.splitlines() if 'C10' in l][:2])
        io.open(os.path.join(r14, 'check_disc.py'), 'wb').write(base_gate)
        rc, _ = run_gate(r14)
        chk('P0r2 restore GATE_VER -> exit 0', rc == 0, 'rc=%d' % rc)

        # ---- N4 改冻结档不重钉 ----
        ft = base_freeze.decode('utf-8')
        assert "'R137'" in ft
        ft2 = ft.replace("grep=(?m)^GATE_VER = 'R137'", "grep=(?m)^GATE_VER = 'R199'", 1)
        assert ft2 != ft, 'frozen row 20 anchor not found'
        io.open(os.path.join(r14, 'DISC_UNVERIFIABLE.tsv'), 'w', encoding='utf-8').write(ft2)
        rc, out = run_gate(r14)
        chk('N4 tamper frozen registry w/o re-pin -> exit 1', rc == 1, 'rc=%d' % rc)
        chk('N4b reports TAMPERED', 'TAMPERED' in out,
            [l for l in out.splitlines() if 'TAMPERED' in l][:1])
        io.open(os.path.join(r14, 'DISC_UNVERIFIABLE.tsv'), 'wb').write(base_freeze)
        rc, _ = run_gate(r14)
        chk('P0r3 restore frozen -> exit 0', rc == 0, 'rc=%d' % rc)

        # ---- N5 调小某节下界不重钉 C16 ----
        g = base_gate.decode('utf-8')
        assert '141: 2548' in g
        g2 = g.replace('141: 2548', '141: 2000', 1)
        io.open(os.path.join(r14, 'check_disc.py'), 'w', encoding='utf-8').write(g2)
        rc, out = run_gate(r14)
        chk('N5 lower a floor w/o re-pin -> exit 1', rc == 1, 'rc=%d' % rc)
        chk('N5b reports C16d TAMPERED', 'C16d' in out and 'TAMPERED' in out,
            [l for l in out.splitlines() if 'C16d' in l][:1])
        io.open(os.path.join(r14, 'check_disc.py'), 'wb').write(base_gate)
        rc, _ = run_gate(r14)
        chk('P1 final restore -> exit 0', rc == 0, 'rc=%d' % rc)

        # ---- 咬合：N2 与 N5 是一对，不是同一个判断写两遍 ----
        chk('X1 N2 (内容缺失) 与 N5 (常量被改) 是两条不同判据',
            'hollow' in hol[0] if hol else False, 'N2=hollow-body / N5=C16d-pin')
    finally:
        shutil.rmtree(sb, ignore_errors=True)

    print('\n=== assertions %d, FAIL %d ===' % (len(RES), FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
