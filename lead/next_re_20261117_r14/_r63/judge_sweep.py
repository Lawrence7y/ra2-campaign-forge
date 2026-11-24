import io, os, json, collections

ROOT = r'D:\Project\ra2-campaign-forge'
p = os.path.join(ROOT, r'lead\next_re_20261117_r14\S08_KPROVED2\_audit\EVIDENCE\sweep.json')
print('file:', p.replace(ROOT + '\\', ''))
print('bytes:', os.path.getsize(p))
d = json.load(io.open(p, encoding='utf-8', errors='replace'))
print('keys:', list(d.keys()))
print()
for k in ('instructions', 'e8_sites'):
    print('%s = %r (int?) %s' % (k, d[k], isinstance(d[k], int)))
print()
for k in ('e8', 'installs'):
    v = d[k]
    print('=== %r : list len=%d' % (k, len(v)))
    print('   前 3 元素: %r' % (v[:3],))
    if v:
        print('   首元素类型: %s ; 长度(若可): %s'
              % (type(v[0]).__name__, len(v[0]) if hasattr(v[0], '__len__') else '-'))
        if isinstance(v[0], list):
            print('   首元素明细: %r' % (v[0],))
    print()

# 与 a2_sites 的 calls 对比：e8 是否就是同一批调用点
a2 = None
for dp, _, fs in os.walk(os.path.join(ROOT, 'lead')):
    if 'a2_sites.json' in fs:
        a2 = os.path.join(dp, 'a2_sites.json'); break
a2d = json.load(io.open(a2, encoding='utf-8', errors='replace'))
a2_sites = set()
for k, lst in a2d['calls'].items():
    a2_sites.update(lst)
print('a2_sites calls 调用点集合 = %d 个' % len(a2_sites))

e8 = d['e8']
if e8 and isinstance(e8[0], list) and len(e8[0]) == 2:
    e8_sites_set = set(x[0] for x in e8)
    print('e8 的 site 集合 = %d 个' % len(e8_sites_set))
    print('  与 a2_sites 调用点交集 = %d' % len(e8_sites_set & a2_sites))
    print('  e8 首元素 = %r' % (e8[0],))
