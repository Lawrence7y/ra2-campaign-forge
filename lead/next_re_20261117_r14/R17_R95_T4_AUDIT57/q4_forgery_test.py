# -*- coding: utf-8 -*-
"""R17_R95_T4_AUDIT57 · Q4 第三种伪造路径实测（只读原则：临时改动 + 逐字节复原 + 验证）。

伪造路径 C（§2.58 的反控 A/B 都没测到）：
  让一个「非冻结、col7=无」的纪律（纪律 11）凭空多出一条自述行，并把 col7 从「无」改成「有」，
  看门禁是否会把它判成 ok（即：自述行能否被人事后伪造出来骗过 C11）。

严格复原：进入时对每个被改文件记 sha256 + 原始字节，finally 中用原始字节写回，再核 sha256。
本脚本本身写在 R17_R95_T4_AUDIT57\ 内（唯一允许的写目录）。
"""
import io
import os
import sys
import hashlib
import subprocess

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')
PROD = os.path.join(R14, '_r38', 'checkC3_report.md')
GATE = os.path.join(R14, 'check_disc.py')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'q4_forgery_output.txt')

def rb(p):
    with io.open(p, 'rb') as f:
        return f.read()

def wb(p, b):
    with io.open(p, 'wb') as f:
        f.write(b)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def run_gate(tag, lines):
    p = subprocess.run([sys.executable, GATE], cwd=R14,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode('utf-8', 'replace')
    lines.append('--- GATE %s exit=%d ---' % (tag, p.returncode))
    for l in out.splitlines():
        if ('C11' in l) or ('exit ' in l) or ('PASS ' in l) or ('FAIL ' in l):
            lines.append('  ' + l)
    return p.returncode

def main():
    lines = []
    backup = {}
    for p in (DR, PROD, GATE):
        backup[p] = rb(p)
        lines.append('BACKUP %s bytes=%d sha256=%s' %
                     (os.path.relpath(p, ROOT), len(backup[p]), sha(backup[p])))

    try:
        # 基线
        run_gate('BEFORE(基线)', lines)

        # 读 DISC_RECHECK.tsv，取纪律 11 的原行与 anchor4
        txt = backup[DR].decode('utf-8')
        raw_lines = txt.split('\n')
        idx = None
        for i, ln in enumerate(raw_lines):
            if ln.startswith('11\t'):
                idx = i
                break
        if idx is None:
            lines.append('ABORT: 找不到纪律 11 行')
            return 2
        row = raw_lines[idx].split('\t')
        anchor4 = row[3]  # 逐字，与 recheck_verify.R5 一致
        want_anchor = 'sha256:' + hashlib.sha256(anchor4.encode('utf-8')).hexdigest()
        lines.append('anchor4(repr)=%r' % anchor4)
        lines.append('fabricated anchors=%s' % want_anchor)

        # 构造一条「凭空伪造」的自述行：round/at 都是我挑的（落在 r55 窗口内），
        # conclusion=PASS，anchors 由公开可算的 row[3] 算出——无任何外部可信输入。
        fake = ('DISC_RECHECK discipline=11 round=R55 '
                'at=2026-11-22T17:35:00+08:00 anchors=%s conclusion=PASS' % want_anchor)
        lines.append('fabricated line = %s' % fake)

        # 改 1：把伪造行追加到纪律 11 的产物末尾
        prod_new = backup[PROD]
        if not prod_new.endswith(b'\n'):
            prod_new += b'\n'
        prod_new += fake.encode('utf-8') + b'\n'
        wb(PROD, prod_new)
        lines.append('MODIFY product: bytes %d -> %d (+%d)' %
                     (len(backup[PROD]), len(prod_new), len(prod_new) - len(backup[PROD])))

        # 改 2：把 col7 从「无（仅立条当轮自带）」改成「有（后续轮回跑）」
        row[6] = '\u6709\uff08\u540e\u7eed\u56de\u8f6e\u56de\u8dd1\uff09'
        raw_lines[idx] = '\t'.join(row)
        wb(DR, '\n'.join(raw_lines).encode('utf-8'))
        lines.append('MODIFY DISC_RECHECK.tsv row 11 col7 -> %s' % row[6])

        # 实测：不改 check_disc.py、不改 FREEZE_SHA256、不改 ROUND_WINDOWS、不动冻结档
        rc = run_gate('AFTER-伪造C', lines)
        lines.append('VERDICT: exit=%d ; %s' %
                     (rc, '门禁仍绿，伪造未被抓' if rc == 0 else '门禁变红，伪造被抓'))
    finally:
        # 复原
        for p, b in backup.items():
            wb(p, b)
        lines.append('--- RESTORE 验证 ---')
        allok = True
        for p, b in backup.items():
            now = rb(p)
            ok = (now == b)
            allok = allok and ok
            lines.append('RESTORE %s identical=%s sha256=%s' %
                         (os.path.relpath(p, ROOT), ok, sha(now)))
        lines.append('RESTORE ALL_OK=%s' % allok)
        run_gate('AFTER-复原', lines)

    with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return 0

if __name__ == '__main__':
    sys.exit(main())
