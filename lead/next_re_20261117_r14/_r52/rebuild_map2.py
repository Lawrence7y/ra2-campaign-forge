import io, os, re, csv
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
RC = os.path.join(R14, 'R14_COMMON.md')
MAP = os.path.join(R14, 'DISC_NS_MAP.tsv')
CARDS = os.path.join(R14, 'R14_CARDS.md')

lines = io.open(RC, encoding='utf-8', newline='').read().split('\n')
s6 = next(i for i, l in enumerate(lines) if re.match(r'^##\s*6\s*[\u00b7\.]', l))
end = next((i for i in range(s6 + 1, len(lines)) if re.match(r'^##\s', lines[i])), len(lines))
S6 = {}
for i in range(s6 + 1, end):
    m = re.match(r'^(\d+)\.\s*\*\*(.+?)\*\*', lines[i].strip())
    if m: S6[int(m.group(1))] = m.group(2)

C7 = {}
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

def best(table, topic):
    """返回 (编号, 比率)；空表返回 (None, 0.0)。"""
    if not table or not topic: return None, 0.0
    scored = [(k, lcs_ratio(topic, v)) for k, v in table.items()]
    k, r = max(scored, key=lambda x: x[1])
    return k, r

TOPIC = {
 (68, 1): '每帧迷雾更新总入口 判定错源',
 (467, 2): 'RTTI 读取失败仍继续归类 fail closed 被违反',
 (520, 18): '只查一种等价形式 违等价形式检查',
 (520, 8): '拒绝编名字 不凭印象 启发式',
 (645, 7): '写值逐字符核对',
 (663, 7): '写值逐字符核对',
 (1010, 19): '§6 纪律 19 条原文（数量修饰）',
}

LOOSE = re.compile(r'\u7eaa\u5f8b\s*(\d+)')
cur = None; sec_of = []
for l in lines:
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    sec_of.append(cur)
def in_mine(s):
    try: return bool(s) and s.startswith('2.') and float(s.split('.')[1]) >= 14
    except Exception: return False

hits = []
for i, l in enumerate(lines):
    if in_mine(sec_of[i]): continue
    for m in LOOSE.finditer(l):
        hits.append((i + 1, sec_of[i] or '?', int(m.group(1)), l.strip()))

print('raw hits =', len(hits))
rows_out = []
for ln, sec, n, txt in hits:
    topic = TOPIC.get((ln, n), '')
    if re.search(r'\u7eaa\u5f8b\s*19\s*\u6761', txt):
        rows_out.append([str(ln), sec, str(n), S6.get(n, '')[:44], topic, 'EXCLUDE',
                         '数量修饰（「纪律19条」=条数，非第19号）⇒ 解析假阳性，不入映射', txt[:80]])
        continue
    c7k, c7r = best(C7, topic)
    s6k, s6r = best(S6, topic)
    parts = []
    if c7r >= 0.7: parts.append('派卡[%d] LCS=%.2f' % (c7k, c7r))
    if s6r >= 0.7: parts.append('s6[%d] LCS=%.2f' % (s6k, s6r))
    verdict = '; '.join(parts) if parts else 'UNRESOLVED(LCS<0.7)'
    rows_out.append([str(ln), sec, str(n), S6.get(n, '')[:44], topic, 'INCLUDE', verdict, txt[:80]])

HDR = ['行号', '所在节', '出现编号', '§6 该号纪律', '主题片段（人工取）', '是否计入映射', 'LCS 匹配结论', '原文片段']
tmp = MAP + '.tmp'
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(HDR)
    for r in rows_out: w.writerow(r)
back = [l for l in io.open(tmp, encoding='utf-8', newline='').read().split('\n') if l]
for l in back: assert l.count('\t') == len(HDR) - 1
os.replace(tmp, MAP)

print()
for r in rows_out:
    print('L%-6s n=%-3s %-9s %s' % (r[0], r[2], r[5], r[6][:66]))
inc = sum(1 for r in rows_out if r[5] == 'INCLUDE')
print()
print('§6=%d 条 ; 派卡=%d 条 ; 提及=%d ; 计入=%d ; 剔除假阳性=%d' % (len(S6), len(C7), len(rows_out), inc, len(rows_out) - inc))
print('wrote', MAP, os.path.getsize(MAP), 'B')
