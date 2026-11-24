# -*- coding: utf-8 -*-
"""R37 Check C · 列间一致性（可机械判的那部分）

C1 · 降级声明 vs statement 用法
     limitations 说「X 属推断措辞 / 单源归因 / 行动裁决 / 不随数字一并作已证 / 不入本条证据 / 未经字节证实」，
     而 statement 用到 X 时是否带限定语。
C2 · grade 与 statement 措辞强度
     [已证] 条的 statement 是否把「推断类词」当自己的断言用（而非引用别人的规则）。
C3 · statement 里的地址是否在其任一锚内出现过（可追溯性）

判别力自证（§2.8 A）：
   正控 = v5.10 的 F24/F29（本轮之前未修的原始文本），C1 必须报出；
   反控 = v5.12 的 F24/F29（已修），C1 必须不报。
   若正控不报或反控误报 ⇒ 本检查器不可信，其结论作废。
"""
import io, os, re, sys

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')

def load(p):
    raw = io.open(p, encoding='utf-8', newline='').read()
    lines = raw.split('\n')
    h = lines[0].split('\t')
    return [dict(zip(h, l.split('\t'))) for l in lines[1:] if l.strip()]

V510 = os.path.join(R14, 'R17_R65_FACTINDEX_V510', 'FACT_INDEX.tsv')
V512 = os.path.join(R14, 'R17_R67_FACTINDEX_V512', 'FACT_INDEX.tsv')

# ---------- 归一化（去标点与空白，便于跨列比对同一短语）----------
def key(s):
    return re.sub(r'[\s，。；、「」『』（）()·`*_"\'：:；;,.!?！？\-—]+', '', s)

HEDGE_WORDS = ['推断', '未证', '未经', '存疑', '不能排除', '疑似', '待裁', '待核', '不构成', '不得当']

# limitations 里的「降级声明」句式 → 抽出被降级的短语
DOWNGRADE_PATTERNS = [
    r'[「『]([^」』]{2,40})[」』]\s*(?:是|属)[^。；]{0,20}(?:推断措辞|单源归因|行动裁决|推断)',
    r'[「『]([^」』]{2,40})[」』][^。；]{0,40}(?:不随数字一并作已证|不入本条证据|未经字节证实|未经[^。；]{0,4}证实)',
    r'不得写成[「『]?([^，。；」』]{2,30})',
    r'[「『]([^」』]{2,40})[」』][^。；]{0,20}不得当[^。；]{0,10}用',
]

def downgraded_tokens(lim):
    out = []
    for pat in DOWNGRADE_PATTERNS:
        for m in re.finditer(pat, lim):
            t = m.group(1).strip()
            if len(t) >= 2:
                out.append(t)
    return sorted(set(out))

def stmt_uses_hedged(stmt, token, window=45):
    """statement 里出现 token 时，其邻近窗口是否含限定语。返回 (出现?, 是否带限定, 上下文)"""
    k = key(token)
    if not k:
        return (False, None, '')
    ks = key(stmt)
    idx = ks.find(k)
    if idx < 0:
        return (False, None, '')
    # 在归一化串上取窗口，再回原串做一个粗定位（只用于展示）
    seg = ks[max(0, idx - window):idx + len(k) + window]
    hedged = any(w in seg for w in HEDGE_WORDS)
    # 原文上下文（用原文找 token 的松散定位）
    raw_i = stmt.find(token)
    if raw_i < 0:
        # token 带标点差异，退化为按首个 4 字前缀找
        raw_i = stmt.find(token[:4]) if len(token) >= 4 else -1
    ctx = stmt[max(0, raw_i - 40):raw_i + 60] if raw_i >= 0 else '(原文未能定位)'
    return (True, hedged, ctx)

def check_C1(row):
    hits = []
    for t in downgraded_tokens(row['limitations']):
        used, hedged, ctx = stmt_uses_hedged(row['statement'], t)
        if used and not hedged:
            hits.append((t, ctx))
    return hits

def check_C2(row):
    """[已证] 的 statement 是否把推断词当自身断言。粗判：出现推断词且不在「引号/规则名」上下文。"""
    if row['grade'] != '[已证]':
        return []
    bad = []
    for w in ('推断', '推测', '疑似', '可能'):
        for m in re.finditer(w, row['statement']):
            i = m.start()
            ctx = row['statement'][max(0, i - 25):i + 25]
            # 若处在被引号/书名号包裹，或紧邻「不得/不能/非」等否定，视为合规
            if any(c in ctx for c in '「」『』“”'):
                continue
            if re.search(r'(不得|不能|非|不作|不构成|视为|降级为)' + w, ctx) or re.search(w + r'(强度|类词)', ctx):
                continue
            bad.append((w, ctx))
            break
    return bad

