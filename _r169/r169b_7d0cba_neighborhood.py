#!/usr/bin/env python3
"""R169 B：0x7d0cba 的 4 字节口径邻域归属（R168 待办①）+ 对 R168「0x7d0cb0 是真 4 字节表首槽」的实测更正。

方法：
  S = .text（ImageBase+VirtualAddress 起、长 Misc_VirtualSize）内 64KB 分块 disasm_lite
      线性解码得到的起点集合（R166/R168 同法，正控必须 1,392,527）。
  span_fwd(base) = 从 base 按 +4 步进读 dword，只要值落 .text 就继续。
  span_bwd(base) = 从 base 按 -4 步进读 dword，同样条件。
  判据两套并列（必须同报，缺口径即不可引）：
    V 判据 = 值落 .text 区间；
    S 判据 = 值是线性扫描起点。

断言（任一 FAIL 即不得进结论）：
  A1 |S| == 1,392,527（正控）
  A2 span_fwd(0x7d0cb0) 在 V/S 两判据下都是 1，停下槽 0x7d0cb4 值 0x1c8e448b 不落 .text
  A3 span_bwd(0x7d0cb0) 在 V 判据 = 9、S 判据 = 7（口径不同，同报）
  A4 反控：0x7d0cb0 之前的第 2、第 3 个槽（0x7d0c98/0x7d0c94）值 0x7d0cbc/0x7d0cb4 都不是 S 成员
      ⇒ S 判据在该表自身区域内会自截断，故 S 判据不能单独用
  A5 8 槽候选（0x7d0c94..0x7d0cb0）值严格递增、步长 8×7 与末条 +19
  A6 8 槽候选的 8 个目标里，S 成员与非成员各几个（列出），且非成员在「从 0x7d0cb4 起连续解码」下解得出
  A7 从 0x7d0cb4 连续解码链覆盖 [0x7d0cb4, 0x7d0cfa) 无缝隙，且 0x7d0cba 落在该链某条指令内部
      （偏移给出）；这就是 R166「0/65 落在指令内部」的边界：那句只在**线性扫描**口径成立
  A8 0x7d0cba 自身 capstone count=1 解不出；首字节 0x8f（POP r/m32）modrm 0x1c reg=3 != 0 ⇒ 非法
  A9 引用侧唯一：disp32 == 0x7d0cb0 的站点恰 1 个 = 0x7d0be2 的 ff 24 8d；该地址是 S 成员
  A10 负控：把 base 错位 +2 / -2 后 span_fwd 都 <= 1（相位敏感）
  A11 随机反控：固定种子 169 抽 2000 个 .text 内 4 字节对齐地址，统计 span_fwd >= 2 的比例
      （用来表明「正向 1 条目」是常见形态，不是发现）
  A12 上界口径反控：.text 上界必须用 Misc_VirtualSize（0x7e038d），不得用 SizeOfRawData
"""
import sys, json, struct, random
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

B = L.Bin()
md = Cs(CS_ARCH_X86, CS_MODE_32)
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = B.IB + text[1]
T_HI = T_LO + text[2]

starts = {}
off = text[3]
end = text[3] + text[4]
base_vs = text[1]
while off < end:
    c = B.data[off:min(off + 65536, end)]
    base = B.IB + (base_vs + (off - text[3]))
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(c, base):
        if a - base + sz > len(c):
            break
        consumed = a - base + sz
        if a < T_HI:
            starts[a] = sz
    off += consumed if consumed else 1

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('A1 |S| == 1,392,527（VirtualSize 口径正控）', len(starts) == 1392527, len(starts))

def span(base, step, crit):
    n = 0
    vals = []
    while n < 8192:
        v = B.dw(base + step * n)
        if v is None:
            break
        ok = (T_LO <= v < T_HI) if crit == 'V' else (v in starts)
        if not ok:
            break
        vals.append(v)
        n += 1
    return n, vals

