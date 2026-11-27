#!/usr/bin/env python3
"""R144 G：残余 45 张在 .text 里的原始字节命中，究竟是不是「指令操作数」。

r144f 的发现与 r144e 冲突：disasm 口径说 44/45 文本侧 0 引用，原始字节说 45/45 都在 .text 里出现
（平均 1.82 次）。两者只能有一个解释：
  (a) 这些 4 字节恰好落在指令的**立即数**里但 capstone 打印成十进制（我 R144E 用 0x... 正则 → 漏）；
  (b) 这些 4 字节跨在两条指令之间 / 落在数据填充里（字节巧合）。
本脚本对每个命中 VA 取 ±16 字节上下文反汇编，并判定：
  in_start  : 该 VA 是否为我 sweep 的某条指令起点
  covers    : 是否存在一条指令 [start, start+size) 覆盖全部 4 字节
  operand   : 若 covers，把该指令操作数打印出来（看是不是 imm）
  misalign  : 命中 VA 不在任何 sweep 指令起点上也未被覆盖 ⇒ 字节巧合
"""
import sys, json, struct, collections, hashlib
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
fr = json.load(open('_r144/r144f_raw.json'))
rows = fr['resid_rows']

# 建立 sweep 指令表（起点 -> (size, mn, op)），只对命中位置附近查
hits = []
for r in rows:
    vt = r[0]
    for va in r[3]:
        hits.append((vt, int(va, 16)))

def dis_at(va, back=16, fwd=32):
    b = B.rd(va - back, back + fwd + 4)
    if b is None: return []
    return [(a, sz, mn, L.norm(op)) for a, sz, mn, op in md.disasm_lite(b, va - back)]

verdicts = []
for vt, va in hits:
    seq = dis_at(va)
    in_start = any(a == va for a, sz, mn, op in seq)
    covers = None
    for a, sz, mn, op in seq:
        if a <= va and va + 4 <= a + sz:
            covers = (a, sz, mn, op); break
    kind = 'operand' if covers else ('boundary' if not covers else '?')
    verdicts.append({'vt': vt, 'va': hex(va), 'in_start': in_start,
                     'covers': [hex(covers[0]), covers[1], covers[2], covers[3]] if covers else None,
                     'before': [[hex(a), mn, op] for a, sz, mn, op in seq if a < va][-2:],
                     'at': [[hex(a), mn, op] for a, sz, mn, op in seq if a == va]})

cnt = collections.Counter(v['covers'] is not None for v in verdicts)
imm_hits = [v for v in verdicts if v['covers'] and '0x' in (v['covers'][3] or '')]
dec_hits = [v for v in verdicts if v['covers'] and v['covers'][3] and '0x' not in v['covers'][3]]

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(),
 'hits_total': len(hits), 'in_start_n': sum(1 for v in verdicts if v['in_start']),
 'covered_n': cnt[True], 'uncovered_n': cnt[False],
 'operand_with_hex': len(imm_hits), 'operand_no_hex': len(dec_hits),
 'verdicts': verdicts[:24],
 'sample_uncovered': [v for v in verdicts if not v['covers']][:6],
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('所有原始命中都被某条 sweep 指令覆盖（不是跨指令字节巧合）', cnt[False] == 0, [cnt[True], cnt[False]])
chk('存在「被覆盖但操作数里没有 0x」的命中（这是 R144E 漏计的真原因）', len(dec_hits) > 0, len(dec_hits))
chk('命中位置等于指令起点的很少（多数是 imm 字段）', sum(1 for v in verdicts if v['in_start']) < len(verdicts) / 2, sum(1 for v in verdicts if v['in_start']))
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144g_resid_ctx.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'verdicts'}, indent=1, ensure_ascii=False)[:2500])
print('verdicts', json.dumps(verdicts[:12], ensure_ascii=False)[:2600])
print('\n'.join('%-64s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
