#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102e_landable.py —— 第三个假旋钮：C11_LANDABLE 是死常量且内容自相矛盾

R102 实测三件事：
  1. AST：C11_LANDABLE（check_disc.py:240）在脚本里 Load 次数 = 0 —— 纯死代码。
     它旁边的注释写着「12/28 可补」，读者会以为门禁在按它调度，其实没有。
  2. 内容错：它列的 12 个 id 里，有 7 个（11/12/13/14/15/17/26）在 DISC_RECHECK 第 7 列
     写的是「无（仅立条当轮自带）」⇒ 按 C11 现有逻辑直接 continue、**永远不可能 FAIL**。
     所以「可补」这个说法对这 7 行不成立：它们不是「还没补」，是「声明了不需要补」。
  3. 真值集：结构上能 FAIL 的只有 5 个 id（3/4/22/27/28），恰是 LANDABLE ∩ claims-有。

本脚本不改判据（不改 exit 0），只做两件事：
  P/L1  把死常量变成**载重常量**：读出它、与磁盘派生集比对、把缺口**显式量化**。
        从此改这个集合或改 DISC_RECHECK 第 7 列，都会让门禁输出里的缺口数字变动。
  P/L2  给缺口数字**钉死**（pin）：缺口的 id 列表与规模一旦变化即 FAIL。
        这不是「修好 7 行」，而是「让 7 行的存在无法再被静默忽略」。
        真正的修法（让 7 行各自产出合规自述行，或把它们移进冻结档并写明理由）留待下轮，
        因为那是写入 DISC_RECHECK 第 7 列的重大变更，必须单独一卡 + 跨家族审计。

控制组：
  POS   打补丁原样 ⇒ exit 0，且输出含「gap=7 ids=[11,12,...]」
  M1    把 C11_LANDABLE 里删掉一个 id（如 26）⇒ 必须 FAIL（pin 抓到集合漂移）
  M2    把 id 11 的第 7 列从「无」改「有」⇒ 必须 FAIL（缺口从 7 变 6，pin 抓到）
  NC1   M2 同一情形 + 未打补丁 ⇒ exit 0（证明抓到它的是本补丁）
  NC2   打补丁后 --c6max 仍正常（不互相干扰）
