# -*- coding: utf-8 -*-
"""R210-A 主视图 mdisp==0 表 slot>=3 槽族普查（纯静态，只读 q3.json）。

槽编号约定：q3/q5 中 VT[c][0]/[1]/[2] 是 IUnknown 三方法（slot0/1/2），
故 slot3 == VT[c][3]（第四槽），slot>=3 == index>=3。
"""
import sys, os, json, random, collections
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

class Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, s):
        for st in self.streams:
            st.write(s)
    def flush(self):
        for st in self.streams:
            st.flush()

_fout = open(ROOT + '/_r210/a1.txt', 'w')
sys.stdout = Tee(sys.__stdout__, _fout)

Q3 = json.load(open(ROOT + '/_r209/q3.json'))
Q5 = json.load(open(ROOT + '/_r209/q5.json'))
MD = {int(k, 16): int(v) for k, v in Q3['mdisp'].items()}
VT = {int(k, 16): [int(x, 16) for x in v] for k, v in Q3['vt'].items()}
VO = {int(k, 16): int(v, 16) for k, v in Q3['vt_of'].items()}
NM = {int(k, 16): v for k, v in Q3['names'].items()}

md = Cs(CS_ARCH_X86, CS_MODE_32)   # 不开 detail=True
RET_CACHE = {}

def ret_of(addr, cap=256):
    """只反汇编 addr 起始的 <=256 字节，取第一条 ret 的机器码。"""
    if addr in RET_CACHE:
        return RET_CACHE[addr]
    res = {'addr': hex(addr), 'bytes': None, 'label': 'none', 'imm': None, 'err': None}
    try:
        o = P.r2o(addr)
        if o is None:
            res['err'] = 'not-file-backed'
        else:
            found = False
            for ins in md.disasm(bytes(P.RAW[o:o + cap]), addr):
                if ins.mnemonic == 'ret':
                    b = bytes(ins.bytes)
                    res['bytes'] = b.hex()
                    if b and b[0] == 0xc2 and len(b) >= 3:
                        imm = int.from_bytes(b[1:3], 'little')
                        res['imm'] = imm
                        res['label'] = ('ret 0x%x' % imm) if imm else 'ret'
                    elif b and b[0] == 0xc3:
                        res['imm'] = 0
                        res['label'] = 'ret'
                    else:
                        res['label'] = 'ret-other'
                    found = True
                    break
            if not found:
                res['label'] = 'none'
    except Exception as e:
        res['err'] = repr(e)
    RET_CACHE[addr] = res
    return res

def slot_key(i):
    return str(i) if 3 <= i <= 8 else '9+'

fails = []
NA = 0
def ck(name, cond, detail=''):
    global NA
    NA += 1
    ok = bool(cond)
    if not ok:
        fails.append(name)
    print(('PASS ' if ok else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''))

print('# R210-A 主视图 954 表 slot>=3 槽族普查（静态）')
main = sorted(c for c in MD if MD[c] == 0 and c in VT)
ck('A1 mdisp==0 表数 == 954', len(main) == 954, '实测 %d' % len(main))

total_slots = sum(len(VT[c]) for c in main)
sum_min3 = sum(min(3, len(VT[c])) for c in main)
ge3_expected = total_slots - sum_min3
ge3_actual = 0
per_table = []
for c in main:
    slots = VT[c]
    rows = []
    for i in range(3, len(slots)):
        r = ret_of(slots[i])
        rows.append({'slot': i, 'addr': hex(slots[i]), 'ret_label': r['label'],
                     'ret_bytes': r['bytes'], 'imm': r['imm']})
        ge3_actual += 1
    per_table.append({
        'col': hex(c), 'vt': hex(VO[c]), 'vftable': hex(VO[c]),
        'nslots': len(slots), 'name': NM.get(c),
        'allslots': [hex(x) for x in slots],
        'slot3': hex(slots[3]) if len(slots) > 3 else None,   # index 3 == slot 3
        'slot_ge3': rows,
    })
ck('A2 slot>=3 槽总数 = 全槽数 - 每表 min(3,len) 之和（脚本自算）',
   ge3_actual == ge3_expected,
   '全槽=%d, sum(min(3,len))=%d (954*3=%d), 期望=%d, 实测=%d'
   % (total_slots, sum_min3, 954 * 3, ge3_expected, ge3_actual))

