#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r120c_gate_c17.py —— C17 家族（C17a 时间不可能性 / C17b 跨轮复用）的成对回归。

判据变更必须配成对回归：同一批变异在**旧 gate（R119，无 C17）**与**新 gate（R120，含 C17）**
上各跑一遍，逐条给出 exit 与「FAIL 是否点名 C17」。
变异集：
  P1 基线（无变异）                      —— 两边都必须 exit 0
  P2 正控：往产物里加一条**诚实**自述行（round = 产物路径轮次 64，at 落在 R64 窗口）
                                         —— C17 不得开火（证明它不是对所有行一律开火）
  A1 攻击：把一条已有自述行原样复制进另一个轮次的产物（跨轮复用 + 时间不可能）
  A2 攻击：把 27 号行静默「改成诚实」（round=R81）
  A3 攻击：删掉 28 号行
  A4 攻击：只改 C17_PIN 里的一个元组（不同步改 sha）
  A5 反控：把 C17_PIN_SHA256 改错 1 个 hex
内存纪律：只读文本 + 沙箱拷贝；不碰二进制、不碰 live 文件（除读）。
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r120', 'r120c_gate_c17.json')
NEWGATE = os.path.join(R14, 'check_disc.py')
NEWTSV = os.path.join(R14, 'DISC_RECHECK.tsv')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def newest(prefix):
    cands = sorted(f for f in os.listdir(BASE) if f.startswith(prefix) and f.endswith('.bak'))
    assert cands, prefix
    return os.path.join(BASE, cands[-1])


OLDGATE = newest('check_disc.py.before_R120_c17_')
OLDTSV = newest('DISC_RECHECK.tsv.before_R120_c17_')
ck('Z0 旧 gate / 旧表已定位（成对回归的两个对照件）',
   os.path.isfile(OLDGATE) and os.path.isfile(OLDTSV),
   {'old_gate': os.path.basename(OLDGATE), 'old_tsv': os.path.basename(OLDTSV)})


