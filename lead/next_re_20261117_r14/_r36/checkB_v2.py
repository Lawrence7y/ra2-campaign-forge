# -*- coding: utf-8 -*-
"""R36 Check B v2：修正 v1 的两个正则缺陷后重做清点。
v1 缺陷：
  1) BARECARD 的 COVERAGE 命中了 COVERAGE_ONLY / COVERAGE 两处都是 COVERAGE_ONLY 的子串 ⇒ 假引用
  2) 漏了裸卡号 R\\d{1,2}（F12 的 R22/R19、F14 的 R19）与 S02B-GATE 这类卡名
判据：只列真引用，并给出每项「可解析 / 在本行锚内」。"""
import io, os, re, json, collections

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FI   = os.path.join(R14, 'R17_R66_FACTINDEX_V511', 'FACT_INDEX.tsv')
OUT  = os.path.join(R14, '_r36', 'checkB_inventory_v2.md')

raw = io.open(FI, encoding='utf-8', newline='').read()
lines = raw.split('\n')
header = lines[0].split('\t')
rows = [dict(zip(header, l.split('\t'))) for l in lines[1:] if l.strip()]

# ---- 资源池 ----
fact_ids = set(r['fact_id'] for r in rows)
ledger = io.open(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), encoding='utf-8', newline='').read()
ledger_secs = set(int(x) for x in re.findall(r'(?m)^##\s*§(\d{4})', ledger))
r14common = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
r14_secs = set(re.findall(r'(?m)^##\s*(\d+(?:\.\d+)*)', r14common))
pending = os.path.join(ROOT, 'lead', 'PENDING_DECISIONS.md')
pending_txt = io.open(pending, encoding='utf-8', newline='').read() if os.path.exists(pending) else ''

dirs = set()
for name in os.listdir(R14):
    if os.path.isdir(os.path.join(R14, name)):
        dirs.add(name.upper())

# PANEL M 项所属卡
panel_m = collections.defaultdict(set)
for name in sorted(os.listdir(R14)):
    p = os.path.join(R14, name)
    if not os.path.isdir(p):
        continue
    for dirpath, _, files in os.walk(p):
        for fn in files:
            if fn == 'PANEL.md':
                t = io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
                for m in re.finditer(r'(?<![\w])M(\d{1,3})(?![\d])', t):
                    panel_m['M' + m.group(1)].add(os.path.basename(dirpath))
ll = io.open(os.path.join(ROOT, 'lead', 'LEAD_LOCK'), encoding='utf-8').read()
for m in re.finditer(r'(?<![\w])M(\d{1,3})(?![\d])', ll):
    panel_m['M' + m.group(1)].add('LEAD_LOCK')

# ---- 修正后的模式 ----
PATTERNS = [
    ('SECTION',  re.compile(r'§\s*(\d{4}|\d+(?:\.\d+)*)')),
    ('FACT',     re.compile(r'(?<![\w])F(\d{2})(?![\d])')),
    ('MITEM',    re.compile(r'(?<![\w])M(\d{1,3})(?![\d])')),
    ('CARD',     re.compile(r'(?<![\w])(R1[4-7]_[A-Za-z0-9_]+|NAMED_PUSH_AUDIT\d{1,2}|NAMED_PUSH_S\d\w*|S\d\d[A-Z]?-[A-Z]+|R14_COMMON)')),
    ('BARECARD', re.compile(r'(?<![\w])(R\d{1,2})(?![\d\w])')),      # R22 / R19
    ('DECIDE',   re.compile(r'(?<![\w])(D-\d+)')),                    # D-53 / D-49
    ('FILEREF',  re.compile(r'(?<![\w\\/])([A-Za-z0-9_\-]+\.(?:tsv|md|json|py|txt|exe))')),
]

def strip_noise(st):
    """把不构成引用的串先抹掉，避免子串误匹配。"""
    s = re.sub(r'COVERAGE_ONLY', 'COVERAGEONLYPLACEHOLDER', st)
    s = re.sub(r'RTTI_ONLY', 'RTTIONLYPLACEHOLDER', s)
    s = re.sub(r'BOTH', 'BOTHPLACEHOLDER', s)
    return s

