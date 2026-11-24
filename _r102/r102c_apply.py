#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102c_apply.py —— 把 r102b 已验证的加严**字节级**落到真门禁（写入纪律全流程）

为什么必须字节级：check_disc.py 是 CRLF 主文件（实测 CRLF 321 / LF-only 2 / 14,896 B）。
若用文本读写补丁，几千行会静默统一成 LF —— 那是无声改写，不是我要的改动。
故本脚本全程 bytes：定位锚、插入 CRLF 行、回读再核。

加严内容（语义已由 r102b_harden.py 的 17 项控制组证明，本脚本不重复证明，只负责落地）：
  H1 新增 C12：冻结档 12 行第 4 列校验式**真跑** + 冻结⊆claims-有 + 理由非空 + 时刻严格 ISO8601
  H2 C6MAX 接线（此前是死旋钮：解析了但 load 次数 0）
  H3 GATE_VER R87 -> R102，**并同步** DISC_RECHECK.tsv 第 20 行校验式里的字面版本号
     （三重钉：模块常量 / C7 真跑的该行校验式 / C10 自检；漏改第 20 行则 POS 立刻 FAIL，
      这一点是 r102b 的反控抓出来的，记作 R102 自错 3）

写入纪律：
  1. R17_LEAD_BASELINE/ 下 wx 独占创建唯一备份
  2. 断言旧 sha256 与 CR 计数
  3. 一次性写入
  4. 回读核对 sha256 / CR 计数 / 门禁 exit 0
