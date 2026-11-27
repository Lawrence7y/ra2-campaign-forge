#!/usr/bin/env python3
"""R145 H：两条独立判据在同 4 张上的交叉 + 分母口径修正（含 S-316 自错登记）。

r145c 里我把「修复后覆盖 1214」与「误收 4 张」写成 truth_denom = 1214 - 4 = 1210 —— 算术错：
   VTS = 1218；宽容六形态并集 = 1214；残余 = 4，且残余集合 **恰等于** 误收集合。
   ⇒ 并集 = VTS − 误收 = 真虚表全集 ⇒ 真分母 1214、覆盖 1214/1214 = 100%，
     不是 1210。S-316 登记在此，本脚本用可失败断言重算。

本脚本做交叉：判据 A（RTTI 槽质量：前 8 槽落 .text 的个数为 0 ⇒ 不像虚表）
              判据 B（静态装表：六形态里一个站点都没有 ⇒ 不像被装过的虚表）
两判据互不依赖（A 只看表体字节，B 只看代码里的写站点），若在**同一 4 张**上一致，
则「这 4 张不是虚表」从单判据升为双判据交叉。
"""
import sys, re, json, struct, collections, hashlib
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin()
TDs, COL, VTS = B.vtset()
d = json.load(open('_r145/r145d_tolerant_union.json'))
resid_install = set(int(x, 16) for x in d['resid'])
union = set(VTS) - resid_install

# 判据 A：前 8 槽落 .text 的个数
qual = {}
for vt in VTS:
    n = 0
    for k in range(8):
        v = B.dw(vt + 4 * k)
        if v and B.sec_of(v) == '.text': n += 1
    qual[vt] = n
A_bad = {vt for vt in VTS if qual[vt] == 0}
B_bad = resid_install
both = A_bad & B_bad
onlyA = A_bad - B_bad
onlyB = B_bad - A_bad

# 深一层：判据 A 的「槽值不落在任何节内」子判据
def slots_in_no_section(vt):
    bad = 0
    for k in range(8):
        v = B.dw(vt + 4 * k)
        if v and B.sec_of(v) is None: bad += 1
    return bad
A_bad_nosec = {vt for vt in A_bad if slots_in_no_section(vt) >= 1}

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'vt_distinct': len(VTS),
 'A_bad_n': len(A_bad), 'A_bad': sorted(hex(v) for v in A_bad),
 'B_bad_n': len(B_bad), 'B_bad': sorted(hex(v) for v in B_bad),
 'both_n': len(both), 'onlyA': sorted(hex(v) for v in onlyA), 'onlyB': sorted(hex(v) for v in onlyB),
 'A_bad_with_out_of_section_slot': sorted(hex(v) for v in A_bad_nosec),
 'union_after_fix': len(union),
 'true_denom': len(VTS) - len(A_bad),
 'coverage_of_true': '%d/%d' % (len(VTS) - len(A_bad) - len(onlyB), len(VTS) - len(A_bad)),
 'coverage_rate': round((len(VTS) - len(A_bad) - len(onlyB)) / (len(VTS) - len(A_bad)), 4),
 'denom_1210_was_wrong': True,
 'qual_hist': collections.Counter(qual.values()).most_common(),
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('正控：判据 A 给出恰 4 张（与 r144l zero_slots_n=4 一致）', len(A_bad) == 4, len(A_bad))
chk('正控：判据 B 给出恰 4 张（与 r145d resid 一致）', len(B_bad) == 4, len(B_bad))
chk('两判据在完全相同的 4 张上一致（交集 4、两个差集为空）', both == A_bad == B_bad, [sorted(hex(v) for v in onlyA), sorted(hex(v) for v in onlyB)])
chk('这 4 张都有「槽值不落在任何节内」的槽（A 的独立性佐证）', A_bad_nosec == A_bad, sorted(hex(v) for v in A_bad_nosec))
chk('真分母 = 1218 − 4 = 1214（不是 1210，S-316）', res['true_denom'] == 1214, res['true_denom'])
chk('真虚表覆盖率 = 1214/1214 = 100%', res['coverage_rate'] == 1.0, res['coverage_of_true'])
chk('反控：若把 4 张误收留在分母里，覆盖率是 1214/1218 = 99.67%（两个数都必须报）', round(len(union) / len(VTS), 4) == 0.9967, round(len(union) / len(VTS), 4))
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r145/r145h_dualcrit.json', 'w'), indent=1)
for k in ('A_bad','B_bad','both_n','onlyA','onlyB','A_bad_with_out_of_section_slot','union_after_fix','true_denom','coverage_of_true','coverage_rate','qual_hist'):
    print(k, '=', json.dumps(res[k], ensure_ascii=False))
for p in POS: print(('PASS ' if p[1] else 'FAIL ') + '%-64s %s' % (p[0], p[2]))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
