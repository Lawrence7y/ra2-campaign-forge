# -*- coding: utf-8 -*-
"""gate_n1_lf_20261107.py — N-1 行尾关闭（路径2：按母本 LF 重新物化候选）确定性门禁。

总控会话撰写，工作流以 world.run 调用，子代理不可修改、不可放宽。

用法：
    python -I -X utf8 <abs path> pre    只核上游四件指纹
    python -I -X utf8 <abs path> post   核上游 + 全量 N-1 判定

退出码：0 = 全 PASS；1 = 有 FAIL。

本脚本只读，唯一输出是 stdout。
"""

import ast
import hashlib
import os
import sys

NL = chr(10)
CR = bytes([13])
CRLF = bytes([13, 10])
BOM = bytes([239, 187, 191])
FENCE = chr(96) * 3

MODE = sys.argv[1] if len(sys.argv) > 1 else 'post'

ROOT = 'D:/Project/ra2-campaign-forge'
MOTHER = ROOT + '/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py'
DESIGN = ROOT + '/lead/b2b_design_20261106/B2B_DESIGN.md'
PREAUDIT = ROOT + '/lead/b2b_preaudit_20261106/B2B_PREAUDIT.md'
OLDC = ROOT + '/lead/b2b_candidate_20261106/qc151_trip.candidate.py'
NEWDIR = ROOT + '/lead/b2b_candidate_lf_20261107'
NEWC = NEWDIR + '/qc151_trip.candidate_lf.py'
NEWD = NEWDIR + '/CANDIDATE_LF.diff'

M_SHA = '517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636'
D_SHA = '565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf'
P_SHA = '3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f'
O_SHA = '9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc'

M_BYTES = 399508
D_BYTES = 66735
P_BYTES = 20615
O_BYTES = 420292

# 路径2 的预测值（总控字节级实测：420292 - 7533 = 412759）
PREDICTED_NEW_BYTES = 412759
PREDICTED_NEW_LF = 7533
PREDICTED_NET_GAIN = 13251       # 412759 - 399508
PREDICTED_EOL_BYTES = 7533       # 20784 - 13251

ANCHORS = [
    ('H1', 'FRESHNESS_GROUP = "FRESHNESS"'),
    ('H2', 'backup_mtime_pre:{name}'),
    ('H3', 'def make_pre_freshness_snapshot(except_path: Path) -> dict:'),
    ('H4', 'def copy_post_except_evidence('),
    ('H5', 'pre_freshness_snapshot: dict | None = None) -> int:'),
    ('H6', 'pre_freshness_snapshot=pre_freshness_snapshot'),
    ('H7', '_pre_freshness_snapshot: dict | None = None'),
    ('H8', '_pre_freshness_snapshot = make_pre_freshness_snapshot('),
    ('H9', 'pre_freshness_snapshot=_pre_freshness_snapshot'),
]

SCAN_KEYWORDS = [
    'OpenProcess', 'ReadProcessMemory', 'SuspendThread', 'StackWalk',
    'MiniDump', 'SetWindowsHookEx', 'CreateRemoteThread', 'ctypes',
    'WriteProcessMemory', 'VirtualAllocEx',
]

fails = []


def ck(ok, label, detail=''):
    print(('PASS  ' if ok else 'FAIL  ') + label + (('  |  ' + detail) if detail else ''))
    if not ok:
        fails.append(label)


