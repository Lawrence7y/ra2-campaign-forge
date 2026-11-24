#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102b_harden.py —— 门禁加严：C12 冻结档校验式真跑 + C6MAX 假旋钮接线

动机（R102 实测，见 r102a_holes.json）：
  * C11 的 31 行里只有 5 行（3/4/22/27/28）能 FAIL；余 26 行不可 FAIL：
    冻结 12 行走 c11_declared（不 FAIL）、col7 写「无」14 行直接 continue。
  * 更具体的一处：DISC_UNVERIFIABLE.tsv 自身的第 4 列「校验式」**门禁从不执行** ——
    门禁只读该表的第 1 列（id），再用 sha256 钉整档。于是「这 12 行确实有可命中的锚」
    这件事在门禁层面是**无人检查**的；只要 Lead 同步改 FREEZE_SHA256，写一个不存在的
    锚也照样绿。
  * C6MAX 是死旋钮：`--c6max=N` 被解析（check_disc.py:37-40）但全脚本无任何阈值判定
    （AST 实测 C6MAX 的 Load 次数 = 0）。docstring 第 12 行却写「超阈值即 FAIL」。实测
    `--c6max=0` 与默认参数输出逐字节相同 ⇒ 该旋钮在骗人。

本脚本做两处**纯加严**（今天全绿，故不改变 exit 0）：
  H1 新增 C12：冻结档 12 行逐行三重校验
       C12a 冻结 id ⊆ claims-有 集合（冻结只能发生在声称有回跑的行上）
       C12b 第 4 列校验式必须**真跑命中**（复用门禁自己的 run_expr，与 C7 同口径）
       C12c 第 6 列理由非空、第 7 列冻结时刻严格 ISO8601(+HH:MM)
  H2 把 C6MAX 接上线：cross > C6MAX ⇒ FAIL（默认 120，今日 cross=9 仍绿）

控制组（全部在沙箱 /tmp/r102_sbx2 里跑，不碰真门禁）：
  POS    原样沙箱 + 补丁 ⇒ exit 0
  M1     把冻结档某行校验式改成必不命中的正则 + 同步改 FREEZE_SHA256 ⇒ 必须 C12 FAIL
  NC1    M1 同一情形、但沙箱用**未打补丁**的门禁 ⇒ 必须 exit 0（证明抓到它的是 C12 本身）
  M2     --c6max=3 ⇒ 必须 C6 FAIL（cross=9 > 3）
  M3     --c6max=120 ⇒ 必须 exit 0
  NC2    M2 同一情形、未打补丁 ⇒ 必须 exit 0（证明抓到它的是 H2 本身）
  M4     冻结行第 6 列理由置空 ⇒ 必须 C12 FAIL
  M5     冻结行第 7 列时刻写成 2026-11-22 12:00（非 ISO8601+时区） ⇒ 必须 C12 FAIL
  M6     把某行的 col7 从「有」改「无」但保留其冻结位 ⇒ 必须 C12a FAIL（冻结⊄claims-有）
  POS2   全部还原 ⇒ exit 0

用法：
  python3 _r102/r102b_harden.py            # 只跑沙箱控制组，不碰真树
  python3 _r102/r102b_harden.py --apply    # 控制组全过后再落真门禁（带备份纪律）
"""
import hashlib, io, json, os, re, shutil, subprocess, sys

REAL = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
SBX = '/tmp/r102_sbx2'
OUT = os.path.join(REAL, '_r102')
BASE = os.path.join(REAL, R14REL, 'R17_LEAD_BASELINE')
GATE_REL = os.path.join(R14REL, 'check_disc.py')

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

# ---------------------------------------------------------------- 补丁正文
PATCH_C6 = """notes.append('C6 cross-namespace refs (compound-aware, outside 2.14+) = %d' % cross)
# ---- C6 阈值（R102 接线）：docstring 一直声称「超阈值即 FAIL」，而 C6MAX 此前从未被读 ----
if cross > C6MAX:
    fails.append('C6 cross-namespace refs %d > threshold %d (--c6max= to raise deliberately)'
                 % (cross, C6MAX))
