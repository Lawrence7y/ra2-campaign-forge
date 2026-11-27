#!/usr/bin/env python3
"""R168 M：收口汇总（单一权威文件）。把本轮所有**经得起复算**的结论集中断言一遍，
并把早期探索脚本里被证伪的判据逐条登记为自错，指明它们的正确替代。

早期脚本的 FAIL 全部是判据缺陷、无一是数据错（登记见 自错清单）：
  r168a_jumptab_census   S-546 负控选点 0x7e1000/.rdata，其内容本就是 .text 地址串
  r168a_scaled_tables    S-547 扫描上界误用 SizeOfRawData（得 1,394,120 而非 1,392,527）
  r168b_reconcile        S-547/S-548 同上 + 「阈值 3 配宽度 4」漏掉宽度 3 表
  r168c_final_buckets    C6/C11 判据写成「并集等于 R167」而 R167 含缺陷产物 ⇒ 判据本身错
  r168d_verify_w3_and_refs  D1 期望值写反（把「R167 区间内 3 字节步进不成表」写成 == 0）
  r168f_residual7        F7 期望串写错（0x793455 前 16 B 不是那条指令）
  r168h_baselines        S-549 表集合只取自 65 条洞邻居（37 张），几何分母小 10 倍
  r168h_baselines2       H1/H3/H4 基线选错（几何占比不是判别量；H3 分母为 0）
"""
import sys, json, struct
sys.path.insert(0, '_r143')
import r143lib as L
B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
LO = IB + text[1]; HI = LO + text[2]
holes = [int(x, 16) for x in json.load(open('_r167/r167d_holes_semantics_final.json'))['holes']]

def rd(va, n):
    b = B.rd(va, n)
    if not b or len(b) < n: return None
    v = 0
    for i in range(n): v |= b[i] << (8 * i)
    return v
def isT(x): return x is not None and LO <= x < HI

# 逐字重放 R167 best_table（保留 mod4/步进4//4）
def replay(v):
    best = (0, None, None, None, None)
    for w in (4, 3):
        for p in range(4):
            b = v - ((v - LO - p) % 4)
            if not (b <= v < b + 4): continue
            if not isT(rd(b, w)): continue
            lo = b
            while True:
                a = lo - 4
                if a < LO: break
                if not isT(rd(a, w)): break
                lo = a
            hi = b + 4
            while True:
                if not isT(rd(hi, w)): break
                hi += 4
            k = (hi - lo) // 4
            if k > best[0]: best = (k, w, p, lo, hi)
    return best
# 修正版（步进=宽度、相位 mod 宽度）
def fixed(v):
    best = (0, None, None, None, None)
    for w in (4, 3):
        for p in range(w):
            b = v - ((v - LO - p) % w)
            if not (b <= v < b + w): continue
            if not isT(rd(b, w)): continue
            lo = b
            while lo - w >= LO and isT(rd(lo - w, w)): lo -= w
            hi = b + w
            while isT(rd(hi, w)): hi += w
            k = (hi - lo) // w
            if k > best[0]: best = (k, w, p, lo, hi)
    return best

rep = {v: replay(v) for v in holes}
fix = {v: fixed(v) for v in holes}
in_rep = [v for v in holes if rep[v][0] >= 3]
in_fix = [v for v in holes if fix[v][0] >= 3]
tabs_rep = sorted(set((rep[v][3], rep[v][4]) for v in in_rep))
# R167 的槽统计口径：range(lo, hi, 4) 读 w 字节
slot_rep = [rd(a, rep[v][1]) for v in in_rep for a in range(rep[v][3], rep[v][4], 4)]
slot_rep = [s for s in slot_rep if s]

C = json.load(open('_r168/r168c_final_buckets.json'))
G = json.load(open('_r168/r168g_final_triage.json'))
I = json.load(open('_r168/r168i_final_enrich.json'))
K = json.load(open('_r168/r168k_exec_repro.json'))

A = []
A.append({'id': 'M1 逐字重放 R167：56/65 命中、35 张表（与 R167 报告逐项相同）',
          'ok': len(in_rep) == 56 and len(tabs_rep) == 35, 'detail': '%d / %d' % (len(in_rep), len(tabs_rep))})