# 二维桶：(slot 3..8 / 9+, ret label)
bucket = collections.Counter()
for t in per_table:
    for r in t['slot_ge3']:
        bucket[(slot_key(r['slot']), r['ret_label'])] += 1
labels = sorted({k[1] for k in bucket})
order = ['3', '4', '5', '6', '7', '8', '9+']
buckets_out = {}
for s in order:
    for lab in labels:
        if bucket[(s, lab)]:
            buckets_out['%s|%s' % (s, lab)] = bucket[(s, lab)]

print('\n## 二维桶计数（行=slot，列=ret 立即数/形态）')
print('slot\\ret | ' + ' | '.join(labels) + ' | 行合计')
for s in order:
    vals = [bucket[(s, lab)] for lab in labels]
    print('%-8s | ' % s + ' | '.join(str(v) for v in vals) + ' | %d' % sum(vals))
print('列合计   | ' + ' | '.join(str(sum(bucket[(s, lab)] for s in order)) for lab in labels)
      + ' | %d' % sum(bucket.values()))

# slot3（index 3）地址复用分布
s3 = [t['slot3'] for t in per_table if t['slot3'] is not None]
cnt3 = collections.Counter(s3)
addr_per_n = collections.Counter()
tables_per_n = collections.Counter()
for a, n in cnt3.items():
    key = str(n) if 1 <= n <= 10 else '>10'
    addr_per_n[key] += 1
    tables_per_n[key] += n
own_tables = sum(n for n in cnt3.values() if n == 1)
shared_tables = sum(n for n in cnt3.values() if n >= 2)
nkey = lambda x: (x == '>10', int(x) if x != '>10' else 99)
share_out = {
    'tables_with_slot3': len(s3),
    'tables_without_slot3_short': len(main) - len(s3),
    'distinct_slot3_addrs': len(cnt3),
    'own_impl_tables_N1': own_tables,
    'reuse_tables_Nge2': shared_tables,
    'addr_per_N': dict(sorted(addr_per_n.items(), key=lambda kv: nkey(kv[0]))),
    'tables_per_N': dict(sorted(tables_per_n.items(), key=lambda kv: nkey(kv[0]))),
}
print('\n## slot3（index 3）落点复用：N=1 本类自己实现 / N>=2 与其他表复用')
print('有 slot3 的表 = %d；无 slot3 的短表（长度<=3）= %d' % (len(s3), len(main) - len(s3)))
print('不同 slot3 地址 = %d；N=1 表 = %d；N>=2 表 = %d' %
      (len(cnt3), own_tables, shared_tables))
for k in sorted(addr_per_n, key=nkey):
    print('  N=%-4s : 地址数=%-4d 涉及表数=%d' % (k, addr_per_n[k], tables_per_n[k]))

# A3：slot3 ret top1 vs R209 q5 三槽 ret 分布（只打印对比，不硬判）
slot3_ret = collections.Counter(r['ret_label'] for t in per_table for r in t['slot_ge3'] if r['slot'] == 3)
q5_ret = collections.Counter(ret_of(int(r['qi'], 16))['label'] for r in Q5['rows'])
top1 = slot3_ret.most_common(1)[0] if slot3_ret else (None, 0)
ck('A3 slot3 ret top1 与 q5 三槽 ret 分布可打印对比（不硬判）',
   bool(slot3_ret) and bool(q5_ret),
   'slot3 top1=%s(%d); q5(QI目标 ret)=%s' % (top1[0], top1[1], dict(q5_ret)))
print('  R209 q5 口径：slot0 目标 ret 0xc，slot1/2 目标 ret 4（IUnknown 三方法）；'
      '本轮 slot3 是第 4 槽，二者不互相约束。')

# A4：随机 20 张表，打印 vt 起址/槽数/slot3 地址/slot3 ret；前 3 条供人工核对。
# 为保证人工核对有实质内容，前 3 条从「有 slot3 且 ret 有效」的表中随机取，
# 其余 17 张从全部 954 张表中随机取（含短表，如实反映全貌）。
rng = random.Random(20261117)
def s3ret_of(t):
    for r in t['slot_ge3']:
        if r['slot'] == 3:
            return r['ret_label'] + ' (' + str(r['ret_bytes']) + ')'
    return 'none'