"""
import hashlib, io, json, os, subprocess, sys, datetime

REAL = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
GATE = os.path.join(REAL, R14REL, 'check_disc.py')
DR = os.path.join(REAL, R14REL, 'DISC_RECHECK.tsv')
BASE = os.path.join(REAL, R14REL, 'R17_LEAD_BASELINE')
OUT = os.path.join(REAL, '_r102')

EXPECT_GATE_SHA = '4bc4ef58c5f24fab00b61c374195e5ce64e5b8b2ea5a962dd67d1b11bf2c28ee'
EXPECT_GATE_CRLF, EXPECT_GATE_LFONLY = 321, 2
EXPECT_DR_SHA = 'ededf577b34ab4d004c460b52653c3c3b1a5ccbba3626e82c1b2efb66e9ea9c0'
EXPECT_DR_CRLF = 0

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

C12 = '''# ---- C12 【R102 新增】冻结档自身可核性：12 行「结构性不可验证」不是免检牌 ----
# R102 实测（_r102/r102a_holes.json）：C11 的 31 行里 26 行不可 FAIL，其中 12 行走冻结档。
# 冻结档一旦被读成「免检名单」，本门禁对它们就只剩 sha256 一个约束 —— 而 sha 是同一代码库
# 里的常量，改锚 + 同步改常量即可无声通过（r102b NC1 实测：坏锚 + 同步 sha，未打补丁的
# 门禁 exit 0）。故 C12 把冻结档第 4 列校验式**真跑一遍**：冻结只豁免「自产出 DISC_RECHECK
# 行」，不豁免「它引用的锚真的存在且可命中」。
c12 = 0
if os.path.exists(_FREEZE):
    _fbody = [x.split('\\t') for x in _frows[1:]]
    _claim_ids = set()
    for _r in rows:
        if len(_r) == 7 and _r[6].strip().startswith('\\u6709') and _r[0].strip().isdigit():
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
        if _id not in _claim_ids:
            fails.append('%s frozen but not claims-\\u6709 in DISC_RECHECK (freeze != escape hatch)'
                         % _fid)
        if not _p or _e in ('', 'none'):
            fails.append('%s frozen row has empty product/expr' % _fid)
        else:
            _ok, _det = run_expr(_p, _e)
            if _ok is not True:
                fails.append('%s frozen anchor does not hold (%s) :: %s' % (_fid, _det, _e[:40]))
            else:
                c12 += 1
        if not _why:
            fails.append('%s frozen reason empty' % _fid)
        if not re.fullmatch(r'\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}[+-]\\d{2}:\\d{2}', _at):
            fails.append('%s frozen timestamp not strict ISO8601(+HH:MM): %r' % (_fid, _at))
notes.append('C12 frozen-anchor live-check: %d frozen rows, %d anchors hit' % (len(_fbody), c12))

'''

C6_PATCH_OLD = (b"notes.append('C6 cross-namespace refs (compound-aware, outside 2.14+) = %d' % cross)\r\n")
C6_PATCH_NEW = (
    b"notes.append('C6 cross-namespace refs (compound-aware, outside 2.14+) = %d' % cross)\r\n"
    b"# ---- C6 \xe9\x98\x88\xe5\x80\xbc\xef\xbc\x88R102 \xe6\x8e\xa5\xe7\xba\xbf\xef\xbc\x89"
    b"\xef\xbc\x9adocstring \xe4\xb8\x80\xe7\x9b\xb4\xe5\xa3\xb0\xe7\xa7\xb0\xe3\x80\x8c"
    b"\xe8\xb6\x85\xe9\x98\x88\xe5\x80\xbc\xe5\x8d\xb3 FAIL\xe3\x80\x8d\xef\xbc\x8c"
    b"\xe8\x80\x8c C6MAX \xe6\xad\xa4\xe5\x89\x8d\xe4\xbb\x8e\xe6\x9c\xaa\xe8\xa2\xab\xe8\xaf\xbb"
    b"\xef\xbc\x88AST \xe5\xae\x9e\xe6\xb5\x8b Load=0\xef\xbc\x89\xe3\x80\x82 ----\r\n"
    b"if cross > C6MAX:\r\n"
    b"    fails.append('C6 cross-namespace refs %d > threshold %d (--c6max= to raise deliberately)'\r\n"
    b"                 % (cross, C6MAX))\r\n"
    b"else:\r\n"
    b"    notes.append('C6 threshold ok: %d <= %d' % (cross, C6MAX))\r\n"
)


def crlf_count(b):
    return b.count(b'\r\n'), b.count(b'\n') - b.count(b'\r\n')


def patch_gate_bytes(src):
    """字节级三处补丁。每处断言锚唯一，否则立即中止（不猜）。"""
    # ① GATE_VER
    old_ver = b"GATE_VER = 'R87'\r\n"
    assert src.count(old_ver) == 1, 'GATE_VER anchor count=%d' % src.count(old_ver)
    s = src.replace(old_ver, b"GATE_VER = 'R102'\r\n")
    # ② C6 阈值
    assert s.count(C6_PATCH_OLD) == 1, 'C6 anchor count=%d' % s.count(C6_PATCH_OLD)
    s = s.replace(C6_PATCH_OLD, C6_PATCH_NEW)
    # ③ C12 块，插在 C5 之前
    anchor = b"# ---- C5 CR \xe6\x8a\xbd\xe6\x9f\xa5 ----\r\n"
    assert s.count(anchor) == 1, 'C5 anchor count=%d' % s.count(anchor)
    block = C12.replace('\n', '\r\n').encode('utf-8')
    s = s.replace(anchor, block + anchor)
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    gate_b = io.open(GATE, 'rb').read()
    dr_b = io.open(DR, 'rb').read()

    # ---------- 前提断言 ----------
    ck('A0 门禁旧 sha256 与登记一致',
       hashlib.sha256(gate_b).hexdigest() == EXPECT_GATE_SHA, hashlib.sha256(gate_b).hexdigest()[:16])
    g_crlf, g_lf = crlf_count(gate_b)
    ck('A1 门禁 CRLF/LF-only 与登记一致', (g_crlf, g_lf) == (EXPECT_GATE_CRLF, EXPECT_GATE_LFONLY),
       'CRLF=%d LFonly=%d' % (g_crlf, g_lf))
    ck('A2 DISC_RECHECK 旧 sha256 与登记一致',
       hashlib.sha256(dr_b).hexdigest() == EXPECT_DR_SHA, hashlib.sha256(dr_b).hexdigest()[:16])
    d_crlf, d_lf = crlf_count(dr_b)
    ck('A3 DISC_RECHECK 全 LF', d_crlf == EXPECT_DR_CRLF, 'CRLF=%d LFonly=%d' % (d_crlf, d_lf))

    # ---------- 生成新内容 ----------
    new_gate = patch_gate_bytes(gate_b)
    n_crlf, n_lf = crlf_count(new_gate)
    ck('B0 补丁后仍全 CRLF（新增行也是 CRLF）', n_lf == EXPECT_GATE_LFONLY,
       'CRLF=%d LFonly=%d delta_bytes=%+d' % (n_crlf, n_lf, len(new_gate) - len(gate_b)))
    ck('B1 补丁后语法可编译', (compile(new_gate.decode('utf-8'), 'g', 'exec') or True), '')
    ck('B2 GATE_VER 已是 R102', b"GATE_VER = 'R102'\r\n" in new_gate)
    ck('B3 C12 块只插一次', new_gate.count(b'# ---- C12 ') == 1)
    ck('B4 C6 阈值只插一次', new_gate.count(b'if cross > C6MAX:') == 1)
    ck('B5 未触碰 FREEZE_SHA256', b"FREEZE_SHA256 = '0ffeeff5" in new_gate)

    # DISC_RECHECK 第 20 行：字面版本号同步
    dr_txt = dr_b.decode('utf-8')
    rows = [l.split('\t') for l in dr_txt.split('\n') if l]
    hit = [(i, r) for i, r in enumerate(rows) if len(r) == 7 and 'check_disc.py' in r[4]]
    ck('C0 恰有一行指向 check_disc.py', len(hit) == 1, [(i, r[0]) for i, r in hit])
    idx, row = hit[0]
    old_expr = row[5]
    ck('C1 该行校验式含字面 R87', "GATE_VER = 'R87'" in old_expr, old_expr[:60])
    row[5] = old_expr.replace("GATE_VER = 'R87'", "GATE_VER = 'R102'")
    new_dr = ('\n'.join('\t'.join(r) for r in rows)).encode('utf-8')
    if dr_b.endswith(b'\n'):
        new_dr += b'\n'
    ck('C2 新 DISC_RECHECK 仍全 LF', crlf_count(new_dr)[0] == 0, crlf_count(new_dr))
    ck('C3 只有那一格变化（其余字节全同）',
       new_dr.replace(b"GATE_VER = 'R102'", b"GATE_VER = 'R87'") == dr_b,
       '%d -> %d B' % (len(dr_b), len(new_dr)))

    if '--apply' not in sys.argv:
        print('DRY RUN（未加 --apply）：以上为落地前前提断言')
        json.dump({'stage': 'dry', 'n_checks': len(checks),
                   'n_fail': sum(1 for c in checks if not c['ok']), 'checks': checks},
                  io.open(os.path.join(OUT, 'r102c_apply.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        return 0 if not any(not c['ok'] for c in checks) else 1

    if any(not c['ok'] for c in checks):
        print('REFUSE --apply: 前提断言未全绿')
        return 1

    # ---------- 备份（wx 独占） ----------
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bak_g = os.path.join(BASE, 'R102.before_check_disc_C12_%s.bak' % stamp)
    bak_d = os.path.join(BASE, 'R102.before_DISC_RECHECK_ver_bump_%s.bak' % stamp)
    for bak, blob in ((bak_g, gate_b), (bak_d, dr_b)):
        fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as f:
            f.write(blob)
        ck('D0 wx 独占备份 %s' % os.path.basename(bak),
           hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == hashlib.sha256(blob).hexdigest(),
           '%d B' % len(blob))

    # ---------- 一次性写入 + 回读 ----------
    io.open(GATE, 'wb').write(new_gate)
    io.open(DR, 'wb').write(new_dr)
    back_g = io.open(GATE, 'rb').read()
    back_d = io.open(DR, 'rb').read()
    ck('E0 门禁回读逐字节相同', back_g == new_gate, hashlib.sha256(back_g).hexdigest()[:16])
    ck('E1 DISC_RECHECK 回读逐字节相同', back_d == new_dr, hashlib.sha256(back_d).hexdigest()[:16])
    ck('E2 门禁回读 CRLF/LF-only 不变', crlf_count(back_g) == (n_crlf, n_lf), crlf_count(back_g))

    # ---------- 真跑门禁 ----------
    p = subprocess.run([sys.executable, GATE], capture_output=True, text=True, cwd=REAL)
    ck('F0 真门禁改后 exit 0', p.returncode == 0, p.stdout.strip().splitlines()[-3:])
    ck('F1 输出含 C12 12 行 12 命中',
       'C12 frozen-anchor live-check: 12 frozen rows, 12 anchors hit' in p.stdout, '')
    ck('F2 输出含 C6 阈值 9 <= 120', 'C6 threshold ok: 9 <= 120' in p.stdout, '')
    ck('F3 输出含 C10 self-check: ok(R102)', 'C10 self-check: ok(R102)' in p.stdout, '')
    # 反控：抬阈值参数必须真的能翻红
    p2 = subprocess.run([sys.executable, GATE, '--c6max=3'], capture_output=True, text=True, cwd=REAL)
    ck('F4 反控 --c6max=3 ⇒ exit 1 且报 C6 阈值', p2.returncode == 1 and 'C6 cross-namespace refs 9 > threshold 3' in p2.stdout,
       'exit=%d' % p2.returncode)
    p3 = subprocess.run([sys.executable, GATE], capture_output=True, text=True, cwd=REAL)
    ck('F5 复跑一次仍 exit 0（无状态残留）', p3.returncode == 0, 'exit=%d' % p3.returncode)

    n_fail = sum(1 for c in checks if not c['ok'])
    json.dump({'stage': 'applied', 'n_checks': len(checks), 'n_fail': n_fail,
               'gate_sha_before': EXPECT_GATE_SHA,
               'gate_sha_after': hashlib.sha256(back_g).hexdigest(),
               'dr_sha_before': EXPECT_DR_SHA,
               'dr_sha_after': hashlib.sha256(back_d).hexdigest(),
               'backups': [bak_g, bak_d], 'checks': checks},
              io.open(os.path.join(OUT, 'r102c_apply.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(p.stdout)
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
