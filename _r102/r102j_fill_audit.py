#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102j_fill_audit.py —— 把审计员失败的如实登记回填到三件已写段落的占位符处

背景：write_r102.py 写入时审计员尚未返回，三件里留了占位符 __AUDIT_156__
（在 LEAD_LOCK / STATUS_BOARD 的文本里已替换成「本轮审计员未在预算内产出，见下轮」）。
现在实测：deepseek #156 = failed / error_max_turns / 61 回合 / 15.83 分钟 vs 预算 12
⇒ [OVERTIME]，且盘上**零产物**。

本脚本只做窄事：在这三件里把那段占位文本替换成如实登记，且：
  * 不新增/删除任何行（只改一行内的文字），故 CR 计数天然不变（仍断言）
  * 替换文本内无反引号
  * 逐件给「段前逐字节不变」与「替换次数恰 1」的双向证据
"""
import datetime, hashlib, io, json, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r102')
STAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

OLD = '（本轮审计员未在预算内产出，见下轮）'
NEW = ('failed / error_max_turns / 61 回合，实测 15.83 分钟 vs 预算 12 分钟 ⇒ [OVERTIME] 如实记；'
       '结果为空、**盘上零产物** ⇒ 本轮无跨家族审计结论可用，ED2..ED5 只有主会话自测 + '
       '同家族执行员 hy4 #157 一层独立复现')

TARGETS = [
    (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137, 'LEAD_LOCK'),
    (os.path.join(R14, 'STATUS_BOARD.md'), 0, 'STATUS_BOARD'),
    (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337, 'LEDGER'),
    (os.path.join(R14, 'R14_COMMON.md'), 1081, 'R14_COMMON'),
]

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

def main():
    os.makedirs(OUT, exist_ok=True)
    ck('N0 替换文本无反引号', '`' not in NEW and '`' not in OLD, (NEW.count('`'), OLD.count('`')))
    ck('N1 替换文本无换行（不改行数）', '\n' not in NEW and '\n' not in OLD, '')
    for path, cr, tag in TARGETS:
        raw = io.open(path, 'rb').read()
        txt = raw.decode('utf-8')
        if OLD not in txt:
            ck('%s 无占位符（可能已在别处登记）' % tag, True, 'skip')
            continue
        ck('%s 占位符恰 1 次' % tag, txt.count(OLD) == 1, txt.count(OLD))
        ck('%s 现状 CR = %d' % (tag, cr), raw.count(b'\r\n') == cr, raw.count(b'\r\n'))
        new_txt = txt.replace(OLD, NEW)
        new_raw = new_txt.encode('utf-8')
        ck('%s 行数不变（只改行内文字）' % tag, new_raw.count(b'\n') == raw.count(b'\n'),
           (raw.count(b'\n'), new_raw.count(b'\n')))
        ck('%s CR 计数仍 = %d' % (tag, cr), new_raw.count(b'\r\n') == cr, new_raw.count(b'\r\n'))
        # 段前不变
        i = txt.index(OLD)
        ck('%s 替换点之前逐字节不变' % tag, new_txt.startswith(txt[:i]), '')
        ck('%s 替换后段内无反引号' % tag,
           '`' not in new_txt[i:], new_txt[i:].count('`'))
        if '--apply' not in sys.argv:
            continue
        bak = os.path.join(BASE, 'R102.before_auditnote_%s_%s.bak' % (tag, STAMP))
        fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as f:
            f.write(raw)
        ck('%s wx 独占备份' % tag,
           hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest(),
           os.path.basename(bak))
        io.open(path, 'wb').write(new_raw)
        back = io.open(path, 'rb').read()
        ck('%s 回读逐字节相同' % tag, back == new_raw, hashlib.sha256(back).hexdigest()[:16])
        ck('%s 回读 CR 仍 = %d' % (tag, cr), back.count(b'\r\n') == cr, back.count(b'\r\n'))
    if '--apply' in sys.argv:
        p = subprocess.run([sys.executable, os.path.join(R14, 'check_disc.py')],
                           capture_output=True, text=True, cwd=ROOT)
        ck('Q0 门禁 exit 0', p.returncode == 0, 'exit=%d' % p.returncode)
        if p.returncode:
            print(p.stdout[-1200:])
    n_fail = sum(1 for c in checks if not c['ok'])
    if '--apply' in sys.argv:
        json.dump({'n_checks': len(checks), 'n_fail': n_fail, 'checks': checks},
                  io.open(os.path.join(OUT, 'r102j_fill_audit.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))
    return 0 if n_fail == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