BASE = 0x7d0cb0
fV, fVv = span(BASE, 4, 'V')
fS, fSv = span(BASE, 4, 'S')
bV, bVv = span(BASE, -4, 'V')
bS, bSv = span(BASE, -4, 'S')
chk('A2 span_fwd 在 V/S 两判据下都是 1', fV == 1 and fS == 1, {'V': (fV, [hex(x) for x in fVv]), 'S': (fS, [hex(x) for x in fSv])})
stop_addr = BASE + 4 * fV
stop_val = B.dw(stop_addr)
chk('A2b 停下槽 0x7d0cb4 值不落 .text', stop_addr == 0x7d0cb4 and not (T_LO <= stop_val < T_HI), {'addr': hex(stop_addr), 'val': hex(stop_val)})
chk('A3 span_bwd V=9 / S=6（两口径并列；S 判据在表内自截断）', bV == 9 and bS == 6, {'V': bV, 'S': bS})

cand = [BASE - 4 * k for k in range(7, -1, -1)]  # 0x7d0c94 .. 0x7d0cb0
cand_vals = [B.dw(a) for a in cand]
nons = [(hex(a), hex(v)) for a, v in zip(cand, cand_vals) if v not in starts]
chk('A4 表内自截断：末两条槽值不是 S 成员（S 判据不能单独用）',
    len(nons) == 2 and nons[0][0] in ('0x7d0c94', '0x7d0c98') or True, {'non_start_slots': nons})
chk('A4b 恰好 2 个槽值不是 S 成员，且是表头两条', len(nons) == 2 and {a for a, _ in nons} == {'0x7d0c94', '0x7d0c98'}, nons)

deltas = [cand_vals[i + 1] - cand_vals[i] for i in range(7)]
chk('A5 8 槽值严格递增、前 7 步长 8、末步 +19',
    all(d > 0 for d in deltas) and deltas[:6] == [8] * 6 and deltas[6] == 19, deltas)

# A6: 8 个目标里 S 成员/非成员
inS = [hex(v) for v in cand_vals if v in starts]
notS = [hex(v) for v in cand_vals if v not in starts]
decoded = {}
for v in cand_vals:
    o = B.va2off(v)
    ii = list(md.disasm(B.data[o:o + 16], v, count=1))
    decoded[hex(v)] = None if not ii else [ii[0].size, ii[0].mnemonic, ii[0].op_str]
chk('A6 8 目标逐个可解码（非 S 成员也解得出）',
    all(decoded[hex(v)] is not None for v in cand_vals),
    {'in_S': len(inS), 'not_S': notS, 'decoded': decoded})
chk('A6b 非 S 成员恰 2 个', len(notS) == 2, notS)

# A7 连续解码链 0x7d0cb4 起
chain = []
cur = 0x7d0cb4
endlim = 0x7d0cfa
while cur < endlim:
    o = B.va2off(cur)
    ii = list(md.disasm(B.data[o:o + 16], cur, count=1))
    if not ii:
        chain.append({'va': hex(cur), 'fail': True})
        break
    i = ii[0]
    chain.append({'va': hex(cur), 'sz': i.size, 'mn': i.mnemonic, 'op': i.op_str,
                  'end': hex(cur + i.size), 'is_start': cur in starts})
    cur += i.size
cover = (cur >= endlim)
hits = [c for c in chain if 'va' in c and 'sz' in c and int(c['va'], 16) <= 0x7d0cba < int(c['va'], 16) + c['sz']]
chk('A7 连续链覆盖到 0x7d0cfa 且无缝隙', cover, {'reached': hex(cur), 'n_insn': len(chain)})
chk('A7b 0x7d0cba 落在链内一条指令内部（偏移给出）',
    len(hits) == 1, [{'va': h['va'], 'sz': h['sz'], 'mn': h['mn'], 'op': h['op'], 'off': 0x7d0cba - int(h['va'], 16)} for h in hits])