"""
import hashlib, io, json, os, re, shutil, subprocess, sys, datetime

REAL = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
GATE = os.path.join(REAL, R14REL, 'check_disc.py')
BASE = os.path.join(REAL, R14REL, 'R17_LEAD_BASELINE')
SBX = '/tmp/r102_sbx3'
OUT = os.path.join(REAL, '_r102')

# 现状钉死值（实测，非预估）
PIN_GAP_IDS = [11, 12, 13, 14, 15, 17, 26]
PIN_LANDABLE = [3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28]

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

PATCH_OLD = b"C11_LANDABLE = {3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28}\r\n"
PATCH_NEW = (
    b"C11_LANDABLE = {3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28}\r\n"
    b"# ---- C11b \xe3\x80\x90R102 \xe6\x96\xb0\xe5\xa2\x9e\xe3\x80\x91"
    b"C11_LANDABLE \xe8\xbd\xbd\xe9\x87\x8d\xef\xbc\x9a\xe6\xad\xbb\xe5\xb8\xb8\xe9\x87\x8f"
    b"\xe5\x8f\x98\xe6\x88\x90\xe5\x8f\xaf\xe6\xa0\xb8\xe7\x9a\x84\xe7\xbc\xba\xe5\x8f\xa3"
    b"\xe9\x87\x8f\xe4\xb8\x8e\xe9\x92\x89\xe4\xbd\x8f ----\r\n"
    b"# R102 \xe5\xae\x9e\xe6\xb5\x8b\xef\xbc\x9a\xe8\xaf\xa5\xe5\xb8\xb8\xe9\x87\x8f\xe6"
    b"\xad\xa4\xe5\x89\x8d Load \xe6\xac\xa1\xe6\x95\xb0 = 0\xef\xbc\x88\xe7\xba\xaf\xe6"
    b"\xad\xbb\xe4\xbb\xa3\xe7\xa0\x81\xef\xbc\x89\xef\xbc\x8c\xe4\xb8\x94\xe5\xae\x83"
    b"\xe5\x88\x97\xe7\x9a\x84 12 \xe4\xb8\xaa id \xe9\x87\x8c\xe6\x9c\x89 7 \xe4\xb8\xaa"
    b"\xe5\x86\x99\xe7\x9d\x80\xe3\x80\x8c\xe6\x97\xa0\xe3\x80\x8d\xe2\x80\x94\xe2\x80"
    b"\x94\xe5\xa3\xb0\xe6\x98\x8e\xe4\xb8\x8d\xe9\x9c\x80\xe8\xa6\x81\xe5\x9b\x9e\xe8\xb7\x91"
    b"\xef\xbc\x8c\xe6\x95\x85\xe6\xb0\xb8\xe8\xbf\x9c\xe4\xb8\x8d\xe5\x8f\xaf\xe8\x83\xbd FAIL"
    b"\xe3\x80\x82\xe9\x82\xa3 7 \xe8\xa1\x8c\xe4\xb8\x8d\xe6\x98\xaf\xe3\x80\x8c\xe8\xbf\x98"
    b"\xe6\x9c\xaa\xe8\xa1\xa5\xe3\x80\x8d\xe6\x98\xaf\xe3\x80\x8c\xe5\xa3\xb0\xe6\x98\x8e"
    b"\xe4\xb8\x8d\xe8\xa1\xa5\xe3\x80\x8d\xe3\x80\x82\r\n"
    b"# \xe6\x9c\xac\xe6\xae\xb5\xe4\xb8\x8d\xe4\xbf\xae\xe9\x82\xa3 7 \xe8\xa1\x8c\xef\xbc"
    b"\x88\xe9\x82\xa3\xe6\x98\xaf\xe5\x86\x99\xe5\x85\xa5\xe5\x8f\x98\xe6\x9b\xb4\xef\xbc"
    b"\x8c\xe9\xa1\xbb\xe5\x8d\x95\xe7\x8b\xac\xe4\xb8\x80\xe5\x8d\xa1\xef\xbc\x89\xef\xbc"
    b"\x8c\xe5\x8f\xaa\xe6\x8a\x8a\xe7\xbc\xba\xe5\x8f\xa3\xe6\x98\xbe\xe5\xbc\x8f\xe5\x8c"
    b"\x96\xe5\xb9\xb6\xe9\x92\x89\xe4\xbd\x8f\xe3\x80\x82\r\n"
    b"C11B_PIN_GAP = [11, 12, 13, 14, 15, 17, 26]\r\n"
    b"c11b_gap = []\r\n"
    b"for _r in rows:\r\n"
    b"    if len(_r) == 7 and _r[0].strip().isdigit() and int(_r[0]) in C11_LANDABLE:\r\n"
    b"        if not _r[6].strip().startswith('\\u6709'):\r\n"
    b"            c11b_gap.append(int(_r[0]))\r\n"
    b"c11b_gap = sorted(c11b_gap)\r\n"
    b"notes.append('C11b loadable-registry: declared=%d rows, gap(claims-none, can never FAIL)=%d ids=%s'\r\n"
    b"             % (len(C11_LANDABLE), len(c11b_gap), c11b_gap))\r\n"
    b"if c11b_gap != sorted(C11B_PIN_GAP):\r\n"
    b"    fails.append('C11b loadable gap drifted: %s != pinned %s (fix the rows, then re-pin deliberately)'\r\n"
    b"                 % (c11b_gap, sorted(C11B_PIN_GAP)))\r\n"
)

def build_sandbox(gate_src=None, drop_landable=[], flip_to_you=[]):
    if os.path.isdir(SBX):
        shutil.rmtree(SBX)
    os.makedirs(SBX)
    for e in os.listdir(REAL):
        if e in ('lead', '_r102'):
            continue
        os.symlink(os.path.join(REAL, e), os.path.join(SBX, e))
    os.makedirs(os.path.join(SBX, 'lead'))
    for e in os.listdir(os.path.join(REAL, 'lead')):
        if e != 'next_re_20261117_r14':
            os.symlink(os.path.join(REAL, 'lead', e), os.path.join(SBX, 'lead', e))
    os.makedirs(os.path.join(SBX, R14REL))
    for e in os.listdir(os.path.join(REAL, R14REL)):
        s, d = os.path.join(REAL, R14REL, e), os.path.join(SBX, R14REL, e)
        if e in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv'):
            shutil.copy2(s, d)
        else:
            os.symlink(s, d)
    g = os.path.join(SBX, R14REL, 'check_disc.py')
    if gate_src is not None:
        io.open(g, 'wb').write(gate_src)
    if drop_landable:
        b = io.open(g, 'rb').read()
        base = sorted(set(PIN_LANDABLE) - set(drop_landable))
        new = ('C11_LANDABLE = {%s}' % ', '.join(str(x) for x in base)).encode()
        b = re.sub(rb"C11_LANDABLE = \{[0-9, ]+\}", new, b, count=1)
        io.open(g, 'wb').write(b)
    if flip_to_you:
        p = os.path.join(SBX, R14REL, 'DISC_RECHECK.tsv')
        rows = [l.split('\t') for l in io.open(p, encoding='utf-8').read().split('\n') if l]
        for r in rows[1:]:
            if int(r[0]) in flip_to_you:
                r[6] = '有（R102 控制组故意改成有）'
        io.open(p, 'w', encoding='utf-8', newline='').write(
            '\n'.join('\t'.join(r) for r in rows) + '\n')
    return g

def run_gate(*args):
    g = os.path.join(SBX, R14REL, 'check_disc.py')
    p = subprocess.run([sys.executable, g] + list(args), capture_output=True, text=True, cwd=SBX)
    fails = [l.strip()[6:] for l in p.stdout.splitlines() if l.strip().startswith('FAIL  ')]
    return p.returncode, fails, p.stdout

def main():
    os.makedirs(OUT, exist_ok=True)
    src = io.open(GATE, 'rb').read()
    ck('J0 门禁当前无 C11b（未打过本补丁）', b'C11B_PIN_GAP' not in src)
    ck('J1 补丁锚唯一', src.count(PATCH_OLD) == 1, src.count(PATCH_OLD))
    new = src.replace(PATCH_OLD, PATCH_NEW)
    ck('J2 补丁后语法可编译', (compile(new.decode('utf-8'), 'g', 'exec') or True), '')
    # R102 自错 4：初版断言写「CRLF/LF 结构不变」并要求 (CRLF,LF) 元组相等 —— 那是错的：
    # 本补丁新增 15 行，全部是 CRLF，CRLF 计数必然从 366 涨到 381。正确的不变量是
    # 「LF-only 行数不变」（＝新插入的行没有一行是裸 LF），即不得引入混合行尾。
    old_lfonly = src.count(b'\n') - src.count(b'\r\n')
    new_lfonly = new.count(b'\n') - new.count(b'\r\n')
    ck('J3 不引入裸 LF 行（LF-only 行数不变）', new_lfonly == old_lfonly,
       'CRLF %d->%d ; LFonly %d->%d' % (src.count(b'\r\n'), new.count(b'\r\n'),
                                        old_lfonly, new_lfonly))

    g = build_sandbox(new)
    rc, fails, so = run_gate()
    line = [l for l in so.splitlines() if 'C11b loadable-registry' in l]
    ck('POS 打补丁原样 exit 0', rc == 0, 'exit=%d fails=%s' % (rc, fails[:3]))
    ck('POS 输出含 gap=7 且 id 列表等于钉子',
       bool(line) and 'gap(claims-none, can never FAIL)=7' in line[0]
       and '[11, 12, 13, 14, 15, 17, 26]' in line[0], line)

    # M1 集合漂移：从 LANDABLE 里删掉 26
    build_sandbox(new, drop_landable=[26])
    rc1, f1, so1 = run_gate()
    ck('M1 LANDABLE 删掉 26 ⇒ C11b 缺口漂移 FAIL',
       rc1 == 1 and [x for x in f1 if 'loadable gap drifted' in x],
       [x for x in f1 if 'C11b' in x][:2])

    # M2 第 7 列 11 改「有」⇒ 缺口 7->6
    build_sandbox(new, flip_to_you=[11])
    rc2, f2, so2 = run_gate()
    l2 = [l for l in so2.splitlines() if 'C11b loadable-registry' in l]
    ck('M2 id11 改「有」⇒ 缺口 7->6 且 FAIL',
       rc2 == 1 and [x for x in f2 if 'loadable gap drifted' in x]
       and 'gap(claims-none, can never FAIL)=6' in (l2[0] if l2 else ''),
       [x for x in f2 if 'C11b' in x][:2])

    # NC1 隔离力：找一个「只有 C11b 能抓」的变异 —— 改 C11_LANDABLE 集合本身。
    # R102 自错 5：初版拿「id11 改有」当 NC1 的变异，那本身就会触发 C11 的真判据
    # （id 11 没有合规自述行），所以未打补丁也 exit 1 ⇒ 该对照零信息（纪律 32 同型第三次）。
    # 正确变异：从 LANDABLE 里删一个 id —— 未打补丁的门禁根本不读这个集合，必然 exit 0。
    build_sandbox(src, drop_landable=[26])
    rc2b, f2b, _ = run_gate()
    ck('NC1 LANDABLE 删 26 + 未打补丁 ⇒ exit 0（该变异只有 C11b 能抓）',
       rc2b == 0 and not [x for x in f2b if 'C11b' in x], 'exit=%d fails=%s' % (rc2b, f2b[:3]))

    # NC2 与 C6MAX 互不干扰
    build_sandbox(new)
    rc3, f3, _ = run_gate('--c6max=3')
    ck('NC2 打补丁后 --c6max=3 仍只报 C6（C11b 不误报）',
       rc3 == 1 and all('loadable' not in x for x in f3), f3[:3])

    # POS2
    build_sandbox(new)
    rc4, f4, _ = run_gate()
    ck('POS2 还原后 exit 0', rc4 == 0, 'exit=%d' % rc4)

    if '--apply' in sys.argv and not any(not c['ok'] for c in checks):
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        bak = os.path.join(BASE, 'R102.before_check_disc_C11b_%s.bak' % stamp)
        fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as f:
            f.write(src)
        ck('K0 wx 独占备份',
           hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == hashlib.sha256(src).hexdigest(),
           os.path.basename(bak))
        io.open(GATE, 'wb').write(new)
        back = io.open(GATE, 'rb').read()
        ck('K1 回读逐字节相同', back == new, hashlib.sha256(back).hexdigest()[:16])
        p = subprocess.run([sys.executable, GATE], capture_output=True, text=True, cwd=REAL)
        ck('K2 真门禁 exit 0', p.returncode == 0, 'exit=%d' % p.returncode)
        ck('K3 真门禁输出含 C11b gap=7',
           'gap(claims-none, can never FAIL)=7' in p.stdout, '')
        print(p.stdout)
    elif '--apply' in sys.argv:
        print('REFUSE --apply: 控制组未全绿')
        return 1

    n_fail = sum(1 for c in checks if not c['ok'])
    json.dump({'n_checks': len(checks), 'n_fail': n_fail,
               'pin_gap_ids': PIN_GAP_IDS, 'pin_landable': PIN_LANDABLE,
               'checks': checks},
              io.open(os.path.join(OUT, 'r102e_landable.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))
    return 0 if n_fail == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