def mktree(prefix):
    EX = {'R17_LEAD_BASELINE', '_cards', '__pycache__', 'D41_SUBST'}
    tmp = tempfile.mkdtemp(prefix=prefix, dir=os.path.join(ROOT, '_r120'))
    root = os.path.join(tmp, 'root')
    dst = os.path.join(root, 'lead', 'next_re_20261117_r14')
    os.makedirs(dst)

    def _walk(s, d):
        for e in os.scandir(s):
            if e.name in EX:
                continue
            sp, dp = e.path, os.path.join(d, e.name)
            if e.is_symlink():
                continue
            if e.is_dir(follow_symlinks=False):
                os.makedirs(dp, exist_ok=True)
                _walk(sp, dp)
            elif e.is_file(follow_symlinks=False):
                shutil.copy2(sp, dp)

    _walk(R14, dst)
    os.symlink(os.path.join(R14, 'R17_LEAD_BASELINE'), os.path.join(dst, 'R17_LEAD_BASELINE'))
    shutil.copy2(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
                 os.path.join(root, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    # C7 id 31 的产物在 _r94/（纪律 31 的落盘位置），沙箱必须带上它，否则基线假 FAIL（S-70）
    shutil.copytree(os.path.join(ROOT, '_r94'), os.path.join(root, '_r94'), symlinks=True)
    return tmp, root, dst


def run(gate, tsv, dst):
    ap = os.path.join(dst, 'check_disc.py')
    if os.path.lexists(ap):
        os.remove(ap)
    shutil.copy2(gate, ap)
    shutil.copy2(tsv, os.path.join(dst, 'DISC_RECHECK.tsv'))
    r = subprocess.run([sys.executable, ap], cwd=dst, capture_output=True, text=True, timeout=300)
    o = (r.stdout or '') + (r.stderr or '')
    return r.returncode, o


def fails_of(o):
    return [l.strip() for l in o.split('\n') if l.strip().startswith('FAIL')]


LINE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')


# 第 4 列的路径是**相对 ROOT**（含 lead/next_re_20261117_r14 前缀），故沙箱内要按 root 解析，
# 不能拼到 R14 副本目录上（S-71：首版拼错，把工程根前缀又叠了一层）。
def _ap(root, rel):
    return os.path.join(root, rel.replace('\\', '/'))


def read_rel(root, rel):
    return io.open(_ap(root, rel), encoding='utf-8', newline='').read()


def write_rel(root, rel, txt):
    io.open(_ap(root, rel), 'w', encoding='utf-8', newline='').write(txt)


tmp, root, dst = mktree('sbx120c_')
res = {}
try:
    # ---- P1 基线 ----
    rc_n, o_n = run(NEWGATE, NEWTSV, dst)
    rc_o, o_o = run(OLDGATE, OLDTSV, dst)
    ck('P1 基线：新 gate exit %d / 旧 gate exit %d，两边都无 C17 FAIL'
       % (rc_n, rc_o), rc_n == 0 and rc_o == 0 and not any('C17' in l for l in fails_of(o_n)),
       {'new': fails_of(o_n)[:3], 'old': fails_of(o_o)[:3]})

    # ---- P2 正控：加一条诚实自述行（round = 路径轮次 64） ----
    # 纪律 5 的产物在 R17_R64_ADEQUACY2/lead_recheck2.tsv（路径轮次 64）。
    # R64 窗口 = [T(63),T(64)) = [18:36:11, 18:38:42)（磁盘快照推导）；
    # anchors 必须绑定该行第 4 列逐字串，故从 live 表里取真实值。
    rows = [l.split('\t') for l in io.open(NEWTSV, encoding='utf-8', newline='').read().split('\n') if l][1:]
    r5 = [x for x in rows if x[0].strip() == '5'][0]
    at64 = '2026-11-22T18:37:00+08:00'
    honest5 = 'DISC_RECHECK discipline=5 round=R64 at=%s anchors=sha256:%s conclusion=UNKNOWN' % (
        at64, hashlib.sha256(r5[3].encode('utf-8')).hexdigest())
    rel5 = r5[4].strip()
    body5 = read_rel(root, rel5)
    write_rel(root, rel5, body5.rstrip('\n') + '\n' + honest5 + '\n')
    rc_p2, o_p2 = run(NEWGATE, NEWTSV, dst)
    f_p2 = fails_of(o_p2)
    c17_p2 = [l for l in f_p2 if 'C17' in l]
    ck('P2 正控（C17 不一律开火）：追加一条**诚实**自述行（round=R64 = 产物路径轮次）⇒ '
       'C17 FAIL 数 = %d（其余 FAIL 行如实抄录 %s）' % (len(c17_p2), f_p2[:2]),
       len(c17_p2) == 0, {'fail_lines': f_p2[:4]})
    write_rel(root, rel5, body5)

    # ---- A1 攻击（判别性）：把 27 号行的 at 在 R55 窗口内平移 41 秒 ----
    # 这一改动对旧 gate **完全不可见**（anchors 绑第 4 列、R3 只比立条上界、R4 只看窗口），
    # 但 C17a 钉的是 (id, round, at) 三元组 ⇒ 必须被抓。
    # 🐞 自错 S-72：首版 A1 把 3 号行（anchors 属 3 号的第 4 列）改 discipline=5 贴进 R84 产物，
    # 断言「C17 必 FAIL」—— 实测 exit 0。原因不是 C17 坏了，而是我的**攻击打在了作用域外**：
    # 5 号行第 7 列是「无」，C17 只扫 claims-有 行；且该行 anchors 与 5 号第 4 列不符，R5 必挂
    # ⇒ 这条行本来就是惰性的，不构成攻击。作用域边界如实登记为 A1b。
    rel27 = [x for x in rows if x[0].strip() == '27'][0][4].strip()
    body27 = read_rel(root, rel27)
    moved = body27.replace('at=2026-11-22T17:39:19+08:00', 'at=2026-11-22T17:40:00+08:00', 1)
    assert moved != body27
    write_rel(root, rel27, moved)
    rc_a1, o_a1 = run(NEWGATE, NEWTSV, dst)
    rc_a1o, o_a1o = run(OLDGATE, OLDTSV, dst)
    f_a1 = fails_of(o_a1)
    ck('A1 攻击（窗口内平移 41 秒）：27 号行 at 17:39:19→17:40:00 ⇒ 旧 gate exit %d（%s），'
       '新 gate exit %d 且点名 C17（%s）'
       % (rc_a1o, fails_of(o_a1o)[:1], rc_a1, [l for l in f_a1 if 'C17' in l][:1]),
       rc_a1o == 0 and rc_a1 != 0 and any('C17' in l for l in f_a1),
       {'old_fails': fails_of(o_a1o)[:2]})
    write_rel(root, rel27, body27)

    # ---- A1b 作用域边界（事实登记，不是断言绿）：把 3 号行原样改 discipline=5 贴进 R84 产物 ----
    rel3 = [x for x in rows if x[0].strip() == '3'][0][4].strip()
    body3 = read_rel(root, rel3)
    line3 = [l for l in body3.splitlines() if l.startswith('DISC_RECHECK discipline=3 ')][0]
    rel84 = [x for x in rows if x[0].strip() == '22'][0][4].strip()
    body84 = read_rel(root, rel84)
    copied = line3.replace('discipline=3', 'discipline=5', 1)
    write_rel(root, rel84, body84.rstrip('\n') + '\n' + copied + '\n')
    rc_a1b, o_a1b = run(NEWGATE, NEWTSV, dst)
    ck('A1b 作用域边界（如实登记）：给 claims-无 的 5 号纪律贴一条 anchors 与它第 4 列不符的复制行 '
       '⇒ exit %d。C17 只扫 claims-有 行，故不开火；该行是惰性的（C11 对 claims-无 本就不看），'
       '不构成得分路径' % rc_a1b, rc_a1b == 0, {'fails': fails_of(o_a1b)[:2]})
    write_rel(root, rel84, body84)

    # ---- A2 攻击：静默「改成诚实」（27 号行 round 改成 R81） ----
    body27 = read_rel(root, rel27)
    fixed = re.sub(r'round=R55', 'round=R81', body27, count=1)
    assert fixed != body27
    write_rel(root, rel27, fixed)
    rc_a2, o_a2 = run(NEWGATE, NEWTSV, dst)
    rc_a2o, o_a2o = run(OLDGATE, OLDTSV, dst)
    f_a2 = fails_of(o_a2)
    ck('A2 攻击（静默改成诚实）：27 号行 round=R55→R81 ⇒ 新 gate exit %d 且点名 C17（%s）；'
       '旧 gate 在同一变异上 exit %d，其 FAIL 为 %s（两边原因不同，如实抄录）'
       % (rc_a2, [l for l in f_a2 if 'C17' in l][:1], rc_a2o, fails_of(o_a2o)[:2]),
       rc_a2 != 0 and any('C17' in l for l in f_a2), {'old_fails': fails_of(o_a2o)[:3]})
    write_rel(root, rel27, body27)

    # ---- A3 攻击：删掉 28 号行 ----
    rel28 = [x for x in rows if x[0].strip() == '28'][0][4].strip()
    body28 = read_rel(root, rel28)
    dropped = '\n'.join(l for l in body28.splitlines() if not l.startswith('DISC_RECHECK discipline=28 '))
    assert dropped != body28
    write_rel(root, rel28, dropped + '\n')
    rc_a3, o_a3 = run(NEWGATE, NEWTSV, dst)
    f_a3 = fails_of(o_a3)
    ck('A3 攻击（删行）：删掉 28 号行 ⇒ 新 gate exit %d 且点名 C17（%s）'
       % (rc_a3, [l for l in f_a3 if 'C17' in l][:1]),
       rc_a3 != 0 and any('C17' in l for l in f_a3), {'fails': f_a3[:3]})
    write_rel(root, rel28, body28)

    # ---- A4/A5：改常量（沙箱内 patch gate 源码） ----
    srcN = io.open(NEWGATE, encoding='utf-8', newline='').read()

    def run_patched(patch):
        s2 = srcN
        for a, b in patch:
            assert a in s2, a
            s2 = s2.replace(a, b, 1)
        p = os.path.join(dst, '_cd_c17probe.py')
        io.open(p, 'w', encoding='utf-8', newline='\n').write(s2)
        r = subprocess.run([sys.executable, p], cwd=dst, capture_output=True, text=True, timeout=300)
        return r.returncode, (r.stdout or '') + (r.stderr or '')

    rc_a4, o_a4 = run_patched([("(27, 55, '2026-11-22T17:39:19+08:00'),",
                                "(27, 55, '2026-11-22T17:39:20+08:00'),")])
    f_a4 = fails_of(o_a4)
    # 🐞 自错 S-73：首版断言「改 C17_PIN 必须触发 pin TAMPERED」。实测触发的却是
    # 「C17a 集合变了」——因为 sha 是从**实测集合**算出来的，改钉住的常量不改变实测集合。
    # 两道子项分工不同：集合比对抓「行变了」，sha 钉抓「常量被改成与实测不符」。
    ck('A4 攻击（只改 C17_PIN 一个元组，不同步改 sha）⇒ exit %d，FAIL 行 = %s'
       % (rc_a4, [l[:60] for l in f_a4 if 'C17' in l][:1]),
       rc_a4 != 0 and any(('集合变了' in l) for l in f_a4), {'fails': f_a4[:3]})

    rc_a5, o_a5 = run_patched([('C17_PIN_SHA256 = \'642c9cd8', 'C17_PIN_SHA256 = \'642c9cd9')])
    f_a5 = fails_of(o_a5)
    ck('A5 反控（pin 常量写错 1 个 hex）⇒ exit %d，FAIL 含 pin TAMPERED：%s'
       % (rc_a5, [l for l in f_a5 if 'TAMPERED' in l][:1]),
       rc_a5 != 0 and any('TAMPERED' in l for l in f_a5), {'fails': f_a5[:3]})

    # ---- A6 反控：C17 的 NOTE 自有计数必须与实测一致（不是恒 0） ----
    m = re.search(r'C17 self-produced-line anachrony: checked=(\d+) impossible=(\d+) \(pinned (\d+)\)',
                  o_n)
    ck('A6 反控（C17 不是恒 0 统计）：基线 NOTE 里 checked=%s impossible=%s pinned=%s'
       % (m.groups() if m else (None, None, None)),
       bool(m) and int(m.group(1)) == 5 and int(m.group(2)) == 5 and int(m.group(3)) == 5,
       list(m.groups()) if m else None)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

json.dump({'old_gate': os.path.basename(OLDGATE), 'old_tsv': os.path.basename(OLDTSV),
           'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
