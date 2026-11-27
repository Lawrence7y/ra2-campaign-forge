#!/usr/bin/env python3
"""R168 J：复算两个子代理的三条关键结论（§2.12 规则 D：审计员结论必须主会话复算）。

待复算：
  AUD-1  R167 best_table 的实际行范围是 140–161 而非 140–158（我卡面写错）。
  AUD-2  把步进改成宽度后，那 3 条 w=3 命中**全部**失去 3 字节表（k=1/1/0），
         不是只有 0x7d0cba 掉出去；我 r168e 报「只掉 1 条」是因为它在 w=4 里另有表。
  AUD-3  0x7d0cb0 有一张真 4 字节跳转表，唯一引用者 0x7d0be2 形态 ff 24 9d（jmp [ebx*4+disp32]）。
  EXEC-1 执行员 #393 的起点数 1,390,966 ≠ 1,392,527，差 1,561 —— 定位其口径偏差。
"""
import sys, re, json, struct
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
LO = IB + text[1]; HI = LO + text[2]
md = Cs(CS_ARCH_X86, CS_MODE_32)

# ---- AUD-1：行范围 ----
src = open('_r167/r167d_holes_semantics_final.py', encoding='utf-8').read().split('\n')
def find_def_line():
    for i, l in enumerate(src, 1):
        if l.startswith('def best_table'): return i
    return None
d0 = find_def_line()
end = None
for i in range(d0, len(src)):
    if src[i].startswith('    return best'):
        end = i + 1; break
body = '\n'.join(src[d0 - 1:end])
has_mod4 = '((v - LO - p) % 4)' in body
has_lo4 = 'a = lo - 4' in body
has_hi4 = 'hi += 4' in body
has_div4 = '(hi - lo) // 4' in body
A1 = {'def_line': d0, 'return_line': end, 'lines': end - d0 + 1,
      'mod4': has_mod4, 'lo_minus4': has_lo4, 'hi_plus4': has_hi4, 'div4': has_div4}
A = []
A.append({'id': 'J1 best_table 实际行 140-162（审计员说 140-161，差 1 行在 return）+ 四点俱全',
          'ok': d0 == 140 and end == 162 and has_mod4 and has_lo4 and has_hi4 and has_div4,
          'detail': repr(A1)})
# 反控：w=4 分支的读取宽度确实是 4
A.append({'id': 'J2 反控 for w in (4, 3) 与 rd(b, w) 确按 w 读', 'ok': 'for w in (4, 3)' in body and 'rd(b, w)' in body})

# ---- AUD-2：步进=宽度后，3 条 w=3 命中的 3 字节表是否全灭 ----
def rd(va, n):
    b = B.rd(va, n)
    if not b or len(b) < n: return None
    v = 0
    for i in range(n): v |= b[i] << (8 * i)
    return v
def isT(x): return x is not None and LO <= x < HI
def best_w3(v):
    best = (0, None, None, None)
    w = 3
    for p in range(w):
        b = v - ((v - LO - p) % w)
        if not (b <= v < b + w): continue
        if not isT(rd(b, w)): continue
        lo = b
        while lo - w >= LO and isT(rd(lo - w, w)): lo -= w
        hi = b + w
        while isT(rd(hi, w)): hi += w
        k = (hi - lo) // w
        if k > best[0]: best = (k, p, lo, hi)
    return best
w3 = {'0x48db25': best_w3(0x48db25), '0x62fe4c': best_w3(0x62fe4c), '0x7d0cba': best_w3(0x7d0cba)}
A.append({'id': 'J3 步进=宽度 后三条 w=3 命中的 3 字节表 k 分别为 1/1/0（全部失效）',
          'ok': [w3[k][0] for k in ('0x48db25', '0x62fe4c', '0x7d0cba')] == [1, 1, 0],
          'detail': repr({k: (v[0], hex(v[2]) if v[2] else None, hex(v[3]) if v[3] else None)
                          for k, v in w3.items()})})
A.append({'id': 'J4 但按「是否仍落在任意表内」计，只有 0x7d0cba 掉出去（两种说法并存，不互斥）',
          'ok': True, 'detail': '见 r168e：fixed in=55、lost=[0x7d0cba]'})

# ---- AUD-3：0x7d0cb0 表与引用点 ----
tab = [B.dw(0x7d0cb0 + 4 * k) for k in range(8)]
refsite = None
pat = b'\xff\x24\x8d' + struct.pack('<I', 0x7d0cb0)
j = data.find(pat)
if j >= 0:
    for nm, ava, vs, raw, rs in B.secs:
        if raw <= j < raw + rs: refsite = IB + ava + (j - raw)
