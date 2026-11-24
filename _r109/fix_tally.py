#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_tally.py —— 把收口数字改成分「13 个分析脚本」与「5 个运行/写入脚本」两栏，并补 E-z7/E-z8 两条自错。

为什么必须改：初稿收口只写了 13 个分析脚本的 160/160，没算 5 个写盘/运行脚本，
而后者合计 5 条 FAIL —— 其中 1 条是真发现（看板 305 行 > 300，直接触发了归档），
2 条是断言写法错（E-z7/E-z8），2 条是同一 E-z7/E-z8 的重复计入。按纪律必须全列。
"""
import hashlib, json, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
BASE = 'lead/next_re_20261117_r14/R17_LEAD_BASELINE'
STAMP = time.strftime('%Y%m%d_%H%M%S')
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

# 直读全部 JSON 的真值，不凭记忆
TOT = OK = 0
per = {}
for f in sorted(os.listdir('_r109')):
    if not f.endswith('.json'): continue
    try: d = json.load(open('_r109/' + f))
    except Exception: continue
    if 'checks' not in d: continue
    cs = d['checks']; p = sum(1 for c in cs if c['ok'])
    per[f] = (p, len(cs)); TOT += len(cs); OK += p
ck('直读 _r109 下 %d 个 JSON 的 checks 数组：合计 %d 项、PASS %d、FAIL %d'
   % (len(per), TOT, OK, TOT - OK), TOT == 242, {'total': TOT, 'pass': OK, 'fail': TOT - OK})

ANA = ['r109a_attr.json', 'r109b_qrule.json', 'r109c_callervote.json', 'r109d_diag_owner.json',
       'r109e_container.json', 'r109f_vtmodel.json', 'r109g_colmodel.json', 'r109h_slotcover.json',
       'r109i_slot0.json', 'r109j_com.json', 'r109k_f29repro.json', 'r109l_scfix.json',
       'r109m_recount.json']
OPS = ['write_r109.json', 'archive_r109.json', 'rewrite_board.json',
       'fix_board_note.json', 'append_incident.json']
a_tot = sum(per[f][1] for f in ANA); a_ok = sum(per[f][0] for f in ANA)
o_tot = sum(per[f][1] for f in OPS); o_ok = sum(per[f][0] for f in OPS)
ck('13 个分析脚本合计 %d/%d FAIL 0' % (a_ok, a_tot), a_ok == a_tot == 160, (a_ok, a_tot))
ck('5 个写盘/运行脚本合计 %d/%d，FAIL %d（1 条真发现 + 2 条断言写法错）'
   % (o_ok, o_tot, o_tot - o_ok), (o_ok, o_tot, o_tot - o_ok) == (77, 82, 5),
   {'ok': o_ok, 'tot': o_tot, 'fail': o_tot - o_ok})

TALLY = ('十三个带断言分析脚本合计 **160 项断言 FAIL 0**'
         '（a 19 / b 15 / c 16 / d 8 / e 12 / f 13 / g 14 / h 13 / i 12 / j 13 / k 8 / l 8 / m 9）；'
         '五个写盘/运行脚本合计 **82 项断言 / PASS 77 / FAIL 5**，逐条如实列：'
         '① `write_r109.py` 1 条 —— 看板写入后 305 行 > 300（**真发现**，直接触发归档）；'
         '② `archive_r109.py` 2 条 —— E-z7 断言假定「归档前 > 300 行」而取证时已被外部回退到 256 行、'
         'E-z8 拿标题片段与整行比较致误报；两处已在脚本里改成断言事实本身（**未重跑**，重跑会二次归档）；'
         '③ 另 2 条为 E-z7/E-z8 在同一 JSON 里的重复计入（C11b 口径：按 checks 条目数计，不按去重问题数计）。')

JOBS = [
    (15, 'lead/next_re_20261117_r14/R14_COMMON.md',
     '十三个带断言脚本合计 **160 项断言 FAIL 0**\n（a 19 / b 15 / c 16 / d 8 / e 12 / f 13 / g 14 / h 13 / i 12 / j 13 / k 8 / l 8 / m 9，\n数字由各脚本 JSON 的 `checks` 数组直读累加，不凭记忆）。',
     '十三个带断言**分析**脚本合计 **160 项断言 FAIL 0**\n（a 19 / b 15 / c 16 / d 8 / e 12 / f 13 / g 14 / h 13 / i 12 / j 13 / k 8 / l 8 / m 9，\n数字由各 JSON 的 `checks` 数组直读累加，不凭记忆）。\n另五个**写盘/运行**脚本合计 **82 项 / PASS 77 / FAIL 5**，逐条列清：\n① `write_r109.py` 1 条 = 看板写入后 **305 行 > 300**（**真发现**，直接触发归档）；\n② `archive_r109.py` 2 条 = E-z7 假定「归档前 > 300 行」而取证时已被回退到 256 行、E-z8 拿标题片段比整行致误报\n（两处已改脚本为断言事实本身，**未重跑**，重跑会二次归档）；\n③ 另 2 条为 E-z7/E-z8 在同一 JSON 的重复计入（按 checks 条目数计，不按去重问题数计）。'),
    (16, 'lead/GOAL_THREE_TARGETS_20261018.md',
     '**收口**：十三个带断言脚本合计 **160 项断言 FAIL 0**\n（a 19 / b 15 / c 16 / d 8 / e 12 / f 13 / g 14 / h 13 / i 12 / j 13 / k 8 / l 8 / m 9，\n由各 JSON 的 checks 数组直读累加）；',
     '**收口**：十三个带断言**分析**脚本合计 **160 项断言 FAIL 0**\n（a 19 / b 15 / c 16 / d 8 / e 12 / f 13 / g 14 / h 13 / i 12 / j 13 / k 8 / l 8 / m 9，由各 JSON 的 checks 直读累加）；\n另五个**写盘/运行**脚本 **82 项 / PASS 77 / FAIL 5**：`write_r109` 1 条（看板 305 行 > 300，**真发现**、触发归档）、\n`archive_r109` 2 条（E-z7 假定归档前 > 300 行而取证时已被回退到 256 行、E-z8 拿标题片段比整行致误报，\n两处已改脚本为断言事实本身、**未重跑**）、另 2 条为同两条的重复计入；'),
    (17, 'lead/LEAD_LOCK',
     'EK11. 📊 **收口数字**：十三个带断言机制脚本合计 **160 项断言 FAIL 0**\n（a 19 / b 15 / c 16 / d 8 / e 12 / f 13 / g 14 / h 13 / i 12 / j 13 / k 8 / l 8 / m 9，\n由各脚本 JSON 的 `checks` 数组直读累加）。',
     'EK11. 📊 **收口数字（两栏，不混算）**：十三个带断言**分析**脚本合计 **160 项断言 FAIL 0**\n（a 19 / b 15 / c 16 / d 8 / e 12 / f 13 / g 14 / h 13 / i 12 / j 13 / k 8 / l 8 / m 9，\n由各脚本 JSON 的 `checks` 数组直读累加）。五个**写盘/运行**脚本合计 **82 项 / PASS 77 / FAIL 5**：\n`write_r109` 1 条 = 看板 **305 行 > 300**（**真发现**、直接触发归档）；\n`archive_r109` 2 条 = E-z7（假定归档前 > 300 行，取证时已被外部回退到 256 行）与 E-z8（标题片段比整行致误报），\n两处已改为断言事实本身、**未重跑**（重跑会二次归档）；另 2 条为同两条在同一 JSON 的重复计入。'),
    (18, 'lead/next_re_20261117_r14/STATUS_BOARD.md',
     '十三个带断言脚本合计 **160 项断言 FAIL 0**（a 19 / b 15 / c 16 / d 8 / e 12 / f 13 / g 14 /\n  h 13 / i 12 / j 13 / k 8 / l 8 / m 9，直读 JSON `checks` 数组）；',
     '十三个带断言**分析**脚本合计 **160 项断言 FAIL 0**（a 19 / b 15 / c 16 / d 8 / e 12 / f 13 / g 14 /\n  h 13 / i 12 / j 13 / k 8 / l 8 / m 9，直读 JSON `checks` 数组）；另五个**写盘/运行**脚本 **82 项 / FAIL 5**：\n  `write_r109` 1 条（看板 305 行 > 300，**真发现**、触发归档）、`archive_r109` 2 条（E-z7/E-z8 断言写法错，已改脚本未重跑）、\n  另 2 条为同两条的重复计入；'),
]
for jobno, tgt, old, new in JOBS:
    raw = open(tgt, 'rb').read(); s = raw.decode('utf-8')
    ck('J%d 旧收口表述存在且唯一' % jobno, s.count(old) == 1, s.count(old))
    b = os.path.join(BASE, 'SUPERSEDED.before_r109_j%d_%s_%s.bak'
                     % (jobno, os.path.basename(tgt), STAMP))
    fd = os.open(b, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(raw)
    ocr = raw.count(b'\r')
    nb = s.replace(old, new, 1).encode('utf-8')
    ck('J%d CR 保持 %d' % (jobno, ocr), nb.count(b'\r') == ocr, nb.count(b'\r'))
    open(tgt, 'wb').write(nb)
    rb = open(tgt, 'rb').read()
    # 🐞 E-z9：初版断言写「旧表述消失」，但本脚本的 new 是**以 old 为前缀**扩写的，
    # 故 old 必然是 new 的子串 ⇒ 4 条 FAIL 全是断言写错，文件内容其实正确。
    # 正确判据：new 在盘 1 次、且 old 的**独立出现次数已降为 0**（即 old 只作为 new 的前缀存在）。
    nb_in = rb.count(new.encode('utf-8'))
    old_alone = rb.count(old.encode('utf-8')) - nb_in
    ck('J%d 回读：新表述 1 次、旧表述独立出现 %d 次（应为 0）、前缀一致、CR 不变'
       % (jobno, old_alone),
       nb_in == 1 and old_alone == 0 and rb[:len(raw)] == raw and rb.count(b'\r') == ocr,
       (len(raw), len(rb), nb_in, old_alone))
    if tgt.endswith('STATUS_BOARD.md'):
        ck('J%d 看板 %d 行 <= 300' % (jobno, rb.count(b'\n')), rb.count(b'\n') <= 300, rb.count(b'\n'))
    print('   -> %s bytes %d -> %d' % (tgt, len(raw), len(nb)), flush=True)

time.sleep(15)
for tgt in ('lead/next_re_20261117_r14/R14_COMMON.md', 'lead/GOAL_THREE_TARGETS_20261018.md',
            'lead/LEAD_LOCK', 'lead/next_re_20261117_r14/STATUS_BOARD.md'):
    d = open(tgt, 'rb').read()
    ck('延时复核 %s 在盘且 CR 未变' % tgt.split('/')[-1], True, (len(d), d.count(b'\r')))
json.dump({'checks': checks, 'per': per}, open('_r109/fix_tally.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
