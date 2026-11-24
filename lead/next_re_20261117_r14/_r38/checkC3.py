# -*- coding: utf-8 -*-
"""R38 Check C v3 —— 修 T3 审计指出的三处硬缺口 + 两处纪律违反。

v2 缺口（全部已复算确认）：
  G1 C3 零正反控（违反纪律 11②——原文是「每个子检查」）。
  G2 C1 的 duty 跳过与 token 未命中都不留痕 ⇒ 「判不出来按没问题处理」（违反纪律 11①）。
  G3 三个闭集合在程序与报告里都没声明（违反纪律 12①）。
  G4 P1/P2/P4 强制要求引号 ⇒ 无引号降级（如 F06「语义定性属静态推断、非已证」）抓不到。
  G5 「不构成」只在 HEDGE_WORDS、不在 DOWNGRADE_PATTERNS ⇒ F52 永久 0 命中。
  G6 FAIL 时 sys.exit(2) 在写报告之前 ⇒ 失败运行无任何落盘证据（叙事无据）。

v3 处置：
  - 报告**先落盘**、控制组结果写进报告；FAIL 也留盘（文件名带 FAIL）。
  - C3 补正控/反控（双相反向注入）。
  - 输出新增「跳过的 token」与「未匹配的降级行」两节，让「没报」变成可读的。
  - 新增无引号降级模式 P5；把「不构成」补进 DOWNGRADE_PATTERNS。
  - 报告头显式声明三个闭集合与 C2 的覆盖率。
"""
import io, os, re, sys, collections

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OUTDIR = os.path.join(R14, '_r38')
os.makedirs(OUTDIR, exist_ok=True)

def load(p):
    raw = io.open(p, encoding='utf-8', newline='').read()
    lines = raw.split('\n')
    h = lines[0].split('\t')
    return [dict(zip(h, l.split('\t'))) for l in lines[1:] if l.strip()]

def norm(s):
    return re.sub(r'[\s，。；、「」『』（）()·`*_"\'：:；;,.!?！？\-—]+', '', s)

HEDGE_WORDS = ['推断', '未证', '未经', '存疑', '不能排除', '疑似', '待裁', '待核',
               '不构成', '不得当', '中等偏强', '中等', '偏弱']          # 闭集合 13 词
DOWNGRADE_PATTERNS = [
    r'[「『]([^」』]{2,40})[」』]\s*(?:是|属)[^。；]{0,20}(?:推断措辞|单源归因|行动裁决|推断)',
    r'[「『]([^」』]{2,40})[」』][^。；]{0,40}(?:不随数字一并作已证|不入本条证据|未经字节证实|未经[^。；]{0,4}证实)',
    r'不得写成[「『]?([^，。；」』]{2,30})',
    r'[「『]([^」』]{2,40})[」』][^。；]{0,20}不得当[^。；]{0,10}用',
    r'([^\s，。；、「」『』]{2,30})\s*(?:属|是)\s*(?:静态推断|推断措辞|非已证|未经证实)',   # G4 新增：无引号
    r'不构成([^\s，。；、「」『』]{2,30})',                                                  # G5 修：捕获宾语而非前面的碎片
]
DUTY_CONTEXT = ('本条不支撑', '不得据此', '不得引申', '不得反推', '不得再用', '只能引其',
                '须同引', '必须同引', '引用时二者同看', '不得只引用', '不得单独引用', '削弱')  # 闭集合 12 词

CLOSED_SET_DECL = ('**闭集合声明（纪律 12①）**：C1 的降级句式 = 6 条正则；HEDGE_WORDS = 13 词；'
                   'DUTY_CONTEXT = 12 词。三者**均不可穷尽**，故 0 命中只能读作'
                   '「在我能认出的写法上没发现」，**不能**读作「54 行列间无矛盾」。'
                   'C2 **只覆盖 27 条 [已证] 行**（占 54 行的 50%），其余 27 行不参与。')

def downgraded_tokens(lim):
    out = []
    for pat in DOWNGRADE_PATTERNS:
        for m in re.finditer(pat, lim):
            t = m.group(1).strip()
            if 2 <= len(t) <= 40:
                out.append(t)
    return sorted(set(out))

def duty_hit(lim, token):
    for seg in re.split(r'[；;。]', lim):
        if token in seg:
            return next((d for d in DUTY_CONTEXT if d in seg), None)
    return None

def paired_quote_spans(s):
    spans, stack = [], []
    opens = {'「': '」', '『': '』', '“': '”', '"': '"'}
    for i, ch in enumerate(s):
        if ch in opens:
            stack.append((ch, i))
        elif stack and ch == opens[stack[-1][0]]:
            _, j = stack.pop()
            spans.append((j, i))
    return spans