def check_C3(row):
    """statement 里的 8 位/带 0x 地址，是否在其任一锚文件里出现过。"""
    paths = []
    for it in row['evidence_paths'].split(';'):
        it = it.strip()
        if not it:
            continue
        f = re.sub(r'\([^()]*\)$', '', it).strip()
        paths.append(f)
    pool = []
    for f in paths:
        p = os.path.join(ROOT, f.replace('\\', '/'))
        if os.path.isfile(p):
            try:
                pool.append(io.open(p, encoding='utf-8', errors='replace').read().lower())
            except Exception:
                pass
    blob = '\n'.join(pool)
    miss = []
    for m in re.finditer(r'0x([0-9A-Fa-f]{4,8})', row['statement']):
        hexs = m.group(1).lower()
        # 接受带前导零/不带前导零两种写法
        cands = {hexs, hexs.lstrip('0'), hexs.zfill(8), hexs.zfill(6)}
        # 修：锚里的表常以**十进制**记值（如 lead_byte_checks.tsv 的 va=7839744），必须同时认十进制
        try:
            dec = str(int(hexs, 16))
            cands.add(dec)
        except ValueError:
            pass
        if not any(c in blob for c in cands):
            miss.append('0x' + m.group(1))
    return sorted(set(miss))

# ---------- 判别力自证 ----------
print('=== 判别力自证 ===')
v510 = {r['fact_id']: r for r in load(V510)}
v512 = {r['fact_id']: r for r in load(V512)}

p1 = check_C1(v510['F24']); p2 = check_C1(v510['F29'])
n1 = check_C1(v512['F24']); n2 = check_C1(v512['F29'])
print('  正控 v5.10 F24 C1 命中 = %d %s' % (len(p1), [x[0] for x in p1]))
print('  正控 v5.10 F29 C1 命中 = %d %s' % (len(p2), [x[0] for x in p2]))
print('  反控 v5.12 F24 C1 命中 = %d %s (应为 0)' % (len(n1), [x[0] for x in n1]))
print('  反控 v5.12 F29 C1 命中 = %d %s (应为 0)' % (len(n2), [x[0] for x in n2]))
ok = (len(p1) > 0 and len(p2) > 0 and len(n1) == 0 and len(n2) == 0)
print('  判别力 =', 'PASS' if ok else 'FAIL —— 检查器不可信，后续结论作废')
if not ok:
    sys.exit(2)

# ---------- 正式跑 v5.12 ----------
rows = load(V512)
buf = ['# R37 Check C · 列间一致性（可机械判的部分）\n',
       '判别力自证：正控 v5.10 `F24`/`F29` 各命中、反控 v5.12 `F24`/`F29` 各 0 命中 ⇒ **PASS**\n']
c1 = c2 = c3 = 0
for r in rows:
    h1 = check_C1(r); h2 = check_C2(r); h3 = check_C3(r)
    if not (h1 or h2 or h3):
        continue
    buf.append('## %s [%s]' % (r['fact_id'], r['grade']))
    if h1:
        c1 += 1
        buf.append('- **C1 降级声明 vs 正文用法**')
        for t, ctx in h1:
            buf.append('  - token `%s` 在 limitations 被降级，正文未带限定：…%s…' % (t, ctx))
    if h2:
        c2 += 1
        buf.append('- **C2 grade 与措辞强度**：%s' % '; '.join('%s @…%s…' % (w, c) for w, c in h2))
    if h3:
        c3 += 1
        buf.append('- **C3 地址不可追溯**（其锚内均未出现）：%s' % ' '.join(h3))
    buf.append('')

buf.insert(2, '命中行数：C1=%d / C2=%d / C3=%d\n' % (c1, c2, c3))
out = os.path.join(R14, '_r37', 'checkC_report.md')
io.open(out, 'w', encoding='utf-8').write('\n'.join(buf))
print()
print('C1 rows = %d ; C2 rows = %d ; C3 rows = %d' % (c1, c2, c3))
print('wrote', out)