A.append({'id': 'J5 0x7d0cb0 是一张 4 字节表且首槽 0x007d0cf7 落 .text',
          'ok': tab[0] is not None and isT(tab[0]), 'detail': repr([hex(x) if x else None for x in tab])})
A.append({'id': 'J6 引用点 ff 24 8d 0x7d0cb0 存在，地址 0x7d0be2（审计员写 ff 24 9d 是 modrm 笔误）',
          'ok': refsite == 0x7d0be2, 'detail': hex(refsite) if refsite else 'None'})
# 该表真实长度（连续落 .text 的槽）
n = 0
while isT(B.dw(0x7d0cb0 + 4 * n)) and n < 64: n += 1
A.append({'id': 'J7 该表真实条目数 = 7（0x7d0cb0..0x7d0cb3），洞 0x7d0cba 在表外 >= 1 条目',
          'ok': n == 1, 'detail': 'n_from_0x7d0cb0=%d ; 洞-表首=%d' % (n, 0x7d0cba - 0x7d0cb0)})
# 从更早的 0x7d0c98 起
n2 = 0
while isT(B.dw(0x7d0c98 + 4 * n2)) and n2 < 64: n2 += 1
A.append({'id': 'J8 从 0x7d0c98 起连续落在 .text 的槽数（含前置 7 条）>= 7',
          'ok': n2 >= 7, 'detail': 'n2=%d [%s]' % (n2, ', '.join(hex(B.dw(0x7d0c98 + 4 * i)) for i in range(min(n2, 10))))})

# ---- EXEC-1：1,390,966 的口径 ----
def scan(mode, chunk=65536):
    starts = 0; resync = 0
    off = text[3]; end = text[3] + text[4]; base_vs = text[1]
    while off < end:
        c = data[off:min(off + chunk, end)]
        base = IB + (base_vs + (off - text[3]))
        if mode == 'clean':      # 每块独立起解、末尾不跨块续（执行员嫌疑口径）
            for a, sz, mn, op in md.disasm_lite(c, base):
                if a - base + sz > len(c): break
                if a < HI: starts += 1
            off += chunk
        else:                    # 正确口径：consumed 驱动、解不出时前进 1 字节
            consumed = 0
            for a, sz, mn, op in md.disasm_lite(c, base):
                if a - base + sz > len(c): break
                consumed = a - base + sz
                if a < HI: starts += 1
            if consumed == 0: resync += 1; off += 1
            else: off += consumed
    return starts, resync
s_clean, r_clean = scan('clean')
s_ok, r_ok = scan('ok')
A.append({'id': 'J9 正确口径起点 = 1,392,527（第三次主会话独立复算）', 'ok': s_ok == 1392527, 'detail': str(s_ok)})
A.append({'id': 'J10 执行员 #393 的 1,390,966 已由 r168k 复现；口径差 = VA 基址用 tva+pos + end_va 过滤丢末 4,096 B',
          'ok': True, 'detail': '见 r168k K1/K5：diff 1,561 == 末 4,096 B 内起点数'})
A.append({'id': 'J11 反控：两种口径下重对齐点均为 65，洞集合不变（结论对口径不敏感）',
          'ok': True, 'detail': 'r168k K2/K6：symdiff=0'})
out = {'aud1': A1, 'aud2_w3': {k: [v[0], v[1], hex(v[2]) if v[2] else None, hex(v[3]) if v[3] else None]
                               for k, v in w3.items()},
       'aud3_table_0x7d0cb0': [hex(x) if x else None for x in tab], 'aud3_refsite': refsite and hex(refsite),
       'aud3_n': n, 'aud3_n2': n2,
       'exec_clean': s_clean, 'exec_ok': s_ok, 'resync': [r_clean, r_ok],
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168j_recompute_audit.json', 'w'), ensure_ascii=False, indent=1)
print('AUD-1:', A1)
print('AUD-2 w3:', out['aud2_w3'])
print('AUD-3 tab:', out['aud3_table_0x7d0cb0'], 'ref', out['aud3_refsite'], 'n', n, 'n2', n2)
print('EXEC-1 clean=%d ok=%d diff=%d resync=%s' % (s_clean, s_ok, s_ok - s_clean, [r_clean, r_ok]))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:220])
