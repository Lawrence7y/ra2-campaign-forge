#!/usr/bin/env python3
"""R168 E：逐字重放 R167 的 best_table，检验其「3 字节条目」分支是否真的按 3 字节步进。

R167 `_r167/r167d_holes_semantics_final.py:140-158` 原文关键行：
    b = v - ((v - LO - p) % 4)        # 相位计算恒用 mod 4
    if not (b <= v < b + 4): continue  # 覆盖窗口恒 4 字节
    x = rd(b, w)                       # 取值用 w
    lo = b ; while ...: a = lo - 4 ... # 起点回退恒 4 字节
    hi = b + 4 ; while ...: hi += 4    # 终点推进恒 4 字节
    k = (hi - lo) // 4                 # 条目数恒按 4 除
⇒ w=3 只改变「读几个字节」，不改变步进 ⇒ 不是「3 字节条目表」，是「4 字节槽位上读 3 字节」。
本脚本：
  ① 逐字重放（保留缺陷）⇒ 必须得到 R167 的 56/65 与 35 张表；
  ② 检测缺陷：对每个 w=3 的命中，报告 lo/hi 与逐 4 字节读到的 3 字节值；
  ③ 修正版（w=3 时步进 3、相位 mod 3）⇒ 报告修正后命中数；
  ④ 反控：w=4 分支逐字重放必与 R167 完全相同（说明重放没跑偏）。
"""
import sys, struct, json
sys.path.insert(0, '_r143')
import r143lib as L
B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
LO = IB + text[1]; VSZ = text[2]; HI = LO + VSZ

def rd(va, n):
    b = B.rd(va, n)
    if not b or len(b) < n: return None
    v = 0
    for i in range(n): v |= b[i] << (8 * i)
    return v

def isT(x):
    return x is not None and LO <= x < HI

def best_table_replay(v):
    """逐字重放 R167（含 hi/lo 恒 4 字节步进、相位恒 mod 4）。"""
    best = (0, None, None, None, None)
    for w in (4, 3):
        for p in range(4):
            b = v - ((v - LO - p) % 4)
            if not (b <= v < b + 4): continue
            x = rd(b, w)
            if not isT(x): continue
            lo = b
            while True:
                a = lo - 4
                if a < LO: break
                y = rd(a, w)
                if not isT(y): break
                lo = a
            hi = b + 4
            while True:
                y = rd(hi, w)
                if not isT(y): break
                hi += 4
            k = (hi - lo) // 4
            if k > best[0]: best = (k, w, p, lo, hi)
    return best

def best_table_fixed(v):
    """修正版：w 字节步进 + 相位 mod w。"""
    best = (0, None, None, None, None)
    for w in (4, 3):
        for p in range(w):
            b = v - ((v - LO - p) % w)
            if not (b <= v < b + w): continue
            x = rd(b, w)
            if not isT(x): continue
            lo = b
            while True:
                a = lo - w
                if a < LO: break
                y = rd(a, w)
                if not isT(y): break
                lo = a
            hi = b + w
            while True:
                y = rd(hi, w)
                if not isT(y): break
                hi += w
            k = (hi - lo) // w
            if k > best[0]: best = (k, w, p, lo, hi)
    return best

R167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = [int(x, 16) for x in R167['holes']]
rep = {v: best_table_replay(v) for v in holes}
fix = {v: best_table_fixed(v) for v in holes}

in_rep = [v for v in holes if rep[v][0] >= 3]
in_fix = [v for v in holes if fix[v][0] >= 3]
tabs_rep = sorted(set((rep[v][3], rep[v][4]) for v in in_rep))
tabs_fix = sorted(set((fix[v][3], fix[v][4]) for v in in_fix))
w3hits = [v for v in in_rep if rep[v][1] == 3]

