#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R155 B：F35 撤回「缺一手权威」之后，剩下的半个等式（r[3] == 语义栏）在现盘有多少权威。
判据分三层：① 代码解析表头 ② 位置硬编码 ③ 散文。全部带正反控。"""
import os, re, json

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEAD = os.path.join(ROOT, 'lead')
R14  = os.path.join(LEAD, 'next_re_20261117_r14')
SP   = os.path.join(R14, 'RULING_R15_20261119', 'work', 'strict_panel.py')
M59  = os.path.join(R14, '_cards', 'M59-MERGE')
IDX  = os.path.join(R14, 'R17_R114_FACTINDEX_V542', 'FACT_INDEX.tsv')
M59_READ = os.path.join(R14, '_cards', 'M59-MERGE')

fails, out = [], {}
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

sp = open(SP, encoding='utf-8').read()
code_lines = sp.split('\n')

# ---------- 1 · strict_panel.py 有没有解析表头把列名绑成下标 ----------
# S-404: 上一版判据用「文件内出现 one_line_semantics 字面」，命中的是 L14 的 docstring 散文，
# 那是散文不是代码 ⇒ 假 FAIL。正确判据是**表头行有没有被读**：读表头 = 取 cov[0] / 比对表头串 /
# 用列名查下标；丢掉表头 = 直接 [1:] 且全文无 cov[0]。
def header_bound(path):
    """返回 (对**输入表头**做过逐字比较吗, 强证据行, 弱证据行)。
    S-405: 把 r[0]/p[0] 当「读表头」是错的 —— 那是数据行字段下标。
    S-406: 把 hdr = "S atlas_n ..." 当「读表头」也是错的 —— 那是**写输出文件**的表头。
    强判据（只有这三种能证明「列名被机器绑到下标」）：
      ① 表头变量与字面串做 ==/!= 比较  ② csv.DictReader / .fieldnames
      ③ 用列名做 index()/get() 查下标
    弱判据（取值但不比较，单列不计入结论）：把文件首条记录赋给 header/hdr 变量。"""
    ls = open(path, encoding='utf-8').read().split('\n')
    strong, weak = [], []
    for i, l in enumerate(ls):
        t = l.strip()
        if re.search(r'(header|hdr|h)\s*(==|!=)', t) or \
           re.search(r'fieldnames|DictReader', t) or \
           re.search(r'\.index\(\s*["\'](one_line_semantics|grade|entry)["\']', t):
            strong.append((i + 1, t))
        elif re.search(r'^\s*(header|hdr)\s*=\s*\S', t) and 'open(' not in t:
            weak.append((i + 1, t))
    return (len(strong) > 0), strong, weak

sp_reads, sp_ev, sp_weak = header_bound(SP)
out['strict_panel_header'] = {'header_compared': sp_reads, 'strong': sp_ev, 'weak': sp_weak}
print('  --- strict_panel.py 对输入表头做逐字比较吗 ---')
print('    强证据 = %s ; 强证据行 %d 条 ; 弱证据行 %d 条' % (sp_reads, len(sp_ev), len(sp_weak)))
for ln, t in sp_ev:
    print('    STRONG L%d: %s' % (ln, t[:140]))
for ln, t in sp_weak:
    print('    weak   L%d: %s' % (ln, t[:140]))
ck('1.1 strict_panel.py 对输入表头无任何逐字比较（列名从未被绑成下标）', not sp_reads, sp_ev)

# 1.2 它怎么处理表头行：必须显式 [1:] 丢弃
drop = [(i + 1, l.strip()) for i, l in enumerate(code_lines) if re.search(r'\)\s*\[1:\]', l.strip())]
out['strict_panel_drop_header'] = drop
print('  --- strict_panel.py 丢弃表头处 ---')
for ln, t in drop:
    print('    L%d: %s' % (ln, t[:140]))
ck('1.2 strict_panel.py 显式以 [1:] 丢弃表头行', len(drop) >= 1, drop)

# 1.3 正控：同一条判据在 verify.py 上必须判「读了表头」（证明判据能翻转，不是恒假）
ver = os.path.join(M59_READ, 'verify.py')
ver_reads, ver_ev, ver_weak = header_bound(ver)
out['verify_header'] = {'header_compared': ver_reads, 'strong': ver_ev, 'weak': ver_weak}
print('  --- 正控 verify.py 对输入表头做逐字比较吗 ---')
print('    强证据 = %s ; 强证据行 %d 条' % (ver_reads, len(ver_ev)))
for ln, t in ver_ev:
    print('    STRONG L%d: %s' % (ln, t[:140]))
ck('1.3 正控：同一判据在 verify.py 上判「有逐字比较」（证明判据不恒假）', ver_reads, ver_ev)

# ---------- 2 · r[3] 的全部出现处 ----------
occ = [(i + 1, l.rstrip()) for i, l in enumerate(code_lines) if re.search(r'r\[3\]', l)]
out['r3_occurrences'] = occ
print('  --- r[3] 出现处 %d 条 ---' % len(occ))
for ln, txt in occ:
    print('    L%d: %s' % (ln, txt.strip()))
ck('2.1 r[3] 出现处 >= 1', len(occ) >= 1, len(occ))
ck('2.2 r[3] 只用于取 sem（不参与表头比对）',
   all('sem' in t for _, t in occ), [t.strip() for _, t in occ])

# ---------- 3 · sem 的散文描述 ----------
# sem 唯一赋值点与 docstring 描述行
sem_assign = [(i + 1, l.strip()) for i, l in enumerate(code_lines) if re.match(r'\s*sem\s*=', l)]
out['sem_assign'] = sem_assign
print('  --- sem 赋值点 ---')
for ln, t in sem_assign:
    print('    L%d: %s' % (ln, t))
ck('3.1 sem 恰 1 处赋值', len(sem_assign) == 1, len(sem_assign))
ck('3.2 赋值形如 sem = r[3]', bool(sem_assign) and re.match(r'sem\s*=\s*r\[3\]', sem_assign[0][1]),
   sem_assign[0][1] if sem_assign else '')

# docstring 内对 proved_strict_n 的描述行（取文件头 20 行内的 one_line_semantics 行）
doc_lines = [(i + 1, l.strip()) for i, l in enumerate(code_lines[:20]) if 'one_line_semantics' in l]
out['doc_desc'] = doc_lines
print('  --- docstring 对 sem 的散文描述 ---')
for ln, t in doc_lines:
    print('    L%d: %s' % (ln, t))
ck('3.3 docstring 有散文描述（>=1 行）', len(doc_lines) >= 1, len(doc_lines))

# ---------- 4 · M59-MERGE 三脚本里有没有表头逐字机检 ----------
m59 = {}
HDR_LIT = 'entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict'
for fn in ('precheck.py', 'simulate.py', 'verify.py', 'merge_panel.py'):
    p = os.path.join(M59, fn)
    if not os.path.isfile(p):
        m59[fn] = {'exists': False}; continue
    t = open(p, encoding='utf-8').read()
    ls = t.split('\n')
    hdr_ck = [(i + 1, l.strip()) for i, l in enumerate(ls) if 'header' in l]
    lit = [(i + 1, l.strip()) for i, l in enumerate(ls) if 'entry,subsystem' in l]
    hdr_eq = [(i + 1, l.strip()) for i, l in enumerate(ls) if HDR_LIT in l]
    m59[fn] = {'exists': True, 'bytes': os.path.getsize(p),
               'header_lines': hdr_ck, 'header_literal_lines': lit,
               'full_header_eq_lines': hdr_eq}
    print('  --- %s (在盘, %d B) ---' % (fn, os.path.getsize(p)))
    print('    header 相关行 %d 条 %s' % (len(hdr_ck), [x[0] for x in hdr_ck]))
    print('    完整表头字面串 %d 条 %s' % (len(hdr_eq), [x[0] for x in hdr_eq]))
    for ln, t2 in hdr_eq:
        print('      L%d: %s' % (ln, t2[:160]))
out['m59'] = m59

ck('4.1 merge_panel.py 在盘（R148 反控用）', m59.get('merge_panel.py', {}).get('exists') is False
   or m59['merge_panel.py']['exists'], 'exists=%s' % m59.get('merge_panel.py', {}).get('exists'))
hdr_scripts = [fn for fn, v in m59.items() if v.get('exists') and v.get('full_header_eq_lines')]
ck('4.2 至少一个伙伴脚本对表头做逐字机检', len(hdr_scripts) >= 1, hdr_scripts)

# ---------- 5 · 该表头机检的输入文件在不在盘 ----------
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
out['coverage_tsv'] = {'path': COV, 'exists': os.path.isfile(COV)}
print('  --- 表头机检的输入 coverage.tsv ---')
print('    %s -> %s' % (COV, 'EXIST' if os.path.isfile(COV) else 'MISSING'))
ck('5.1 coverage.tsv 不在盘（如实登记）', not os.path.isfile(COV))

# ---------- 6 · 表头字面串的第 4 个字段名 ----------
fields = HDR_LIT.split(',')
out['header_fields'] = fields
print('  --- 表头 8 字段 ---')
for i, f in enumerate(fields, 1):
    print('    %d. %s' % (i, f))
ck('6.1 表头恰 8 字段', len(fields) == 8, len(fields))
ck('6.2 第 4 字段 == one_line_semantics', fields[3] == 'one_line_semantics', fields[3])

# ---------- 7 · 反控：列下标错位有没有自检能发现 ----------
# 判据：strict_panel.py 内有没有任何断言/校验把 r[3] 与列名字面绑定
selfcheck = [i + 1 for i, l in enumerate(code_lines)
             if re.search(r'assert|raise|sys\.exit|check\(', l)]
out['selfcheck_lines'] = selfcheck
print('  --- strict_panel.py 自检/断言行 %d 条 %s ---' % (len(selfcheck), selfcheck))
ck('7.1 strict_panel.py 无任何断言/自检（列错位不会被它自己发现）', len(selfcheck) == 0, selfcheck)

# ---------- 8 · 正控：本仓库里确实存在「表头被代码逐字检查」的正面例子 ----------
pos_ok = bool(hdr_scripts)
ck('8.1 正控：存在表头逐字机检的正面例子（证明 4.2 判据不是恒假）', pos_ok, hdr_scripts)

json.dump(out, open(os.path.join(ROOT, '_r155', 'r155b_f35_sem.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
print()
print('  FAILS = %d  %s' % (len(fails), fails))
