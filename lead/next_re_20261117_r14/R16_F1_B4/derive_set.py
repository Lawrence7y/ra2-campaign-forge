# -*- coding: utf-8 -*-
"""
R16_F1_B4 — 独立派生 F1 缺口集合（判据见卡面 §3 第一步）。

权威输入：R16_PROBE_4GAP/scan_F1_audit.tsv
背景报告：R16_PROBE_4GAP/REPORT.md

四条判据（卡面 §3）：
  1) same_source == no
  2) ring4_at 能解析出装表指令 mov <mem>, imm32 且 imm32 指向该行活表
     —— TSV 代理列：n_install_decoded >= 1（f_reason=audit_ring4_ctor_install）
  3) 装表点位于 entry 体外（装表点所在函数 != entry）
     —— TSV 代理列：n_install_outside_body >= 1
  4) 现盘 coverage.tsv grade==[已证] 且第 4 列不含 "④ 活表槽位见证"

按 entry 升序排序；B1=1..18, B2=19..36, B3=37..54, **B4=55..72**（本批）。
硬要求：B4 与 B1/B2/B3 的 entry 集合（各 fields.tsv 第 1 列）交集均为空。
只读：不写 coverage.tsv / 任何他人目录；只写本目录 derived_set.tsv + 控制台报告。
"""
import os
import sys
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
AUDIT = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
B1F = os.path.join(R14, 'R16_F1_B1', 'fields.tsv')
B2F = os.path.join(R14, 'R16_F1_B2', 'fields.tsv')
B3F = os.path.join(R14, 'R16_F1_B3', 'fields.tsv')
OUT = os.path.join(HERE, 'derived_set.tsv')

WITNESS = '④ 活表槽位见证'


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_cov():
    """entry -> (grade, sem4)。数据行 TAB 分隔 8 列；表头是逗号（已知坑，跳过）。"""
    d = {}
    with open(COV, 'rb') as f:
        raw = f.read()
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) != 8:
            continue
        e = c[0].decode('ascii', 'ignore').strip().upper()
        if not e:
            continue
        d.setdefault(e, (c[4].decode('utf-8', 'ignore'),
                         c[3].decode('utf-8', 'ignore')))
    return d


def load_batch_entries(path):
    out = set()
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    for ln in lines[1:]:
        if not ln.strip():
            continue
        e = ln.split('\t')[0].strip().upper()
        if e:
            out.add(e)
    return out