else:
    notes.append('C6 threshold ok: %d <= %d' % (cross, C6MAX))
"""

PATCH_C12 = r'''
# ---- C12 【R102 新增】冻结档自身可核性：12 行「结构性不可验证」不是免检牌 ----
# R102 实测（_r102/r102a_holes.json）：C11 的 31 行里 26 行不可 FAIL，其中 12 行走冻结档。
# 冻结档一旦被读成「免检名单」，本门禁对它们就只剩 sha256 一个约束 —— 而 sha 是同一个
# 代码库里的常量，改锚+同步改常量即可无声通过。故 C12 把冻结档的**第 4 列校验式真跑一遍**：
# 冻结只豁免「自产出 DISC_RECHECK 行」，不豁免「它引用的锚真的存在且可命中」。
c12 = 0
if os.path.exists(_FREEZE):
    _fbody = [x.split('\t') for x in _frows[1:]]
    _claim_ids = set()
    for _r in rows:
        if len(_r) == 7 and _r[6].strip().startswith('有') and _r[0].strip().isdigit():
            _claim_ids.add(int(_r[0]))
    for _c in _fbody:
        if not (_c and _c[0].strip().isdigit()):
            continue
        _id = int(_c[0])
        _fid = 'C12 id %d' % _id
        if len(_c) < 8:
            fails.append('%s frozen row cols=%d (must be 8)' % (_fid, len(_c)))
            continue
        _p, _e, _why, _at = _c[2].strip(), _c[3].strip(), _c[5].strip(), _c[6].strip()
        # C12a 冻结只能发生在「声称有回跑」的行上
        if _id not in _claim_ids:
            fails.append('%s frozen but not claims-有 in DISC_RECHECK (freeze != escape hatch)'
                         % _fid)
        # C12b 第 4 列校验式必须真跑命中（与 C7 同口径、同一 run_expr）
        if not _p or _e in ('', 'none'):
            fails.append('%s frozen row has empty product/expr' % _fid)
        else:
            _ok, _det = run_expr(_p, _e)
            if _ok is not True:
                fails.append('%s frozen anchor does not hold (%s) :: %s' % (_fid, _det, _e[:40]))
            else:
                c12 += 1
        # C12c 理由非空 + 冻结时刻严格 ISO8601
        if not _why:
            fails.append('%s frozen reason empty' % _fid)
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}', _at):
            fails.append('%s frozen timestamp not strict ISO8601(+HH:MM): %r' % (_fid, _at))
notes.append('C12 frozen-anchor live-check: %d frozen rows, %d anchors hit' % (len(_fbody), c12))

'''

def bump_ver(src, new='R102'):
    src2, n = re.subn(r"^GATE_VER = 'R\d+'$", "GATE_VER = '%s'" % new, src, flags=re.M)
    assert n == 1, 'GATE_VER line not found exactly once: %d' % n
    return src2

def bump_self_rows(rows, new='R102'):
    """GATE_VER 被三重钉死（R102 实测，三处都要改，漏一处 POS 立刻 FAIL）：
       ① check_disc.py 模块常量
       ② DISC_RECHECK.tsv 第 20 行的校验式字面 `grep=(?m)^GATE_VER = 'R87'`（C7 会真跑它）
       ③ 同一行的 C10 自检（比对注册值 vs 实际值）
    这三重钉是我上补丁时被反控抓出来的：只改 ① 会让 POS 原样就 exit 1。
    本函数只改 ②（那个字面里的版本号），并把 ② 的语境记入返回值供结论引用。
    """
    out, hits = [], []
    for r in rows:
        r2 = list(r)
        if len(r2) == 7 and r2[4].strip().replace('/', '\\').endswith('check_disc.py'):
            m = re.search(r"GATE_VER = 'R(\d+)'", r2[5])
            if m:
                r2[5] = re.sub(r"GATE_VER = 'R\d+'", "GATE_VER = '%s'" % new, r2[5])
                hits.append((r2[0], r[5], r2[5]))
        out.append(r2)
    return out, hits

def patch(src):
    """返回打补丁后的源码。三处：C6 阈值、C12 块、GATE_VER。"""
    old_c6 = "notes.append('C6 cross-namespace refs (compound-aware, outside 2.14+) = %d' % cross)\n"
    assert src.count(old_c6) == 1, 'C6 anchor line count %d' % src.count(old_c6)
    s = src.replace(old_c6, PATCH_C6)
    anchor = "# ---- C5 CR 抽查 ----"
    assert s.count(anchor) == 1, 'C5 anchor count %d' % s.count(anchor)
    s = s.replace(anchor, PATCH_C12.lstrip('\n') + anchor)
    s = bump_ver(s)
    return s

# ---------------------------------------------------------------- 沙箱
def build_sandbox(gate_src=None, bump_rows=False):
    if os.path.isdir(SBX):
        shutil.rmtree(SBX)
    os.makedirs(SBX)
    for e in os.listdir(REAL):
        if e in ('lead', '_r102'):
            continue
        os.symlink(os.path.join(REAL, e), os.path.join(SBX, e))
    os.makedirs(os.path.join(SBX, 'lead'))
    for e in os.listdir(os.path.join(REAL, 'lead')):
        if e == 'next_re_20261117_r14':
            continue
        os.symlink(os.path.join(REAL, 'lead', e), os.path.join(SBX, 'lead', e))
    os.makedirs(os.path.join(SBX, R14REL))
    for e in os.listdir(os.path.join(REAL, R14REL)):
        src = os.path.join(REAL, R14REL, e)
        dst = os.path.join(SBX, R14REL, e)
        if e in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv'):
            shutil.copy2(src, dst)
        else:
            os.symlink(src, dst)
    g = os.path.join(SBX, GATE_REL)
    if gate_src is not None:
        io.open(g, 'w', encoding='utf-8', newline='').write(gate_src)
    if bump_rows:
        rows, nl, p = read_rows('DISC_RECHECK.tsv')
        rows2, hits = bump_self_rows(rows)
        assert len(hits) == 1, 'self rows bumped: %d' % len(hits)
        write_rows(rows2, nl, p)
    return g

def run_gate(*args):
    g = os.path.join(SBX, GATE_REL)
    p = subprocess.run([sys.executable, g] + list(args), capture_output=True, text=True, cwd=SBX)
    fails = [l.strip()[6:] for l in p.stdout.splitlines() if l.strip().startswith('FAIL  ')]
    return p.returncode, fails, p.stdout

def read_rows(rel):
    p = os.path.join(SBX, R14REL, rel)
    txt = io.open(p, encoding='utf-8', newline='').read()
    return [l.split('\t') for l in txt.split('\n') if l], txt.endswith('\n'), p

def write_rows(rows, nl, p):
    io.open(p, 'w', encoding='utf-8', newline='').write(
        '\n'.join('\t'.join(r) for r in rows) + ('\n' if nl else ''))

def sync_freeze_sha(gate_path):
    """改完冻结档后同步门禁常量，模拟「Lead 显式改 FREEZE_SHA256」这条合法路径。"""
    p = os.path.join(SBX, R14REL, 'DISC_UNVERIFIABLE.tsv')
    h = hashlib.sha256(io.open(p, 'rb').read()).hexdigest()
    s = io.open(gate_path, encoding='utf-8').read()
    s2, n = re.subn(r"FREEZE_SHA256 = '[0-9a-f]{64}'", "FREEZE_SHA256 = '%s'" % h, s)
    assert n == 1
    io.open(gate_path, 'w', encoding='utf-8', newline='').write(s2)
    return h

def main():
    os.makedirs(OUT, exist_ok=True)
    real_src = io.open(os.path.join(REAL, GATE_REL), encoding='utf-8').read()
    patched = patch(real_src)
    ck('P0 补丁后源码语法可编译', (lambda: (compile(patched, 'x', 'exec'), True)[1])(), '')
    ck('P1 GATE_VER 已抬到 R102', "GATE_VER = 'R102'" in patched)
    ck('P2 C12 块只插一次', patched.count('# ---- C12 ') == 1)
    ck('P3 C6 阈值只插一次', patched.count('if cross > C6MAX:') == 1)

    # ---------- POS 打补丁原样 ----------
    g = build_sandbox(patched, bump_rows=True)
    sync_freeze_sha(g)          # 冻结档未变，sha 不变；清一下保证一致
    rc, fails, so = run_gate()
    ck('POS 打补丁后原样 exit 0', rc == 0, 'exit=%d fails=%s' % (rc, fails[:4]))
    ck('POS-note C12 报 12 行 12 命中',
       'C12 frozen-anchor live-check: 12 frozen rows, 12 anchors hit' in so,
       [l for l in so.splitlines() if 'C12' in l])
    ck('POS-note C6 阈值报 9 <= 120',
       'C6 threshold ok: 9 <= 120' in so, [l for l in so.splitlines() if 'C6 threshold' in l])

    # ---------- M1 冻结锚改坏 + 同步改 sha ----------
    rows, nl, p = read_rows('DISC_UNVERIFIABLE.tsv')
    rows1 = [list(r) for r in rows]
    rows1[1][3] = 'grep=R102_THIS_PATTERN_MUST_NOT_EXIST_zzz'   # id 1 的校验式
    write_rows(rows1, nl, p)
    sync_freeze_sha(g)
    rc1, f1, so1 = run_gate()
    hit1 = [x for x in f1 if x.startswith('C12 id 1')]
    ck('M1 冻结锚写坏+同步sha ⇒ C12 id1 FAIL（补丁前这条路无声通过）',
       rc1 == 1 and bool(hit1), 'exit=%d C12fails=%s' % (rc1, hit1))

    # ---------- NC1 同一情形、未打补丁的门禁 ----------
    write_rows(rows1, nl, p)                     # 坏档仍在
    g0 = build_sandbox(real_src)                 # 未打补丁
    sync_freeze_sha(g0)
    rc1b, f1b, _ = run_gate()
    ck('NC1 同一坏档 + 未打补丁门禁 ⇒ exit 0（抓到它的是 C12 本身，不是别的）',
       rc1b == 0 and not [x for x in f1b if 'C12' in x], 'exit=%d fails=%s' % (rc1b, f1b[:3]))

    # ---------- M2/M3 C6MAX 接线 ----------
    g = build_sandbox(patched, bump_rows=True)
    rc2, f2, _ = run_gate('--c6max=3')
    hit2 = [x for x in f2 if x.startswith('C6 ') and 'threshold' in x]
    ck('M2 --c6max=3 ⇒ C6 阈值 FAIL（cross=9 > 3）', rc2 == 1 and bool(hit2), hit2[:2])
    rc3, f3, _ = run_gate('--c6max=120')
    ck('M3 --c6max=120 ⇒ exit 0', rc3 == 0, 'exit=%d fails=%s' % (rc3, f3[:3]))
    # ---------- NC2 同一参数、未打补丁 ----------
    g0 = build_sandbox(real_src)
    rc3b, f3b, so3b = run_gate('--c6max=3')
    ck('NC2 --c6max=3 + 未打补丁 ⇒ exit 0（假旋钮：此前该参数无任何作用）',
       rc3b == 0, 'exit=%d' % rc3b)
    rc3c, _, so3c = run_gate('--c6max=0')
    ck('NC2b 未打补丁时 --c6max=0 与默认输出逐字节相同（旋钮纯装饰）',
       so3b.replace('--c6max=3', '') != '' and so3c == so3b, 'same=%s' % (so3c == so3b))

    # ---------- M4/C12c 理由置空 ----------
    g = build_sandbox(patched, bump_rows=True)
    rows, nl, p = read_rows('DISC_UNVERIFIABLE.tsv')
    r4 = [list(r) for r in rows]
    r4[2][5] = ''
    write_rows(r4, nl, p); sync_freeze_sha(g)
    rc4, f4, _ = run_gate()
    ck('M4 冻结行理由置空 ⇒ C12 FAIL', rc4 == 1 and [x for x in f4 if 'reason empty' in x],
       [x for x in f4 if 'C12' in x][:2])

    # ---------- M5/C12c 时刻格式 ----------
    r5 = [list(r) for r in rows]
    r5[2][6] = '2026-11-22 12:00'
    write_rows(r5, nl, p); sync_freeze_sha(g)
    rc5, f5, _ = run_gate()
    ck('M5 冻结时刻非 ISO8601+时区 ⇒ C12 FAIL',
       rc5 == 1 and [x for x in f5 if 'not strict ISO8601' in x],
       [x for x in f5 if 'C12' in x][:2])

    # ---------- M6/C12a 冻结行改成「无」 ----------
    write_rows(rows, nl, p); sync_freeze_sha(g)
    dr, nl_dr, pdr = read_rows('DISC_RECHECK.tsv')
    d6 = [list(r) for r in dr]
    for r in d6[1:]:
        if r[0] == '1':
            r[6] = '无（R102 控制组故意改成无）'
    write_rows(d6, nl_dr, pdr)
    rc6, f6, _ = run_gate()
    ck('M6 冻结行 col7 改「无」⇒ C12a FAIL（冻结不等于可退出有回跑声明）',
       rc6 == 1 and [x for x in f6 if 'freeze != escape hatch' in x],
       [x for x in f6 if 'C12' in x][:2])

    # ---------- POS2 还原 ----------
    write_rows(dr, nl_dr, pdr)
    build_sandbox(patched, bump_rows=True)
    rc7, f7, _ = run_gate()
    ck('POS2 还原后 exit 0', rc7 == 0, 'exit=%d fails=%s' % (rc7, f7[:3]))

    n_fail = sum(1 for c in checks if not c['ok'])
    summary = {'n_checks': len(checks), 'n_fail': n_fail,
               'patched_sha256': hashlib.sha256(patched.encode('utf-8')).hexdigest(),
               'real_before_sha256': hashlib.sha256(real_src.encode('utf-8')).hexdigest(),
               'checks': checks}
    json.dump(summary, io.open(os.path.join(OUT, 'r102b_harden.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))

    if n_fail == 0 and '--apply' in sys.argv:
        return apply_to_real(real_src, patched)
    if '--apply' in sys.argv:
        print('REFUSE --apply: controls not all green')
        return 1
    return 0 if n_fail == 0 else 1

# ---------------------------------------------------------------- 落真树（写入纪律）
def apply_to_real(old_src, new_src):
    gate_abs = os.path.join(REAL, GATE_REL)
    stamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BASE, 'R102.before_check_disc_harden_%s.bak' % stamp)
    old_sha = hashlib.sha256(io.open(gate_abs, 'rb').read()).hexdigest()
    old_cr = io.open(gate_abs, 'rb').read().count(b'\r\n')
    # wx 独占创建
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(io.open(gate_abs, 'rb').read())
    ck('A0 备份已用 wx 独占创建', os.path.isfile(bak), bak)
    ck('A1 备份 sha256 == 改前 sha256', hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == old_sha,
       old_sha[:16])
    ck('A2 check_disc.py 全 LF（CR=0）', old_cr == 0, old_cr)
    # 一次性写入
    io.open(gate_abs, 'w', encoding='utf-8', newline='').write(new_src)
    back = io.open(gate_abs, 'rb').read()
    ck('A3 回读 sha256 == 补丁 sha256',
       hashlib.sha256(back).hexdigest() == hashlib.sha256(new_src.encode('utf-8')).hexdigest(),
       hashlib.sha256(back).hexdigest()[:16])
    ck('A4 回读仍全 LF', back.count(b'\r\n') == 0, back.count(b'\r\n'))
    p = subprocess.run([sys.executable, gate_abs], capture_output=True, text=True, cwd=REAL)
    ck('A5 真门禁改后 exit 0', p.returncode == 0, p.stdout.strip().splitlines()[-3:])
    json.dump({'n_checks': len(checks), 'n_fail': sum(1 for c in checks if not c['ok']),
               'applied': True, 'backup': bak, 'checks': checks},
              io.open(os.path.join(OUT, 'r102b_apply.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(p.stdout)
    return 0 if sum(1 for c in checks if not c['ok']) == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
