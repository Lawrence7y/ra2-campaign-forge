# -*- coding: utf-8 -*-
"""R36 Check B v3：修 v2 的三个判定器缺陷：
  1) R14_COMMON 是**文件**不是目录，v2 用目录池判 ⇒ 假 False
  2) R14_COMMON 的 §2.6 是 `###` 三级标题，v2 只匹配 `^##` ⇒ 假 False
  3) 卡名 `S02B-GATE`（连字符）vs 目录 `S02B_GATE`（下划线）未归一 ⇒ 假 False
另外把「对象 vs 来源」的分辨写进输出，避免把 FILEREF 当成缺陷。
"""
import io, os, re, collections

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FI   = os.path.join(R14, 'R17_R66_FACTINDEX_V511', 'FACT_INDEX.tsv')
OUT  = os.path.join(R14, '_r36', 'checkB_v4.md')

raw = io.open(FI, encoding='utf-8', newline='').read()
lines = raw.split('\n')
header = lines[0].split('\t')
rows = [dict(zip(header, l.split('\t'))) for l in lines[1:] if l.strip()]
fact_ids = set(r['fact_id'] for r in rows)

ledger = io.open(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), encoding='utf-8', newline='').read()
ledger_secs = set(int(x) for x in re.findall(r'(?m)^##\s*§(\d{4})', ledger))
r14c = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
# 修 #2：允许 ## 到 ####
r14_secs = set(re.findall(r'(?m)^#{2,4}\s*§?\s*(\d+(?:\.\d+)*)\s', r14c))
pending = os.path.join(ROOT, 'lead', 'PENDING_DECISIONS.md')
pending_txt = io.open(pending, encoding='utf-8', newline='').read() if os.path.exists(pending) else ''

# 修 #1：目录池 + 文件池分开
dirs, files_in_r14 = set(), set()
for name in os.listdir(R14):
    p = os.path.join(R14, name)
    (dirs if os.path.isdir(p) else files_in_r14).add(name.upper())
files_in_root = set(os.listdir(ROOT))
# 修 #4：卡名/文件名常量可能不带扩展名（如 R14_COMMON），补一个去扩展名池
files_stem = set(os.path.splitext(x)[0].upper() for x in (files_in_r14 | files_in_root))

def norm_card(t):
    return t.upper().replace('-', '_')

panel_m = collections.defaultdict(set)
for name in sorted(os.listdir(R14)):
    p = os.path.join(R14, name)
    if not os.path.isdir(p):
        continue
    for dirpath, _, fs_ in os.walk(p):
        for fn in fs_:
            if fn == 'PANEL.md':
                t = io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
                for m in re.finditer(r'(?<![\w])M(\d{1,3})(?![\d])', t):
                    panel_m['M' + m.group(1)].add(os.path.basename(dirpath))
ll = io.open(os.path.join(ROOT, 'lead', 'LEAD_LOCK'), encoding='utf-8').read()
for m in re.finditer(r'(?<![\w])M(\d{1,3})(?![\d])', ll):
    panel_m['M' + m.group(1)].add('LEAD_LOCK')

PATTERNS = [
    ('SECTION',  re.compile(r'§\s*(\d{4}|\d+(?:\.\d+)*)')),
    ('FACT',     re.compile(r'(?<![\w])F(\d{2})(?![\d])')),
    ('MITEM',    re.compile(r'(?<![\w])M(\d{1,3})(?![\d])')),
    ('CARD',     re.compile(r'(?<![\w])(R1[4-7]_[A-Za-z0-9_]+|NAMED_PUSH_AUDIT\d{1,2}|NAMED_PUSH_S\d\w*|S\d\d[A-Z]?-[A-Z]+|R14_COMMON)')),
    ('BARECARD', re.compile(r'(?<![\w])(R\d{1,2})(?![\d\w])')),
    ('DECIDE',   re.compile(r'(?<![\w])(D-\d+)')),
    ('FILEREF',  re.compile(r'(?<![\w\\/])([A-Za-z0-9_\-]+\.(?:tsv|md|json|py|txt|exe))')),
]

def strip_noise(st):
    s = re.sub(r'COVERAGE_ONLY', 'CONLYPH', st)
    s = re.sub(r'RTTI_ONLY', 'RONLYPH', s)
    s = re.sub(r'\bBOTH\b', 'BOTHX', s)
    return s