def main():
    cov_sha = sha256p(COV)
    cov_bytes = os.path.getsize(COV)
    cov = load_cov()

    with open(AUDIT, encoding='utf-8') as f:
        lines = f.read().splitlines()
    hdr = lines[0].split('\t')
    idx = {k: i for i, k in enumerate(hdr)}
    data = [ln.split('\t') for ln in lines[1:] if ln.strip()]
    print('audit data rows:', len(data))
    print('coverage.tsv sha256:', cov_sha, 'bytes:', cov_bytes)

    s0 = data
    s1 = [r for r in s0 if r[idx['same_source']] == 'no']
    s2 = [r for r in s1 if int(r[idx['n_install_decoded']]) >= 1]
    s3 = [r for r in s2 if int(r[idx['n_install_outside_body']]) >= 1]

    def cov_ok(r):
        e = r[idx['entry']].upper()
        g, sem = cov.get(e, (None, None))
        return (g == '[已证]') and (WITNESS not in sem)

    s4 = [r for r in s3 if cov_ok(r)]

    print('stage counts:')
    print('  S0 all F1 gap rows             :', len(s0))
    print('  S1 same_source==no             :', len(s1))
    print('  S2 +ring4 install decoded      :', len(s2))
    print('  S3 +install outside entry body :', len(s3))
    print('  S4 +coverage [已证] & no witness:', len(s4), '  <== clean-now count')
    dropped4 = [r[idx['entry']] for r in s3 if not cov_ok(r)]
    print('  dropped by criterion 4:', len(dropped4), dropped4[:20])

    # ---- 关键：S3（判据 1-3，来自稳定的 scan_F1_audit.tsv）才是分批用的权威 76 行集合 ----
    # 判据 4 是「已写过的不重做」过滤：本卡开工读数时它对 76 行剔除 0 行（见 REPORT）。
    # 期间发生并发并表（F1 B1 delta 写入 coverage.tsv），使现盘判据 4 现在剔除 B1 的 18 行。
    # 这不改变分批边界：B4=稳定 76 集合的第 55-72 行；B4 这 18 行在现盘仍 grade=[已证] 且无 witness。
    from collections import Counter
    print('  f_reason distribution in S3:', dict(Counter(r[idx['f_reason']] for r in s3)))
    print('  sem_unproved in S3:', dict(Counter(r[idx['sem_unproved']] for r in s3)))
    base = s3
    print('\n  [batch-defining base set = S3, criteria 1-3]:', len(base))
    print('  [criterion-4 clean-now subset]:', len(s4),
          '(delta = already-merged rows:', len(dropped4), ')')

    s4s = sorted(base, key=lambda r: int(r[idx['entry']], 16))
    ents = [r[idx['entry']].upper() for r in s4s]
    assert len(ents) == len(set(ents)), 'duplicate entry in derived set'
    # B4 的 18 行必须在现盘仍干净（grade=[已证] 且无 witness），否则脚本报警
    b4_check = [(r[idx['entry']].upper(), cov_ok(r)) for r in s4s[54:72]]
    print('  B4 rows clean on current disk:', sum(1 for _e, ok in b4_check if ok), '/', len(b4_check))

    b1_set = load_batch_entries(B1F)
    b2_set = load_batch_entries(B2F)
    b3_set = load_batch_entries(B3F)
    print('\nB1 fields entries:', len(b1_set))
    print('B2 fields entries:', len(b2_set))
    print('B3 fields entries:', len(b3_set))

    def tag(i):
        if i <= 18:
            return '<== B1'
        if i <= 36:
            return '<== B2'
        if i <= 54:
            return '<== B3'
        if i <= 72:
            return '<== B4 (this batch)'
        return ''

    print('\nsorted derived set entries (1..%d):' % len(ents))
    for i, r in enumerate(s4s, 1):
        print('%2d %s  %-5s %-52s %s' % (
            i, r[idx['entry']].upper(), r[idx['subsystem']],
            r[idx['name']][:52], tag(i)))

    b1_ents = ents[0:18]
    b2_ents = ents[18:36]
    b3_ents = ents[36:54]
    b4_ents = ents[54:72]
    print('\nB1(1-18) matches fields.tsv:', set(b1_ents) == b1_set)
    print('B2(19-36) matches fields.tsv:', set(b2_ents) == b2_set)
    print('B3(37-54) matches fields.tsv:', set(b3_ents) == b3_set)

    # 硬交集检查：B4 与 B1/B2/B3 的 fields entry 集合交集必须为空
    b4s = set(b4_ents)
    inter_b1 = sorted(b4s & b1_set)
    inter_b2 = sorted(b4s & b2_set)
    inter_b3 = sorted(b4s & b3_set)
    print('B4 ∩ B1(fields):', inter_b1)
    print('B4 ∩ B2(fields):', inter_b2)
    print('B4 ∩ B3(fields):', inter_b3)
    assert not inter_b1 and not inter_b2 and not inter_b3, 'B4 intersects B1/B2/B3!'
    assert b4s <= set(ents), 'B4 not subset of derived set'
    assert all(ok for _e, ok in b4_check), 'B4 rows not all clean on current disk!'

    print('\n=== BATCH-DEFINING BASE SET HIT COUNT:', len(ents), '(card transcribed 76) ===')
    print('B4 (rows 55-72) entries (%d):' % len(b4_ents))
    for i, e in enumerate(b4_ents, 55):
        r = next(x for x in s4s if x[idx['entry']].upper() == e)
        print('  %2d %s  %-5s %s' % (i, e, r[idx['subsystem']], r[idx['name']]))

    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('entry\tsubsystem\tname\taudit_dir\tring4_at\n')
        for r in s4s:
            f.write('\t'.join([r[idx['entry']].upper(), r[idx['subsystem']],
                               r[idx['name']], r[idx['audit_dir']],
                               r[idx['ring4_at']]]) + '\n')
    print('wrote', OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