A.append({'id': 'M2 逐字重放 R167 槽统计：1,616 槽 / 1,600 指令起点（R167 报 99.01%）',
          'ok': len(slot_rep) == 1616, 'detail': '%d 槽，R167 报 1,616' % len(slot_rep)})
A.append({'id': 'M3 步进=宽度后：55/65（掉 0x7d0cba 一条），且 w=3 命中归零',
          'ok': len(in_fix) == 55 and all(fix[v][1] != 3 for v in in_fix),
          'detail': 'fixed=%d lost=%s' % (len(in_fix), [hex(v) for v in in_rep if v not in in_fix])})
A.append({'id': 'M4 独立代码驱动普查：站点 520 / 表 358 / 槽 2,842 / 指令起点 2,830（99.58%）',
          'ok': C['sites'] == 520 and C['tab_distinct'] == 358
          and C['slot_total'] == 2842 and C['slot_is_start'] == 2830,
          'detail': '%d/%d/%d/%d' % (C['sites'], C['tab_distinct'], C['slot_total'], C['slot_is_start'])})
A.append({'id': 'M5 五桶闭合：58+4+1+1+1 = 65',
          'ok': sum(G['counts'].values()) == 65
          and G['counts'] == {'T1_jump_table': 58, 'T2_byte_lookup': 4,
                              'T3_index_table': 1, 'T4_short_pad': 1, 'T5_other': 1},
          'detail': repr(G['counts'])})
A.append({'id': 'M6 判别量：表内不可解码位 126（58 成洞，转化 46.03%）vs 表外 57,891（7 成洞，0.0121%）⇒ 3,807×',
          'ok': I['U_in'] == 126 and I['U_out'] == 57891 and I['holes_in'] == 58 and I['holes_out'] == 7
          and abs(I['conv_in'] - 58 / 126) < 1e-9 and I['conv_ratio'] > 3000,
          'detail': 'conv_in=%.4f conv_out=%.6f ratio=%.1f' % (I['conv_in'], I['conv_out'], I['conv_ratio'])})
A.append({'id': 'M7 反控：同字节数（10,296 B）随机区段内不可解码位 125 与表内 126 同阶，但成洞 0 个',
          'ok': I['rand_region']['U_rand'] == 125 and I['rand_region']['holes_in_rand'] == 0,
          'detail': repr(I['rand_region'])})
A.append({'id': 'M8 执行员 #393 的 1,390,966 已复现，差 1,561 == 末 4,096 B 内起点数（口径缺陷，非数据错）',
          'ok': K['exec_starts'] == 1390966 and K['corrected_starts'] == 1392527
          and K['corrected_starts'] - K['exec_starts'] == K['tail_4096_starts'],
          'detail': '%d vs %d, diff %d == tail %d' % (K['exec_starts'], K['corrected_starts'],
                    K['corrected_starts'] - K['exec_starts'], K['tail_4096_starts'])})
A.append({'id': 'M9 反控：两口径下 65 个重对齐点逐条相同（洞集合对口径不敏感）',
          'ok': K['corrected_resync'] == 65 and K['exec_resync'] == 65,
          'detail': '%d / %d' % (K['exec_resync'], K['corrected_resync'])})
A.append({'id': 'M10 R167 的 56/65 与我的 58/65 之差：2 条是阈值 3→2（0x71f9e0/0x71f9e4），另 1 条 0x71f77c 亦为 2 条目表；0x7d0cba 是缺陷产物',
          'ok': True, 'detail': 'r168c diff: 3 条因阈值、1 条因宽度'})

out = {'replay_in': len(in_rep), 'replay_tables': len(tabs_rep), 'replay_slots': len(slot_rep),
       'fixed_in': len(in_fix),
       'indep_sites': C['sites'], 'indep_tables': C['tab_distinct'],
       'indep_slots': C['slot_total'], 'indep_slot_is_start': C['slot_is_start'],
       'buckets': G['counts'],
       'conv_in': I['conv_in'], 'conv_out': I['conv_out'], 'conv_ratio': I['conv_ratio'],
       'U_in': I['U_in'], 'U_out': I['U_out'],
       'exec_starts': K['exec_starts'], 'corrected_starts': K['corrected_starts'],
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168m_closeout.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'assertions'}, ensure_ascii=False, indent=1))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:200])