def rd(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def split_lines(b):
    """按 LF 切行；末尾单个空串丢弃（等价于 text.splitlines() 对 LF 文本的行为）。"""
    t = b.decode('utf-8')
    lines = t.split(NL)
    if lines and lines[-1] == '':
        lines = lines[:-1]
    return lines


def block_lines(content):
    ls = content.split(NL)
    if ls and ls[-1] == '':
        ls = ls[:-1]
    return ls


def parse_hdr(line):
    if not line.startswith('@@ '):
        return None
    inner = line[3:].split('@@')[0].strip()
    toks = inner.split(' ')
    if len(toks) != 2:
        return None

    def span(tok):
        sign = tok[0]
        body = tok[1:]
        if ',' in body:
            a, b = body.split(',')
            return sign, int(a), int(b)
        return sign, int(body), 1

    s1, o_start, o_count = span(toks[0])
    s2, n_start, n_count = span(toks[1])
    if s1 != '-' or s2 != '+':
        return None
    return o_start, o_count, n_start, n_count


# ---------------------------------------------------------------- 上游指纹
mb = rd(MOTHER)
db = rd(DESIGN)
pb = rd(PREAUDIT)

ck(sha(mb) == M_SHA and len(mb) == M_BYTES, 'U1 母本指纹零漂移',
   '%d B %s' % (len(mb), sha(mb)[:16]))
ck(sha(db) == D_SHA and len(db) == D_BYTES, 'U2 B2b 设计指纹零漂移',
   '%d B %s' % (len(db), sha(db)[:16]))
ck(sha(pb) == P_SHA and len(pb) == P_BYTES, 'U3 B2b 预审指纹零漂移',
   '%d B %s' % (len(pb), sha(pb)[:16]))

ob = b''
if os.path.exists(OLDC):
    ob = rd(OLDC)
    ck(sha(ob) == O_SHA and len(ob) == O_BYTES, 'U4 旧候选（CRLF 版）零漂移',
       '%d B CRLF=%d' % (len(ob), ob.count(CRLF)))
else:
    ck(False, 'U4 旧候选（CRLF 版）零漂移', '文件缺失 ' + OLDC)

if MODE == 'pre':
    print('SUMMARY_PRE fails=%d' % len(fails))
    raise SystemExit(0 if not fails else 1)

# ---------------------------------------------------------------- 新候选字节层
ck(os.path.exists(NEWC), 'N0 新候选文件存在', NEWC)
if not os.path.exists(NEWC):
    print('SUMMARY_POST fails=%d' % len(fails))
    raise SystemExit(1)

nb = rd(NEWC)
ck(nb.count(CR) == 0, 'N1 新候选零 CR 字节', 'CR=%d' % nb.count(CR))
ck(nb.count(b'\n') == PREDICTED_NEW_LF, 'N2 新候选 LF 数 == 7533',
   'LF=%d' % nb.count(b'\n'))
ck(len(nb) == PREDICTED_NEW_BYTES, 'N3 新候选字节数 == 412759（预测值）',
   '%d B %s' % (len(nb), sha(nb)[:16]))
ck(not nb.startswith(BOM), 'N4 无 UTF-8 BOM')
ck(nb.endswith(b'\n') and not nb.endswith(b'\n\n'), 'N5 文件以单个 LF 收尾',
   repr(nb[-3:]))

# ---------------------------------------------------------------- 设计 9 hunk
design_text = db.decode('utf-8')
parts = design_text.split(FENCE)
blocks = []
for p in parts:
    if p.startswith('diff' + NL):
        blocks.append(p[len('diff' + NL):])
ck(len(blocks) == 9, 'N6 设计稿解析出 9 个 diff 块', 'blocks=%d' % len(blocks))

mother_lines = split_lines(mb)
ck(len(mother_lines) == 7291, 'N7 母本按 LF 切行 == 7291', 'lines=%d' % len(mother_lines))

hunks = []
bare_empty = 0
parse_ok = True
for idx, blk in enumerate(blocks):
    bl = block_lines(blk)
    if not bl:
        ck(False, 'N8.%d 空 diff 块' % (idx + 1))
        parse_ok = False
        continue
    parsed = parse_hdr(bl[0])
    if parsed is None:
        ck(False, 'N8.%d 无法解析 hunk 头' % (idx + 1), bl[0][:60])
        parse_ok = False
        continue
    o_start, o_count, n_start, n_count = parsed
    minus_side = []
    plus_side = []
    bad_prefix = None
    for l in bl[1:]:
        if l.startswith('+++') or l.startswith('---'):
            continue
        if l.startswith(' '):
            minus_side.append(l[1:])
            plus_side.append(l[1:])
        elif l.startswith('-'):
            minus_side.append(l[1:])
        elif l.startswith('+'):
            plus_side.append(l[1:])
        elif l == '':
            bare_empty += 1
            minus_side.append('')
            plus_side.append('')
        else:
            bad_prefix = l
            break
    if bad_prefix is not None:
        ck(False, 'N8.%d 未知行前缀' % (idx + 1), repr(bad_prefix[:60]))
        parse_ok = False
        continue
    ck(len(minus_side) == o_count, 'N9.%d hunk#%d -侧行数 == 头部声明' % (idx + 1, idx + 1),
       '%d/%d' % (len(minus_side), o_count))
    ck(len(plus_side) == n_count, 'N10.%d hunk#%d +侧行数 == 头部声明' % (idx + 1, idx + 1),
       '%d/%d' % (len(plus_side), n_count))
    mine = mother_lines[o_start - 1:o_start - 1 + o_count]
    ck(mine == minus_side, 'N11.%d hunk#%d -侧与母本逐行逐字一致' % (idx + 1, idx + 1),
       'L%d..L%d' % (o_start, o_start + o_count - 1))
    hunks.append({'hdr': bl[0], 'o': o_start, 'oc': o_count, 'ps': plus_side})

print('INFO  设计 diff 块中的裸空行数（无前缀、被当作上下文行） = %d' % bare_empty)

# ---------------------------------------------------------------- 重建 == 新候选
rebuilt = []
cur = 1
for h in sorted(hunks, key=lambda x: x['o']):
    if h['o'] > cur:
        rebuilt.extend(mother_lines[cur - 1:h['o'] - 1])
    rebuilt.extend(h['ps'])
    cur = h['o'] + h['oc']
rebuilt.extend(mother_lines[cur - 1:])

expected = (NL.join(rebuilt) + NL).encode('utf-8')
ck(nb == expected, 'N12 新候选 == 母本+9hunk 重建（逐字节，H1–H9 之外恒等母本）',
   '%d vs %d B' % (len(nb), len(expected)))
ck(len(hunks) == 9, 'N13 参与重建的 hunk 数 == 9', '%d' % len(hunks))

# ---------------------------------------------------------------- 独立来源交叉验证
if ob:
    as_lf = ob.replace(CRLF, b'\n')
    ck(nb == as_lf, 'N14 新候选 == 旧候选 CRLF→LF（独立来源交叉验证）',
       '%d vs %d B' % (len(nb), len(as_lf)))
    ck(len(ob) - len(as_lf) == ob.count(CRLF), 'N15 旧候选字节差 == 其 CRLF 计数',
       '%d' % ob.count(CRLF))

net_gain = len(nb) - len(mb)
ck(net_gain == PREDICTED_NET_GAIN, 'N16 真实净增 == 13251 B', 'actual=%d' % net_gain)
ck((O_BYTES - M_BYTES) - net_gain == PREDICTED_EOL_BYTES,
   'N17 名义净增 − 真实净增 == 7533（纯行尾字节）',
   '%d' % ((O_BYTES - M_BYTES) - net_gain))

# ---------------------------------------------------------------- 语法与锚点
new_text = nb.decode('utf-8')
mother_text = mb.decode('utf-8')
try:
    tree = ast.parse(new_text)
    ast_ok = True
except SyntaxError as exc:
    ast_ok = False
    print('INFO  ast.parse 失败: %s' % exc)
ck(ast_ok, 'N18 新候选 ast.parse 成功')
if ast_ok:
    fnames = set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fname in ('make_pre_freshness_snapshot', 'classify_except_freshness',
                  'copy_post_except_evidence', 'finalize_trip', 'main'):
        ck(fname in fnames, 'N19 关键函数存在 %s' % fname)

for hid, token in ANCHORS:
    ck(token in new_text, 'N20 锚点 %s 可定位' % hid, token[:44])

# ---------------------------------------------------------------- 反扫描
for kw in SCAN_KEYWORDS:
    nc = new_text.count(kw)
    mc = mother_text.count(kw)
    ck(nc == mc, 'N21 反扫描 %s 计数与母本相同' % kw, '%d vs %d' % (nc, mc))

# ---------------------------------------------------------------- diff 文件
if os.path.exists(NEWD):
    ndb = rd(NEWD)
    ck(ndb.count(CR) == 0, 'N22 新 diff 零 CR 字节')
    dlines = ndb.decode('utf-8').split(NL)
    dhdr = [l for l in dlines if l.startswith('@@ ')]
    ck(len(dhdr) == 9, 'N23 新 diff 含 9 个 @@ hunk', 'found=%d' % len(dhdr))
    if len(dhdr) == 9 and len(hunks) == 9:
        same = all(dhdr[i] == hunks[i]['hdr'] for i in range(9))
        ck(same, 'N24 新 diff 的 9 个 hunk 头与设计逐一相同')
        if not same:
            for i in range(9):
                if dhdr[i] != hunks[i]['hdr']:
                    print('       #%d design=%r actual=%r' % (i + 1, hunks[i]['hdr'], dhdr[i]))
    ck(('+++' + ' qc151_trip.candidate_lf.py') in ndb.decode('utf-8')
       or 'qc151_trip.candidate_lf.py' in ndb.decode('utf-8'),
       'N25 新 diff 指向新候选文件名')

    # N26/N27：结构合法性 —— 头身必须交错，每个头紧跟其 body 且行数与声明相符。
    # N22–N25 只核「零 CR / 头个数 / 头与设计同序 / 文件名」，
    # 头身分离时四项照样全 PASS（2026-11-07 实证：9 个头挤在第 3–11 行仍全绿）。
    dls = [l for l in dlines]
    if dls and dls[-1] == '':
        dls = dls[:-1]
    hpos = [i for i, l in enumerate(dls) if l.startswith('@@ ')]
    struct_ok = True
    detail = []
    for k, i in enumerate(hpos):
        end = hpos[k + 1] if k + 1 < len(hpos) else len(dls)
        seg = dls[i + 1:end]
        parsed = parse_hdr(dls[i])
        if parsed is None:
            struct_ok = False
            detail.append('#%d 头无法解析' % (k + 1))
            continue
        _os, oc, _ns, nc = parsed
        seg = [l for l in seg if not l.startswith('+++') and not l.startswith('---')]
        newcnt = sum(1 for l in seg if l.startswith(' ') or l.startswith('+'))
        oldcnt = sum(1 for l in seg if l.startswith(' ') or l.startswith('-'))
        if newcnt != nc or oldcnt != oc:
            struct_ok = False
            detail.append('#%d old=%d/%d new=%d/%d' % (k + 1, oldcnt, oc, newcnt, nc))
    ck(struct_ok, 'N26 每个 @@ 头后紧跟其 body 且行数与头部声明相符',
       '; '.join(detail) if detail else '9/9')

    # N27：正向应用 —— 拿母本按 diff 的 hunk 逐段替换，必须得到新候选。
    # unified diff 只含 3 行上下文，**无法从 diff 单独还原全文**，
    # 所以唯一正确的判据是「母本 + diff == 候选」。
    # 这一条同时证明：diff 结构合法、内容正确、可被标准 patch 工具消费。
    cur = 1
    applied = []
    apply_ok = True
    apply_note = []
    for k, i in enumerate(hpos):
        parsed = parse_hdr(dls[i])
        if parsed is None:
            apply_ok = False
            apply_note.append('#%d 头无法解析' % (k + 1))
            continue
        o_start, o_count, _ns, _nc = parsed
        end = hpos[k + 1] if k + 1 < len(hpos) else len(dls)
        seg = [l for l in dls[i + 1:end]
               if not l.startswith('+++') and not l.startswith('---')]
        plus = [l[1:] for l in seg
                if l.startswith(' ') or l.startswith('+')]
        if o_start < cur:
            apply_ok = False
            apply_note.append('#%d 区间倒序 o_start=%d < cur=%d' % (k + 1, o_start, cur))
            continue
        applied.extend(mother_lines[cur - 1:o_start - 1])
        applied.extend(plus)
        cur = o_start + o_count
    applied.extend(mother_lines[cur - 1:])

    if not apply_ok:
        ck(False, 'N27 母本 + diff 逐 hunk 应用 == 新候选（逐字节）',
           '; '.join(apply_note))
    else:
        ap = (NL.join(applied) + NL).encode('utf-8')
        ck(ap == nb, 'N27 母本 + diff 逐 hunk 应用 == 新候选（逐字节）',
           '%d vs %d B' % (len(ap), len(nb)))
else:
    ck(False, 'N22 新 diff 文件存在', NEWD)

print('SUMMARY_POST fails=%d bytes=%d sha256=%s net_gain=%d' %
      (len(fails), len(nb), sha(nb), net_gain))
raise SystemExit(0 if not fails else 1)
