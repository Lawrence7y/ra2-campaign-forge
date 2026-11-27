#!/usr/bin/env python3
"""R144 L：VTS 建表质量普查 —— 1218 里有几张其实不是虚表？

R144K 发现 4 张（0x877000/0x877010/0x87b17c/0x87b18c）前 8 槽里落 .text 的有 0 个，
但被 VTS 规则（dword[vt-4] ∈ COL）收进来了，且共用同一个 COL 0x800040。
本脚本对全部 1218 张统计「前 N 槽里有几个落 .text」，给出分布与阈值敏感性，
并回答：改正后分母是多少、R143 的 838/1218 与 68/2741 会不会变。

判据（可失败）：真虚表的槽必须是函数指针 ⇒ 前 8 槽中落 .text 的个数应 >= 1。
反控：随机取 1218 个 .data dword 作伪虚表，同一统计量的分布必须几乎全为 0。
"""
import sys, json, struct, collections, random, hashlib
sys.path.insert(0, '_r143')
import r143lib as L

B = L.Bin()
TDs, COL, VTS = B.vtset()
GEN = L.GEN

def txt_slots(vt, n=8):
    c = 0
    for k in range(n):
        v = B.dw(vt + 4 * k)
        if v and B.sec_of(v) == '.text': c += 1
    return c

dist = collections.Counter()
zero = []
for vt in VTS:
    c = txt_slots(vt)
    dist[c] += 1
    if c == 0: zero.append(vt)

# 按阈值敏感性
ths = {t: sum(n for c, n in dist.items() if c >= t) for t in (1, 2, 3, 4)}
# 对 1218 之外的对照
random.seed(144)
pool = [vt for vt in VTS]      # 用 VTS 自己的地址作对照：不，用等势随机 .data 地址
rand_pts = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        base = B.IB + ava
        for i in range(0, rs - 40, 4):
            rand_pts.append(base + i)
CTRL = random.sample(rand_pts, len(VTS))
ctrl_zero = sum(1 for p in CTRL if txt_slots(p) == 0)
ctrl_dist = collections.Counter(txt_slots(p) for p in CTRL)

# 这 4 张的 COL 是不是「假 COL」：COL 0x800040 的 sig/classdesc 是否合规
sus = zero
susinfo = []
for vt in sus:
    c = B.dw(vt - 4)
    susinfo.append({'vt': hex(vt), 'col': hex(c) if c else None,
                    'in_COL': c in COL,
                    'col_sig': hex(B.dw(c)) if c else None,
                    'td': hex(B.dw(c + 12)) if c else None,
                    'td_sec': B.sec_of(B.dw(c + 12)) if c else None,
                    'offset': B.dw(c + 4) if c else None})

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'vt_distinct': len(VTS), 'td': len(TDs), 'col': len(COL),
 'slots_into_text_hist': dict(sorted(dist.items())),
 'zero_slots_n': len(zero), 'zero_slots': [hex(v) for v in zero],
 'threshold_sensitivity': ths,
 'ctrl_zero_slots_n': ctrl_zero, 'ctrl_hist': dict(sorted(ctrl_dist.items())),
 'adjusted_vt_distinct': len(VTS) - len(zero),
 'susinfo': susinfo,
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('绝大多数 VTS 成员前 8 槽里有 >=1 个落 .text（>= 99%）', ths[1] >= 0.99 * len(VTS), [ths[1], len(VTS)])
chk('前 8 槽全不落 .text 的 VTS 成员是少数（<= 10）', len(zero) <= 10, len(zero))
chk('随机对照点前 8 槽落 .text 为 0 的比例远高于 VTS 组', ctrl_zero / len(CTRL) > 0.9, round(ctrl_zero / len(CTRL), 4))
chk('把零槽成员剔除后分母 >= 1200（改动量小）', len(VTS) - len(zero) >= 1200, len(VTS) - len(zero))
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144l_vts_quality.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'POS'}, indent=1, ensure_ascii=False)[:3000])
print('\n'.join('%-62s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
