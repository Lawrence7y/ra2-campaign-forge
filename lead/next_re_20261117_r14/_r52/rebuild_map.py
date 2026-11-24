import io, os, re, csv
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
RC = os.path.join(R14, 'R14_COMMON.md')
MAP = os.path.join(R14, 'DISC_NS_MAP.tsv')
CARDS = os.path.join(R14, 'R14_CARDS.md')

lines = io.open(RC, encoding='utf-8', newline='').read().split('\n')

# --- §6 的 21 条 ---
s6 = next(i for i, l in enumerate(lines) if re.match(r'^##\s*6\s*[\u00b7\.]', l))
end = next((i for i in range(s6 + 1, len(lines)) if re.match(r'^##\s', lines[i])), len(lines))
S6 = {}
for i in range(s6 + 1, end):
    m = re.match(r'^(\d+)\.\s*\*\*(.+?)\*\*', lines[i].strip())
    if m: S6[int(m.group(1))] = m.group(2)

# --- 派卡文通用尾部的 9 条 ---
C7 = {}
if os.path.isfile(CARDS):
    cl = io.open(CARDS, encoding='utf-8', newline='').read().split('\n')
    inblk = False
    for l in cl:
        if l.strip().startswith('```'): inblk = not inblk; continue
        if inblk:
            m = re.match(r'^(\d+)\s+(.+)$', l.strip())
            if m: C7[int(m.group(1))] = m.group(2)

def clean(s): return re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', s)
def lcs_ratio(a, b):
    a, b = clean(a), clean(b)
    if not a or not b: return 0.0
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if ca == cb else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1] / len(a)

# 每处提及的「主题片段」（人工从上下文取，已核对）
TOPIC = {
 '68': '每帧迷雾更新总入口 判定错源',
 '467': 'RTTI 读取失败仍继续归类 fail-closed 被违反',
 '520a': '只查一种等价形式 违等价形式检查',
 '520b': '拒绝编名字 不凭印象 启发式',
 '645': '写值逐字符核对',
 '663': '写值逐字符核对',
 '1010': '§6 纪律 19 条原文（数量修饰）',
}

LOOSE = re.compile(r'\u7eaa\u5f8b\s*(\d+)')
cur = None
sec_of = []
for l in lines:
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    sec_of.append(cur)
def in_mine(s):
    try: return bool(s) and s.startswith('2.') and float(s.split('.')[1]) >= 14
    except Exception: return False

raw_hits = []
for i, l in enumerate(lines):
    if in_mine(sec_of[i]): continue
    for m in LOOSE.finditer(l):
        raw_hits.append((i + 1, sec_of[i] or '?', int(m.group(1)), l.strip()))

print('raw cross-namespace hits =', len(raw_hits))

rows_out = []
for idx, (ln, sec, n, txt) in enumerate(raw_hits):
    key = str(ln) if not (ln == 520 and idx > 0) else '520b'
    if ln == 520:
        key = '520a' if '18' == str(n) else '520b'
    topic = TOPIC.get(key, '')
    # L1010 假阳性判定：出现「19 条」这种数量修饰
    if re.search(r'\u7eaa\u5f8b\s*19\s*\u6761', txt):
        rows_out.append([str(ln), sec, str(n), S6.get(n, '')[:44], topic,
                         'EXCLUDE', '数量修饰（「纪律19条」=条数，非第19号）⇒ 假阳性，不入映射',
                         txt[:80]])
        continue
    best_s6 = max(S6.items(), key=lambda kv: lcs_ratio(topic, kv[1])) if topic else (None, 0)
    best_c7 = max(C7.items(), key=lambda kv: lcs_ratio(topic, kv[1])) if (topic and C7) else (None, 0)
    c7n, c7r = best_c7
    s6n, s6r = best_s6
    concl = []
    if c7n and c7r >= 0.7:
        concl.append('派卡[%d] LCS=%.2f' % (c7n, c7r))
    if s6n and s6r >= 0.7:
        concl.append('s6[%d] LCS=%.2f' % (s6n, s6r))
    verdict = '; '.join(concl) if concl else 'UNRESOLVED(LCS<0.7)'
    rows_out.append([str(ln), sec, str(n), S6.get(n, '')[:44], topic, 'INCLUDE', verdict, txt[:80]])

HDR = ['行号', '所在节', '出现编号', '§6 该号纪律', '主题片段（人工取）', '是否计入映射', 'LCS 匹配结论', '原文片段']
tmp = MAP + '.tmp'
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(HDR)
    for r in rows_out:
        w.writerow(r)
back = [l for l in io.open(tmp, encoding='utf-8', newline='').read().split('\n') if l]
for l in back:
    assert l.count('\t') == len(HDR) - 1, l.count('\t')
os.replace(tmp, MAP)

print()
for r in rows_out:
    print('L%-6s n=%-3s %-9s %s' % (r[0], r[2], r[5], r[6][:62]))
included = sum(1 for r in rows_out if r[5] == 'INCLUDE')
print()
print('§6 条数=%d ; 派卡条数=%d ; 总提及=%d ; 计入映射=%d ; 剔除假阳性=%d'
      % (len(S6), len(C7), len(rows_out), included, len(rows_out) - included))
print('wrote', MAP, os.path.getsize(MAP), 'B')
