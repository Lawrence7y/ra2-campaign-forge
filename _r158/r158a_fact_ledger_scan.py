#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158a — 两项机械取证（正反控自测）
A. 台账/四件套里「新增事实项」条目结构计数（两口径 E1 宽 / E2 严），
   取 R157 报的「32 条部分失联事实项」判据：谁按条目、谁按 section。
B. 「自指增长」指标在 R157 未测的三处（FACT_INDEX / R14_COMMON / LEAD_LOCK）
   是否有同类自指指标（F23 四计数 458/291/293/1,196 分口径 A / B）。
"""
import re, sys, json, csv, os

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, '..', 'lead', 'next_re_20261117_r14')   # lead/next_re_20261117_r14
LEAD = os.path.join(ROOT, '..', 'lead')                            # lead/
REPO = os.path.join(LEAD, '..')          # project root

FILES = {
    'R14_COMMON':   os.path.join(BASE, 'R14_COMMON.md'),
    'LEDGER':       os.path.join(LEAD, 'GOAL_THREE_TARGETS_20261018.md'),
    'LEAD_LOCK':    os.path.join(LEAD, 'LEAD_LOCK'),
    'BOARD':        os.path.join(BASE, 'STATUS_BOARD.md'),
    'BOARD_ARCHIVE': os.path.join(BASE, 'BOARD_ARCHIVE.md'),
    'FACT_INDEX':   os.path.join(BASE, 'R17_R114_FACTINDEX_V542', 'FACT_INDEX.tsv'),
}

R = []
def chk(name, cond, detail):
    R.append({'name': name, 'pass': bool(cond), 'detail': detail})
    print(('  PASS  ' if cond else '  FAIL  ') + name + ' :: ' + str(detail))

def load(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()

TXT = {k: load(v) for k, v in FILES.items()}
LINES = {k: v.split('\n') for k, v in TXT.items()}

# ---------------- A: 「新增事实项」条目计数（两口径） ----------------
E1 = re.compile(r'新增事实|新事实项|新失联|新增的失联|新增失联|新的失联')
# 严口径：同一 section 内同时出现 F\d\d + (新增|新发现|新进) + (失联|不可读|现不在盘|不在现盘)
FID = re.compile(r'\bF\d\d\b')
NEWW = re.compile(r'新增|新发现|新进|新判')
LOSTW = re.compile(r'失联|不可读|现不在盘|不在现盘|已失')

def sections(name):
    """按标题行切 section，返回 [(start_line_no, title, text)]"""
    out, cur, cur_t = [], None, None
    sep = '\t' if name == 'FACT_INDEX' else '\n'
    ls = LINES[name] if name != 'FACT_INDEX' else None
    if name == 'FACT_INDEX':
        # TSV：以行号当 section（一行一 fact）
        for i, ln in enumerate(LINES[name], 1):
            out.append((i, 'row%d' % i, ln))
        return out
    for i, ln in enumerate(ls, 1):
        if re.match(r'^#{2,3} ', ln):
            if cur is not None:
                out.append((cur, cur_t, '\n'.join(ls[cur-1:i-1])))
            cur, cur_t = i, ln.strip()
    if cur is not None:
        out.append((cur, cur_t, '\n'.join(ls[cur-1:])))
    return out

print('=== A. 新增事实项条目计数（两口径）===')
A = {}
for k in FILES:
    secs = sections(k)
    if k == 'FACT_INDEX':
        e1_rows = [s for s in secs if E1.search(s[2])]
        e2_rows = [s for s in secs if E1.search(s[2]) and FID.search(s[2])]
    else:
        e1_rows = [s for s in secs if E1.search(s[2])]
        e2_rows = [s for s in secs if FID.search(s[2]) and NEWW.search(s[2]) and LOSTW.search(s[2])]
    e1_line = sum(len(E1.findall(s[2])) for s in secs)
    A[k] = {'secs': len(secs), 'E1_sections': len(e1_rows), 'E1_line_hits': e1_line,
            'E2_sections': len(e2_rows),
            'E1_sec_titles': [s[1][:40] for s in e1_rows][:12],
            'E2_sec_titles': [s[1][:40] for s in e2_rows][:12]}
    print('  %-13s sections=%-5d E1_sections=%-3d E1_line_hits=%-4d E2_sections=%-3d'
          % (k, A[k]['secs'], A[k]['E1_sections'], A[k]['E1_line_hits'], A[k]['E2_sections']))

tot_E1 = sum(A[k]['E1_sections'] for k in FILES)
tot_E2 = sum(A[k]['E2_sections'] for k in FILES)
print('  TOTAL E1_sections=%d  E2_sections=%d' % (tot_E1, tot_E2))

# 正控：R157 正文确实报过「32 条部分失联事实项」⇒ 该串必须在盘上出现
pat32 = re.compile(r'32\s*条[^\n]{0,40}(部分失联|失联)')
hits32 = [(k, len(pat32.findall(TXT[k]))) for k in ('LEAD_LOCK', 'BOARD', 'BOARD_ARCHIVE', 'R14_COMMON')]
chk('A0 正控：「32 条…失联」串在四件套可寻', any(n for _, n in hits32), hits32)
# 负控：自造串必须 0
NEG = 'ZZZ_R158_NO_SUCH_FACT_ITEM_QQQ'
chk('A0b 负控：自造串全库 0 命中', all(NEG not in TXT[k] for k in FILES),
    {k: TXT[k].count(NEG) for k in FILES})
# E1 口径若把 section 当条目，其数不得等于 R157 报的 32（判据要写清是谁的口径）
chk('A1 E1(section 口径) 合计 != 32（说明 32 不是 section 口径）', tot_E1 != 32, {'E1': tot_E1})
chk('A2 E2(section 严口径) 合计 != 32', tot_E2 != 32, {'E2': tot_E2})
chk('A3 E1_line_hits 合计 >= E1_sections（每 section 至少 1 命中）',
    sum(A[k]['E1_line_hits'] for k in FILES) >= tot_E1,
    {'line_hits': sum(A[k]['E1_line_hits'] for k in FILES)})
# 反控：把 E1 正则换成自造正则，命中必须为 0
E1_NEG = re.compile(r'ZZZ_R158_NO_SUCH_FACT_ITEM_QQQ')
chk('A4 反控：E1 换自造正则合计 0', sum(len(E1_NEG.findall(TXT[k])) for k in FILES) == 0, 0)

# ---------------- B: F23 四计数的自指增长（三处未测文件） ----------------
print('\n=== B. F23 四计数 458/291/293/1,196 在各文件的行命中（口径 A / B / C）===')
# 口径定义**逐字照抄** R157 的 r157b（S-431：本脚本首版自造了「token 计数 == 4」，
# 那是另一把尺子；R157 的谓词是四个 token 的**合取**，不是计数和）。
def tok_lite(p):
    """口径 A：只禁 0-9A-Fa-f 邻近。"""
    return re.compile(r'(?<![0-9A-Fa-f])' + p + r'(?![0-9A-Fa-f])')

def tok_strict(p):
    """口径 B：再禁逗号邻近（排除 293,512 这类千位分隔字节串）。"""
    return re.compile(r'(?<![0-9A-Fa-f,])' + p + r'(?![0-9A-Fa-f,])')

A_STRICT = {
    '458': tok_lite('458'), '291': tok_lite('291'), '293': tok_lite('293'),
    '1196': re.compile(r'(?<![0-9A-Fa-f])(?:1,196|1196)(?![0-9A-Fa-f])'),
}
B_STRICT = {
    '458': tok_strict('458'), '291': tok_strict('291'), '293': tok_strict('293'),
    '1196': re.compile(r'(?<![0-9A-Fa-f,])(?:1,196|1196)(?![0-9A-Fa-f,])'),
}
C_STRICT = dict(B_STRICT, **{'1196': tok_strict(r'1,196')})

def rows_of(ls, m):
    return [i for i, l in enumerate(ls, 1) if all(rx.search(l) for rx in m.values())]

META = re.compile(r'不可重数|未取得|承载|仍不可|无归属|口径')
B = {}
for k, ls in LINES.items():
    rA, rB, rC = rows_of(ls, A_STRICT), rows_of(ls, B_STRICT), rows_of(ls, C_STRICT)
    meta_A = [i for i in rA if META.search(ls[i-1])]
    B[k] = {'A': len(rA), 'B': len(rB), 'C': len(rC), 'metaA': len(meta_A),
            'A_lines': rA[:8], 'meta_lines': meta_A[:8]}
    print('  %-13s A=%-3d B=%-3d C=%-3d 含元描述词=%-3d A首批=%s'
          % (k, B[k]['A'], B[k]['B'], B[k]['C'], B[k]['metaA'], rA[:8]))

led_A = B['LEDGER']['A']
chk('B1 台账口径 A == 17（复现 R157 现盘值）', led_A == 17, {'ledgerA': led_A})
chk('B2 台账口径 B == 15（复现 R157 现盘值）', B['LEDGER']['B'] == 15, {'ledgerB': B['LEDGER']['B']})
chk('B3 台账四计数行绝大多数含元描述词（自指判据）',
    B['LEDGER']['metaA'] >= 13, {'metaA': B['LEDGER']['metaA'], 'A': led_A})
chk('B4 LEAD_LOCK 也有四计数行（指标可推广）', B['LEAD_LOCK']['A'] > 0, {'lockA': B['LEAD_LOCK']['A']})
chk('B5 FACT_INDEX 零四计数行（F23 statement 用「458/291/293/1,196」但被自身口径吃掉）',
    B['FACT_INDEX']['A'] == 0, {'fiA': B['FACT_INDEX']['A']})
chk('B6 R14_COMMON 也有四计数行（A>0，指标须推广到这处）',
    B['R14_COMMON']['A'] > 0, {'rcA': B['R14_COMMON']['A'], 'rcC': B['R14_COMMON']['C']})
# 正控：在人为构造行上口径 A/B 必须行为不同（禁逗号口径生效）
demo = '见 458 行 / 291 行 / 293,512 与 1,196 四计数'
chk('B7 正控：demo 行 A 命中而 B 不命中（禁逗号口径真生效）',
    all(rx.search(demo) for rx in A_STRICT.values()) and not all(rx.search(demo) for rx in B_STRICT.values()),
    {'A_all': all(rx.search(demo) for rx in A_STRICT.values()),
     'B_all': all(rx.search(demo) for rx in B_STRICT.values())})
# 负控：缺一个 token 必须不命中
demo2 = '458 行 / 291 行 / 293 行 但无总数'
chk('B8 负控：缺 1,196 的 demo 行不命中',
    not all(rx.search(demo2) for rx in A_STRICT.values()),
    {'A_all': all(rx.search(demo2) for rx in A_STRICT.values())})
chk('B9 正控：R157 报的两个台账值在本脚本实现下复现（A=17 / B=15）',
    B['LEDGER']['A'] == 17 and B['LEDGER']['B'] == 15,
    {'A': B['LEDGER']['A'], 'B': B['LEDGER']['B']})

# ---------------- 汇总 ----------------
out = {'A': A, 'B': B, 'summary': {'E1_total': tot_E1, 'E2_total': tot_E2,
                                   'ledger_A': led_A, 'ledger_B': B['LEDGER']['B']},
       'checks': R, 'n_pass': sum(1 for x in R if x['pass']), 'n_fail': sum(1 for x in R if not x['pass'])}
with open(os.path.join(ROOT, 'r158a_fact_ledger_scan.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('\nPASS=%d FAIL=%d' % (out['n_pass'], out['n_fail']))
sys.exit(0 if out['n_fail'] == 0 else 1)
