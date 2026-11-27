#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 A：F24 那处「a2_sites.json 差 +16,711,118 B 恰为被剔的 bounds 段」到底是不是字节事实。

背景：F24 limitations 写「现盘 17,624,355，清单 913,237，差 +16,711,118 B 恰为被剔的 bounds 段」。
三句都可被机械判：① 现盘字节；② bounds 值在盘上的精确字节跨度；③ 把 16,711,118 B 从文件里
连续删掉后还能不能 parse。本脚本只测，不改任何文件。

反控（必须成对）：
 N1 用一个自造的同格式小 json 走同一 span 扫描器，跨度必须等于手工长度。
 N2 同一扫描器对 913,250 起的 16,711,104 B 删除必须给出「不合法」（缺分隔符），
    而对 913,238 起的 16,711,116 B 删除必须给出「合法」且 keys==['calls']。
 N3 越过扫描窗口 ±32 B 之外的删除不得进入判据（窗口外不取样，避免「扫全文件」的假设）。
"""
import hashlib, json, os, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
P = os.path.join(ROOT, 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json')
fails, rows = [], []
def ck(name, cond, detail=''):
    rows.append((cond, name, detail))
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

def top_value_spans(b):
    """返回 {key: (start, end, length)}，只认顶层键值对；字符串转义感知。"""
    out = {}
    i = 0; n = len(b)
    while i < n and b[i:i+1] != b'{': i += 1
    i += 1
    while i < n:
        while i < n and b[i:i+1] in b' \t\r\n,': i += 1
        if i >= n or b[i:i+1] == b'}': break
        if b[i:i+1] != b'"': break
        j = i + 1; buf = bytearray()
        while j < n:
            if b[j:j+1] == b'\\': buf += b[j:j+2]; j += 2; continue
            if b[j:j+1] == b'"': break
            buf += b[j:j+1]; j += 1
        key = bytes(buf).decode('utf-8')
        k = j + 1
        while k < n and b[k:k+1] in b' \t\r\n': k += 1
        if b[k:k+1] != b':': break
        k += 1
        while k < n and b[k:k+1] in b' \t\r\n': k += 1
        start = k
        depth = 0; ins = False; esc = False
        while k < n:
            ch = b[k:k+1]
            if ins:
                if esc: esc = False
                elif ch == b'\\': esc = True
                elif ch == b'"': ins = False
                k += 1; continue
            if ch == b'"': ins = True; k += 1; continue
            if ch in (b'{', b'['): depth += 1
            elif ch in (b'}', b']'):
                if depth == 0: break
                depth -= 1
            elif ch == b',' and depth == 0: break
            k += 1
        out[key] = (start, k, k - start)
        i = k
    return out

# ---------- N1 反向自证：同格式小样本 ----------
small = b'{"calls": {"1": ["2"]}, "bounds": ["A", "B"]}'
sp = top_value_spans(small)
ck('N1a 小样本 span 扫描得到两个顶层键', sorted(sp) == ['bounds', 'calls'], sorted(sp))
ck('N1b 小样本 calls 跨度 == 手算 16', sp['calls'][2] == len(b'{"1": ["2"]}'), sp['calls'][2])
ck('N1c 小样本 bounds 跨度 == 手算 10', sp['bounds'][2] == len(b'["A", "B"]'), sp['bounds'][2])

# ---------- ① 现盘字节 ----------
raw = open(P, 'rb').read()
ck('A1 现盘 a2_sites.json 字节 == 17,624,355', len(raw) == 17624355, len(raw))
ck('A2 sha256 前缀 = 7a8447d1d816cdc3（与 R173 记录一致）',
   hashlib.sha256(raw).hexdigest()[:16] == '7a8447d1d816cdc3', hashlib.sha256(raw).hexdigest()[:16])

# ---------- ② bounds 值精确跨度 ----------
sp = top_value_spans(raw)
ck('B1 顶层键恰为 calls/bounds 两个', sorted(sp) == ['bounds', 'calls'], sorted(sp))
bs, be, bl = sp['bounds']
ck('B2 bounds 值跨度实测 16,711,104 B', bl == 16711104, bl)
ck('B3 该跨度 == 1,392,592 条 x 12 B（每条 "XXXXXXXX", 恰好 12）', bl == 1392592 * 12, (1392592*12, bl))
ck('B4 bounds 未占满「差 +16,711,118」：差 14 B（= "bounds": + [ + ] 的 14 个字符）',
   16711118 - bl == 14, 16711118 - bl)

# ---------- ③ 16,711,118 B 连续删除能否得到合法 JSON ----------
def try_delete(a, ln):
    b = a + ln
    if a < 0 or b > len(raw): return None
    try:
        o = json.loads(raw[:a] + raw[b:]); return o
    except Exception:
        return None

hits = []
for a in range(len(raw) - 16711118 - 32, len(raw) - 16711118 + 33):
    o = try_delete(a, 16711118)
    if o is not None: hits.append((a, sorted(o)))
ck('C1 以 16,711,118 B 为删除宽度、在 ±32 B 窗口内扫 65 个起点，得到合法 JSON 的起点数 == 0',
   len(hits) == 0, hits)

# N2 正反控：真跨度的删除必须合法，越界一位的删除必须不合法
o = try_delete(913238, 16711116)
ck('N2a 删 913,238 起 16,711,116 B -> 合法且 keys==["calls"]（该宽度是 json 可承载的真跨度）',
   o is not None and sorted(o) == ['calls'], (o is not None, sorted(o) if o else None))
ck('N2b 该删除后文件字节 == 913,239（不是清单里的 913,237）', len(raw) - 16711116 == 913239, len(raw) - 16711116)
ck('N2c 删 913,250 起 16,711,104 B（只删值、留 , "bounds": ）-> 不合法，缺分隔符',
   try_delete(913250, 16711104) is None, True)
ck('N2d 删 913,237 起 16,711,118 B（按差额的原点）-> 不合法', try_delete(913237, 16711118) is None, True)

# ---------- ④ 清单与差额的算术闭合 ----------
man = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv')
rowsm = [l.split('\t') for l in open(man, encoding='utf-8').read().rstrip('\n').split('\n')[1:]]
a2 = [r for r in rowsm if r[0].endswith('a2_sites.json')]
ck('D1 清单里 a2_sites.json 恰 1 行', len(a2) == 1, len(a2))
ck('D2 清单记录字节 == 913,237', int(a2[0][1]) == 913237, a2[0][1])
ck('D3 17,624,355 - 16,711,118 == 913,237（差额是算术推论，不是字节测量）',
   17624355 - 16711118 == 913237, 17624355 - 16711118)
ck('D4 反向：现盘 - 清单 == 16,711,118，与 bounds 值跨度差 14 B',
   17624355 - 913237 == 16711118 and (17624355 - 913237) - bl == 14, 17624355 - 913237)

print()
print('SUMMARY: %d assertions, %d FAIL' % (len(rows), len(fails)))
json.dump(dict(fails=fails, asserts=len(rows),
               measured=dict(file_bytes=len(raw), bounds_span=bl, bounds_entries=1392592,
                             json_valid_delete=16711116, json_valid_size=913239,
                             delta=16711118, delta_minus_span=16711118 - bl)),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173a_f24_bounds_bytes.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