# 缺陷证据：每个 w=3 命中的槽上，逐 4 字节读 3 字节的值是否都是 .text 地址，而逐 3 字节不是
defect = []
for v in w3hits:
    k, w, p, lo, hi = rep[v]
    slots = [rd(lo + 4 * i, 3) for i in range(k)]
    slots3 = [rd(lo + 3 * i, 3) for i in range(k)]
    defect.append({'va': hex(v), 'k': k, 'w': w, 'p': p, 'lo': hex(lo), 'hi': hex(hi),
                   'stride4_reads': [hex(x) if x else None for x in slots],
                   'stride4_all_text': all(isT(x) for x in slots),
                   'stride3_reads': [hex(x) if x else None for x in slots3],
                   'stride3_all_text': all(isT(x) for x in slots3),
                   'fixed_best': {'k': fix[v][0], 'w': fix[v][1], 'lo': fix[v][3] and hex(fix[v][3]),
                                  'hi': fix[v][4] and hex(fix[v][4])}})

A = []
A.append({'id': 'E1 逐字重放命中 56/65（R167 原值）', 'ok': len(in_rep) == 56, 'detail': str(len(in_rep))})
A.append({'id': 'E2 逐字重放涉及表数 35（R167 原值）', 'ok': len(tabs_rep) == 35, 'detail': str(len(tabs_rep))})
A.append({'id': 'E3 逐字重放命中的集合 == R167 holes_in_table 逐条',
          'ok': set(in_rep) == set(int(x, 16) for x in R167['holes_in_table']),
          'detail': 'symdiff=%d' % len(set(in_rep) ^ set(int(x, 16) for x in R167['holes_in_table']))})
A.append({'id': 'E4 逐字重放的宽度标注 == R167 table_entry_width 逐条',
          'ok': all(R167['table_entry_width'].get(hex(v)) == rep[v][1] for v in in_rep),
          'detail': 'w3=%d' % len(w3hits)})
A.append({'id': 'E5 所有 w=3 命中的槽值在「4 字节步进」读法下全是 .text 地址（即步进确为 4）',
          'ok': all(d['stride4_all_text'] for d in defect) and len(defect) > 0,
          'detail': 'n=%d' % len(defect)})
A.append({'id': 'E6 同样这些槽在「3 字节步进」读法下不全成立 ⇒ 宽度标签为误称',
          'ok': all(not d['stride3_all_text'] for d in defect) and len(defect) > 0,
          'detail': repr([(d['va'], d['stride3_all_text']) for d in defect])})
A.append({'id': 'E7 修正版（步进=宽度）命中数 <= 重放命中数，且 w=3 命中归零',
          'ok': len(in_fix) <= len(in_rep) and all(fix[v][1] != 3 for v in in_fix),
          'detail': 'replay=%d fixed=%d fixed_w3=%d' % (len(in_rep), len(in_fix),
                    sum(1 for v in in_fix if fix[v][1] == 3))})
A.append({'id': 'E8 修正版里 0x7d0cba 不再命中（该条是缺陷产物）',
          'ok': not (0x7d0cba in in_fix),
          'detail': 'fixed=%s' % (fix[0x7d0cba],)})

out = {'replay_in': len(in_rep), 'replay_tables': len(tabs_rep),
       'fixed_in': len(in_fix), 'fixed_tables': len(tabs_fix),
       'w3_hits': [hex(v) for v in w3hits], 'defect': defect,
       'fixed_only_new': [hex(v) for v in in_fix if v not in in_rep],
       'fixed_lost': [hex(v) for v in in_rep if v not in in_fix],
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168e_replay_r167_table.json', 'w'), ensure_ascii=False, indent=1)
print('replay in=%d tables=%d | fixed in=%d tables=%d' % (len(in_rep), len(tabs_rep), len(in_fix), len(tabs_fix)))
print('w3 hits:', [hex(v) for v in w3hits])
for d in defect: print(json.dumps(d, ensure_ascii=False))
print('fixed_lost:', [hex(v) for v in in_rep if v not in in_fix])
print('fixed_only_new:', [hex(v) for v in in_fix if v not in in_rep])
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:220])
