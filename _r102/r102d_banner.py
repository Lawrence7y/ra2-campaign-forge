#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102d_banner.py —— 修掉门禁自报版本横幅的「标签撒谎」（字节级，含写入纪律）

实测（R102）：GATE_VER 抬到 R102 后，横幅仍打印 --- check_disc.py (R49) ---，
因为它是**硬编码字符串字面**，与 GATE_VER 无关。这是本次加严里最容易漏的一处：
C10 自检比对的是 GATE_VER 常量、C7 比对的是 DISC_RECHECK 第 20 行字面，
而横幅谁都不管 —— 于是门禁会一边自报 R49、一边按 R102 的判据运行。

判据：横幅必须由 GATE_VER 派生，不得再出现第二处版本字面。
  正控：改后门禁输出必须含 '(R102)'，且不得再含 '(R49)'。
  反控：把 GATE_VER 临时改回 R87（沙箱）⇒ 横幅必须跟着变 R87 ⇒ 证明派生而非硬编码。

同 r102c：check_disc.py 是 CRLF 主文件，全程 bytes。
"""
import hashlib, io, json, os, re, shutil, subprocess, sys, datetime

REAL = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
GATE = os.path.join(REAL, R14REL, 'check_disc.py')
BASE = os.path.join(REAL, R14REL, 'R17_LEAD_BASELINE')
OUT = os.path.join(REAL, '_r102')

OLD = b"print('--- check_disc.py (R49) ---')"
NEW = b"print('--- check_disc.py (%s) ---' % GATE_VER)"
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

def main():
    os.makedirs(OUT, exist_ok=True)
    src = io.open(GATE, 'rb').read()
    sha = hashlib.sha256(src).hexdigest()
    ck('G0 门禁当前 sha256', True, sha[:16])
    n_old = src.count(OLD)
    ck('G1 硬编码横幅恰一处', n_old == 1, n_old)
    ck('G2 全文件中 R49 字面只出现在该横幅', src.count(b'(R49)') == 1, src.count(b'(R49)'))
    new = src.replace(OLD, NEW)
    ck('G3 补丁后无 (R49) 字面', new.count(b'(R49)') == 0)
    ck('G4 补丁后仍只有一个 GATE_VER 定义', new.count(b"GATE_VER = '") == 1)
    ck('G5 补丁后语法可编译', (compile(new.decode('utf-8'), 'g', 'exec') or True), '')
    ck('G6 补丁后 CRLF/LF-only 不变',
       (new.count(b'\r\n'), new.count(b'\n') - new.count(b'\r\n'))
       == (src.count(b'\r\n'), src.count(b'\n') - src.count(b'\r\n')),
       (new.count(b'\r\n'), new.count(b'\n') - new.count(b'\r\n')))

    if '--apply' not in sys.argv:
        print('DRY RUN（未加 --apply）')
        json.dump({'stage': 'dry', 'sha_before': sha,
                   'n_checks': len(checks), 'n_fail': sum(1 for c in checks if not c['ok']),
                   'checks': checks},
                  io.open(os.path.join(OUT, 'r102d_banner.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        return 0 if not any(not c['ok'] for c in checks) else 1

    if any(not c['ok'] for c in checks):
        print('REFUSE --apply')
        return 1

    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BASE, 'R102.before_check_disc_banner_%s.bak' % stamp)
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(src)
    ck('H0 wx 独占备份', hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == sha,
       os.path.basename(bak))
    io.open(GATE, 'wb').write(new)
    back = io.open(GATE, 'rb').read()
    ck('H1 回读逐字节相同', back == new, hashlib.sha256(back).hexdigest()[:16])

    p = subprocess.run([sys.executable, GATE], capture_output=True, text=True, cwd=REAL)
    ck('H2 真门禁 exit 0', p.returncode == 0, 'exit=%d' % p.returncode)
    ck('H3 横幅自报 (R102)', '--- check_disc.py (R102) ---' in p.stdout,
       [l for l in p.stdout.splitlines() if '--- check_disc' in l])
    ck('H4 输出不再含 (R49)', '(R49)' not in p.stdout, '')

    # 反控：沙箱里把 GATE_VER 改回 R87 ⇒ 横幅必须跟着变（证明派生）
    sbx = '/tmp/r102_banner_sbx'
    if os.path.isdir(sbx):
        shutil.rmtree(sbx)
    os.makedirs(sbx)
    for e in os.listdir(REAL):
        if e in ('lead', '_r102'):
            continue
        os.symlink(os.path.join(REAL, e), os.path.join(sbx, e))
    os.makedirs(os.path.join(sbx, 'lead'))
    for e in os.listdir(os.path.join(REAL, 'lead')):
        if e != 'next_re_20261117_r14':
            os.symlink(os.path.join(REAL, 'lead', e), os.path.join(sbx, 'lead', e))
    os.makedirs(os.path.join(sbx, R14REL))
    for e in os.listdir(os.path.join(REAL, R14REL)):
        s, d = os.path.join(REAL, R14REL, e), os.path.join(sbx, R14REL, e)
        if e in ('check_disc.py', 'DISC_RECHECK.tsv'):
            shutil.copy2(s, d)
        else:
            os.symlink(s, d)
    g2 = os.path.join(sbx, R14REL, 'check_disc.py')
    b2 = io.open(g2, 'rb').read().replace(b"GATE_VER = 'R102'", b"GATE_VER = 'R87'")
    io.open(g2, 'wb').write(b2)
    dr2 = os.path.join(sbx, R14REL, 'DISC_RECHECK.tsv')
    d2 = io.open(dr2, 'rb').read().replace(b"GATE_VER = 'R102'", b"GATE_VER = 'R87'")
    io.open(dr2, 'wb').write(d2)
    p2 = subprocess.run([sys.executable, g2], capture_output=True, text=True, cwd=sbx)
    ck('NC1 反控：沙箱 GATE_VER=R87 ⇒ 横幅自报 (R87)（派生而非硬编码）',
       '--- check_disc.py (R87) ---' in p2.stdout,
       [l for l in p2.stdout.splitlines() if '--- check_disc' in l])

    n_fail = sum(1 for c in checks if not c['ok'])
    json.dump({'stage': 'applied', 'sha_before': sha,
               'sha_after': hashlib.sha256(back).hexdigest(), 'backup': bak,
               'n_checks': len(checks), 'n_fail': n_fail, 'checks': checks},
              io.open(os.path.join(OUT, 'r102d_banner.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))
    return 0 if n_fail == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
