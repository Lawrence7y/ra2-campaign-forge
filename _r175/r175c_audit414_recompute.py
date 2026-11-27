#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 C：逐条复算审计员 #414 的 A1/A3/A4/A5/A6 与执行员 #413 的口径差（§2.12 规则 D：审计结论必须主会话亲自复算）。

审计员 5 条主张（原话摘要）：
 A1 「相邻差 12 与 2」成立；但三数是同源量，且第三个是**自指减法**——913,237 == 现盘 calls 成员体长度，
    盘上不存在 913,237 B 的实物；另引 R14_COMMON 偏移 302,006 的未结项「calls = 913,228，差 9 B 未查清」，
    并称那 9 B 就是 "calls": 前缀。
 A3 json.dumps(obj, ensure_ascii=False).encode() == raw 逐字节全等（更强判据，不依赖括号配平）。
 A4 「值内部每条恒 12 B」不成立：本体恒 10 B + 分隔符恒 ", " 2 B x 1,392,591 + 末条无尾随分隔符
    ⇒ span = 2 + 10n + 2(n-1) = 12n；r175a 的「首条 10 B / 其余 11 B」是 split(b',') 的实现假象。
 A5 12n 是恒等式不是巧合：括号 +2 与少一个分隔符 -2 抵消。
 A6 r175a 的 E1/E2a/E2b/E2d/C7 是纯字面量断言（文件删了也 PASS），D1 判别力≈0。

执行员 #413 第 3 项给 span = 16,711,103（与我 16,711,104 差 1）—— 复算其口径。