buf = ['# R36 Check B v3 · `statement` 列引用核验（判定器三缺陷已修）\n']
tot = collections.Counter(); n_rows = 0; findings = []

for r in rows:
    st, ev, fid = r['statement'], r['evidence_paths'], r['fact_id']
    s = strip_noise(st)
    refs, seen = [], set()
    for name, pat in PATTERNS:
        for m in pat.finditer(s):
            tok = m.group(0).strip()
            if name in ('SECTION', 'FACT', 'MITEM', 'BARECARD'):
                tok = {'SECTION': '§', 'FACT': 'F', 'MITEM': 'M', 'BARECARD': ''}[name] + m.group(1)
            if (name, tok) in seen:
                continue
            seen.add((name, tok)); refs.append((name, tok))
    if not refs:
        continue
    n_rows += 1
    buf.append('## %s [%s]' % (fid, r['grade']))
    for k, t in refs:
        tot[k] += 1
        if k == 'SECTION':
            num = t[1:]
            if num.isdigit() and len(num) == 4:
                ns, res = '台账', int(num) in ledger_secs
            else:
                ns, res = 'R14_COMMON', num in r14_secs
            ina = t in ev
            buf.append('  - SECTION  %-8s ns=%-10s 可解析=%-5s 在本行锚内=%s' % (t, ns, res, ina))
            if not res or not ina:
                findings.append((fid, 'SECTION', t, res, ina))
        elif k == 'FACT':
            res = t in fact_ids; ina = t.upper() in ev.upper()
            buf.append('  - FACT     %-8s 存在于索引=%-5s 在本行锚内=%s' % (t, res, ina))
            if not res:
                findings.append((fid, 'FACT', t, res, ina))
        elif k == 'MITEM':
            owners = sorted(panel_m.get(t, [])); ina = any(o.upper() in ev.upper() for o in owners)
            buf.append('  - MITEM    %-8s 所属卡=%-20s 锚内=%s' % (t, ','.join(owners) or 'NONE', ina))
            if not owners or not ina:
                findings.append((fid, 'MITEM', t, bool(owners), ina))
        elif k == 'CARD':
            n = norm_card(t)
            res = (n in dirs) or (n in files_in_r14) or (n in files_stem)
            ina = t.upper() in ev.upper() or n in ev.upper()
            buf.append('  - CARD     %-14s 存在=%-5s 在本行锚内=%s' % (t, res, ina))
            if not res:
                findings.append((fid, 'CARD', t, res, ina))
        elif k == 'BARECARD':
            cands = [x for x in dirs if re.match(r'^R17_%s_' % t.upper(), x) or re.match(r'^R17_AUDIT_%s_' % t.upper(), x)]
            buf.append('  - BARECARD %-8s 候选目录=%s' % (t, ','.join(sorted(cands)[:3]) or 'NONE'))
            if not cands:
                findings.append((fid, 'BARECARD', t, False, None))
        elif k == 'DECIDE':
            inpend, incommon, ina = t in pending_txt, t in r14c, t in ev
            buf.append('  - DECIDE   %-8s PENDING=%-5s R14_COMMON=%-5s 锚内=%s' % (t, inpend, incommon, ina))
            if not (inpend or incommon):
                findings.append((fid, 'DECIDE', t, False, ina))
        elif k == 'FILEREF':
            exists = os.path.exists(os.path.join(ROOT, t)) or os.path.exists(os.path.join(R14, t)) or t.upper() in files_in_root
            buf.append('  - FILEREF  %-14s 文件存在=%s（多为主张对象、非来源）' % (t, exists))
    buf.append('')

buf.insert(1, '含引用的行数 = %d；各类计数 = %s\n' % (n_rows, dict(tot)))
buf.append('\n## findings（可解析失败 或 声称而锚外）\n')
if not findings:
    buf.append('- 无')
for f in findings:
    buf.append('- %s %s `%s` 可解析=%s 锚内=%s' % (f[0], f[1], f[2], f[3], f[4]))

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(buf))
print('rows with refs =', n_rows, dict(tot))
print('findings =', len(findings))
for f in findings:
    print('   ', f)
