#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 A：独立复算「16,711,118」到底是算术差还是字节跨度，并给 F24 statement 里 4 处出现逐个定性。

独立实现（与 R173 的转义感知顶层 span 扫描器不同）：
  S1  用 stdlib json.loads 取 keys 与 len(bounds)，再从原文用 b'"bounds"' 定位到值的起始 '[',
      用**括号配平**（只数 [ ]，遇到字符串内的括号先跳过）找结束位置，跨度 = end-start。
  S2  用「删段后能否 json.loads」做交叉判：删值跨度必须**不合法**（缺分隔符），
      删整条成员（含前置逗号与键名）必须**合法**且只剩 calls。
  S3  单条长度逐个量：取前 1000 条的字节长度集合，证明「每条定长」不是假设而是实测。
  S4  算术差 = 现盘 17,624,355 − 快照清单 913,237 = 16,711,118。
本脚本只测，不改任何文件。
"""
import hashlib, io, json, os, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
P = os.path.join(ROOT, 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json')
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
LED = os.path.join(TIER, 'R17_R128_FACTINDEX_V556/FACT_INDEX.tsv')
OUT = os.path.join(ROOT, '_r175/r175a_f24_span_recheck.json')
fails, n, res = [], 0, {}
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)
    res[name] = {'pass': bool(cond), 'detail': str(detail)}

raw = io.open(P, 'rb').read()
res['a2_bytes'] = len(raw)
res['a2_sha16'] = hashlib.sha256(raw).hexdigest()[:16]
ck('A1 现盘 a2_sites.json 恰 17,624,355 B', len(raw) == 17624355, len(raw))
ck('A2 sha256 前 16 位 = 7a8447d1d816cdc3', res['a2_sha16'] == '7a8447d1d816cdc3', res['a2_sha16'])

obj = json.loads(raw)
ck('A3 顶层只有 calls/bounds 两个键', sorted(obj) == ['bounds', 'calls'], sorted(obj))
res['n_bounds'] = len(obj['bounds'])
ck('A4 bounds 元素数 1,392,592', res['n_bounds'] == 1392592, res['n_bounds'])
res['n_calls'] = len(obj['calls'])
ck('A5 calls 键数 6,728', res['n_calls'] == 6728, res['n_calls'])

# ---- S1 括号配平找 bounds 值跨度 ----
ki = raw.index(b'"bounds"')
ck('B1 b"\"bounds\"" 在原文恰 1 次（键名）', raw.count(b'"bounds"') == 1, raw.count(b'"bounds"'))
bstart = raw.index(b'[', ki)
depth, i, in_str, esc = 0, bstart, False, False
while i < len(raw):
    ch = raw[i:i+1]
    if in_str:
        if esc: esc = False
        elif ch == b'\\': esc = True
        elif ch == b'"': in_str = False
        i += 1; continue
    if ch == b'"': in_str = True; i += 1; continue
    if ch == b'[': depth += 1
    elif ch == b']':
        depth -= 1
        if depth == 0: break
    i += 1
bend = i + 1
res['bounds_span'] = bend - bstart
ck('B2 bounds 值跨度 == 16,711,104', res['bounds_span'] == 16711104, res['bounds_span'])
ck('B3 值以 [ 开头、以 ] 结尾', raw[bstart:bstart+1] == b'[' and raw[bend-1:bend] == b']', (raw[bstart:bstart+1], raw[bend-1:bend]))

# ---- S3 每条定长实测（不是假设） ----
inner = raw[bstart+1:bend-1]
lens, cur = set(), 0
pieces = inner.split(b',')
ck('C1 split(,) 后片段数 == bounds 元素数', len(pieces) == res['n_bounds'], (len(pieces), res['n_bounds']))
# ★ 订正（自错 S-626）：分隔符是「逗号+空格」2 B，故首条裸长 10、其余 11（前导空格），
#   不是全部 11。R173 记的「每条 12 B」= 10 B 引号串 + 2 B 分隔符，仅对「非末条」成立。
sample = pieces[:1000]
res['piece_len_counter'] = dict((k, sum(1 for p in pieces if len(p) == k)) for k in set(len(p) for p in pieces))
ck('C2 全表条目长度集合恰为 {10, 11}（不是单一长度）', set(len(p) for p in pieces) == {10, 11}, sorted(set(len(p) for p in pieces)))
ck('C3 恰 1 条为 10 B（首条，无前导空格）', sum(1 for p in pieces if len(p) == 10) == 1, sum(1 for p in pieces if len(p) == 10))
ck('C4 恰 1,392,591 条为 11 B（前导空格 + 引号串 10 B）', sum(1 for p in pieces if len(p) == 11) == 1392591, sum(1 for p in pieces if len(p) == 11))
ck('C5 每条引号串本体都恰 10 B', set(len(p.strip()) for p in pieces) == {10}, sorted(set(len(p.strip()) for p in pieces))[:5])
ck('C6 分隔符恒为 b", "（1,392,591 个）', inner.count(b', ') == 1392591, inner.count(b', '))
ck('C7 换算 10*n + 2*(n-1) + 2 括号 == 16,711,104',
   10 * 1392592 + 2 * 1392591 + 2 == 16711104, 10*1392592 + 2*1392591 + 2)
ck('C8 值跨度 == 10*n + 2*(n-1) + 2', res['bounds_span'] == 10*res['n_bounds'] + 2*(res['n_bounds']-1) + 2,
   (res['bounds_span'], 10*res['n_bounds'] + 2*(res['n_bounds']-1) + 2))

# ---- S2 交叉判：删值 vs 删整条成员 ----
def legal(b):
    try:
        json.loads(b); return True, None
    except Exception as e:
        return False, type(e).__name__
del_val = raw[:bstart] + raw[bend:]
res['del_val_bytes'] = len(del_val)
ok_val, err_val = legal(del_val)
ck('D1 只删值跨度后**不合法**', not ok_val, err_val)

jprev = raw.rindex(b'}', 0, ki)
ck('D0 calls 值结束的 } 恰在偏移 913,237（与 R174 的「calls 成员文本长 913,237」互证）',
   jprev == 913237, jprev)
mstart = jprev + 1          # 从 ',' 起：913,238
ck('D0b 成员起点字节是逗号', raw[mstart:mstart+1] == b',', raw[mstart:mstart+1])
member = raw[:mstart] + raw[bend:]
res['del_member_bytes'] = len(member)
ok_m, err_m = legal(member)
ck('D2 删「, "bounds": [...] 」整条成员后**合法**', ok_m, err_m)
res['member_span'] = bend - mstart
ck('D3 整条成员跨度 == 16,711,116', res['member_span'] == 16711116, res['member_span'])
if ok_m:
    o2 = json.loads(member)
    ck('D4 删成员后顶层键只剩 calls', list(o2) == ['calls'], list(o2))
    ck('D5 删成员后字节 == 913,239', len(member) == 913239, len(member))

# ---- S4 算术差 ----
res['arith_diff'] = 17624355 - 913237
ck('E1 17,624,355 - 913,237 == 16,711,118', res['arith_diff'] == 16711118, res['arith_diff'])
# ★ 订正（自错 S-626）：R173 落的「三个宽度两两相差 2 B」**假**。实测两两差是 12 与 2：
#   值跨度 -> 整条成员差 **12**（`, "bounds": ` 前缀恰 12 B），成员 -> 算术差 2 B（两个收尾花括号）。
ck('E2a 值跨度 -> 成员跨度 差 12 B', 16711116 - 16711104 == 12, 16711116 - 16711104)
ck('E2b 成员跨度 -> 算术差 差 2 B', 16711118 - 16711116 == 2, 16711118 - 16711116)
res['prefix_len'] = bstart - mstart
ck('E2c 前缀 b", \"bounds\": " 实测 12 B 且逐字节相等', raw[mstart:bstart] == b', "bounds": ',
   (res['prefix_len'], raw[mstart:bstart]))
ck('E2d 精确分解 12 + 16,711,104 + 1 + 1 == 16,711,118',
   12 + 16711104 + 1 + 1 == 16711118, 12 + 16711104 + 1 + 1)
ck('E2e 成员后恰 1 字节收尾 }', len(raw[bend:]) == 1 and raw[bend:] == b'}', raw[bend:])
ck('E2f 偏移 913,237 的字节是 calls 的收尾 }', raw[913237:913238] == b'}', raw[913237:913238])

# ---- F24 statement 里 4 处逐个定性 ----
d = io.open(LED, 'rb').read().decode('utf-8')
import csv
rows = list(csv.reader(io.StringIO(d), delimiter='\t'))
rec = {r[0]: r for r in rows[1:]}
st, lim = rec['F24'][1], rec['F24'][4]
res['st_bytes'] = len(st.encode())
res['lim_bytes'] = len(lim.encode())
ck('F1 F24 statement 字节 == 10,613', res['st_bytes'] == 10613, res['st_bytes'])
ck('F2 F24 limitations 字节 == 33,011（== facts_floors 的 F24 下界，两者同为现值）',
   res['lim_bytes'] == 33011, res['lim_bytes'])
import re
occ = [(m.start(), st[max(0, m.start()-60):m.start()+60]) for m in re.finditer('16,711,118', st)]
res['st_occurrences'] = [o[0] for o in occ]
ck('F3 statement 内 16,711,118 恰 4 处', len(occ) == 4, [o[0] for o in occ])
for off, ctx in occ:
    print('   @%d  ...%s...' % (off, ctx))
lo = [m.start() for m in re.finditer('16,711,118', lim)]
res['lim_occurrences'] = lo
ck('F4 limitations 内 16,711,118 恰 11 处（R173/R174 补记后实测，非预估）', len(lo) == 11, len(lo))
claim = [o for o in occ if ('段 16,711,118' in o[1] or '恰为被剔' in o[1])]
res['claim_occurrences'] = [o[0] for o in claim]
ck('F5 其中「断言为段长」型恰 2 处', len(claim) == 2, [o[0] for o in claim])

out = {'fails': fails, 'n': n, 'res': res}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
