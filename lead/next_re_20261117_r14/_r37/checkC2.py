# -*- coding: utf-8 -*-
"""R37 Check C v2 —— 修 v1 被审计（T3）与自测发现的四处结构性缺陷。

v1 缺陷（均已在盘上复现确认）：
  D1  C3 剥锚只用 r'\\([^()]*\\)$'，遇嵌套括号錨「(§2.10 / 一 / (a′))」剥不掉 ⇒ 该项静默丢弃（F06/F07 各 1 个锚从未参与）。
  D2  C3 是 fail-open：锚解析失败 ⇒ pool 为空 ⇒ 该行全部地址被报出（v3 的 F17 缺目录前缀、F21 是裸目录，两例整行全报）。
      修正方向与 §2.15 一致：**解析失败必须单独报「锚不可解析」，而不是把它转成「地址不存在」**。
  D3  C2 的引号豁免是「窗口内存在任一引号字符」，不是配对区间 ⇒ 只要有半个引号就整段豁免。
  D4  C2 无正控/反控（v1 只对 C1 做了自证）。

本版同时给出 C2 的正控与反控；C1/C3 保留 v1 的判据（C1 仅新增「引用义务类」排除，避免把范围限制当过度断言）。
"""
import io, os, re, sys, collections

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')

def load(p):
    raw = io.open(p, encoding='utf-8', newline='').read()
    lines = raw.split('\n')
    h = lines[0].split('\t')
    return [dict(zip(h, l.split('\t'))) for l in lines[1:] if l.strip()]

def key(s):
    return re.sub(r'[\s，。；、「」『』（）()·`*_"\'：:；;,.!?！？\-—]+', '', s)

HEDGE_WORDS = ['推断', '未证', '未经', '存疑', '不能排除', '疑似', '待裁', '待核', '不构成', '不得当', '中等偏强', '中等', '偏弱']

DOWNGRADE_PATTERNS = [
    r'[「『]([^」』]{2,40})[」』]\s*(?:是|属)[^。；]{0,20}(?:推断措辞|单源归因|行动裁决|推断)',
    r'[「『]([^」』]{2,40})[」』][^。；]{0,40}(?:不随数字一并作已证|不入本条证据|未经字节证实|未经[^。；]{0,4}证实)',
    r'不得写成[「『]?([^，。；」』]{2,30})',
    r'[「『]([^」』]{2,40})[」』][^。；]{0,20}不得当[^。；]{0,10}用',
]
# 引用义务/范围限制句式：其引号内对象是「别人可能的误用」，不是本行断言 ⇒ 不参与 C1
DUTY_CONTEXT = ('本条不支撑', '不得据此', '不得引申', '不得反推', '不得再用', '只能引其',
                '须同引', '必须同引', '引用时二者同看', '不得只引用', '不得单独引用', '削弱')

def downgraded_tokens(lim):
    out = []
    for pat in DOWNGRADE_PATTERNS:
        for m in re.finditer(pat, lim):
            t = m.group(1).strip()
            if len(t) >= 2:
                out.append(t)
    return sorted(set(out))

def is_duty_sentence(lim, token):
    """token 所在分句是否属引用义务类"""
    for seg in re.split(r'[；;。]', lim):
        if token in seg:
            return any(d in seg for d in DUTY_CONTEXT)
    return False

def paired_quote_spans(s):
    """返回被成对引号包裹的区间列表（支持「」『』“” 与 "" ）"""
    spans = []
    stack = []
    opens = {'「': '」', '『': '』', '“': '”', '"': '"'}
    for i, ch in enumerate(s):
        if ch in opens:
            stack.append((ch, i))
        elif stack and ch == opens[stack[-1][0]]:
            _, j = stack.pop()
            spans.append((j, i))
    return spans

def inside_spans(i, spans):
    return any(a <= i <= b for a, b in spans)

def stmt_uses_hedged(stmt, token, window=45):
    k = key(token)
    if not k:
        return (False, None, '')
    ks = key(stmt)
    idx = ks.find(k)
    if idx < 0:
        return (False, None, '')
    seg = ks[max(0, idx - window):idx + len(k) + window]
    hedged = any(w in seg for w in HEDGE_WORDS)
    raw_i = stmt.find(token)
    if raw_i < 0 and len(token) >= 4:
        raw_i = stmt.find(token[:4])
    ctx = stmt[max(0, raw_i - 40):raw_i + 60] if raw_i >= 0 else '(原文未能定位)'
    return (True, hedged, ctx)

def check_C1(row):
    hits = []
    for t in downgraded_tokens(row['limitations']):
        if is_duty_sentence(row['limitations'], t):
            continue          # 引用义务类：不要求在正文带限定
        used, hedged, ctx = stmt_uses_hedged(row['statement'], t)
        if used and not hedged:
            hits.append((t, ctx))
    return hits

def check_C2(row):
    """[已证] 行的正文若用推断类词作为**自身断言**（不在成对引号内、且非否定式），报出。"""
    if row['grade'] != '[已证]':
        return []
    st = row['statement']
    spans = paired_quote_spans(st)
    bad = []
    for w in ('推断', '推测', '疑似'):
        for m in re.finditer(w, st):
            i = m.start()
            if inside_spans(i, spans):
                continue
            # 括注式豁免：紧邻「静态推断/中等偏强」等显式强度标注
            ctx = st[max(0, i - 30):i + 30]
            if re.search(r'(静态|中等|偏强|偏弱|待裁|推断强度)', ctx):
                continue
            # 否定式豁免（含「不再是 / 不是 / 不再」这类此前漏掉的形式）
            if re.search(r'(不再是|不是|不再|不得|不能|非|不作|不构成|视为|降级为|改为|升级为)\s*' + w, ctx):
                continue
            if re.search(w + r'\s*(措辞)?\s*(?:已|经)[^。；]{0,10}证实', ctx):
                continue
            bad.append((w, ctx))
            break
    return bad

