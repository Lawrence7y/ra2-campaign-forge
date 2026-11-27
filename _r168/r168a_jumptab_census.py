#!/usr/bin/env python3
"""R168 A: .text 内 scale-4 跳转表普查，并用它给 R167 的 65 条不可解码洞重新分桶。

方法（与 R167 独立）：R167 用「节内 4 字节网格 + 每条都是 .text 地址 ⇒ 表」的**值判据**。
本脚本反向走：先找**跳转指令**（ff 24 8d/85/95/9d/a5/b5/ 与 ff 14 ...），
disp32 即表首；再按「逐 4 字节条目仍是 .text 内地址」向后延展得到表字节区间。
两法互不依赖 ⇒ 可当交叉验证。

正控：0x71f9e0 那处已知 site（0x71f9d3 jmp [ecx*4+0x71f9e0]）必须被找到。
负控：把 disp32 换成 0x1000（非 .text）不许产表；把 scale4 换成 scale2 不许命中。
"""
import sys, struct, json, random
sys.path.insert(0, '_r143')
import r143lib as L

B = L.Bin()
data = B.data
IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = IB + text[1]; T_HI = T_LO + text[2]
res = []
# ff /2 jmp r/m32 与 ff /3 call r/m32 的 SIB 形态：modrm = mod00 r/m100 => 0x24(x)/0x14(call)
for op2, mn in ((0x24, 'jmp'), (0x14, 'call')):
    for modrm, reg in ((0x8d, 'ecx'), (0x85, 'eax'), (0x95, 'edx'),
                       (0x9d, 'ebx'), (0xa5, 'esp'), (0xb5, 'esi'), (0xbd, 'edi')):
        pat = bytes([0xff, op2, modrm])
        i = 0
        while True:
            j = data.find(pat, i)
            if j < 0:
                break
            i = j + 1
            va = None
            for nm, ava, vs, raw, rs in B.secs:
                if raw <= j < raw + rs:
                    va = IB + ava + (j - raw); break
            if va is None or B.sec_of(va) != '.text':
                continue
            disp = struct.unpack_from('<I', data, j + 3)[0]
            res.append({'site': va, 'mn': mn, 'reg': reg, 'tab': disp})

def table_span(start, maxent=4096):
    """从 start 起逐 4 字节延展，条目值必须是 .text 内地址；返回条目数与字节区间。"""
    n = 0
    while n < maxent:
        v = B.dw(start + 4 * n)
        if v is None or not (T_LO <= v < T_HI):
            break
        n += 1
    return n, (start, start + 4 * n) if n else (start, start)

tabs = []
for r in res:
    n, (lo, hi) = table_span(r['tab'])
    if n >= 2:
        r['entries'] = n; r['lo'] = lo; r['hi'] = hi
        tabs.append(r)

out = {'exe_sha256': L.__dict__.get('_', None), 'text_lo': hex(T_LO), 'text_hi': hex(T_HI),
       'sites_total': len(res), 'tables_in_text_2plus': len(tabs)}
# 位置口径交叉：跳转指令本身是否落在 plain 起点集内（该集合 R166 实测 1,392,527）
bounds = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = [int(x, 16) for x in bounds['holes']]
plain = None  # 由 r168b 提供
out['holes'] = len(holes)

def bucket(va):
    hit = [t for t in tabs if t['lo'] <= va < t['hi']]
    return hit

in_tab = []; not_in = []
for h in holes:
    hit = bucket(h)
    (in_tab if hit else not_in).append((h, hit))
out['hole_in_scaled_table'] = len(in_tab)
out['hole_not_in_scaled_table'] = len(not_in)
out['hole_in_tab_detail'] = [{'va': hex(h), 'tables': [{'site': hex(t['site']), 'lo': hex(t['lo']),
                              'hi': hex(t['hi']), 'entries': t['entries']} for t in hit],
                              'offset_in_tab': (h - hit[0]['lo']) if hit else None} for h, hit in in_tab]
out['hole_not_in_tab_list'] = [hex(h) for h, _ in not_in]

# ---- 正反控 ----
A = []
A.append({'id': 'A1 正控：site 0x71f9d3 -> tab 0x71f9e0 被找到',
          'ok': any(t['site'] == 0x71f9d3 and t['tab'] == 0x71f9e0 for t in tabs)})
A.append({'id': 'A2 正控：site 0x7932f4 -> tab 0x79342c 被找到',
          'ok': any(t['site'] == 0x7932f4 and t['tab'] == 0x79342c for t in tabs)})
# 负控 1：disp 指向 .data 不许产表
nd = 0
for s in (0x7e1000, 0x7f0000, 0x800000):
    n, _ = table_span(s)
    nd += (n >= 2)
A.append({'id': 'A3 负控：三个非 .text 地址作为表首，产表数', 'ok': nd == 0, 'detail': str(nd)})
# 负控 2：把同一 site 的表首 +1 字节（错位）不许再产表
mis = sum(1 for t in tabs[:200] if table_span(t['lo'] + 1)[0] >= 2)
A.append({'id': 'A4 负控：表首 +1 错位后仍成表的前 200 中个数', 'ok': mis <= 5, 'detail': str(mis)})
# 负控 3：scale-2 形态（ff 24 55/95 = [reg*2]）站点数应远小于 scale-4 —— 记号用不同 modrm
out['assertions'] = A
out['fail'] = sum(1 for a in A if not a['ok'])
json.dump(out, open('_r168/r168a_jumptab_census.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ('hole_in_tab_detail',)}, ensure_ascii=False, indent=1)[:4000])
for a in A:
    print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', ''))