buf = ['# R36 Check B v2 · `statement` 列引用核验（修正正则后）\n']
tot = collections.Counter()
n_rows = 0
findings = []

for r in rows:
    st, ev, fid = r['statement'], r['evidence_paths'], r['fact_id']
    s = strip_noise(st)
    refs = []
    for name, pat in PATTERNS:
        for m in pat.finditer(s):
            tok = m.group(0).strip()
            if name in ('SECTION', 'FACT', 'MITEM', 'BARECARD'):
                tok = {'SECTION': '§', 'FACT': 'F', 'MITEM': 'M', 'BARECARD': ''}[name] + m.group(1)
            refs.append((name, tok))
    # 去重
    seen = set(); refs2 = []
    for k, t in refs:
        if (k, t) in seen:
            continue
        seen.add((k, t)); refs2.append((k, t))
    if not refs2:
        continue
    n_rows += 1
    buf.append('## %s [%s]' % (fid, r['grade']))
    for k, t in refs2:
        tot[k] += 1
        # 判定
        if k == 'SECTION':
            num = t[1:]
            if num.isdigit() and len(num) == 4:
                ns = '台账'; res = int(num) in ledger_secs
            else:
                ns = 'R14_COMMON'; res = num in r14_secs
            inanchor = t in ev
            buf.append('  - SECTION  %-8s ns=%-10s 可解析=%-5s 在本行锚内=%s' % (t, ns, res, inanchor))
            if not res or not inanchor:
                findings.append((fid, 'SECTION', t, res, inanchor))
        elif k == 'FACT':
            res = t in fact_ids
            inanchor = t.upper() in ev.upper()
            buf.append('  - FACT     %-8s 存在于索引=%-5s 在本行锚内=%s' % (t, res, inanchor))
            if not res:
                findings.append((fid, 'FACT', t, res, inanchor))
        elif k == 'MITEM':
            owners = sorted(panel_m.get(t, []))
            inanchor = any(o.upper() in ev.upper() for o in owners)
            buf.append('  - MITEM    %-8s 所属卡=%-22s 锚内=%s' % (t, ','.join(owners) or 'NONE', inanchor))
            if not owners or not inanchor:
                findings.append((fid, 'MITEM', t, bool(owners), inanchor))
        elif k == 'CARD':
            d = t.upper() in dirs
            inanchor = t.upper() in ev.upper()
            buf.append('  - CARD     %-22s 目录存在=%-5s 在本行锚内=%s' % (t, d, inanchor))
            if not d:
                findings.append((fid, 'CARD', t, d, inanchor))
        elif k == 'BARECARD':
            # 裸卡号：试着映射到 R17_<Rnn>_* 或 R17_AUDIT_<Rnn>
            cands = [x for x in dirs if re.match(r'^R17_%s_' % t.upper(), x) or re.match(r'^R17_AUDIT_%s_' % t.upper(), x)]
            buf.append('  - BARECARD %-8s 候选目录=%s' % (t, ','.join(sorted(cands)[:3]) or 'NONE'))
            if not cands:
                findings.append((fid, 'BARECARD', t, False, None))
        elif k == 'DECIDE':
            inpend = t in pending_txt
            incommon = t in r14common
            inanchor = t in ev
            buf.append('  - DECIDE   %-8s PENDING_DECISIONS=%-5s R14_COMMON=%-5s 在本行锚内=%s' % (t, inpend, incommon, inanchor))
            if not (inpend or incommon):
                findings.append((fid, 'DECIDE', t, False, inanchor))
        elif k == 'FILEREF':
            buf.append('  - FILEREF  %-14s （见下：对象 vs 来源）' % t)
    buf.append('')

buf.insert(1, '含引用的行数 = %d；各类计数 = %s\n' % (n_rows, dict(tot)))
buf.append('\n## 判定汇总（需人工追查的项）\n')
for f in findings:
    buf.append('- %s %s `%s` 可解析=%s 锚内=%s' % (f[0], f[1], f[2], f[3], f[4]))

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(buf))
print('rows with refs =', n_rows, dict(tot))
print('findings =', len(findings))
for f in findings:
    print('   ', f)
print('wrote', OUT)