eligible = [t for t in per_table if t['slot3'] is not None and s3ret_of(t) != 'none']
head3 = rng.sample(eligible, 3)
rest_pool = [t for t in per_table if t not in head3]
sample20 = head3 + rng.sample(rest_pool, 17)
print('\n## 随机 20 张表（seed=20261117，前 3 条从 slot3 有效表抽取供人工核对）')
print('%-3s %-10s %-10s %-4s %-10s %-16s %-10s' %
      ('#', 'COL', 'vt起址', '槽数', 'slot3地址', 'slot3 ret', '标记'))
for i, t in enumerate(sample20):
    print('%-3d %-10s %-10s %-4d %-10s %-16s %-10s' %
          (i + 1, t['col'], t['vt'], t['nslots'], t['slot3'], s3ret_of(t),
           '人工核对' if i < 3 else ''))
    if i < 3:
        print('      前3槽: %s' % t['allslots'][:3])
# 输出完备 = 每个表行的 4 个字段均已打印（短表 slot3=None / ret=none 是合法实测值）
sample_lines_ok = (len(sample20) == 20 and
                   all(t['vt'] and t['nslots'] > 0 and
                       ('slot3' in t) and s3ret_of(t) is not None for t in sample20))
short_in_sample = sum(1 for t in sample20 if t['slot3'] is None)
ck('A4 随机 20 表输出完备（vt起址/槽数/slot3地址/slot3 ret 四字段均已打印）',
   sample_lines_ok,
   '%d 张，其中短表无 slot3=%d 张（合法实测值 None/none）' % (len(sample20), short_in_sample))

# 正控：构造已知槽地址 0x401950，必须在结果中且 ret 读取不报错
PC = 0x401950
pc_hits = []
for t in per_table:
    if hex(PC) in t['allslots']:
        idx = t['allslots'].index(hex(PC))
        pc_hits.append({'col': t['col'], 'vt': t['vt'], 'slot': idx})
pc_ret = ret_of(PC)
positive_control = {'addr': hex(PC), 'hits': pc_hits[:10], 'nhits': len(pc_hits), 'ret': pc_ret}
ck('PC 正控 0x401950 在结果中且 ret 读取无异常',
   len(pc_hits) > 0 and pc_ret['err'] is None and pc_ret['bytes'] is not None,
   '出现 %d 次, ret=%s, bytes=%s' % (len(pc_hits), pc_ret['label'], pc_ret['bytes']))
print('  正控明细（前10条）: %s' % pc_hits[:10])

# 5 行核心数字
print('\n## 5 行核心数字')
print('1. 主视图 mdisp==0 表数: %d' % len(main))
print('2. slot>=3 槽总数: %d' % ge3_actual)
print('3. slot3 本类自己实现表(N=1): %d；复用表(N>=2): %d' % (own_tables, shared_tables))
print('4. slot3 ret top1: %s (%d 次)' % (top1[0], top1[1]))
print('5. 正控 0x401950: ret=%s, bytes=%s, 出现=%d 次' %
      (pc_ret['label'], pc_ret['bytes'], len(pc_hits)))

out = {
    'meta': {
        'card': 'R210-A', 'mode': 'static-only', 'source': '_r209/q3.json',
        'main_view_rule': 'mdisp==0', 'slot3_definition': 'VT[c][3] (0-based, IUnknown occupies 0/1/2)',
        'cap_bytes_per_slot': 256, 'random_seed': 20261117,
        'assertions_total': NA, 'assertions': None, 'fails': fails,
    },
    'statistics': {
        'slot_ret_bucket': buckets_out,
        'slot3_share': share_out,
        'slot3_ret_dist': dict(slot3_ret),
        'q5_QI_ret_dist': dict(q5_ret),
    },
    'main_tables': per_table,
    'sample20': sample20,
    'positive_control': positive_control,
    'ret_cache': {hex(k): v for k, v in RET_CACHE.items()},
}
out['meta']['assertions'] = ('ALL PASS' if not fails else 'FAIL: ' + ','.join(fails))
json.dump(out, open(ROOT + '/_r210/a1.json', 'w'), indent=1)
print('\n== 断言汇总: %s (%d 项) ==' % (out['meta']['assertions'], NA))
print('== 产物: _r210/a1.json, _r210/a1.txt ==')
sys.stdout = sys.__stdout__
_fout.flush()
_fout.close()