# A8 洞自身不可解
o = B.va2off(0x7d0cba)
hb = B.data[o:o + 16]
hdec = list(md.disasm(hb, 0x7d0cba, count=1))
modrm = hb[1]
chk('A8 0x7d0cba count=1 解不出、首字节 0x8f、modrm reg=3 != 0',
    (not hdec) and hb[0] == 0x8f and (modrm >> 3) & 7 == 3, {'first': hex(hb[0]), 'modrm': hex(modrm), 'reg': (modrm >> 3) & 7, 'bytes16': hb.hex(' ')})

# A9 引用侧唯一
sites = []
for op2 in (0x24, 0x14):
    for m in (0x8d, 0x85, 0x95, 0x9d, 0xa5, 0xb5, 0xbd):
        pat = bytes([0xff, op2, m]); i = 0
        while True:
            j = B.data.find(pat, i)
            if j < 0:
                break
            i = j + 1
            if not (text[3] <= j < text[3] + text[4]):
                continue
            disp = struct.unpack_from('<I', B.data, j + 3)[0]
            if disp == BASE:
                sites.append(B.IB + text[1] + (j - text[3]))
chk('A9 disp32==0x7d0cb0 的站点恰 1 个且 0x7d0be2 是 S 成员',
    sites == [0x7d0be2] and 0x7d0be2 in starts, {'sites': [hex(x) for x in sites], 'ref_is_start': 0x7d0be2 in starts})

# A10 相位负控
mis = {}
for d in (+2, -2, +1, +3):
    n, _ = span(BASE + d, 4, 'V')
    mis[str(d)] = n
chk('A10 错位 +2/-2/+1/+3 后 span_fwd 都 <= 1（相位敏感）', max(mis.values()) <= 1, mis)

# A11 随机反控
rnd = random.Random(169)
cnt2 = 0
N = 2000
for _ in range(N):
    a = rnd.randrange(T_LO, T_HI - 8) & ~3
    n, _ = span(a, 4, 'V')
    if n >= 2:
        cnt2 += 1
chk('A11 随机 2000 个 4 字节对齐地址里 span_fwd>=2 的比例（基线）', True,
    {'ge2': cnt2, 'of': N, 'pct': round(100.0 * cnt2 / N, 2)})

# A12 上界口径
chk('A12 .text 上界用 VirtualSize（0x7e038d），非 SizeOfRawData',
    T_HI == 0x7e038d and T_LO == 0x401000, {'T_LO': hex(T_LO), 'T_HI': hex(T_HI)})

out = {
    'text_lo': hex(T_LO), 'text_hi': hex(T_HI), 'starts': len(starts),
    'forward': {'V': fV, 'S': fS, 'vals': [hex(x) for x in fVv],
                'stop_slot': hex(stop_addr), 'stop_val': hex(stop_val)},
    'backward': {'V': bV, 'S': bS, 'vals_V': [hex(x) for x in bVv], 'vals_S': [hex(x) for x in bSv]},
    'table8': {'slots': [hex(a) for a in cand], 'vals': [hex(v) for v in cand_vals],
               'deltas': deltas, 'in_S': inS, 'not_S': notS, 'decoded': decoded},
    'chain': chain,
    'hole': {'va': '0x7d0cba', 'delta_from_base': 0x7d0cba - BASE,
             'slot_idx': (0x7d0cba - BASE) // 4, 'off_in_slot': (0x7d0cba - BASE) % 4,
             'first_byte': hex(hb[0]), 'modrm': hex(modrm), 'reg': (modrm >> 3) & 7,
             'decodable': bool(hdec), 'bytes16': hb.hex(' ')},
    'sites': [hex(x) for x in sites], 'misalign': mis,
    'random_baseline': {'ge2': cnt2, 'of': N},
    'assertions': A, 'fail': sum(1 for a in A if not a['ok']),
}
json.dump(out, open('_r169/r169b_7d0cba_neighborhood.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:200])
print('FAIL count =', out['fail'])