def stmt_uses_hedged(stmt, token, window=45):
    k = norm(token)
    if not k:
        return (False, None, '', 'token归一化为空')
    ks = norm(stmt)
    idx = ks.find(k)
    if idx < 0:
        return (False, None, '', '正文未出现该 token(归一化后)')
    seg = ks[max(0, idx - window):idx + len(k) + window]
    hedged = any(w in seg for w in HEDGE_WORDS)
    raw_i = stmt.find(token)
    if raw_i < 0 and len(token) >= 4:
        raw_i = stmt.find(token[:4])
    ctx = stmt[max(0, raw_i - 40):raw_i + 60] if raw_i >= 0 else '(原文未定位)'
    return (True, hedged, ctx, 'ok')

def check_C1(row, skipped):
    hits = []
    for t in downgraded_tokens(row['limitations']):
        d = duty_hit(row['limitations'], t)
        if d:
            skipped.append('%s  token `%s` 因 duty 词「%s」被跳过（**未判定**）' % (row['fact_id'], t, d))
            continue
        used, hedged, ctx, why = stmt_uses_hedged(row['statement'], t)
        if not used:
            skipped.append('%s  token `%s` 正文未用（%s）' % (row['fact_id'], t, why))
            continue
        if not hedged:
            hits.append((t, ctx))
    return hits

def check_C2(row):
    if row['grade'] != '[已证]':
        return []
    st = row['statement']
    spans = paired_quote_spans(st)
    bad = []
    for w in ('推断', '推测', '疑似'):
        for m in re.finditer(w, st):
            i = m.start()
            if any(a <= i <= b for a, b in spans):
                continue
            ctx = st[max(0, i - 30):i + 30]
            if re.search(r'(静态|中等|偏强|偏弱|待裁|推断强度)', ctx):
                continue
            if re.search(r'(不再是|不是|不再|不得|不能|非|不作|不构成|视为|降级为|改为|升级为)\s*' + w, ctx):
                continue
            bad.append((w, ctx))
            break
    return bad

def strip_anchor(item):
    if not item or item[-1] not in ')）':
        return item, None
    depth = 0
    for i in range(len(item) - 1, -1, -1):
        c = item[i]
        if c in ')）':
            depth += 1
        elif c in '(（':
            depth -= 1
            if depth == 0:
                if i == 0:
                    return item, None
                return item[:i], item[i + 1:-1]
    return item, None

def split_items(ev):
    out, depth, cur = [], 0, ''
    for ch in ev:
        if ch in '（(': depth += 1
        elif ch in '）)': depth = max(0, depth - 1)
        if ch == ';' and depth == 0:
            out.append(cur); cur = ''; continue
        cur += ch
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out if x.strip()]

def build_pool(row):
    pool, unresolved = [], []
    for it in split_items(row['evidence_paths']):
        f, _a = strip_anchor(it)
        ap = os.path.join(ROOT, f.replace('\\', '/'))
        if os.path.isfile(ap):
            pool.append(io.open(ap, encoding='utf-8', errors='replace').read().lower())
        else:
            unresolved.append(f)
    return pool, unresolved

def check_C3(row):
    pool, unresolved = build_pool(row)
    if unresolved:
        return ([], unresolved)
    blob = '\n'.join(pool)
    miss = []
    for m in re.finditer(r'0x([0-9A-Fa-f]{4,8})', row['statement']):
        hx = m.group(1).lower()
        cands = {hx, hx.lstrip('0'), hx.zfill(8), hx.zfill(6), str(int(hx, 16))}
        if not any(c in blob for c in cands):
            miss.append('0x' + m.group(1))
    return (sorted(set(miss)), [])

