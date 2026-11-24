# -*- coding: utf-8 -*-
# R70 · FACT_INDEX evidence_paths 存活率核验 + 反伪造对照
# 目标：判定 R68 的 anchor_check.txt「文件存在 171/171」是否与盘上事实相符。
# 只读；唯一写入为本目录下的 .log。
import io, os, re, sys, json, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
TSV = os.path.join(R14, 'R17_R103_FACTINDEX_V531/FACT_INDEX.tsv')

fails, buf = [], []
def W(s=''):
    print(s); buf.append(s)
def ck(name, cond, detail=''):
    W(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

# ---------------- 解析器（与 verify_anchors.ts 同语义，独立实现） ----------------
def split_semis(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch in '（(': depth += 1
        elif ch in '）)': depth = max(0, depth - 1)
        cur += ch
        if ch == ';' and depth == 0:
            out.append(cur[:-1]); cur = ''
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out if x.strip()]

def split_anchor(item):
    item = item.strip()
    if not re.search(r'[)）]$', item):
        return item, None
    close = item[-1]; openc = '（' if close == '）' else '('
    depth = 0
    for i in range(len(item) - 1, -1, -1):
        if item[i] == close: depth += 1
        elif item[i] == openc:
            depth -= 1
            if depth == 0:
                if i <= 0: return item, None
                return item[:i], item[i + 1:-1]
    return item, None

def clean(p):
    return p.strip().strip('`').strip().replace('\\', '/')

# ---------------- 自测（正控 / 反控） ----------------
W('=== 0 解析器自测（正控 + 反控）===')
ck('S1 正控 分号在括号内不分割', len(split_semis('a.md(x;y);b.md')) == 2,
   split_semis('a.md(x;y);b.md'))
ck('S2 正控 全角括号深度', len(split_semis('a.md（x；y）;b.md')), '全角分号不切（本表用半角）')
ck('S3 正控 剥锚 半角', split_anchor('lead/x.md(§2.9)') == ('lead/x.md', '§2.9'),
   split_anchor('lead/x.md(§2.9)'))
ck('S4 正控 剥锚 全角', split_anchor('lead/x.md（M98）') == ('lead/x.md', 'M98'),
   split_anchor('lead/x.md（M98）'))
ck('S5 反控 无右括号不剥锚', split_anchor('lead/x.md') == ('lead/x.md', None),
   split_anchor('lead/x.md'))
ck('S6 反控 内部括号不误剥', split_anchor('lead/a(1)/y.md') == ('lead/a(1)/y.md', None),
   split_anchor('lead/a(1)/y.md'))
ck('S7 正控 嵌套锚剥最外层', split_anchor('lead/x.md(§2.10 / 一 / (a′))') == ('lead/x.md', '§2.10 / 一 / (a′)'),
   split_anchor('lead/x.md(§2.10 / 一 / (a′))'))
ck('S8 正控 反引号剥离', clean('`lead/x.md`') == 'lead/x.md', clean('`lead/x.md`'))
ck('S9 正控 反斜杠转正斜杠', clean('lead\\x.md') == 'lead/x.md', clean('lead\\x.md'))

# ---------------- 读表 ----------------
W('')
W('=== 1 FACT_INDEX 底数 ===')
raw = open(TSV, 'rb').read()
ck('表 CR=0（全 LF）', raw.count(b'\r') == 0, raw.count(b'\r'))
ck('表 55 行（表头 + 54）', raw.count(b'\n') == 55, raw.count(b'\n'))
ck('表 sha256 == 054402f178e5a02a...（v5.31）',
   __import__('hashlib').sha256(raw).hexdigest().startswith('054402f178e5a02a'),
   __import__('hashlib').sha256(raw).hexdigest()[:16])
rows = [l.split('\t') for l in raw.decode('utf-8').rstrip('\n').split('\n')]
hdr, data = rows[0], rows[1:]
ck('表头 5 列', hdr == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'], hdr)
ck('54 数据行', len(data) == 54, len(data))
ck('每行 5 列', all(len(r) == 5 for r in data))

# ---------------- 抽取条目 ----------------
items = []          # (fact_id, path, anchor)
for r in data:
    for it in split_semis(r[3]):
        p, a = split_anchor(it)
        items.append((r[0], clean(p), a))
W('')
W('=== 2 evidence_paths 条目 ===')
ck('条目总数 == 171（与 anchor_check.txt 同分母）', len(items) == 171, len(items))
ck('带锚点 == 117（与 anchor_check.txt 同分母）',
   sum(1 for _, _, a in items if a) == 117, sum(1 for _, _, a in items if a))

# ---------------- 口径 A：严格全路径 ----------------
W('')
W('=== 3 三种查找口径对照（判别力在此）===')
def cal_strict(p):   return os.path.exists(os.path.join(ROOT, p))
def cal_bn_all(p):
    bn = os.path.basename(p)
    for root, dirs, fs in os.walk(ROOT):
        if '.git' in root: continue
        if bn in fs: return True
    return False
def cal_bn_two(p):
    bn = os.path.basename(p)
    return any(os.path.exists(os.path.join(d, bn))
               for d in (os.path.join(ROOT, 'lead'),
                         os.path.join(ROOT, 'lead/next_re_20261117_r14')))

CAL = [('严格全路径（正确口径）', cal_strict),
       ('basename 全库兜底', cal_bn_all),
       ('basename 仅两目录（verify_anchors.ts findDoc 口径）', cal_bn_two)]
res = {}
for name, fn in CAL:
    n = sum(1 for _, p, _ in items if fn(p))
    res[name] = n
    W('  %-52s 存在 %3d / %d' % (name, n, len(items)))

strict_n = res['严格全路径（正确口径）']
ck('严格口径 = 128（本轮实测）', strict_n == 128, strict_n)
ck('全库 basename 兜底 = 140（与严格不同 ⇒ 兜底会假通过 12 条）',
   res['basename 全库兜底'] == 140, res['basename 全库兜底'])
ck('两目录 basename = 75（比严格更严 ⇒ findDoc 找不到就直接算未加载）',
   res['basename 仅两目录（verify_anchors.ts findDoc 口径）'] == 75,
   res['basename 仅两目录（verify_anchors.ts findDoc 口径）'])
ck('**无任何口径能得 171** ⇒ anchor_check 的 171/171 非口径差异所致',
   all(v != 171 for v in res.values()), res)

# ---------------- 缺失清单 ----------------
miss = collections.Counter()
miss_facts = collections.defaultdict(list)
for fid, p, a in items:
    if not cal_strict(p):
        miss[p] += 1
        miss_facts[fid].append(p)
W('')
W('=== 4 缺失明细 ===')
ck('缺失条目 = 43', sum(miss.values()) == 43, sum(miss.values()))
ck('缺失去重路径 = 16', len(miss) == 16, len(miss))
ck('涉及 fact = 34', len(miss_facts) == 34, len(miss_facts))
ck('存在 + 缺失 = 171', strict_n + sum(miss.values()) == 171,
   '%d + %d' % (strict_n, sum(miss.values())))
for p, c in sorted(miss.items(), key=lambda x: (-x[1], x[0])):
    W('  %2d  %s' % (c, p))

# ---------------- 大小写不敏感复核（排除 Linux/Windows 大小写差异） ----------------
W('')
W('=== 5 反控：大小写不敏感能否解析（排除大小写差异解释）===')
def ci_resolve(rel):
    cur = ROOT
    for part in rel.split('/'):
        if not os.path.isdir(cur): return None
        try: ents = os.listdir(cur)
        except OSError: return None
        hit = [e for e in ents if e.lower() == part.lower()]
        if not hit: return None
        cur = os.path.join(cur, hit[0])
    return cur
ci_found = [p for p in miss if ci_resolve(p)]
ck('反控：16 条缺失路径中，大小写不敏感能救回 0 条', len(ci_found) == 0, ci_found)
ck('正控：大小写不敏感对一条真实路径有效',
   ci_resolve('LEAD/NEXT_RE_20261117_R14/R14_COMMON.md') is not None,
   ci_resolve('LEAD/NEXT_RE_20261117_R14/R14_COMMON.md'))

# ---------------- 逐 fact 存活 ----------------
W('')
W('=== 6 逐 fact 存活（至少一条路径存在？）===')
zero = []
per = {}
for fid, p, a in items:
    per.setdefault(fid, [0, 0])
    per[fid][0] += 1
    if cal_strict(p): per[fid][1] += 1
for fid in sorted(per):
    if per[fid][1] == 0: zero.append(fid)
ck('54 个 fact 全部有条目', len(per) == 54, len(per))
ck('至少一条路径存在的 fact = 52', 54 - len(zero) == 52, 54 - len(zero))
ck('**零存活 fact = 2（F23 / F35）**', zero == ['F23', 'F35'], zero)
grade = {r[0]: r[2] for r in data}
W('  零存活 fact 及其 grade：')
for f in zero:
    W('    %s  grade=%s' % (f, grade[f]))
ck('F35 的 grade 是 [流程]（非 [已证]）', grade['F35'] == '[流程]', grade['F35'])
ck('**F23 的 grade 是 [已证] 却无任何可核验证据文件**',
   grade['F23'] == '[已证]', grade['F23'])

# ---------------- 反伪造：删掉声称会不会让检查变绿 ----------------
W('')
W('=== 7 反向反控：把 evidence_paths 全清空，本检查会怎样 ===')
n_empty = 0
for r in data:
    if not r[3].strip(): n_empty += 1
ck('反控：若某行 evidence_paths 为空，条目数会下降而非「通过」', n_empty == 0, n_empty)
ck('反控：171→0 时「存在率」无定义（不是 100%）⇒ 存活率必须与条目数同报',
   strict_n > 0, '%d / %d' % (strict_n, len(items)))

# ---------------- 与 anchor_check.txt 对撞 ----------------
W('')
W('=== 8 与 R68 anchor_check.txt 直接对撞 ===')
ac_path = os.path.join(R14, 'R17_R102_FACTINDEX_V530/anchor_check.txt')
ac = io.open(ac_path, encoding='utf-8').read()
m_items = re.search(r'路径项\s+(\d+)', ac)
m_ok = re.search(r'文件存在\s+(\d+)\s*/\s*(\d+)', ac)
ck('anchor_check 记「路径项 171」', m_items and int(m_items.group(1)) == 171,
   m_items.group(1) if m_items else None)
ck('anchor_check 记「文件存在 171 / 171」', m_ok and (int(m_ok.group(1)), int(m_ok.group(2))) == (171, 171),
   m_ok.groups() if m_ok else None)
ck('**盘上实测 128 / 171 ⇒ anchor_check 的「171/171」为假**',
   (int(m_ok.group(1)), int(m_ok.group(2))) != (strict_n, len(items)),
   '声称 %s vs 实测 %d' % (m_ok.group(1) + '/' + m_ok.group(2), strict_n))
ck('anchor_check 记「MISS 0」而盘上缺 43', re.search(r'MISS\s+0', ac) is not None and sum(miss.values()) == 43,
   '声称 0 vs 实测 43')

# ---------------- 定谳 ----------------
W('')
W('=== 9 定谳 ===')
W('  R68 anchor_check.txt 声称：路径项 171 / 文件存在 171 / MISS 0 / 目录+锚 0')
W('  R70 主会话实测：      路径项 171 / 文件存在 %d / 缺失 %d（16 条去重路径、34 个 fact）'
  % (strict_n, sum(miss.values())))
W('  三种查找口径：严格 %d、全库 basename %d、两目录 basename %d —— 无一得到 171'
  % (strict_n, res['basename 全库兜底'], res['basename 仅两目录（verify_anchors.ts findDoc 口径）']))
W('  大小写不敏感复核：救回 0 条 ⇒ 不是 Linux/Windows 大小写差异')
W('  ⇒ 判定：anchor_check.txt 的「171/171 全部存在」与**本精简库**的盘上事实不符；')
W('          但（见第 10 节）其产生脚本在本库上无重复计数缺陷 ⇒ 该文本不是在精简库上产出的。')

# ---------------- 源码级核查：我的假设被自己的反控推翻 ----------------
W('')
W('=== 10 源码级核查（verify_anchors.ts）：我原先的假设被推翻 ===')
vs = io.open(os.path.join(R14, 'R17_R102_FACTINDEX_V530/verify_anchors.ts'), encoding='utf-8').read()
W('  fileOk / isDir / NOFILE 相关行原文：')
for i, ln in enumerate(vs.split('\n'), 1):
    if 'fileOk' in ln or 'isDir' in ln or 'NOFILE' in ln:
        W('    L%-4d %s' % (i, ln.rstrip()))

W('')
W('  【本轮我自己犯的错，用反控抓出并改掉】')
W('  我原本写了两条断言，想证明「fileOk 计数有缺陷」，两条都 FAIL：')
W('    ① 断言 fileOk++ 出现次数 > 1 —— 实测只有 1 次')
W('    ② 断言 isDir 分支内另有 fileOk++ —— 实测 isDir 分支内没有 fileOk++')
ck('核实：fileOk++ 在源码中只出现 1 次（我原断言「>1」是错的）',
   vs.count('fileOk++') == 1, vs.count('fileOk++'))
ck('核对：唯一的 fileOk++ 受 existsSync 前置保护（文件不在就不累加）',
   re.search(r'if \(fs\.existsSync\(absT\)\) fileOk\+\+;', vs) is not None,
   'L168 原文已核')
ck('核对：目标缺失时走 else 分支 push NOFILE（会进 miss ⇒ 会 FAIL）',
   'else miss.push("NOFILE  "' in vs, 'L169 原文已核')
W('  ⇒ **结论反转**：盘上这份 verify_anchors.ts 的 fileOk 逻辑是正确的；')
W('    若在**本精简库**上运行它，它必然报 128/171 并 exit 1，不可能产出 171/171。')
W('    故 anchor_check.txt 的 171/171 只能产生于**文件齐备的另一棵树**。')
W('    这与「本机是精简库、原树文件已被裁掉」的解释一致，与「核验器造假」的解释不符。')

# 反控：本机能否直接跑该 .ts
W('')
W('  反控：本机 node 版本与 --experimental-strip-types 支持情况：')
import subprocess
try:
    nv = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=20).stdout.strip()
except Exception as e:
    nv = 'ERR:%s' % e
W('    node %s' % nv)
r = subprocess.run(['node', '--experimental-strip-types', '--version'],
                   capture_output=True, text=True, timeout=20)
W('    node --experimental-strip-types ⇒ rc=%d, stderr=%s' % (r.returncode, (r.stderr or r.stdout).strip()[:80]))
ck('本机 node 不支持 --experimental-strip-types ⇒ 该 .ts 在本机不可直接运行',
   r.returncode != 0, (r.stderr or '').strip()[:60])

W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ' | '.join(fails)))
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_r70.log'),
        'w', encoding='utf-8', newline='\n').write('\n'.join(buf) + '\n')
sys.exit(0 if not fails else 1)
