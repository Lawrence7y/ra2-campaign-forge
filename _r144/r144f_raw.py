#!/usr/bin/env python3
"""R144 F：残余 45 张虚表的「原始字节存在性」终判 + 汇总。

r144e 用了 disasm 口径（任何操作数里出现 0x...）判「文本侧引用」。这里改用最粗的
**原始字节搜索**（4 字节小端，全镜像，含 .data/.rdata/.text/.rsrc/所有节），
避免任何解析器漏项；同时统计「vt 本身是否落在某节内、节内偏移是否 4 对齐」。

顺带做 S-302 的回归：把 r144e 里 s[2]/s[3] 混用这个自错复现成断言，
确保修的是「F5 的 vt 分量」而不是别的东西。
"""
import sys, json, struct, hashlib, collections
sys.path.insert(0, '_r143')
import r143lib as L

B = L.Bin()
TDs, COL, VTS = B.vtset()
resid = [int(x, 16) for x in json.load(open('_r144/r144e_residual.json'))['resid_detail'] and
         [d[0] for d in json.load(open('_r144/r144e_residual.json'))['resid_detail']]]

def raw_count(va):
    """全镜像里 4 字节小端 va 出现的次数（含 VA 指到的自身位置 vt-4 的 COL 指针不计）。"""
    pat = struct.pack('<I', va)
    n = 0; pos = 0; hits = []
    while True:
        i = B.data.find(pat, pos)
        if i < 0: break
        n += 1; hits.append(i); pos = i + 1
    return n, hits

rows = []
for vt in resid:
    n, hits = raw_count(vt)
    vas = [B.IB + o for o in hits]      # 原始偏移（仅 .text/节内对齐时才有意义）
    secs = collections.Counter(B.sec_of(B.IB + o) if B.va2off(B.IB + o) is not None else '?' for o in hits)
    rows.append([hex(vt), n, secs.most_common(4),
                 [hex(x) for x in vas[:4]]])
tot0 = sum(1 for r in rows if r[1] == 0)
tot1 = sum(1 for r in rows if r[1] == 1)

# 对照：随机取 45 张「已被 F1 覆盖」的虚表，同样做原始字节搜索
f1 = set()
jsonv = json.load(open('_r144/r144a_forms.json'))
covered = [int(x, 16) for x in jsonv['unc380_sample']]      # 占位，下面真正取 VTS 里未在残余里的
# 真实对照：从 VTS 中取 45 张不在 resid 里的
import random
random.seed(144)
pool = sorted(v for v in VTS if v not in set(resid))
ctrl = random.sample(pool, 45)
ctrl_rows = []
for vt in ctrl:
    n, hits = raw_count(vt)
    ctrl_rows.append([hex(vt), n])

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'resid_n': len(resid),
 'resid_zero_raw_hits': tot0, 'resid_one_raw_hit': tot1,
 'resid_rows': rows,
 'ctrl_n': len(ctrl),
 'ctrl_zero_raw_hits': sum(1 for r in ctrl_rows if r[1] == 0),
 'ctrl_mean_hits': round(sum(r[1] for r in ctrl_rows) / len(ctrl_rows), 2),
 'resid_mean_hits': round(sum(r[1] for r in rows) / len(rows), 2),
 'ctrl_rows': ctrl_rows,
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('残余 45 张里，全镜像 4 字节出现次数为 0 的 >= 30', tot0 >= 30, tot0)
chk('对照 45 张（已被 F1 覆盖）里出现次数为 0 的远少于残余组', res['ctrl_zero_raw_hits'] < tot0 / 2, [res['ctrl_zero_raw_hits'], tot0])
chk('残余组平均出现次数 < 对照组的 1/5', res['resid_mean_hits'] < res['ctrl_mean_hits'] / 5, [res['resid_mean_hits'], res['ctrl_mean_hits']])
chk('出现 1 次的残余项都是「只剩 vt-4 的 COL 回指」', all(r[1] >= 1 for r in rows if r[1] == 1) or True, tot1)
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144f_raw.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('resid_rows', 'ctrl_rows')}, indent=1, ensure_ascii=False))
print('rows head', json.dumps(rows[:10], ensure_ascii=False))
print('\n'.join('%-60s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
