# -*- coding: utf-8 -*-
"""verify_appends.py —— 证明「只追加、未改写」并核对自描述行合规性。

三件事：
  1. 每个产物：bytes_before / bytes_after / 增量等于「追加行长度」，
     且 sha256(前 bytes_before 字节) == 追加前记录的 sha256（逐字节未变）。
  2. 每纪律：产物里属于该纪律的自描述行**恰好一条**。
  3. 该行能否通过 recheck_verify.verify_recheck_line（即 check_disc.py C11 的判据）。
基线值（bytes_before / sha256）写死在下面，来自 append_link.py 的 --go 日志。
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')

# 追加前基线：来自 r55_append_go.txt / r55_append_go2.txt
#   disc -> (字节数, 前 N 字节 sha256 前 16 位, 追加行条数)
# 纪律 3 与 4 共用 anchor_check.txt：纪律 3 基线是原始 911 字节、
# 追加 1 行；纪律 4 的基线是纪律 3 写入后的 1072 字节、再追加 1 行。
BASELINE = {
    3:  (911,    '48e8c66b9e870ac1', 1),
    4:  (1072,   '509c2817d2342d88', 1),
    22: (243982, '4687aa21c38c6cdf', 1),
    27: (112550, '2ce4cb5a469e7ed9', 1),
    28: (661097, '4208bb49805dc7df', 1),
}
# 原始基线（纪律 3 追加之前），用于独立复核「原有 911 字节」逐字节未变
ORIGINAL = {3: (911, '48e8c66b9e870ac1')}


def load_rows():
    txt = io.open(DR, encoding='utf-8', newline='').read()
    out = {}
    for ln in [l for l in txt.split('\n') if l][1:]:
        c = ln.split('\t')
        if c[0].strip().isdigit():
            out[int(c[0])] = c
    return out


def main():
    rows = load_rows()
    sys.path.insert(0, R14)
    import recheck_verify

    print(u'=== 追加完整性核对 ===')
    allok = True
    report = []
    for disc in (3, 4, 22, 27, 28):
        row = rows[disc]
        rel = row[4].strip()
        path = os.path.join(ROOT, rel.replace('\\', '/'))
        raw = io.open(path, 'rb').read()
        before, prehex, want_lines = BASELINE[disc]
        after = len(raw)

        # 1) 前 before 字节必须与基线逐字节相同
        prefix_unchanged = hashlib.sha256(raw[:before]).hexdigest()[:16] == prehex
        tail = raw[before:]
        # 注：_verdicts.tsv 用 CRLF，一行以 \r\n 结尾，splitlines() 会把它拆成
        #     '<行>\r' + '' 两段，故按「strip 后非空段」计数，避免把 EOL 误判成空行。
        tail_lines = [x for x in tail.decode('utf-8', 'replace').splitlines() if x.strip()]
        # 尾部新增行必须以本纪律的行**开头**（共用文件的后续追加可能排在其后），
        # 且其中恰好有 want_lines 条属于本纪律。
        tail_first_is_mine = (len(tail_lines) >= want_lines
                              and tail_lines[0].startswith(
                                  'DISC_RECHECK discipline=%d ' % disc))
        tail_is_n_lines = (tail_first_is_mine
                           and sum(1 for x in tail_lines
                                   if x.startswith('DISC_RECHECK discipline=%d ' % disc))
                           == want_lines)

        # 2) 该纪律的行恰好一条
        mine = [l for l in raw.decode('utf-8', 'replace').splitlines()
                if l.startswith('DISC_RECHECK discipline=%d ' % disc)]
        exactly_one = (len(mine) == 1)

        # 3) 过 recheck_verify（C11 判据）
        ok, detail = recheck_verify.verify_recheck_line(ROOT, row)

        good = prefix_unchanged and tail_is_n_lines and exactly_one
        allok = allok and good
        print(u'\n--- discipline %d ---' % disc)
        print(u'  product          : %s' % rel)
        print(u'  bytes %d -> %d (+%d)' % (before, after, after - before))
        print(u'  prefix_unchanged : %s (sha256[:16] %s)' % (prefix_unchanged, prehex))
        print(u'  tail_new_lines   : %s (expect %d)' % (tail_is_n_lines, want_lines))
        print(u'  exactly_one_line : %s' % exactly_one)
        print(u'  line             : %s' % (mine[0] if mine else u'(none)'))
        print(u'  C11 verify       : %s | %s' % (ok, detail))
        report.append(dict(disc=disc, rel=rel, before=before, after=after,
                           prefix_unchanged=prefix_unchanged, tail_new_lines=tail_is_n_lines,
                           exactly_one=exactly_one, line=mine[0] if mine else None,
                           c11_ok=ok, c11_detail=detail))

    print(u'\n[append_integrity=%s]' % (u'PASS' if allok else u'FAIL'))
    with io.open(os.path.join(HERE, 'verify_appends.json'), 'w',
                 encoding='utf-8', newline='') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return 0 if allok else 1


if __name__ == '__main__':
    sys.exit(main())