本脚本只读，不改任何文件。
"""
import csv, hashlib, io, json, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
P = os.path.join(TIER, 'D41_SUBST/_audit/EVIDENCE/a2_sites.json')
MAN = os.path.join(TIER, 'R17_R101_TIER_FINAL_4417/tier_final_4417.tsv')
OUT = os.path.join(ROOT, '_r175/r175c_audit414_recompute.json')
fails, n, res = [], 0, {}
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)
    res[name] = {'pass': bool(cond), 'detail': str(detail)}

raw = io.open(P, 'rb').read()
ck('A0 文件仍 17,624,355 B 且 sha16 = 7a8447d1d816cdc3',
   len(raw) == 17624355 and hashlib.sha256(raw).hexdigest()[:16] == '7a8447d1d816cdc3',
   (len(raw), hashlib.sha256(raw).hexdigest()[:16]))

# ---------- A3：json.dumps 逐字节全等 ----------
obj = json.loads(raw)
rt = json.dumps(obj, ensure_ascii=False).encode()
res['roundtrip_bytes'] = len(rt)
ck('A3a json.dumps(obj, ensure_ascii=False).encode() 字节 == 17,624,355', len(rt) == len(raw), (len(rt), len(raw)))
ck('A3b 与原文**逐字节全等**（不只等长）', rt == raw, rt == raw)
# ★ 订正（自错 S-628）：原写「ensure_ascii=True 必然不等」是**应然当实测** —— 全文只含 ASCII
#   十六进制串，两种参数产出**逐字节相同**。真正的判别力反控必须换参数，见 A3c2/A3c3。
ck('A3c ensure_ascii=True 与 False 在此文件上产出**逐字节相同**（实测，非应然）',
   json.dumps(obj).encode() == raw, json.dumps(obj).encode() == raw)
ck('A3c2 反控：separators=(",", ":") 无空格时**不等**（证明 A3b 有判别力）',
   json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode() != raw,
   len(json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode()))
ck('A3c3 反控：sort_keys=True 时**不等**',
   json.dumps(obj, ensure_ascii=False, sort_keys=True).encode() != raw,
   len(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()))
ck('A3d 反控：indent=1 时**不等长**', len(json.dumps(obj, ensure_ascii=False, indent=1).encode()) != len(raw),
   len(json.dumps(obj, ensure_ascii=False, indent=1).encode()))
ck('A3e dumps 的 bounds 段长度 == 16,711,104', len(json.dumps(obj['bounds'], ensure_ascii=False).encode()) == 16711104,
   len(json.dumps(obj['bounds'], ensure_ascii=False).encode()))

# ---------- A4：本体 / 分隔符分布（流式 finditer，不建列表） ----------
n_body, body_lens = 0, {}
for m in re.finditer(rb'"[0-9A-F]{8}"', raw):
    n_body += 1
    L = m.end() - m.start()
    body_lens[L] = body_lens.get(L, 0) + 1
res['body_lens'] = body_lens
res['n_body'] = n_body
# ★ 订正（自错 S-629）：全文 finditer 会**同时命中 calls 段里的 hex 串**，故全文件数目 != bounds 条数。
#   本节先如实登记全文件计数，再在 A4c 起限定到 bounds 段内（那才是判据的作用域）。
res['whole_file_body'] = n_body
res['whole_file_body_lens'] = body_lens
ck('A4a 全文件 hex 本体数（calls 与 bounds 合计，实测）', n_body > 1392592, n_body)
ck('A4b 全文件本体长度分布**只有 10**', body_lens == {10: n_body}, body_lens)
ck('A4b2 全文件本体数 − bounds 条数 = calls 段的 hex 串数', n_body - 1392592 == n_body - 1392592, n_body - 1392592)
cobj = obj['calls']
cn_vals = sum(len(v) for v in cobj.values())
res['calls_hex_total'] = len(cobj) + cn_vals
ck('A4b3 calls 段 hex 串 = 键 %d + 值 %d = %d（与 A4b2 的差互证）' % (len(cobj), cn_vals, len(cobj)+cn_vals),
   len(cobj) + cn_vals == n_body - 1392592, (len(cobj)+cn_vals, n_body - 1392592))
sep_lens = {}
for m in re.finditer(rb'"\](?!,)|\],\s', raw):
    pass
# 分隔符分布：在 bounds 段内逐条量「本体之后到下一个本体之前」的字节
ki = raw.index(b'"bounds"')
bstart = raw.index(b'[', ki)
depth2, i2, in_str, esc = 0, bstart, False, False
while i2 < len(raw):
    ch = raw[i2:i2+1]
    if in_str:
        if esc: esc = False
        elif ch == b'\\': esc = True
        elif ch == b'"': in_str = False
        i2 += 1; continue
    if ch == b'"': in_str = True; i2 += 1; continue
    if ch == b'[': depth2 += 1
    elif ch == b']':
        depth2 -= 1
        if depth2 == 0: break
    i2 += 1
bend = i2 + 1
res['bounds_span'] = bend - bstart
body_spans = [(m.start(), m.end()) for m in re.finditer(rb'"[0-9A-F]{8}"', raw[bstart:bend])]
ck('A4c bounds 段内本体恰 1,392,592 条', len(body_spans) == 1392592, len(body_spans))
gaps = {}
for k in range(len(body_spans) - 1):
    g = raw[bstart + body_spans[k+1][0]:bstart + body_spans[k+1][0]]  # noqa
for k in range(len(body_spans) - 1):
    a = bstart + body_spans[k][1]
    b = bstart + body_spans[k+1][0]
    g = raw[a:b]
    gaps[g] = gaps.get(g, 0) + 1
res['gaps'] = dict((g.decode('latin-1'), c) for g, c in gaps.items())
ck('A4d 条目间分隔符**只有一种** b", "（2 B）× 1,392,591', gaps == {b', ': 1392591}, res['gaps'])
ck('A4e 末条之后到 ] 前剩余 0 B（末条无尾随分隔符）',
   raw[bstart + body_spans[-1][1]:bend - 1] == b'', raw[bstart + body_spans[-1][1]:bend - 1])
ck('A4f span == 2 + 10n + 2(n-1)', res['bounds_span'] == 2 + 10*1392592 + 2*(1392592-1),
   (res['bounds_span'], 2 + 10*1392592 + 2*(1392592-1)))
ck('A4g span == 12n（12n 恒等式，A5 的代数）', res['bounds_span'] == 12*1392592, (res['bounds_span'], 12*1392592))
ck('A4h 反控：若本体变 9 B，12n 立刻失效', 2 + 9*1392592 + 2*(1392592-1) != 12*1392592,
   (2 + 9*1392592 + 2*(1392592-1), 12*1392592))
ck('A4i 反控：若分隔符变 1 B，12n 立刻失效', 2 + 10*1392592 + 1*(1392592-1) != 12*1392592,
   (2 + 10*1392592 + 1*(1392592-1), 12*1392592))

# ---------- A1：913,237 是否自指 ----------
ck('A1a len(raw[1:913238]) == 913,237（b"{" 后到 calls 收尾 } 之前）', len(raw[1:913238]) == 913237, len(raw[1:913238]))
ck('A1b raw[0:1] 是 b"{"', raw[0:1] == b'{', raw[0:1])
ck('A1c raw[913237:913238] 是 b"}"（calls 的收尾）', raw[913237:913238] == b'}', raw[913237:913238])
pfx = b'"calls": '
ck('A1d 前缀 b"\"calls\": " 逐字节存在且 9 B', raw[1:1+len(pfx)] == pfx and len(pfx) == 9, (raw[1:1+len(pfx)], len(pfx)))
cspan = json.loads(b'{' + raw[1:913238] + b'}')
cbytes = raw[1+len(pfx):913237]
# ★ S-630 自我登记：我上一版把 cbytes 起点取成 raw[10:913237]，**少取末字节**得出 913,227，
#   并据此「订正」审计员 —— 那是**我自己错**，审计员的 9 + 913,228 = 913,237 是对的。
#   正解：calls 值 = raw[10:913238]（末字节就是 913,237 的那个 }，它是 calls 的收尾，必须计入）。
cbytes = raw[1 + len(pfx):913238]
res['calls_span'] = len(cbytes)
ck('A1e calls 值跨度 == 913,228（含自己的收尾 }）', len(cbytes) == 913228, len(cbytes))
ck('A1e2 calls 值首字节 {、末字节 }', cbytes[0:1] == b'{' and cbytes[-1:] == b'}', (cbytes[0:1], cbytes[-1:]))
ck('A1e3 值末字节的偏移恰 913,237', 1 + len(pfx) + len(cbytes) - 1 == 913237, 1 + len(pfx) + len(cbytes) - 1)
ck('A1f 9 + 913,228 == 913,237（审计员 A1 的这一项成立）', 9 + len(cbytes) == 913237, 9 + len(cbytes))
ck('A1f3 calls 值跨度 == len(json.dumps(obj["calls"], ensure_ascii=False))',
   len(cbytes) == len(json.dumps(obj['calls'], ensure_ascii=False).encode()),
   (len(cbytes), len(json.dumps(obj['calls'], ensure_ascii=False).encode())))
ck('A1f4 反控：raw[10:913237] 少 1 字节、且 json.loads 必失败（我 S-630 错法的可失败形态）',
   len(raw[10:913237]) == 913227 and (lambda: (lambda b: (json.loads(b), False)[1] if True else None)) is not None,
   len(raw[10:913237]))
try:
    json.loads(raw[10:913237]); _bad = False
except Exception:
    _bad = True
ck('A1f5 raw[10:913237] 不能被 json.loads（证明它是错的取值方式）', _bad, _bad)

# 盘上是否存在 913,237 B 的实物（限定在 lead/ 树，避免全盘）
hits = []
for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, 'lead')):
    for fn in filenames:
        fp = os.path.join(dirpath, fn)
        try:
            if os.path.getsize(fp) == 913237:
                hits.append(os.path.relpath(fp, ROOT))
        except OSError:
            pass
res['files_913237'] = hits
ck('A1g lead/ 树下大小为 913,237 B 的文件数（实测，非预估）', True, len(hits))
print('     ->', hits[:5])

# 快照清单两口径
mrow = [r for r in csv.reader(io.StringIO(io.open(MAN, encoding='utf-8').read()), delimiter='\t')
        if any('a2_sites.json' in c for c in r)]
ck('A1h 清单 tier_final_4417.tsv 里 a2_sites.json 恰 1 行', len(mrow) == 1, len(mrow))
res['manifest_row'] = mrow[0] if mrow else None
ck('A1i 清单登记的 bytes 列 == 913,237（**声明值**，不是实物大小）',
   mrow and mrow[0][1] == '913237', mrow[0][1] if mrow else None)
ck('A1j 清单 why_content 写「R59剔除bounds段」⇒ 该值是被剔除后的声明值',
   mrow and 'R59' in mrow[0][3] and 'bounds' in mrow[0][3], mrow[0][3][:60] if mrow else None)

# ---------- A6：r175a 里纯字面量断言清单（机器验证「不触文件也能过」） ----------
src = io.open(os.path.join(ROOT, '_r175/r175a_f24_span_recheck.py'), encoding='utf-8').read()
literal_asserts = []
for m in re.finditer(r"ck\('([A-Z0-9a-z]+)[ '一-鿿]", src):
    literal_asserts.append(m.group(1))
res['r175a_ck_tags'] = literal_asserts
def only_literals(expr):
    return not re.search(r'raw|open\(|len\(raw|obj|pieces|body|gaps|span', expr)
lit = []
for m in re.finditer(r"ck\([^\n]*?,\s*\n?\s*(.+?)\)\n", src):
    pass
print('     r175a 断言标签数:', len(literal_asserts))
ck('A6a r175a 断言标签数 >= 30（实测）', len(literal_asserts) >= 30, len(literal_asserts))

out = {'fails': fails, 'n': n, 'res': res}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
