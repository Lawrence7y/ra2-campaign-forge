# -*- coding: utf-8 -*-
"""
R16_F1_B1 — 独立派生 F1 缺口成文集合（只读输入，只写本目录）。

输入（只读）：
  lead/next_re_20261117_r14/R16_PROBE_4GAP/scan_F1_audit.tsv
  lead/next_re_20261117_r14/COVERAGE/coverage.tsv
判据（照 R16-SLOTN-F1.md §3）：
  1. same_source == no
  2. ring4_at 解出装表指令 (n_install_decoded>0, imm32 指向本行活表 —— 由扫描列 n_install_decoded 给出)
  3. 装表点在 entry 体外 (n_install_outside_body > 0)
  4. coverage.tsv 中 grade == [已证] 且第 4 列尚不含 '④ 活表槽位见证'
  附加（同卡转述的「③ 全干净」）：sem_unproved == 0
输出：derived_set.tsv（命中行，entry 升序）；并打印命中数供与 76 对照。
"""
import os, sys, hashlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
SCAN = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
OUT = os.path.join(HERE, 'derived_set.tsv')


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    cov_sha = sha256p(COV)
    cov_bytes = os.path.getsize(COV)
    print('coverage.tsv sha256:', cov_sha, 'bytes:', cov_bytes)

    # --- 读 coverage：byte 级 entry -> 8 列 ---
    with open(COV, 'rb') as f:
        raw = f.read()
    cov = {}
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) == 8:
            try:
                e = c[0].decode('ascii').upper()
            except Exception:
                continue
            cov.setdefault(e, c)
    print('coverage data rows parsed:', len(cov))

    # --- 读 scan ---
    with open(SCAN, encoding='utf-8') as f:
        lines = f.read().splitlines()
    hdr = lines[0].split('\t')
    idx = {h: i for i, h in enumerate(hdr)}
    print('scan columns:', len(hdr))
    data = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        c = ln.split('\t')
        data.append(c)
    print('scan data rows:', len(data))

    # --- 判据 ---
    hit = []
    rej = {'same_source': 0, 'no_install_decoded': 0, 'no_install_outside': 0,
           'sem_unproved': 0, 'not_in_cov': 0, 'grade_not_proved': 0,
           'already_has_witness': 0}
    for c in data:
        e = c[idx['entry']].upper()
        reasons = []
        if c[idx['same_source']] != 'no':
            reasons.append('same_source')
        if int(c[idx['n_install_decoded']]) <= 0:
            reasons.append('no_install_decoded')
        if int(c[idx['n_install_outside_body']]) <= 0:
            reasons.append('no_install_outside')
        if int(c[idx['sem_unproved']]) != 0:
            reasons.append('sem_unproved')
        crow = cov.get(e)
        if crow is None:
            reasons.append('not_in_cov')
        else:
            grade = crow[4].decode('utf-8', 'replace')
            sem = crow[3].decode('utf-8', 'replace')
            if grade != '[已证]':
                reasons.append('grade_not_proved')
            if '④ 活表槽位见证' in sem:
                reasons.append('already_has_witness')
        if reasons:
            for r in reasons:
                rej[r] += 1
        else:
            hit.append(dict(entry=e, subsystem=c[idx['subsystem']],
                            name=c[idx['name']], audit_dir=c[idx['audit_dir']],
                            ring4_at=c[idx['ring4_at']]))

    # --- 排序、去重 ---
    hit.sort(key=lambda r: int(r['entry'], 16))
    print('\n=== 派生结果 ===')
    print('命中行数:', len(hit), '（卡面预期 76）')
    print('拒绝计次（每行可多项）:', rej)
    assert len(set(r['entry'] for r in hit)) == len(hit), 'duplicate entries in hit set'
    print('entry 全部唯一: True')

    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('entry\tsubsystem\tname\taudit_dir\tring4_at\n')
        for r in hit:
            f.write('%s\t%s\t%s\t%s\t%s\n' % (
                r['entry'], r['subsystem'], r['name'], r['audit_dir'], r['ring4_at']))
    print('wrote', OUT)

    # --- B1 = 第 1-18 行 ---
    b1 = hit[:18]
    print('\n=== B1 (第 1-18 行, entry 升序) ===')
    for i, r in enumerate(b1, 1):
        print('%2d %s %s  [%s]' % (i, r['entry'], r['name'], r['audit_dir']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