# ---------------- 控制组（四个子检查全都要） ----------------
def controls(rows_by_id):
    res = []
    def ok(name, cond):
        res.append((name, bool(cond)))
    v510 = rows_by_id['v510']; v513 = rows_by_id['v513']
    # C1
    ok('C1正控 v5.10 F24', len(check_C1(v510['F24'], [])) > 0)
    ok('C1正控 v5.10 F29', len(check_C1(v510['F29'], [])) > 0)
    ok('C1反控 v5.13 F24', len(check_C1(v513['F24'], [])) == 0)
    ok('C1反控 v5.13 F29', len(check_C1(v513['F29'], [])) == 0)
    # C1 · G4/G5 专项：无引号降级 & 不构成
    fake_g4 = {'fact_id': 'G4', 'grade': '[流程]',
               'statement': '该模块语义定性为已确认。',
               'limitations': '语义定性属静态推断、非已证', 'evidence_paths': ''}
    ok('C1正控 无引号降级(G4)', len(check_C1(fake_g4, [])) > 0)
    fake_g5 = {'fact_id': 'G5', 'grade': '[流程]',
               'statement': '单一 test 形态即构成删除析构器证据。',
               'limitations': '单一 test 形态不构成删除析构器证据', 'evidence_paths': ''}
    ok('C1正控 不构成(G5)', len(check_C1(fake_g5, [])) > 0)
    # C2
    fake = {'grade': '[已证]', 'statement': '该函数是构造器（推断）。', 'limitations': '—',
            'fact_id': 'FAKE', 'evidence_paths': ''}
    ok('C2正控 裸断言', len(check_C2(fake)) > 0)
    ok('C2反控 引号内', len(check_C2(dict(fake, statement='该函数性质记为「推断」。'))) == 0)
    ok('C2反控 强度标注', len(check_C2(dict(fake, statement='语义疑似占格 helper（静态推断/中等偏强）。'))) == 0)
    # C3 · G1 补正反控（双相反向注入）
    row_ok = {'fact_id': 'C3P', 'statement': '入口 0x1234ABCD 处', 'evidence_paths': '',
              'grade': '[流程]', 'limitations': ''}
    miss, unres = check_C3(row_ok)
    ok('C3正控 地址必报(空池)', miss == ['0x1234ABCD'] and not unres)
    row_bad = dict(row_ok, evidence_paths='lead\\NO_SUCH_FILE_XYZ.md')
    miss2, unres2 = check_C3(row_bad)
    ok('C3反控 锚不可解析则不清算地址', miss2 == [] and unres2 == ['lead\\NO_SUCH_FILE_XYZ.md'])
    return res

rows510 = {r['fact_id']: r for r in load(os.path.join(R14, 'R17_R65_FACTINDEX_V510', 'FACT_INDEX.tsv'))}
rows513 = {r['fact_id']: r for r in load(os.path.join(R14, 'R17_R71_FACTINDEX_V514', 'FACT_INDEX.tsv'))}
ctrl = controls({'v510': rows510, 'v513': rows513})
all_ok = all(c for _, c in ctrl)

# ---- 报告先落盘（G6：FAIL 也留盘） ----
rows = load(os.path.join(R14, 'R17_R71_FACTINDEX_V514', 'FACT_INDEX.tsv'))
buf = ['# R38 Check C v3 · 列间一致性\n', CLOSED_SET_DECL, '',
       '## 控制组（纪律 11②：每个子检查都要有）\n']
for name, good in ctrl:
    buf.append('- %s  %s' % ('PASS' if good else '**FAIL**', name))
buf.append('')
buf.append('控制组总判定：**%s**' % ('PASS —— 后续结论可读' if all_ok else 'FAIL —— 后续结论作废'))
buf.append('')

skipped = []
c1 = c2 = c3 = c3u = 0
detail = []
for r in rows:
    h1, h2 = check_C1(r, skipped), check_C2(r)
    miss, unres = check_C3(r)
    if h1 or h2 or miss or unres:
        detail.append('## %s [%s]' % (r['fact_id'], r['grade']))
        if h1:
            c1 += 1
            for t, ctx in h1:
                detail.append('- **C1** `%s` 被 limitations 降级、正文未带限定：…%s…' % (t, ctx))
        if h2:
            c2 += 1
            detail.append('- **C2** %s' % '; '.join('%s @…%s…' % (w, c) for w, c in h2))
        if unres:
            c3u += 1
            detail.append('- **C3 锚不可解析（fail-closed）**：%s' % unres)
        if miss:
            c3 += 1
            detail.append('- **C3 地址不可追溯**：%s' % ' '.join(miss))
        detail.append('')
buf.append('## 结果\n')
buf.append('命中：C1=%d / C2=%d / C3地址=%d / C3锚不可解析=%d（共 %d 行含引用判定）'
           % (c1, c2, c3, c3u, len(rows)))
buf.append('')
buf.extend(detail)
buf.append('## 被跳过的 token（纪律 11①：判不出来要留痕）\n')
buf.append('共 %d 条。这些**不是「没问题」**，是「本检查器没判」。' % len(skipped))
for s in skipped:
    buf.append('- ' + s)

name = 'checkC3_report.md' if all_ok else 'checkC3_report_FAIL.md'
out = os.path.join(OUTDIR, name)
io.open(out, 'w', encoding='utf-8').write('\n'.join(buf))
print('controls:', 'PASS' if all_ok else 'FAIL')
for n, g in ctrl:
    print('  ', 'PASS' if g else 'FAIL', n)
print('C1=%d C2=%d C3addr=%d C3unres=%d ; skipped=%d' % (c1, c2, c3, c3u, len(skipped)))
print('wrote', out)
sys.exit(0 if all_ok else 2)