ANCHOR_TAIL = None
def strip_anchor(item):
    """D1 修正：括号按深度配对，从尾部向前找配对的左括号。"""
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

def check_C3(row):
    """返回 (地址缺失列表, 解析失败锚列表)。D2：解析失败单独返回，不转成地址缺失。"""
    pool, unresolved = [], []
    for it in split_items(row['evidence_paths']):
        f, _anchor = strip_anchor(it)
        ap = os.path.join(ROOT, f.replace('\\', '/'))
        if os.path.isfile(ap):
            pool.append(io.open(ap, encoding='utf-8', errors='replace').read().lower())
        else:
            unresolved.append(f)
    if unresolved:
        return ([], unresolved)          # fail-closed：锚都解析不了，就不对地址下结论
    blob = '\n'.join(pool)
    miss = []
    for m in re.finditer(r'0x([0-9A-Fa-f]{4,8})', row['statement']):
        hx = m.group(1).lower()
        cands = {hx, hx.lstrip('0'), hx.zfill(8), hx.zfill(6), str(int(hx, 16))}
        if not any(c in blob for c in cands):
            miss.append('0x' + m.group(1))
    return (sorted(set(miss)), [])

# ---------------- 判别力自证 ----------------
V510 = os.path.join(R14, 'R17_R65_FACTINDEX_V510', 'FACT_INDEX.tsv')
V513 = os.path.join(R14, 'R17_R69_FACTINDEX_V513', 'FACT_INDEX.tsv')
v510 = {r['fact_id']: r for r in load(V510)}
v513 = {r['fact_id']: r for r in load(V513)}

print('=== 判别力自证 ===')
p1, p2 = check_C1(v510['F24']), check_C1(v510['F29'])
n1, n2 = check_C1(v513['F24']), check_C1(v513['F29'])
print('  C1 正控 v5.10 F24 = %d %s' % (len(p1), [x[0] for x in p1]))
print('  C1 正控 v5.10 F29 = %d %s' % (len(p2), [x[0] for x in p2]))
print('  C1 反控 v5.13 F24 = %d (应 0)' % len(n1))
print('  C1 反控 v5.13 F29 = %d (应 0)' % len(n2))

# D4：C2 正控 —— 构造一条「[已证] 正文用推断词当断言」的行
fake = {'grade': '[已证]', 'statement': '该函数是构造器（推断）。', 'limitations': '—',
        'fact_id': 'FAKE', 'evidence_paths': ''}
c2pos = check_C2(fake)
# C2 反控 —— 同一个词但放进成对引号 / 带显式强度标注
fake_ok1 = dict(fake, statement='该函数性质记为「推断」。')
fake_ok2 = dict(fake, statement='语义疑似占格 helper（静态推断/中等偏强）。')
c2neg1, c2neg2 = check_C2(fake_ok1), check_C2(fake_ok2)
print('  C2 正控(裸断言) = %d (应 >0) ; 反控(引号内) = %d (应 0) ; 反控(强度标注) = %d (应 0)'
      % (len(c2pos), len(c2neg1), len(c2neg2)))

ok = (len(p1) > 0 and len(p2) > 0 and len(n1) == 0 and len(n2) == 0
      and len(c2pos) > 0 and len(c2neg1) == 0 and len(c2neg2) == 0)
print('  判别力 =', 'PASS' if ok else 'FAIL —— 后续结论作废')
if not ok:
    sys.exit(2)

# ---------------- 正式跑 v5.13 ----------------
rows = load(V513)
buf = ['# R37 Check C v2 · 列间一致性（修 D1–D4 后）\n',
       '判别力自证：C1 正控 2/2 命中、反控 0/2 误报；C2 正控命中、反控 0/2 误报 ⇒ **PASS**\n']
c1 = c2 = c3 = c3u = 0
for r in rows:
    h1, h2 = check_C1(r), check_C2(r)
    miss, unresolved = check_C3(r)
    if not (h1 or h2 or miss or unresolved):
        continue
    buf.append('## %s [%s]' % (r['fact_id'], r['grade']))
    if h1:
        c1 += 1
        for t, ctx in h1:
            buf.append('- **C1** token `%s` 被 limitations 降级，正文未带限定：…%s…' % (t, ctx))
    if h2:
        c2 += 1
        buf.append('- **C2** %s' % '; '.join('%s @…%s…' % (w, c) for w, c in h2))
    if unresolved:
        c3u += 1
        buf.append('- **C3-锚不可解析（fail-closed，未对地址下结论）**：%s' % unresolved)
    if miss:
        c3 += 1
        buf.append('- **C3 地址不可追溯**：%s' % ' '.join(miss))
    buf.append('')

buf.insert(2, '命中：C1=%d / C2=%d / C3地址=%d / C3锚不可解析=%d\n' % (c1, c2, c3, c3u))
out = os.path.join(R14, '_r37', 'checkC2_report.md')
io.open(out, 'w', encoding='utf-8').write('\n'.join(buf))
print()
print('C1=%d C2=%d C3地址=%d C3锚不可解析=%d' % (c1, c2, c3, c3u))
print('wrote', out)
